'''
Created on Dec 25, 2022

@author: lorenzo
'''

import sys, os, re
import signal
from dataclasses import dataclass
import subprocess as sp


@dataclass
class Entry:
    '''
    Holds information about ONE gcc warning/error in
    an unified fashion - no matter if gcc/clang or version
    '''
    file: str
    severity: str
    message: str
    lineno: int = None
    column: int = None
    
    def __str__(self):
        severity = self.severity.upper()
        if self.column is not None:
            return f"{severity}: line {self.lineno}, column {self.column}: {self.message}"
        elif self.lineno is not None:
            return f"{severity}: line {self.lineno}: {self.message}"
        else:
            return f"{severity}: {self.message}"


class Compiler:
    command = "gcc"
    all_warnings_command = "gcc -Wall"
    RE_GCC_WITH_COLUMN = re.compile('^(.*):(\\d+):(\\d+):.*?(warning|error):(.*)$')
    RE_GCC_WITHOUT_COLUMN = re.compile('^(.*):(\\d+):.*?(warning|error):(.*)$')
    RE_GCC_LINKER = re.compile('^(.*):(.*): (undefined reference)(.*)$')
    
    def __init__(self, options):
        self.options = options
        
        if "command" in options:
            Compiler.command = options["command"]
            
        if "all_warnings_command" in options:
            Compiler.all_warnings_command = options["all_warnings_command"]

        if options["debug_symbols"]:
            Compiler.command += " -g2"
            Compiler.all_warnings_command += " -g2"
        
        self.warnings = list()
        self.all_warnings = list()
        self.errors = list()
        
        self.source_file = options["filename"]
        exe_name = os.path.splitext(self.source_file)[0]
        self.exe_file = os.path.join(os.getcwd(), exe_name)
        self.compile()

    def _severity(self, message):
        if "error" in message:
            return "error"
        elif "warning" in message:
            return "warning"
        elif "undefined reference" in message:
            return "linker"
        else:
            return "unknown"
        
    def _entry_with_column(self, m):
        file_ = m.group(1).strip()
        lineno = m.group(2)
        column = m.group(3)
        severity = self._severity(m.group(4))
        message = m.group(5)
        return Entry(file_, severity, message, lineno, column)

    def _entry_without_column(self, m):
        file_ = m.group(1).strip()
        lineno = m.group(2)
        severity = self._severity(m.group(3))
        message = m.group(4)
        return Entry(file_, severity, message, lineno)
    
    def _entry_linker(self, m):
        file_ = m.group(1).strip()
        severity = self._severity(m.group(3))
        message = m.group(3) + m.group(4)
        return Entry(file_, severity, message)
    
    def _entry_from_line(self, line):
        line = line.rstrip()
        m = Compiler.RE_GCC_WITH_COLUMN.match(line)
        if m:
            return self._entry_with_column(m)
        else:
            m = Compiler.RE_GCC_WITHOUT_COLUMN.match(line)
            if m:
                return self._entry_without_column(m)
            else:
                m = Compiler.RE_GCC_LINKER.match(line)
                if m:
                    return self._entry_linker(m)
            
        return None
        
    def _invoke_compiler(self, command):
        result = sp.run(command.split() + ["-o", self.exe_file, self.source_file], stdout=sp.PIPE, stderr=sp.STDOUT, text=True)
        return result.returncode, result.stdout
        
    def compiled(self):
        return self.regular_return_code == 0
        
    def compile(self):
        self.regular_return_code, self.regular_output = self._invoke_compiler(self.command)
            
        for line in self.regular_output.splitlines():
            entry = self._entry_from_line(line)
            if entry is not None:
                if entry.severity == 'warning':
                    self.warnings.append(entry)
                if entry.severity == 'error' or entry.severity == "linker":
                    self.errors.append(entry)
                    
        if options["all_warnings"]:
            self.all_warnings_return_code, self.all_warnings_output = self._invoke_compiler(self.all_warnings_command)
            
            for line in self.all_warnings_output.splitlines():
                entry = self._entry_from_line(line)
                if entry is not None and entry.severity == "warning":
                    self.all_warnings.append(entry)
                    
    def write_report(self, filename):
        with open(filename, "w") as f:
            if self.compiled():
                print("--> COMPILATION SUCCESSFUL <--", file=f)
            else:
                print("--> COMPILATION FAILED <--", file=f)
            print("", file=f)
            
            print("------------------------", file=f)
            print(f"OUTPUT FOR '{self.command}'", file=f)
            print("------------------------\n", file=f)
            for e in self.errors:
                print(e, file=f)
    
            for w in self.warnings:
                print(w, file=f)
        
            if options["all_warnings"]:
                print("\n------------------------", file=f)
                print(f"OUTPUT FOR '{self.all_warnings_command}'", file=f)
                print("------------------------\n", file=f)
                
                for w in self.all_warnings:
                    print(w, file=f)
    

class Launcher:
    def __init__(self, options, exe_file):
        self.options = options
        self.exe_file = exe_file
        self.arguments = self.options["arguments"].split()
        self.command = [self.exe_file] + self.arguments
        
        self.execute()
        
    def success(self):
        return self.return_code == 0

    def execute(self):
        result = sp.run(self.command, stdout=sp.PIPE, stderr=sp.PIPE, text=True)
        
        self.return_code = result.returncode
        self.stdout = result.stdout
        self.stderr = result.stderr
        
    def write_report(self, filename):
        with open(filename, "w") as f:
            if self.success():
                print("--> EXECUTION SUCCESSFUL <--\n", file=f)
                
                print("------------------------", file=f)
                print(f"STANDARD OUTPUT", file=f)
                print("------------------------\n", file=f)
                print(self.stdout, file=f)
                
                print("------------------------", file=f)
                print(f"STANDARD ERROR", file=f)
                print("------------------------\n", file=f)
                print(self.stderr, file=f)
            else:
                print("--> EXECUTION FAILED <--\n", file=f)
                
                print(f"Return code: {self.return_code}", file=f)
                if self.return_code == -signal.SIGSEGV:
                    print(f"Error type: SEGMENTATION FAULT (SIGSEGV)", file=f)
                elif self.return_code == -signal.SIGABRT:
                    print(f"Error type: SIGABRT", file=f)
                    
                if options["valgrind"]:
                    command = f"{self.options['valgrind_path']} --log-file={self.options['valgrind_log_file']} {self.exe_file}".split()
                    sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE, text=True)
                    
                    print(f"\nThe output of valgrind has been printed to '{self.options['valgrind_log_file']}'", file=f)
                    

class Analyser:
    def __init__(self):
        pass


class Input(dict):
    required = ["filename"]
    booleans = ["all_warnings"]
    defaults = {
        "all_warnings" : True,
        "debug_symbols" : True,
        "arguments" : "",
        "valgrind" : True,
        "valgrind_path" : "valgrind",
        "valgrind_log_file" : "valgrind_log.txt"
    }
    
    def __init__(self, input_file):
        self.update(Input.defaults)
        
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
    compiler.write_report("compilation_report.txt")
    
    if compiler.compiled():
        launcher = Launcher(options, compiler.exe_file)
        launcher.write_report("execution_report.txt")
    