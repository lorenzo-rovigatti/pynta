'''
Created on Dec 25, 2022

@author: lorenzo
'''

import sys, os
import subprocess as sp
import gccoutputparser as gcc

class Compiler:
    command = "gcc"
    
    def __init__(self, source_file):
        self.source_file = source_file
        self.compile()
        
    def compile(self):
        try:
            result = sp.run([Compiler.command, "-o", self.source_file[:-2], self.source_file], stdout=sp.PIPE, stderr=sp.STDOUT, text=True)
        except sp.CalledProcessError as e:
            print(e.stdout.decode("utf-8"))
        else:
            self.output = result.stdout
    

class FileAnalyser:
    def __init__(self):
        pass


class Input(dict):
    def __init__(self, input_file):
        with open(input_file) as f:
            for line in f.readlines():
                line = line.strip()
                if line[0] != '#' and len(line) > 0:
                    spl = [s.strip() for s in line.split("=", 1)]
                    if len(spl) == 2:
                        super().__setitem__(spl[0], spl[1])
                    else:
                        print(f"malformed line '{line}'", file=sys.stderr)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage is {sys.argv[0]} input_file")
        exit(1)
        
    inp = Input(sys.argv[1])
    compiler = Compiler(inp["filename"])
    parser = gcc.GccOutputParser()
    parser.record(compiler.output)

    for w in parser.warnings():
        print(w)
    
    for e in parser.errors():
        print(e)
    