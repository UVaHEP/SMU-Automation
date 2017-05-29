#!/usr/bin/python

import vxi11
import time,os
from sourcemeter import *
from FT232H import *
from datetime import datetime
from settingsHandler import *

import signal,sys


# Register signal handler to do cleanup on ctrl-C.
def signal_handler(signal, frame):
    print
    print 'signal_handler: received ctrl-C indicating user wants run stopped'
    global run
    run=0
    sys.exit(1)
run = 1
signal.signal(signal.SIGINT,signal_handler)


parser = buildParser()
args = parser.parse_args()
settings = {}

if args.config:
    settings = loadSettings(args.config)
    if not settings:
        print 'Failed to load settings from {0}'.format(args.config)
        exit()
else:
    settings =  {'script':None, 'host':None, 'port':23}


settings = processArgs(args, settings)


    






luaScript = None 
if settings['script']: 
    try:
        f = open(settings['script'])
        luaScript = f.readlines()
        f.close()
#        print 'Using the following luascript \n------------------------'
#        for line in luaScript:
#            print line.strip()
    except Exception as e:
        print 'Failed to load script: {0}'.format(e)
        exit()


ft232Controller = FT232H('spi')

# first configure the sourcemeter
host = settings['host']
port = settings['port']
print settings['model']
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

if settings['led'] < 0:
    #skip setting the led
    print 'Skipping led setup'
else:
    ft232Controller.SetLight(settings['led'])
    ft232Controller.Persist()
    
ft232Controller = None
time.sleep(0.25)
if settings['serial']:
    ft232Controller = FT232H('spi', serial=settings['serial'])
else:
    ft232Controller = FT232H('spi')

if settings['channelMap']:
    #Replace with access fn
    ft232Controller.pinMap = pinMaps[settings['channelMap']]
    
if settings['backterm']:
    s.UseRearTerm()

vSteps = None
if settings['voltageSteps']:
    try:
        vf = open(settings['voltageSteps'])
        vSteps = vf.readline().strip().split(',')  #map(float, vf.readline().split(','))
#        print vSteps
    except Exception as e:
        print 'Failed to load voltage steps from: {0}'.format(settings['voltageSteps'])
        print 'Reason: {0}'.format(e)
        
# stamp all files with starting time of this script
now = datetime.now()
tstamp=now.strftime("%Y%m%d-%H%M")

    
if luaScript:
    print 'Uploading script from: {0}'.format(settings['script'])
    s.handle.write('script.delete("{0}")'.format('IVRunnerScript'))
    if settings['model'].find('k2611a') != -1:
        ## Small delay to avoid queue full error
        s.uploadScript('IVRunnerScript', luaScript, 0.01)
    else:
        s.uploadScript('IVRunnerScript', luaScript)
    s.handle.write('IVRunnerScript.run()')
    time.sleep(0.25)

    s.SetSourceDelay(0.1)
    s.SetNPLC(3)

        
    
    
    start = settings['min']
    end = settings['max']
    step = settings['stepSize']

    for channel in args.channel:
        print 'Using these voltage steps {0}'.format(settings['voltageSteps'])
        start = datetime.now()
        skip = False 
        lockfile=open("lock",'w+')
        ft232Controller.ClearChannel()
        ft232Controller.ActivateChannel(channel)
        s.Discharge(3)
        s.EnableOutput()
                
        if vSteps:
            lstBuilderCmd = 'vList = {}'


            s.handle.write(lstBuilderCmd)
            

            for i in range (1, len(vSteps)+1):
                if vSteps[i-1].find(':') != -1:
                    ## If we have a settling step
                    cmd = "vList[{0}] = '{1}'"
                else:
                    cmd = 'vList[{0}] = {1}'
                    
                s.handle.write(cmd.format(i, vSteps[i-1]))
                #print cmd.format(i, vSteps[i-1])
                if settings['model'].find('2611a') != -1:
                    #Small delay to avoid queue full
                    time.sleep(0.01)

            
            cmd = 'IVRunnerList({0}, {1})'.format('vList', settings['currentLimit'])
            s.handle.write(cmd)
        else:
            print "++++++++++++++++++++++++++++++++++++++++"
            print "Doing I-V scan for pin #{0}, start: {1}, end: {2}, step: {3}".format(channel,start , end, step)
            cmd = 'IVRunner({0}, {1}, {2})'.format(start, end, step)
            s.handle.write(cmd)

        time.sleep(0.25)
        s.handle.timeout = 2
        l = s.handle.read()
        while l.find('Done') == -1:
            try:
                print l
                l = s.handle.read()
            except vxi11.vxi11.Vxi11Exception as e:
                print 'exception {0}'.format(e)
                break

        s.DisableOutput()
        s.handle.clear()
        time.sleep(0.25)
        i = None
        v = None
        try:
            s.handle.timeout = 3
            cmdi = 'printbuffer(1,defbuffer1.n,defbuffer1.readings)'
            cmdv = 'printbuffer(1,defbuffer1.n,defbuffer1.sourcevalues)'
            if settings['model'].find('2611a') != -1:
                cmdi = 'printbuffer(1,smua.nvbuffer1.n,smua.nvbuffer1.readings)'
                cmdv = 'printbuffer(1,smua.nvbuffer1.n,smua.nvbuffer1.sourcevalues)'

            for x in range(0, 3):
                
                if not i:
                    try:
                        s.handle.clear()
                        s.handle.write(cmdi)
                        time.sleep(0.1)
                        lastMeasure = s.handle.read()
                        #print lastMeasure
                        i = lastMeasure.strip().split(',')
                    except Exception as e:
                        print 'Failed read {0} of 3'.format(x)
                        i = None
                elif not v:
                    try:
                        s.handle.clear()
                        s.handle.write(cmdv)
                        time.sleep(0.1)
                        lastMeasure = s.handle.read()
                        #print lastMeasure
                        v = lastMeasure.strip().split(',')
                    except Exception as e:
                        print 'Failed v. read {0} of 3'.format(x)
                        v = None
                if i is not None and v is not None:
                    break

        except Exception as e:
            print 'Failed to read values for this run: {0}'.format(e)
            print 'Values seen: {0}, {1}'.format(i, v)
            skip = True
            
        s.Discharge(3)

        outfile = None
        if settings['output']:
            outfile = settings['output']
        else:
            outfile = '{0}_Ch{1}_iLED{2}-{3}.csv'.format(settings['device'], channel, settings['led'], tstamp)

        if not skip:
            print 'i:{0}, v:{1}'.format(i, v)
            print "Outputfile:",outfile
            lockfile.write("Outfile= "+outfile+"\n")
            lockfile.flush()
            f = open(outfile,'w+')
            map(lambda x,y: f.write('{0},{1}\n'.format(x,y)), v,i)
            f.flush()
        else:
            print 'Skipping output'
        s.Beep([(0.5,400)])
        stop = datetime.now()
        mins = (stop-start).seconds/60
        secs = (stop-start).seconds % 60
        print('Time Elapsed: min: {0}, seconds: {1}'.format(mins, secs))

    print 'Finished Running Curves!'
    
    exit()



### Scan for potentially working channels
def detectGoodChannels(controller, chLst, LEDValue):
    ## First get a list of dark currents at 0 and -1 Volts
    data = []
    for channel in chLst:
        controller.ClearChannel()
        controller.ActivateChannel(channel)
        datum = [channel, s.ReadVIPoint(0), s.ReadVIPoint(-1)]
        darkCh.append(dark)
        controller.SetLight(LEDValue)
        datum.append(s.ReadVIPoint(0))
        data.append(datum)
        s.DisableOutput()

    print 'Ch, Dark(0) V, Dark(-1 )V, Light {0}'.format(LEDValue)
    for datum in data:
        print '{0}: {1}, {2}, {3}'.format(datum[0], datum[1], datum[2], datum[3])




# hack: if string "fast" is included in the device name, then update the
# default SMU settings
if "fast" in args.device:
    print "Using 10ms source delay for faster scan" 
    s.SetSourceDelay(0.01)      # 10 ms source delay
    s.SetDischargeCycles(3,3)   # just do 3 cycles before/after measurement 
    s.SetNPLC(3)

    
for channel in args.channel:
    s.SetVsteps(settings['min'], settings['max'], 0, settings['stepSize'])
    lockfile=open("lock",'w+')
    print "++++++++++++++++++++++++++++++++++++++++"
    print "Doing I-V scan for pin #",channel
    # construct file name
    if channel<0: ch="00"
    else: ch="%02d" % channel
    if args.output=="":
        outfile=args.device+'_Ch'+ch+'_iLED-'+str(args.iLED)+tstamp+'.csv'
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
    
