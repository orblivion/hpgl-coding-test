#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) 2022 Jonathan Neuhauser (jonathan.neuhauser@outlook.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

"""Parser for HP/GL Documents"""

import pyparsing as pp

from inkex.base import SvgOutputMixin
import inkex
from inkex.localization import inkex_gettext as _

# Comments will refer to a page number in the HP-GL plotter manual found here:
# http://www.hp.com/ctg/Manual/bpl13211.pdf
#
# The goal of this parser is to handle Pen Up (PU) and Pen Down (PD) commands
# and ignore the other commands. However, some of the other commands have
# special parsing rules that we need to account for. We need to pay attention
# to them in order to ignore them properly, paradoxically.
#
# PD and PU are allowed in LOST mode so we don't need to worry about that.
#
# Despite whitespace being cited in specific parts of the spec, the test data
# appear to allow for it between tokens. Thus, we will skip (and split tokens)
# on whitespace (which is the default for pyparising) except for select areas
# that are more intricate.

##############
# Some basics
##############

all_chars = {chr(x) for x in range(256)}  # TODO - utf-8?
not_semicolon = pp.Char(all_chars - set(";"))

# Page 9: "Most HP-GL/2 commands are terminated by a semicolon or the first
# letter of the next mnemonic, a white space, or a tab" (with exceptions, which
# we will account for). Again, test data seem to indicate that spaces are used
# generally to split tokens, which pyparsing does by default, so we will only
# concern ourselves with semicolons.
#
# In most commands, we'll make command_terminator optional, thereby allowing
# the first letter of the next mnemonic to serve as a terminator. If some other
# character shows up instead, parsing will fail on the next command.
command_terminator = pp.Literal(";")

############
# Mnemonics
############

# HP-GL manual Page 9: "The mnemonic can be uppercase or lowercase". This
# wording seems to preclude a mixture of case within one mnemonic, so we only
# accept both upper or both lower.
mnemonic = lambda m: pp.Literal(m.lower()) | pp.Literal(m.upper())
mn_pen_up = mnemonic("PU")
mn_pen_down = mnemonic("PD")
mn_polyline_encoded = mnemonic("PE")
mn_symbol_mode = mnemonic("SM")
mn_label = mnemonic("LB")
mn_define_label_terminator = mnemonic("DT")
mn_other = pp.Word(pp.alphas.upper(), exact=2) | pp.Word(pp.alphas.lower(), exact=2)

#####################
# Numeric Parameters
#####################

# We want unsigned integer or decimal. The options available in `pp.common`
# don't quite offer this.
numeric_parameter = pp.Combine(
    pp.Word(pp.nums) + pp.Opt(pp.Literal(".") + pp.Word(pp.nums))
)

# Page 9: "When you use parameters, you must separate them with a comma or
# space, or in the case of a numeric parameter, with a + or - sign"
numeric_separator = pp.Char(",+-")

# Normal numeric parameter pairs. The first pair doesn't begin with a
# separator, but every other one does. We make numeric_separator optional to
# allow for whitespace, which is also a valid separator. Subtle point: even
# though the  numeric_separator is optional, it is impossible to accidentally
# parse two adjacent numeric_parameter out of a single number, given how
# numeric_parameter is defined.

first_numeric_parameter_pair = (
    numeric_parameter + pp.Opt(numeric_separator) + numeric_parameter
)
next_numeric_parameter_pair = (
    pp.Opt(numeric_separator)
    + numeric_parameter
    + pp.Opt(numeric_separator)
    + numeric_parameter
)

# Page 125 (PD command) and Page 139 (PU command): "If an odd number of
# coordinates is specified (an X coordinate without a corresponding Y
# coordinate), the printer ignores the last unmatched coordinate"
unpaired_first_numeric_parameter = numeric_parameter
unpaired_next_numeric_parameter = pp.Opt(numeric_separator) + numeric_parameter

# Zero or more "normal" pairs, followed either by a "last" pair, or an extra
# unpaired parameter. Or, maybe no parameters at all.
numeric_parameter_pair_list = (
    (
        pp.Group(
            first_numeric_parameter_pair + pp.ZeroOrMore(next_numeric_parameter_pair)
        )
        + pp.Opt(unpaired_next_numeric_parameter)
    )
    | pp.Opt(unpaired_first_numeric_parameter)
) + ~numeric_separator

###############
# PD, Pen Down
###############

# Page 123
# PD X,Y[,...;]
# PD [;]

cmd_pen_down = mn_pen_down + numeric_parameter_pair_list + pp.Opt(command_terminator)

#############
# PU, Pen Up
#############

# Page 138
# PU X,Y[,...;]
# PU [;]

cmd_pen_up = mn_pen_up + numeric_parameter_pair_list + pp.Opt(command_terminator)

#############################
# Skip: PE, Polyline Encoded
#############################

# In order to ignore PE commands, we need to parse it properly, though we
# ignore as much as we can.

# Page 126 "Also, you must use a semicolon to terminate PE." Furthermore, a
# semicolon is not a valid character in any parameter of PE. This makes it
# pretty straightforward to skip.

cmd_polyline_encoded = (
    mn_polyline_encoded + pp.ZeroOrMore(not_semicolon) + command_terminator
)

########################
# Skip: SM, Symbol Mode
########################

# In order to ignore SM commands, we need to parse it properly, though we
# ignore as much as we can.

# Page 231
#
# As written, this spec creates an undetermined state. We have two forms:
#
# SM character [;]
# SM [;]
#
# How would, for example, "SMP" be interpreted, given that "P" is the first
# letter of some mnemonics? If we assume the first form, "P" is the character
# parameter. If we assume the second form, "P" is the first letter of the
# second mnemonic.
#
# Surely the first form is the correct one, otherwise we could never have a
# character set to "P", and "P" is in the valid character range. It would also
# be complicated to have different parsing rules for different letters. Given
# the imprecise tendency in this document, *intentionally* complicated parsing
# rules seems unlikely.
#
# The only other possibilty is to look ahead to see if it seems like it really
# is a mnemonic and well formatted command. But this is even more complicated.
#
# That said, it's not impossible that people (perhaps 3rd parties) who have
# written file *generators* didn't consider these factors, and wrote SM
# commands in the second form with omitted terminator. In such a case, we may
# need to resort to these sort of awful complicated parsing rules some day.
#
# We will for now assume that the terminator is required in the second form,
# making the actual two valid forms:
#
# SM character [;]
# SM;
#
# The valid values for `character` do not include colon space or tab, so we
# don't need to leave_whitespace here.

sm_valid_characters = {
    chr(x) for x in {161, 254}.union(range(33, 59)).union(range(60, 126))
}

cmd_symbol_mode = mn_symbol_mode + (
    (pp.Char(sm_valid_characters) + pp.Opt(command_terminator)) | command_terminator
)

####################################
# DT, Define Label Terminator
####################################

# Unfortunately we cannot skip DT commands because it gives us updates to the
# label terminator which will affect the skipping of LB commands.

# Page 288
#
# DT label terminator [,mode;]
# DT;
#
# Unlike SM, the semicolon appears to be required in case of omitted parameter.
# But oddly, if a "label terminator" is given, the semicolon is expected *if
# and only if* a mode is given. All the same, we check for it in any case since
# it is plausibly a mistake, given the overall level of precision in this
# document.

label_terminator_chars = all_chars - {chr(x) for x in [0, 5, 27, 59]}
label_terminator = pp.Char(label_terminator_chars)

# Page 9: "When you use parameters, you must separate them with a comma or
# space, or in the case of a numeric parameter, with a + or - sign". In this
# case, one parameter is numeric and the other is not. Best to allow + and -
# probably, since there is no ambiguity: the only possible alternate characters
# are ";" or the first letter of a mnemonic, none of which are separator
# characters. Also note that the label_terminator might be a space, so we
# leave_whitespace for everything up to that point.
cmd_define_label_terminator = (
    (
        pp.Opt(pp.White()) + mn_define_label_terminator + label_terminator
    ).leave_whitespace()
    + pp.Opt(pp.Opt(numeric_separator) + pp.Char("01"))
    + pp.Opt(command_terminator)
) | (mn_define_label_terminator + command_terminator)

##################
# Skip: LB, Label
##################

# In order to ignore LB commands, we need to parse it properly, though we
# ignore as much as we can.

# Page 303
#
# The format given here is:
#
# LB text ... text label terminator
#
# "LB uses a user-defined terminator" (Page 9). This presumably refers to the
# label terminator, and yet the examples on Page 303 include a semicolon after
# the label terminator. Since the rule is ambiguous, assume the broadest case,
# an optional semicolon:
#
# LB text ... text label terminator [;]


def cmd_label(label_terminator):
    # The label_terminator might be a space, so we leave_whitespace for
    # everything up to that point.
    return (
        mn_label
        + pp.ZeroOrMore(pp.Word(all_chars - set(label_terminator)))
        + pp.Literal(label_terminator)
    ).leave_whitespace() + pp.Opt(command_terminator)


###############################################
# Skip: Other Commands With Numeric Parameters
###############################################

# In order to ignore the remaining commands, we need to parse them properly,
# though we ignore as much as we can.

# The remaining commands have numeric parameters. We won't even bother to
# validate the format within. Because the valid characters are limited, and
# can't be confused with the next mnemonic, we can unambiguously determine the
# end of the command.
cmd_other = (
    mn_other
    + pp.ZeroOrMore(numeric_separator | numeric_parameter)
    + pp.Opt(command_terminator)
)


###########
# Commands
###########


def command(label_terminator):
    # Generalizing into one parser for a command. We need to pass in the
    # label_terminator because it affects parsing LB commands.
    return (
        cmd_pen_up
        | cmd_pen_down
        | cmd_polyline_encoded
        | cmd_symbol_mode
        | cmd_label(label_terminator)
        | cmd_define_label_terminator
        | cmd_other
    )


##########################
# Parsing the entire file
##########################

# Make the name similar to but distinct from ParseException
class HPGLParseException(Exception):
    pass


def extract_param_pairs(cmd):
    """Helper function for extracting and preparing pairs of params from a parsed command"""

    # Find the grouped params within the parse result
    parsed_params = []
    for token in cmd:
        if isinstance(token, pp.ParseResults):
            parsed_params = list(token)

    # Filter out any non-numeric tokens that were parsed, convert them to ints
    int_params = []
    for param in parsed_params:
        # For lack of a convenient "does this match?" function
        try:
            numeric_parameter.parse_string(param)
        except pp.ParseException:
            pass
        else:
            # TODO - clamp the numbers per the spec. also confirm that it's not a float
            int_params.append(int(param))

    # Put them in pairs
    param_pairs = []
    while int_params:
        x, y, *int_params = int_params
        param_pairs.append((x, y))

    return param_pairs


# We need to parse one command at a time because label terminator (defined in
# DT) affects parsing of LB. So long as we're doing this, we will only yield
# the commands that we care about: PD and PU.
def parse_hp_gl(document):
    # The default terminator is the ASCII end-of-text character ETX (decimal
    # code 03). Page 247.
    label_terminator = chr(3)

    this_ptr = 0
    this_command = None

    # Cut off trailing whitespace so it's easier to determine the end of the file.
    document = document.strip()

    while this_ptr < len(document):
        command_parser = command(label_terminator)

        try:
            this_command, first, next_ptr_offset = next(
                command_parser.scan_string(document[this_ptr:])
            )
        except StopIteration:
            raise HPGLParseException(
                "Failed to parse from this part of the document",
                # Give at least part of the document in the error message so we
                # know what we failed to parse.
                document[this_ptr : this_ptr + 20],
            )

        if first != 0:
            # We want to use scan_string to parse one command at the given
            # position in the document, see where parsing stopped, and scan
            # again for the next command. However, if scan_string doesn't find
            # a match from the beginning of the string, it'll look for it
            # further in the string. We only want it to match from the very
            # beginning, so we throw an exception if it did not.
            raise HPGLParseException(
                "Parsing did not begin at the expected place in the document",
                # Give at least part of the document in the error message so we
                # know what we failed to parse.
                document[this_ptr : this_ptr + 20],
                "Parsing began after %d characters" % first,
            )

        # Yield the commands we care about
        if this_command[0] in (mn_pen_up, mn_pen_down):
            param_pairs = extract_param_pairs(this_command)
            yield this_command[0], param_pairs

        # Handle updating the label terminator
        if len(this_command) == 2 and this_command[0] == mn_define_label_terminator:
            label_terminator = this_command[1]
        if (
            len(this_command) == 3
            and this_command[0].strip() == ""
            and this_command[1] == mn_define_label_terminator
        ):
            label_terminator = this_command[2]

        this_ptr = this_ptr + next_ptr_offset

    # It seems safe to regard a zero-command file as invalid. Importing it into
    # Inkscape would be equivalent to creating a new file anyway.
    if this_command == None:
        raise HPGLParseException("Empty file")

    # The parsing rules to allow for:
    #
    # 1) optional semicolon, space or tab after some commands
    # 2) required semicolons after some commands
    # 3) required semicolons on the last command
    #   (Page 9: "The last command prior to exiting HP-GL/2 mode must be
    #   terminated with a semicolon")
    #
    # Implementing all three of these with pyparsing rules alone would be very
    # tricky, if possible at all. Instead, we use pyparsing for 1) and 2) as
    # part of the individual command definitions, and just check for 3) right
    # here after the parsing is done.
    if ";" not in this_command[-1]:
        raise HPGLParseException("File did not end with a semicolon")


class HpglInput(inkex.InputExtension):
    """InputExtension to import HP/GL2 documents."""

    def add_arguments(self, pars):
        pass

    def load(self, stream):
        """Load the document, making sure that we operate on a decoded string"""
        res = stream.read()
        if isinstance(res, str):
            return res
        return res.decode()

    def effect(self):
        # interpret HPGL data

        # Create an 8x11 inch document in mm units.
        doc: inkex.SvgDocumentElement = SvgOutputMixin.get_template(
            width=8 * 25.4,
            height=11 * 25.4,
            unit="mm",
        )

        # Add a root layer that takes care of transforming the HPGL coordinate
        # system to SVG coordinates.
        layer = doc.getroot().add(inkex.Layer())

        plu_to_svg = inkex.Transform(
            scale=(
                0.025,
                -0.025,
            ),
            translate=(0, 11 * 25.4),
        )
        layer.transform = plu_to_svg

        self.parse_document(self.document, layer)

        # deliver document to inkscape
        self.document = doc

    def parse_document(self, string, layer):
        """Convert a document stored in string to SVG elements."""

        # TODO: Add your code here
        # parse the document, which is provided as utf8-decoded string in self.document,
        # i.e. create path elements (inkex.PathElement), set their .path, and .style,
        # and append them to "layer"

        inkex.errormsg("I still have work to do.")


if __name__ == "__main__":
    HpglInput().run()
