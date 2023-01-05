'''
Created on Jan 1, 2023

@author: lorenzo
'''

import os

from utils import print_log_section


class Output():

    def __init__(self, options):
        self.options = options
        self.type = options["type"]
        self.errors = []
        
        if options["type"] == "file":
            self.name = self.options["name"]
            if not os.path.isfile(self.options["name"]):
                self.errors.append(f"File '{self.options['name']}' not present")
            else:
                with open(self.options['name'], "r") as f:
                    self.options["output"] = f.read()
        else:
            self.name = self.type
            
    def has_errors(self):
        return len(self.errors) > 0
        
    def check(self):
        if "empty" in self.options and self.options["empty"]:
            if len(self.options["output"]) > 0:
                self.errors.append(f"Not empty as it should be")
                
        if "equal_to" in self.options:
            if not os.path.isfile(self.options["equal_to"]):
                self.errors.append(f"'equal_to' file '{self.options['equal_to']}' not found")
            else:
                with open(self.options['equal_to'])  as f:
                    equal_to_content = f.read()
                    
                if self.options["output"] != equal_to_content:
                    self.errors.append(f"Not equal to the content of the '{self.options['equal_to']}' file")
        

class CheckOutput():

    def __init__(self, options, stdout, stderr):
        self.options = options
        self.outputs = []
        for output in options["output"]:
            if output["type"] == "stdout":
                output["output"] = stdout
            elif output["type"] == "stderr":
                output["output"] = stderr
            
            self.outputs.append(Output(output))
        
        self.check()
        
    def summary(self):
        lines = []
        
        for output in self.outputs:
            line = f"Output {output.name}: "
            if output.has_errors():
                line += f"FAILED ({len(output.errors)} errors)"
            else:
                line += "OK"
            lines.append(line)
            
        return "\n".join(lines)
    
    def write_report(self):
        with open(self.options["output_report_path"], "w") as f:
            for output in self.outputs:
                print_log_section(f"OUTPUT {output.name}", f)
                
                if output.has_errors():
                    for error in output.errors:
                        print(error, file=f)
                else:
                    print("OK", file=f)
        
    def check(self):
        for output in self.outputs:
            output.check()
