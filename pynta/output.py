'''
Created on Jan 1, 2023

@author: lorenzo
'''

import os, sys

class CheckOutput():
    def __init__(self, options, stdout, stderr):
        self.options = options
        self.stdout = stdout
        self.stderr = stderr
        
        self.check()
        
    def check(self):
        for output in self.options["output"]:
            if output["type"] == "file":
                if not os.path.isfile(output["name"]):
                    pass
            else:
                if output["type"] == "stdout":
                    to_check = self.stdout
                else: to_check = self.stderr
                
                if "empty" in output and output["empty"]:
                    if len(to_check) > 0:
                        print(f"Output {output['type']} is not empty as it should be", file=sys.stderr)
                        