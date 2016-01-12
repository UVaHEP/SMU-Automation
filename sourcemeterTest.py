#!/usr/bin/python

import argparse
import vxi11
import time,os
from sourcemeter import *
from FT232H import *
from datetime import datetime


parser = argparse.ArgumentParser(description='Takes I-V Curves')

parser.add_argument('-a','--agilent', action='store_true',
                    help="Use Agilent SMU to take the I-V curve")
parser.add_argument('-k','--k2611', action='store_true',
                    help="Use Keithley 2611 to take the I-V curve")
parser.add_argument('-K','--k2450', action='store_true',
                    help="Use Keithley 2450 to take I-V curve")
parser.add_argument('-f', '--file', type=str, nargs='?', default=None,
                    help="Input data file that activates list sweep")
parser.add_argument('-R','--reverse', action='store_true',
                    help="Takes default reverse bias curve if no data file")
parser.add_argument('-D','--device', type=str, nargs='?', default="noname",
                    help="Device identifier")
parser.add_argument('-F','--forward', action='store_true',
                    help="Takes default forward bias I-V curve if no data file")
parser.add_argument('-H','--hysteresis', action='store_true', default=False,
                    help="Repeat I-V measurement in reverse for hysteresis curve")
parser.add_argument('-l', '--limit', type=float, default = 0,
                    help="The current limit [smu default]")
parser.add_argument('-s', '--numsteps', type=int, default=300,
                    help="The number of steps in the staircase sweep [300]")
parser.add_argument('-S', '--stepsize', type=float, default=None,
                    help="Maximum step size in sweep [determined from nsteps]")
parser.add_argument('-m', '--min', type=float, default=0.0,
                    help="Voltage at which to start staircase sweep")
parser.add_argument('-x', '--max', type=float, default= -60.0,
                    help="Voltage at which to stop staircase sweep")
parser.add_argument('-o', '--output', type=str, nargs='?', default="",
                    help="Output file for data")
parser.add_argument('-g', '--graph', action='store_true',
                    help='Prints the I-V curve graph to the screen')
parser.add_argument('-c', '--channel', type=int, nargs ='*',
                    help="Take I-V curves at specified channels")
parser.add_argument('-A', '--all', action='store_true',
                    help="Take I-V curve for all channels")
parser.add_argument('-i', '--iLED', type=int, nargs = '?', default = 0,
                    help="Specifies intensity of LEDs")

args = parser.parse_args()
#host = '128.143.196.77'
host = '192.168.0.2'
port = 23
Ilimit = args.limit

ft232Controller = FT232H('spi')

# first configure the sourcemeter
s = Keithley2450(host, port)
if args.limit>0: s.SetCurrentLimit(args.limit)

vEnd = args.max
if args.forward:
    vStart = "FwdIVdefault"
elif args.reverse:
    vStart = "RevIVdefault"
elif args.file != None:
    vStart = args.file
else:
    vStart = args.min
    vEnd = args.max
    nsteps = args.numsteps
    print "vStart, vEnd",vStart,vEnd
    if args.stepsize == None: deltaV=0
    else: deltaV = abs(args.stepsize)   # overrides num steps
    if deltaV>0:
        print "Maximum step is",deltaV,"Volts"
    else:
        print "Using",nsteps,"voltage steps"
    
if args.stepsize == None:
    s.SetVsteps(vStart, vEnd, args.numsteps)   # define voltage steps
else:
    s.SetVsteps(vStart, vEnd, 0, deltaV)

if args.hysteresis: s.AddHysteresis()


if args.all:
    args.channel = range(1,11)
channels = str(args.channel).strip('[]')
print 'The following channels will be used: '+channels
if args.channel == None:
    args.channel = [-1]
    print args.channel

# set the LED
if args.iLED != None:
    print "Light curves will use LED value",args.iLED
    ft232Controller.SetLight(args.iLED) #turn on LEDs
    ft232Controller.Persist()
    ft232Controller = None
    time.sleep(0.25)
    ft232Controller = FT232H('spi')
    
else: args.iLED=0
    
# stamp all files with starting time of this script
now = datetime.now()
tstamp=now.strftime("-%Y%m%d-%H:%M")

# hack: if string "fast" is included in the device name, then update the
# default SMU settings
if "fast" in args.device:
    s.SetSourceDelay(0.01)      # 10 ms soure delay
    s.SetDischargeCycles(10,10) # just do 10 cycles after measurement 


for channel in args.channel:
    lockfile=open("lock",'w+')
    print "++++++++++++++++++++++++++++++++++++++++"
    print "Doing I-V scan for pin #",channel
    # construct file name
    if channel<0: ch="00"
    else: ch="%02d" % channel
    if args.output=="":
        outfile=args.device+'_Ch'+ch+'_iLED'+str(args.iLED)+tstamp+'.csv'
    else: outfile=args.output
    lockfile.write("Outfile= "+outfile+"\n")
    lockfile.flush()
    if channel != -1:
        ft232Controller.ClearChannel()
        ft232Controller.ActivateChannel(channel)
        
    print "Start I-V on channel",ch,"at time:",datetime.now().strftime("%H:%M")
    s.MeasureIV()   # take data
    s.WriteData(outfile)   # write out data
    print "Finish channel",ch,"at time:",datetime.now().strftime("%H:%M")
    print "----------------------------------------"
    lockfile.close()
    os.remove("lock")
