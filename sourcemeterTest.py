import argparse
import vxi11
import time
from sourcemeter import *
from FT232H import *

parser = argparse.ArgumentParser(description='Takes I-V Curves')

parser.add_argument('-a','--agilent', action='store_true',
                    help="Uses the agilent to take the iv curve")
parser.add_argument('-k','--keithley', action='store_true',
                    help="Uses the keithley to take the iv curve")
parser.add_argument('-K','--new_keithley', action='store_true',
                    help="Uses the Keythley 2450 to take iv curve")
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
                    default="", help="Output file for data")
parser.add_argument('-g', '--graph', action='store_true',
                    help='Prints the I-V curve graph to the screen')
parser.add_argument('-c', '--channel', type=int, nargs ='*',
                    help="Take iv curves at specified channels")
parser.add_argument('-A', '--all', action='store_true',
                    help="Takes iv curve at all of the channels")
parser.add_argument('-i', '--light', type=int, nargs = '?', default = None,
                    help="Specifies intensity of LEDs")

args = parser.parse_args()
host = '128.143.196.77'
port = 23
Ilimit = args.limit

ft232Controller = FT232H('spi')


if args.all:
    args.channel = range(1,11)
channels = str(args.channel).strip('[]')
print 'The following channels will be used: '+channels
if args.channel == None:
    args.channel = [-1]
    print args.channel



    
if args.forward:
    vStart = "FwdIVdefault"
elif args.reverse:
    vStart = "RevIVdefault"
elif not args.file == None:
    vStart = args.file
else:
    vStart = args.min
    vEnd = args.max
    steps = args.steps

# order of operations is important
# LEDs must be set before relays 
# Seting LEDs clears the relay settings

if args.light != None:
    print "Setting LEDs to value",args.light
    ft232Controller.SetLight(args.light) # turn on LEDs


for channel in args.channel:
    if channel != -1:
        ft232Controller.ClearChannel()
        ft232Controller.ActivateChannel(channel)
        output = args.output+'_Ch'+str(channel)
    else:              
        output = args.output
        
    s = Keithley2450(host, port,Ilimit) # remove args from SM base cls
    s.SetVsteps(vStart, vEnd, steps)   # define voltage steps 
    s.MeasureIV()   # take data
    s.WriteData(output)   # write out data
