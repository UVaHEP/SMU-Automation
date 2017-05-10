#!/usr/bin/python

import argparse
import vxi11
import time,os
from sourcemeter import *
from FT232H import *
from datetime import datetime

import signal,sys
import ConfigParser

# Register signal handler to do cleanup on ctrl-C.
def signal_handler(signal, frame):
    print
    print 'signal_handler: received ctrl-C indicating user wants run stopped'
    global run
    run=0
    sys.exit(1)
run = 1
signal.signal(signal.SIGINT,signal_handler)


parser = argparse.ArgumentParser(description='Takes I-V Curves')

##### Deprecated Args #####
parser.add_argument('-a','--agilent', action='store_true',
                    help="Use Agilent SMU to take the I-V curve")
parser.add_argument('-k','--k2611', action='store_true',
                    help="Use Keithley 2611 to take the I-V curve")
parser.add_argument('-K','--k2450', action='store_true',
                    help="Use Keithley 2450 to take I-V curve")
parser.add_argument('--script', type=str, nargs='?', default=None,
                    help='Script to upload and run')
parser.add_argument('-H','--hysteresis', action='store_true', default=False,
                    help="Repeat I-V measurement in reverse for hysteresis curve")
parser.add_argument('--host', type=str, default=None,
                    help="Host to use")
parser.add_argument('--port', type=int, default=23,
                    help="Port to use")



##### General Arguments #####
parser.add_argument('-f', '--file', type=str, nargs='?', default=None,
                    help="Input data file that activates list sweep")
parser.add_argument('-D','--device', type=str, nargs='?', default="noname",
                    help="Device identifier, append _fast for fast collection mode")
parser.add_argument('-o', '--output', type=str, nargs='?', default="",
                    help="Output file for data")
parser.add_argument('-g', '--graph', action='store_true',
                    help='Prints the I-V curve graph to the screen')
parser.add_argument('-B','--BackTerm', action='store_true',
                    help="Use rear terminals on SMU (model 2450 only, for now)")
parser.add_argument('-c', '--channel', type=int, nargs ='*',
                    help="Take I-V curves at specified channels")
parser.add_argument('-A', '--all', action='store_true',
                    help="Take I-V curve for all channels")
parser.add_argument('-i', '--iLED', type=int, nargs = '?', default=None,
                    help="Specifies intensity of LEDs, range is integers 0-4095")
parser.add_argument('--config', type=str, default=None,
                    help="Specify the configuration file to use")



##### I-V Curve Specific Arguments #####
parser.add_argument('-R','--reverse', action='store_true',
                    help="Takes default reverse bias curve if no data file")
parser.add_argument('-F','--forward', action='store_true',
                    help="Takes default forward bias I-V curve if no data file")

parser.add_argument('-l', '--limit', type=float, default = -1,
                    help="Set the current limit [0.01 A]")
parser.add_argument('-s', '--numsteps', type=int, default=100,
                    help="The number of steps in the staircase sweep [100]")
parser.add_argument('-S', '--stepsize', type=float, default=None,
                    help="Step size for the staircase sweep in units of volts [None]")
parser.add_argument('-m', '--min', type=float, default=0.0,
                    help="Voltage at which to start staircase sweep")
parser.add_argument('-x', '--max', type=float, default= -60.0,
                    help="Voltage at which to stop staircase sweep")


args = parser.parse_args()


settings = {'script':None, 'host':None, 'port':23}

if args.config:
    print 'Trying to use {0} for Configuration file'.format(args.config)
    try:
        c = ConfigParser.ConfigParser()
        c.readfp(open(args.config))

        # Load General Settings first 
        section = 'SMU-Automation-General'
        settings['host'] = c.get(section, 'host')
        settings['port'] = c.getint(section, 'port')
        settings['model'] = c.get(section, 'model')
        settings['currentLimit'] = c.getfloat(section, 'ilimit')
        settings['backterm'] = c.getboolean(section, 'backterm')
        settings['autorange'] = c.getboolean(section, 'autorange')



        try:
            settings['script'] = c.get(section, 'programfile')
        except:
            settings['script'] = None
        if args.script:
            settings['script'] = args.script

        if c.getboolean(section, 'fastmode'):
            section = 'SMU-Automation-Fast'
        else:
            section = 'SMU-Automation-Slow'

        settings['repeatAvg'] = c.getint(section, 'repeatAvg')
        settings['sourcedelay'] = c.getfloat(section, 'sourcedelay')
        settings['dischargebefore'] = c.getint(section, 'dischargebefore')
        settings['dischargeafter'] = c.getint(section, 'dischargeafter')
        settings['nplc'] = c.getint(section, 'nplc')

        section = 'IV-Curve'
        settings['stepSize'] = c.getfloat(section, 'stepSize')
        settings['min'] = c.getfloat(section, 'min')
        settings['max'] = c.getfloat(section, 'max')
        settings['file'] = c.get(section, 'file')
            
    except Exception as e:
        print 'Failed to load {0}, reason: {1}'.format(args.config, e)
        exit()
else:
    if args.limit < 0:
        # use default current limit
        settings['currentLimit'] = 0.01
    else:
        settings['currentLimit'] = args.limit

    if not args.host:
        print 'I need a host to connect to, use --host or add it to a config file'
        exit()
    else:
        settings['host'] = args.host

    settings['port'] = args.port 

    if args.k2611:
        settings['model'] = 'k2611'
    elif args.k2450:
        settings['model'] = 'k2450'
    else:
        settings['model'] = 'unknown'


luaScript = None 
if settings['script']: 
    try:
        f = open(settings['script'])
        luaScript = f.readlines()
        f.close()
        print 'Using the following luascript \n------------------------'
        for line in luaScript:
            print line.strip()
    except Exception as e:
        print 'Failed to load script: {0}'.format(e)
        exit()


ft232Controller = FT232H('spi')

# first configure the sourcemeter
host = settings['host']
port = settings['port']
print 'Connecting to {0}:{1}'.format(host, port)
if 'k2611' in settings['model']:
    s = Keithley2611(host, port)
elif 'k2450' in settings['model']:
    s = Keithley2450(host, port)
else:
    print 'non supported model, {0}'.format(settings['model'])
    exit()

print 'Resetting'
s.Reset()

if args.BackTerm: s.UseRearTerm()

#s.Config() # not needed, done by Reset()
if args.limit>0: s.SetCurrentLimit(args.limit)

# vEnd = args.max
# if args.forward:
#     vStart = "FwdIVdefault"
# elif args.reverse:
#     vStart = "RevIVdefault"
# elif args.file != None:
#     vStart = args.file
# else:
#     vStart = args.min
#     vEnd = args.max
#     nsteps = args.numsteps
#     print "vStart, vEnd",vStart,vEnd
#     if args.stepsize == None: deltaV=0
#     else: deltaV = abs(args.stepsize)   # overrides num steps
#     if deltaV>0:
#         print "Maximum step is",deltaV,"Volts"
#     else:
#         print "Using",nsteps,"voltage steps"
    
# if args.stepsize == None:
#     s.SetVsteps(vStart, vEnd, args.numsteps)   # define voltage steps
# else:
#     s.SetVsteps(vStart, vEnd, 0, deltaV)

# if args.hysteresis: s.AddHysteresis()


# if args.all:
#     args.channel = range(1,11)
# channels = str(args.channel).strip('[]')
# print 'The following channels will be used: '+channels
# if args.channel == None:
#     args.channel = [-1]
#     print args.channel

# # set the LED
# if args.iLED != None:
#     print "Light curves will use LED value",args.iLED
#     ft232Controller.SetLight(args.iLED) #turn on LEDs
#     ft232Controller.Persist()
#     ft232Controller = None
#     time.sleep(0.25)
#     ft232Controller = FT232H('spi')
    
# else: args.iLED=0
    
# # stamp all files with starting time of this script
# now = datetime.now()
# tstamp=now.strftime("-%Y%m%d-%H:%M")

if luaScript:
    print 'Uploading script from: {0}'.format(settings['script'])
    s.uploadScript('IVRunner', luaScript)
    s.handle.write('IVRunner.run()')
    time.sleep(0.25)
    s.EnableOutput()
    s.handle.write('IVRunner(0, -72, -0.1)')

    #s.handle.write("print('Donezo, done')")
    s.handle.timeout = 5
    time.sleep(0.25)
        
    l = s.handle.read()
    while l.find('Done') == -1:
        try:
            print l
            l = s.handle.read()
        except vxi11.vxi11.Vxi11Exception as e:
            print 'exception {0}'.format(e)
            break

    s.DisableOutput()
    exit()


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
        
    print "Start I-V on channel",ch,"at time:",datetime.now().strftime("%H:%M")
    s.MeasureIV()   # take data
    s.WriteData(outfile)   # write out data
    print "Finish channel",ch,"at time:",datetime.now().strftime("%H:%M")
    print "----------------------------------------"
    lockfile.close()
    os.remove("lock")
    
