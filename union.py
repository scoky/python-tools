#!/usr/bin/python

import os
import sys
import argparse
import traceback

if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Compute union of column(s)')
    parser.add_argument('infiles', nargs='+', type=argparse.FileType('r'), default=[sys.stdin])
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-c', '--columns', nargs='+', type=int, default=[0])
    parser.add_argument('-d', '--delimiter', default=None)
    args = parser.parse_args()
    if len(args.columns) == 1:
        args.columns = args.columns*len(args.infiles)
    if len(args.columns) != len(args.infiles):
        sys.stderr.write('InputError: invalid columns argument\n')
        exit()
        
    res = set()
    for infile,col in zip(args.infiles, args.columns):
        for line in infile:
            chunk = line.rstrip().split(args.delimiter, col+1)[col]
            if chunk not in res:
                res.add(chunk)
                args.outfile.write(chunk + '\n')

