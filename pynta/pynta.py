'''
Created on Dec 25, 2022

@author: lorenzo
'''

import sys, os
import tomli

from compiler import Compiler
from launcher import Launcher
from output import CheckOutput


class Analyser:
    def __init__(self):
        pass


class Input(dict):
    required = ["filename"]
    
    defaults = {
        "compilation" : {
            "command" : "gcc",
            "command_post" : "",
            "all_warnings" : True,
            "all_warnings_command" : "gcc -Wall",
            "report_path" : "compilation_report.txt"
        },
        "execution" : {
            "arguments" : "",
            "stdin" : None,
            "report_path" : "execution_report.txt",
            "expected_return_code" : 0
        },
        "valgrind" : {
            "enable" : True,
            "command" : "valgrind --leak-check=full --show-leak-kinds=all",
            "xml_file" : "valgrind_log.xml"
        },
        "output_report_path" : "output_report.txt",
        "working_dir" : "."
        
    }
    
    def __init__(self, input_file):
        self.update(Input.defaults)
        
        self.input_file = input_file
        
        with open(input_file, "rb") as f:
            try:
                options = tomli.load(f)
            except tomli.TOMLDecodeError as e:
                print(f"Cannot parse input file {input_file}: {e}", file=sys.stderr)
                exit(1)
            self.update(options)
            
        self["filename"] = os.path.abspath(self["filename"])
        
        self._check()
        
    def _check(self):
        for key in Input.required:
            if key not in self:
                print(f"Required key '{key}' not found in '{self.input_file}'", file=sys.stderr)
                exit(1)
                
        for output in self["output"]:
            if output["type"] not in ["stdout", "stderr", "file"]:
                print(f"Invalid output type '{output['type']}'", file=sys.stderr)
                exit(1)
            if output["type"] == "file":
                if "name" not in output:
                    print("The 'name' option is mandatory for output files", file=sys.stderr)
                    exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage is {sys.argv[0]} input_file")
        exit(1)
        
    options = Input(sys.argv[1])
    
    if not os.path.isdir(options["working_dir"]):
        # TODO: add an info log entry about creating working_dir
        os.mkdir(options["working_dir"])
        
    os.chdir(options["working_dir"])
    
    compiler = Compiler(options)
    compiler.write_report()
    print(compiler.summary())
    
    if compiler.compiled():
        launcher = Launcher(options, compiler.exe_file)
        launcher.write_report()
        print(launcher.summary())
        
        check_output = CheckOutput(options, launcher.stdout, launcher.stderr)
        check_output.write_report()
        print(check_output.summary())
    