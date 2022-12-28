'''
Created on Dec 25, 2022

@author: lorenzo
'''

import sys
import tomli

from compiler import Compiler
from launcher import Launcher


class Analyser:
    def __init__(self):
        pass


class Input(dict):
    required = ["filename"]
    
    defaults = {
        "compilation" : {
            "command" : "gcc",
            "all_warnings" : True,
            "all_warnings_command" : "gcc -Wall"
        },
        "execution" : {
            "arguments" : "",
        },
        "valgrind" : {
            "enable" : True,
            "command" : "valgrind --leak-check=full --show-leak-kinds=all",
            "xml_file" : "valgrind_log.xml"
        }
        
    }
    
    def __init__(self, input_file):
        self.update(Input.defaults)
        
        self.input_file = input_file
        
        with open(input_file, "rb") as f:
            options = tomli.load(f)
            self.update(options)
        
        self._check()
        
    def _check(self):
        for key in Input.required:
            if key not in self:
                print(f"Required key '{key}' not found in '{self.input_file}'", file=sys.stderr)
                exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage is {sys.argv[0]} input_file")
        exit(1)
        
    options = Input(sys.argv[1])
    compiler = Compiler(options)
    compiler.write_report("compilation_report.txt")
    
    print(compiler.summary())
    
    if compiler.compiled():
        launcher = Launcher(options, compiler.exe_file)
        launcher.write_report("execution_report.txt")
        
        print(launcher.summary())
    