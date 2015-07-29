import subprocess
import sys
import os
import csv
import time
import argparse
import pexpect
import mpsse

from iv_func_a import sweepa
from iv_func_k import sweepk

parser = argparse.ArgumentParser(description='Takes I-V Curves')

parser.add_argument('-a','--agilent', action='store_true',
                    help="Uses the agilent to take the iv curve")
parser.add_argument('-k','--keithley', action='store_true',
                    help="Uses the keithley to take the iv curve")
parser.add_argument('-f', '--file', type=str, nargs='?', default=None,
                    help="Input data file that activates list sweep")
parser.add_argument('-R','--reverse', action='store_true',
                    help="Takes default reverse bias curve if no data file")
parser.add_argument('-F','--forward', action='store_true',
                    help="Takes default forward bias iv curve if no data file")
parser.add_argument('-l', '--limit', type=float, default = 8E-3,
                    help="The compliance value")
parser.add_argument('-s', '--steps', type=int, default=300,
                    help="The number of steps in the staircase sweep")
parser.add_argument('-m', '--min', type=float, default=0.0,
                    help="Voltage at which to start staircase sweep")
parser.add_argument('-x', '--max', type=float, default= -80.0,
                    help="Voltage at which to stop staircase sweep")
parser.add_argument('-o', '--output', type=str, nargs='?',
                    default='formattedData.csv', help="Output file for data")
parser.add_argument('-g', '--graph', action='store_true',
                    help='Prints the I-V curve graph to the screen')
parser.add_argument('-c', '--channel', type=int, nargs ='*',
                    help="Take iv curves at specified channels")
parser.add_argument('-A', '--all', action='store_true',
                    help="Takes iv curve at all of the channels")

args = parser.parse_args()

if args.all:
    args.channel = range(1,11)
channels = str(args.channel).strip('[]')
print 'The following channels will be used: '+channels


if args.agilent:

    #formats compliance value
    s = '{0:5.0E}'.format(args.limit)
    num, exp = s.split('E')
    exp_new = exp[0]+exp[1:].lstrip('0')
    limit = '{0}E{1}'.format(num, exp_new)

    host = '128.143.196.234'
    port = '5024'
    
    sweepa(args.output, host, port,limit,args)
elif args.keithley:
    sweepk(args.output, args)
else:
    print 'No Source Meter Unit was selected.'
