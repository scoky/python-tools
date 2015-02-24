#!/usr/bin/python

import logging
import argparse
import sys
import traceback
import os
import copy
import math
import numpy
from input_handling import findNumber
from command import Command,PerformReturn
from percentile import PercentileCommand
from fit import FitCommand

class SortedInputGrouper(object):
    def __init__(self, infile, group_cols=[0], delimiter=None):
        self.infile = infile
        self.group_cols = group_cols
        self.delimiter = delimiter
        self.tup = None
        self.chunks = None

    def group(self):
        line = self.infile.readline()
        if not line:
            return
        
        self.chunks = line.rstrip().split(self.delimiter)
        self.tup = [self.chunks[g] for g in self.group_cols]
        while self.tup:
            yield self._gather()
                
    def _gather(self):
        # Yield the capture chunks
        yield self.chunks
        # Look for more matching the tuple
        for line in self.infile:
            self.chunks = line.rstrip().split(self.delimiter)
            ntup = [self.chunks[g] for g in self.group_cols]
            if ntup == self.tup:
                yield self.chunks
            else:
                self.tup = ntup
                return
        self.tup = None
        
        
class Group(object):
    def __init__(self, tup):
        self.tup = tup
        
    def add(self, chunks):
        pass
        
    def done(self):
        pass
    
class UnsortedInputGrouper(object):
    def __init__(self, infile, group_cls=Group, group_cols=[0], delimiter=None):
        self.infile = infile
        self.group_cols = group_cols
        self.delimiter = delimiter
        self.dict = {}
        self.group_cls = group_cls

    def group(self):
        jdelim = ' ' if not self.delimiter else self.delimiter
        keys = []
        for line in self.infile:
            chunks = line.rstrip().split(self.delimiter)
            tup = [chunks[g] for g in self.group_cols]
            key = jdelim.join(tup)
            if key not in self.dict:
                self.dict[key] = self.group_cls(tup)
                keys.append(key)
            self.dict[key].add(chunks)
        for key in keys:
            self.dict[key].done()

commands = {
'min' : 	Command(sys.maxint, lambda g,a,b: min(a, findNumber(b)), lambda g,a: str(a)),
'mean' : 	Command([], PerformReturn(lambda g,a,b: a.append(findNumber(b))).perform, lambda g,a: str(sum(a)/len(a))),
'sum' : 	Command(0, lambda g,a,b: a+findNumber(b), lambda g,a: str(a)),
'count' : 	Command(0, lambda g,a,b: a+1, lambda g,a: str(a)),
'unique' : 	Command(set(), PerformReturn(lambda g,a,b: a.add(b)).perform, lambda g,a: str(len(a))),
'aggregate' : 	Command([], PerformReturn(lambda g,a,b: a.append(b)).perform, lambda g,a: ' '.join(a)),
'percentile' :	PercentileCommand(),
'fit' : 	FitCommand()
#,
#'distribution' : Command([], PerformReturn(lambda a,b: a.append(findNumber(b))).perform, lambda a: str(
}


def group(infile, outfile, group_col, action, action_col=-1, delimiter=None, fuzzy=None):
	command = commands[action]
        if fuzzy:
		fuzzy = eval(fuzzy)
	groups = {}
	for line in infile:
           try:
		chunks = line.rstrip().split(delimiter)
		g = chunks[group_col]
		if fuzzy:
			g = fuzzy(g)
		if g not in groups:
			groups[g] = copy.deepcopy(command.init)

		groups[g] = command.on_row(g, groups[g], chunks[action_col])
	   except Exception as e:
           	logging.error('Error on input: %s%s\n%s', line, e, traceback.format_exc())

	if delimiter == None:
		delimiter = ' '		
	for g in sorted(groups.keys()):
		outfile.write(str(g)+delimiter+command.on_finish(g, groups[g])+'\n')
		

def main():
    group(args.infile, args.outfile, args.group_col, args.action, args.action_col, args.delimiter, args.fuzzy)

if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Group rows by a given column value and perform an operation on the group')
    parser.add_argument('group_col', type=int, default=0, help='Column to group upon')
    parser.add_argument('action', choices=commands.keys(), help='Action to perform')
    parser.add_argument('action_col', nargs='?', type=int, default=0, help='Column to act upon')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-f', '--fuzzy', default=None, help='Fuzz the grouping')
    parser.add_argument('-d', '--delimiter', default=None)
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help='only print errors')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='print debug info. --quiet wins if both are present')
    args = parser.parse_args()

    # set up logging
    if args.quiet:
        level = logging.WARNING
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(
        format = "%(levelname) -10s %(asctime)s %(module)s:%(lineno) -7s %(message)s",
        level = level
    )

    main()

