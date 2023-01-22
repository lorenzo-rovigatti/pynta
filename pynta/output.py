'''
Created on Jan 1, 2023

@author: lorenzo
'''

import os, sys

from utils import print_log_section


class Column():
    def __init__(self, col_options):
        self.casting_function = None
        self.datatype = None
        self.decimal_positions = None
        self.max_length = None
        
        if "datatype" in col_options:
            self.datatype = col_options["datatype"]
            if self.datatype == "int":
                self.casting_function = int
            elif self.datatype == "float":
                self.casting_function = float
                if "decimal_positions" in col_options:
                    try:
                        self.decimal_positions = int(col_options["decimal_positions"])
                    except ValueError:
                        print(f"Invalid decimal_positions value '{col_options['decimal_positions']}'", file=sys.stderr)
                        exit(1)
            elif self.datatype == "string":
                self.casting_function = str
            else:
                print(f"Invalid column datatype '{col_options['datatype']}'", file=sys.stderr)
                exit(1)
                
        if "max_length" in col_options:
            try:
                self.max_length = int(col_options["max_length"])
            except ValueError:
                print(f"Invalid max_length value '{col_options['max_length']}'", file=sys.stderr)
                exit(1)
            
    def check_value(self, v):
        errors = []
        
        if self.casting_function != None:
            try:
                self.casting_function(v)
            except ValueError:
                errors.append(f"'{v}' cannot be cast to {self.datatype}")
                
        if self.decimal_positions != None:
            decimal = v.split(".")[1]
            if len(decimal) != self.decimal_positions:
                errors.append(f"'{v}' has the wrong number of decimal positions ({len(decimal)} instead of {self.decimal_positions})")
                
        if self.max_length != None:
            if len(v) > self.max_length:
                errors.append(f"'{v}' length exceeds max_length {self.max_length}")
                
        return errors
    
    
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
        # this happens when this Output is linked to a file that does not exist
        if "options" not in self.options:
            return
        
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
                    
        if "columns" in self.options:
            columns = [Column(col_option) for col_option in self.options["columns"]]
            for nl, line in enumerate(self.options["output"].split("\n")):
                spl = line.split()
                if len(spl) > 0:
                    if len(spl) != len(columns):
                        self.errors.append(f"Line n. {nl + 1}: {len(spl)} field(s) found instead of {len(columns)}")
                        
                    for i, v in enumerate(spl):
                        for error in columns[i].check_value(v):
                            self.errors.append(f"Line n. {nl + 1}, column n. {i + 1}: {error}")
            
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
                line += f"FAILED ({len(output.errors)} error(s))"
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
