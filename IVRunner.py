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


print 'LED Set To: {0}'.format(settings['led'])
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
        vSteps = parseSteps(settings['voltageSteps'])
#        vf = open(settings['voltageSteps'])
#        vSteps = vf.readline().strip().split(',')  
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

    s.SetSourceDelay(settings['sourcedelay'])
    s.SetNPLC(settings['nplc'])
    s.SetRepeatAverage(settings['repeatAvg'])
    
    
    
    start = settings['min']
    end = settings['max']
    step = settings['stepSize']

    if settings['channels'] == None:
        print 'No Channels, assuming device has been directly connected'
        settings['channels'] = [-1]
    
    for channel in settings['channels']:
        print 'Using these voltage steps {0}'.format(settings['voltageSteps'])
        start = datetime.now()
        skip = False 
        lockfile=open("lock",'w+')
        if channel != -1:
            ft232Controller.ClearChannel()
            ft232Controller.ActivateChannel(channel)
        else:
            channel = 'direct'

        s.Discharge(settings['dischargebefore'])
        s.EnableOutput()
                
        if vSteps:
            lstBuilderCmd = 'vList = {}'
            print '+++++++++++++++++++++++++++++++++++++'
            print 'Running voltage steps for pin #{0}'.format(channel)

            s.handle.write(lstBuilderCmd)

            for i in range (1, len(vSteps)+1):                
                step = vSteps[i-1]
                if step.mode == 's':
                    #settling
                    cmd = "vList[{0}] = '{1}:{2}'"
                    print(cmd.format(i, step.level, step.value))
                elif step.mode == 'p':
                    #pausing
                    cmd = "vList[{0}] = '{1}/{2}'"
                    print(cmd.format(i, step.level, step.value))
                else:
                    #normal case
                    cmd = "vList[{0}] = {1}"
                    #print(cmd.format(i, step.level, step.value))

                s.handle.write(cmd.format(i, step.level, step.value))
                if settings['model'].find('2611a') != -1:
                    #Small delay to avoid queue full
                    time.sleep(0.05)

            cmd = 'IVRunnerList({0}, {1})'.format('vList', settings['currentLimit'])
            s.handle.write(cmd)
        else:
            print "++++++++++++++++++++++++++++++++++++++++"
            print "Doing I-V scan for pin #{0}, start: {1}, end: {2}, step: {3}".format(channel,start , end, step)
            cmd = 'IVRunner({0}, {1}, {2})'.format(start, end, step)
            s.handle.write(cmd)

        time.sleep(0.25)
        s.handle.timeout = 2.5
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
            s.handle.timeout = 2.5
            cmdi = 'printbuffer(1,ivBuffer.n,ivBuffer.readings)'
            cmdv = 'printbuffer(1,ivBuffer.n,ivBuffer.sourcevalues)'
            #cmdi = 'printbuffer(1,defbuffer1.n,defbuffer1.readings)'
            #cmdv = 'printbuffer(1,defbuffer1.n,defbuffer1.sourcevalues)'
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
                        i = lastMeasure.strip().split(',')
                    except Exception as e:
                        print 'Failed read {0} of 3'.format(x)
                        i = None
                elif not v:
                    try:
                        s.handle.clear()
                        print 'Past Clear'
                        s.handle.write(cmdv)
                        time.sleep(0.1)
                        lastMeasure = s.handle.read()
                        v = lastMeasure.strip().split(',')
                        print 'v:{0}'.format(v)
                    except Exception as e:
                        print 'Failed v. read {0} of 3'.format(x)
                        print 'Exception: {0}'.format(e)
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
        #s.Beep([(0.1,400)])
        stop = datetime.now()
        mins = (stop-start).seconds/60
        secs = (stop-start).seconds % 60
        print('Time Elapsed: min: {0}, seconds: {1}'.format(mins, secs))

    print 'Finished Running Curves!'
    s.handle.write('logout')
    exit()


## Use built-in IV-Curve Function     
for channel in settings['channels']:
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

# turn off LED
ft232Controller.SetLight(0)

