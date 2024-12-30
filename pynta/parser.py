'''
Created on Dec 30, 2024

@author: lorenzo
'''

import os, re
from utils import print_log_section

class Parser:
    def __init__(self, options):
        self.options = options

        self.source_file = options["filename"]
        if not os.path.isfile(self.source_file):
            raise Exception(f"Source file '{self.source_file}' does not exist or it is not accessible")

        self._source = open(self.source_file, "r").read()
        self._clean_source()
        self._functions = self._extract_functions()
        self.errors = []

        for user_function in self.options["parsing"]["functions"]:
            name = user_function["name"]
            if name in self._functions:
                if user_function["return_type"] != self._functions[name]["return_type"]:
                    self.errors.append(f"Function {name}: return type {self._functions[name]['return_type']} != {user_function['return_type']}")

                # now we check that the function takes all the required arguments
                func_args = self._functions[name]["arg_types"][:]
                for req_arg in user_function["arg_types"]:
                    if req_arg in func_args:
                        func_args.remove(req_arg)
                    else:
                        self.errors.append(f"Function {name}: missing argument of type {req_arg}")
            else:
                self.errors.append(f"Function {name} not found")

    def summary(self):
        N_errors = len(self.errors)

        if N_errors == 0:
            return "Parsing: OK"
        else:
            return f"Parsing: FAILED ({N_errors} error(s))"

    def write_report(self):
        with open(self.options["parsing"]["report_path"], "w") as f:
            for e in self.errors:
                print(e, file=f)

    def _clean_source(self):
        """
        Clean C code by:
        - Replacing tabs with spaces
        - Replacing multiple spaces with a single space
        - Removing comments (both single-line and multi-line)
        """
        # remove single-line comments
        self._source = re.sub(r'//.*', '', self._source)
        # remove multi-line comments
        self._source = re.sub(r'/\*.*?\*/', '', self._source, flags=re.DOTALL)
        # replace tabs with spaces
        self._source = self._source.replace('\t', ' ')
        # replace multiple spaces with a single space
        self._source = re.sub(r' +', ' ', self._source)

    def _parse_function_argument(self, arg):
        arg = arg.strip()
        last_star = arg.rfind("*")
        if last_star != -1:
            arg = arg[0:last_star + 1]
            spl_arg = arg.split()
            arg = " ".join(spl_arg[0:-1]) + spl_arg[-1] # turns "type *" into "type*" to enforce consistency
        else:
            arg = arg.rsplit(" ", 1)[0].strip()

        return arg

    def _extract_functions(self):
        # regular expression to match C function signatures
        function_pattern = re.compile(
            r'(?P<return_type>[a-zA-Z_][a-zA-Z0-9_\s\*]*)\s+'   # Return type
            r'(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*'              # Function name
            r'\((?P<args>[^\)]*)\)\s*\{'                        # Arguments inside parentheses
        )

        functions = {}

        for match in function_pattern.finditer(self._source):
            return_type = match.group('return_type').strip()
            name = match.group('name').strip()
            args = match.group('args').strip()

            # split and clean argument types
            arg_types = []
            if args:
                for arg in args.split(","):
                    arg_types.append(self._parse_function_argument(arg))
            else:
                arg_types = []

            functions[name] = {
                'return_type': return_type,
                'arg_types': arg_types
            }

        return functions
    