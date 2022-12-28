# pynta

pynta is a Python library that can be used to evaluate the compilation, execution and (in the future) the quality and adherence to specific guidelines of C programs written by students.

pynta is not an automatic grader, but rather a tool that can be used to quickly analyse a (not too complicated) C code so as to provide information to the marker.

## Usage

pynta expects a single argument: the path to an input file formatted with [https://github.com/toml-lang/toml](TOML) which specifies how the analysis should be carried out.

## The input file

An example input file containing all the supported options can be found in `examples/full` folder.

## Acknowledgements

* The valgrind output parser has been adapted from [https://github.com/bcoconni/ValgrindCI](ValgrindCI)
