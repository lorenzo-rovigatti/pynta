'''
Created on Dec 25, 2022

@author: lorenzo
'''

import sys, os, re
from dataclasses import dataclass
import subprocess as sp


@dataclass
class Entry:
    '''
    Holds information about ONE gcc warning/error in
    an unified fashion - no matter if gcc/clang or version
    '''
    file: str
    lineno: int
    severity: str
    message: str
    column: int = None
    
    def __str__(self):
        severity = self.severity.upper()
        if self.column is not None:
            return f"{severity}: line {self.lineno}, column {self.column}: {self.message}"
        else:
            return f"{severity}: line {self.lineno}: {self.message}"


class Compiler:
    command = "gcc"
    all_warnings_command = "gcc -Wall"
    RE_GCC_WITH_COLUMN = re.compile('^(.*):(\\d+):(\\d+):.*?(warning|error):(.*)$')
    RE_GCC_WITHOUT_COLUMN = re.compile('^(.*):(\\d+):.*?(warning|error):(.*)$')
    
    def __init__(self, options):
        self.options = options
        
        if "command" in options:
            Compiler.command = options["command"]
            
        if "all_warnings_command" in options:
            Compiler.all_warnings_command = options["all_warnings_command"]
        
        self.warnings = list()
        self.all_warnings = list()
        self.errors = list()
        
        self.source_file = options["filename"]
        self.exe_file = os.path.splitext(self.source_file)[0]
        self.compile()
        

    def _severity(self, message):
        if "error" in message:
            return "error"
        elif "warning" in message:
            return "warning"
        else:
            return "unknown"
        
    def _entry_with_column(self, m):
        file_ = m.group(1).strip()
        lineno = m.group(2)
        column = m.group(3)
        severity = self._severity(m.group(4))
        message = m.group(5)
        return Entry(file_, lineno, severity, message, column)

    def _entry_without_column(self, m):
        file_ = m.group(1).strip()
        lineno = m.group(2)
        severity = self._severity(m.group(3))
        message = m.group(4)
        return Entry(file_, lineno, severity, message)
    
    def _entry_from_line(self, line):
        line = line.rstrip()
        m = Compiler.RE_GCC_WITH_COLUMN.match(line)
        if m:
            return self._entry_with_column(m)
        else:
            m = Compiler.RE_GCC_WITHOUT_COLUMN.match(line)
            if m:
                return self._entry_without_column(m)
            
        return None
        
    def _compiler_output(self, command):
        try:
            result = sp.run(command.split() + ["-o", self.exe_file, self.source_file], stdout=sp.PIPE, stderr=sp.STDOUT, text=True)
        except sp.CalledProcessError as e:
            print(e.stdout)
            return False
        else:
            return result.stdout
        
    def compile(self):
        self.regular_output = self._compiler_output(self.command)
            
        for line in self.regular_output.splitlines():
            entry = self._entry_from_line(line)
            if entry is not None:
                if entry.severity == 'warning':
                    self.warnings.append(entry)
                if entry.severity == 'error':
                    self.errors.append(entry)
                    
        self.all_warnings_output = self._compiler_output(self.all_warnings_command)
        
        for line in self.all_warnings_output.splitlines():
            entry = self._entry_from_line(line)
            if entry is not None:
                self.all_warnings.append(entry)
    

class FileAnalyser:
    def __init__(self):
        pass


class Input(dict):
    required = ["filename"]
    booleans = ["all_warnings"]
    
    def __init__(self, input_file):
        self.input_file = input_file
        
        with open(input_file) as f:
            for line in f.readlines():
                line = line.strip()
                if line[0] != '#' and len(line) > 0:
                    spl = [s.strip() for s in line.split("=", 1)]
                    if len(spl) == 2:
                        self[spl[0]] = spl[1]
                    else:
                        print(f"Malformed line '{line}'", file=sys.stderr)
                        
        self._check()
        
    def __setitem__(self, key, value):
        if key in self.booleans and isinstance(value, str):
            cap_value = value.capitalize()
            if cap_value == "True":
                value = True
            elif cap_value == "False":
                value = False
            else:
                print(f"Invalid boolean value '{value}' set for key '{key}'", file=sys.stderr)
                return
                
        super().__setitem__(key, value)
                        
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
    
    with open("compilation_results.txt", "w") as f:
        print("------------------------", file=f)
        print(f"AS COMPILED WITH '{compiler.command}'", file=f)
        print("------------------------\n", file=f)
        for e in compiler.errors:
            print(e, file=f)

        for w in compiler.warnings:
            print(w, file=f)
    
        if "all_warnings" in options and options["all_warnings"]:
            print("\n------------------------", file=f)
            print(f"AS COMPILED WITH '{compiler.all_warnings_command}'", file=f)
            print("------------------------\n", file=f)
            
            for w in compiler.all_warnings:
                print(w, file=f)
    