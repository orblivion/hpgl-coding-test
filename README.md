# Programming test for the Inkscape Python Developer contract role (2023 Q1)

This repository contains the instructions to perform the programming test of the role that the Inkscape project is currently filling.

Note that this is not the file format that will be implemented during the contract. The HPGL file format is already supported by Inkscape - the code submitted by the candidates will be used solely for the purpose of selecting the candidates. 

This readme contains:
 * the task instructions,
 * instructions how to run the provided unit tests.

This repository provides the following starting points:
 * boilerplate code for an Inkscape import extension for HPGL files
 * unit test files,
 * and the unit tests themselves.

## Task description

Your task is to implement two commands from the HP-GL plotter language. The user guide of this language is given here: http://www.hp.com/ctg/Manual/bpl13211.pdf

The general syntax of HPGL files is provided on page 9-10. The two commands that should be supported are PD (page 123) and PU (page 138), which is sufficient to read simple line diagrams. All other commands should be ignored by the parser. If the syntax of the file is invalid, raise an `inkex.AbortExtension`.

The unit tests evaluate all paths in the output file together; it does not matter whether paths are split into subpaths (i.e. after each PU command) or not. The style of the path must contain a black stroke and a non-zero stroke width. The coordinate transformation between HPGL plotter units (plu) and SVG units is handled by the parent layer that already exists in the boilerplate code; your paths may directly copy the coordinates of the HPGL file.

For example, the HPGL string

`IN; SP1; PU 10,10; PD 10, 30; PU 20, 30 PD 20, 10, 10, 10;`

translates to 

`M 10 10 L 10 30 M 20 30 L 20 10 L 10 10`

or equivalently (a lot of options are possible and valid)

`m 10 10 v 20 m 10 0 v -20 h -10`

which renders as a "u" shaped path.

It is strongly recommended to use `pyparsing>=3.0.0` (or another parsing library that you're comfortable with) for this assignment, even though it might seem overkill for this simple problem - but it shows us that you can work with parsing libraries.

The boilerplate code uses Inkscape's python library `inkex` (https://inkscape.gitlab.io/extensions/documentation/). The library will be needed to create and append `PathElements` to the document, setting the style and path data, and raising an error if the provided file is invalid.

## Deadline

The assignment must be submitted by Jan 23, 23:59 UTC.

## Unit tests / Development setup

Please create a **private fork** of this repository.

TODO (install inkex master from sources, run unit tests)

## Submission

Please invite Gitlab user @joneuhauser into your private fork with Reporter access permissions.

Respond to the email that you received from the Hiring team by providing the link to your repository as well as the commit hash that contains your submission. 

## Evaluation criteria

* Your code must pass the provided unit tests. If any unit tests fail, please explain these failures along with your submission via email.
* Your code should be adequately documented.
* Use a consistent coding style. Use of an automatted code formatting tool is encouraged.
* The history of the submitted commit hash should be clean; and the commit messages should adhere to standard practice.
