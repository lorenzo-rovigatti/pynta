'''
Created on Dec 27, 2022

@author: lorenzo
'''

from dataclasses import dataclass
import os, re
import subprocess as sp

from utils import print_log_section


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
    RE_GCC_WITH_COLUMN = re.compile('^(.*):(\\d+):(\\d+):.*?(warning|error):(.*)$')
    RE_GCC_WITHOUT_COLUMN = re.compile('^(.*):(\\d+):.*?(warning|error):(.*)$')
    RE_GCC_LINKER = re.compile('^(.*):(.*): (undefined reference)(.*)$')
    
    def __init__(self, options):
        self.options = options
        
        self.command = self.options["compilation"]["command"]
        self.all_warnings_command = self.options["compilation"]["all_warnings_command"]
            
        if self.options["valgrind"]["enable"]:
            self.command += " -g2"
            self.all_warnings_command += " -g2"
        
        self.warnings = list()
        self.all_warnings = list()
        self.errors = list()
        
        self.source_file = options["filename"]
        exe_name = os.path.splitext(os.path.basename(self.source_file))[0]
        self.exe_file = os.path.join(os.getcwd(), exe_name)
        
        if not os.path.isfile(self.source_file):
            raise Exception(f"Source file '{self.source_file}' does not exist or it is not accessible")
        
        self.compile()
        
    def summary(self):
        lines = []
        
        if self.compiled():
            lines.append(u"Compilation: OK ({} warnings)".format(len(self.warnings)))
        else:
            lines.append("Compilation: FAILED ({} error(s))".format(len(self.errors)))
            
        if self.all_warnings:
            lines.append("\tCompiling with all warnings enabled found {} warnings".format(len(self.all_warnings)))
            
        return "\n".join(lines)

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
                    
        if self.options["compilation"]["all_warnings"]:
            self.all_warnings_return_code, self.all_warnings_output = self._invoke_compiler(self.all_warnings_command)
            
            for line in self.all_warnings_output.splitlines():
                entry = self._entry_from_line(line)
                if entry is not None and entry.severity == "warning":
                    self.all_warnings.append(entry)
                    
    def write_report(self):
        with open(self.options["compilation"]["report_path"], "w") as f:
            if self.compiled():
                print("--> COMPILATION SUCCESSFUL <--", file=f)
            else:
                print("--> COMPILATION FAILED <--", file=f)
            print("", file=f)
            
            print_log_section(f"OUTPUT FOR '{self.command}'", f)
            
            for e in self.errors:
                print(e, file=f)
    
            for w in self.warnings:
                print(w, file=f)
        
            if self.options["compilation"]["all_warnings"]:
                print_log_section(f"OUTPUT FOR '{self.all_warnings_command}'", f)
                
                for w in self.all_warnings:
                    print(w, file=f)
                    
