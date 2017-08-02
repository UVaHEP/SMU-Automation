#!/usr/bin/python

import argparse
import vxi11
import time,os
from FT232H import *
from sourcemeter import *
from datetime import datetime

# to run, use the command below:
 # ./findLEDsetting.py -c [] -D [] -i [] -sLED [] -B 
 
 # CMD Line Options I want to include
 # sLED # default 10
 # i # default 0
 # halfVbr # default -27 V
 
 

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
                    help="Device identifier, append _fast for fast collection mode")
parser.add_argument('-F','--forward', action='store_true',
                    help="Takes default forward bias I-V curve if no data file")
parser.add_argument('-H','--hysteresis', action='store_true', default=False,
                    help="Repeat I-V measurement in reverse for hysteresis curve")
parser.add_argument('-l', '--limit', type=float, default = 0.001,
                    help="The current limit [0.01]")
parser.add_argument('-s', '--numsteps', type=int, default=100,
                    help="The number of steps in the staircase sweep [100]")
parser.add_argument('-S', '--stepsize', type=float, default=None,
                    help="Step size for the staircase sweep in units of volts [None]")
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
parser.add_argument('-i', '--iLED', type=int, nargs = '?', default=0,
                    help="Specifies intensity of LEDs, range is integers 0-4095")
parser.add_argument('-B','--BackTerm', action='store_true',
                    help="Use rear terminals on SMU (model 2450 only, for now)")
parser.add_argument('-sLED', '--LEDstepsize', type=int, default=10,
                    help="size of LED step")
parser.add_argument('-halfV', '--halfVbr', type=float, default=-30.0,
                    help="Voltage at which to start staircase sweep")

args = parser.parse_args()
#host = '128.143.196.77'
host = '192.168.0.2'
port = 23
Ilimit = args.limit

ft232Controller = FT232H('spi')

# first configure the sourcemeter
if args.k2611:
    s = Keithley2611("128.143.196.249", port)
else:
    s = Keithley2450(host, port)

s.Reset()

if args.BackTerm: s.UseRearTerm()

#s.Config() # not needed, done by Reset()
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

# stamp all files with starting time of this script
now = datetime.now()
tstamp=now.strftime("-%Y%m%d-%H:%M")


# hack: if string "fast" is included in the device name, then update the
# default SMU settings
if "fast" in args.device:
    print "Using 10ms source delay for faster scan" 
    s.SetSourceDelay(0.01)      # 10 ms source delay
    s.SetDischargeCycles(3,3)   # just do 3 cycles before/after measurement 
    s.SetNPLC(3)

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
    print "Outputfile:",outfile
    lockfile.write("Outfile= "+outfile+"\n")
    lockfile.flush()
    if channel != -1:
        ft232Controller.ClearChannel()
        ft232Controller.ActivateChannel(channel)
        
    print "Start I-V on channel",ch,"at time:",datetime.now().strftime("%H:%m")
    ft232Controller.Persist()
    ft232Controller = None
    
    time.sleep(0.25)
    ft232Controller = FT232H('i2c')
    
    halfVbr = args.halfVbr
    s.SetVoltage(halfVbr)
    s.EnableOutput()
    s.ReadVIPoint()
  
    time.sleep(1.0)
    I_d = float(s.ReadVIPoint())
    print "Zero measure I_d({0}) is: {1} ".format(halfVbr, I_d)
    print "Will increase LED until I_l(halfVbr) - I_d(halfVbr) >= 10nA"
   
    LED = args.iLED
    print "Starting with LED value: ",LED , " and LED step size: ",args.LEDstepsize
    
    
    while True:
        print "Using LED value: ",LED
        ft232Controller.SetLight(LED) #turn on LEDs

        

        time.sleep(0.5)
        I_l = float(s.ReadVIPoint())
        LminusD = I_l - I_d
        print "Current measure I_l({0}) is: {1} and LminusD is: {2}".format(halfVbr, I_l, abs(LminusD))
        if abs(LminusD) >= 10e-09: break
        if LED>1480: break
       
       
        LED = LED + args.LEDstepsize
        print "....................."
    print "For channel ",ch, " use LED value: ",LED
    ft232Controller.SetLight(0)
    s.SetVoltage(0.0)
    #s.WriteData(outfile)   # write out data
    
    print "Finish channel",ch,"at time:",datetime.now().strftime("%H:%M")
    print "----------------------------------------"
    lockfile.close()
    os.remove("lock")
