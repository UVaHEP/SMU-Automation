import vxi11
import time,sys
from math import sqrt
from numpy import array

# To do kill other possible conenctions in Connect method before starting

# Sourcemeter base class
class Sourcemeter:
    def __init__(self, host, port):
        # "hardwired" limits
        self.Connected = False
        self.Ilimit=1e-3
        self.Vmax=3
        self.Vmin=-80
        self.Host = host
        self.Port = port
        self.Volts = []
        self.Current = []
        self.Discharge0=10  # discharge cycles before
        self.Discharge1=60  # and after measurement
        
    def Connect(self):
        print 'connecting'
        pass
    
    # limit V for safety
    def CheckVlimit(self,volt):
        if volt<self.Vmin:
            print "Warning voltage limited at",self.Vmin
            return self.Vmin
        if volt>self.Vmax:
            print "Warning voltage limited at",self.Vmax
            return self.Vmax
        return volt

    # number of measurements to averarage in hardware
    def SetRepeatAverage(self, nsamples):
        pass
    # set hold source time before taking measurement
    def SetSourceDelay(self,delay):
        pass

    # todo update this to be a Wall Time
    def SetDischargeCycles(self,t0,t1):
        self.Discharge0=t0
        self.Discharge1=t1
    
    def SetVsteps(self,vStart,vEnd=0,steps=0,dV=0):
        if type(vStart)==str:
            print vStart
            scanType=vStart
            if scanType=="RevIVdefault" : self.MakeList(-1)
            elif scanType=="FwdIVdefault" : self.MakeList(1)
            else: self.ReadVfile(scanType)
            return
        if steps>0:  # number of steps is set
            if steps==1:
                self.Volts.append(vEnd)
                return
            delta = float(vEnd-vStart)/float(steps)
            for i in range(0,steps+1):
                self.Volts.append(i*delta+vStart)
                
            #volts=array(range(steps+1))*1.0/steps*(vEnd-vStart) # fix bug!
            #self.Volts=volts.tolist()
        else: # (maximum) step size is set
            volt=vStart
            dV=cmp(vEnd-vStart,0)*dV # get the sign right
            while abs(volt)<abs(vEnd):
                self.Volts.append(volt)
                volt=volt+dV
            self.Volts.append(vEnd)

            
    def MakeList(self,direction):        
        if direction>0:
            volt = 0.0
            while round(volt,4) <= 3.0:
                self.Volts.append(str(round(volt,4)))
                volt += 0.05

        else:
            volt = 0.0
            while round(volt,4)>=(-60.0):
                self.Volts.append(str(round(volt,4)))
                volt += -0.1
                #if round(volt,4) >(-40.0):
                #    volt += -0.5
                #elif round(volt,4) >(-50.0):
                #    volt += -0.1
                #else:
                #    volt += -0.05

                    
    # Get list of voltages from a text file
    def ReadVfile(self, file):
        f = open(file, 'r')
        if file[-3:] == 'csv':
            for line in f:
                values = line.split(',')
                if len(values) > 4:
                    self.Volts.append(values[3])
            if not self.Volts == []:        
                del self.Volts[0]
        elif self.Volts == []:
            for line in f:
                splitSpace =[]
                newline = line.replace(',',' ')
                splitSpace = newline.split()
                if len(splitSpace) >1:
                    for i in range(len(splitSpace)):
                        self.Volts.append(splitSpace[i])
                    else:
                        if not splitSpace == []:
                            self.Volts.append(splitSpace[0])
        f.close()

    def MeasureIV(self):
        print 'doing list sweep'
        pass

    def UploadScript(self, scriptName, script, delay=None):
        #Upload a user script to a Keithley sourcemeter
        print 'Uploading {0}'.format(scriptName)
        try:
            #First remove the script from the runtime environment
#            self.Handle.write('{0} = nil\n'.format(scriptName))
            self.Handle.write('loadscript {0}\n'.format(scriptName))
            for l in script:
                self.Handle.write(l)
            if delay:
                time.sleep(0.01)
            self.Handle.write('endscript')
            
        except Exception as e:
            print 'Failed: {0}'.format(e)


    
    # dump the IV curve data to the screen and optionally a file
    def WriteData(self, output=""):
        if output != "":
            print 'Writing SMU data to {0}.'.format(output)
            outputFile = open(output,'w+')
            outputFile.write('Repeat,VAR2,Point,Voltage,Current,Time\n')
        # len(self.Volts) possibly > len(self.Current)
        for i in range(len(self.Current)): # n.b. sample list may be truncated by ilimit
            try:
                current = str(self.Current[i]).lstrip('+')
                outputStr = '1,1,1,{0},{1},1\n'.format(self.Volts[i], current)
                if outputFile: outputFile.write(outputStr)
                else: 
                    oStr = '%3d %6.2f %6.2e' % (i, float(self.Volts[i]), float(current))
                    print oStr
            except Exception as e:
                print 'something went wrong when writing: {0}.'.format(e)

        if output != "":
             outputFile.close()
         

    #################
    # Sourcemeter Controls
    #################

    def Beep(self, notes):
        pass 
    def Arm(self):
        pass
    def DisArm(self):
        pass
    def EnableOutput(self):
        pass
    def DisableOutput(self):
        pass
    def Autorange(self, state):
        pass
    def OutputFn(self, func):
        pass
    def Reset(self):
        pass
    def SetVoltageLimit(self, voltage):
        pass
    def SetCurrentLimit(self, current):
        pass
    def SetRepeatAverage(self,samples):
        pass
    def Model(self):
        pass
    
    # set static voltage here
    def SetVoltage(self,v):
        pass
    # method to set and read an single V-I point
    def ReadVIPoint(self,v=None):
        if setVoltage==None: pass # use current setting
        else: self.SetVoltage(v)
        # read voltage here
        pass

    
      

class Keithley2611(Sourcemeter):

    def __init__(self, host, port):
        Sourcemeter.__init__(self, host, port)
        self.Handle = vxi11.Instrument(self.Host)
        self.ClearBuffer()
        self.Connect()
        self.Config()
        
    def Config(self):
        self.SetRepeatAverage(3)  # Average 3 samples / measurement
        self.SetSourceDelay(1.0)  # hold off time before measurements
        self.SetVoltageLimit(-80) # need to improve for Fwd protection
        self.SetCurrentLimit(self.Ilimit)
        self.Autorange(1)
        self.SetNPLC(3)
        #self.Handle.write('smu.source.autodelay = smu.ON')
        #self.Handle.write('trigger.model.abort()')
                    
    def __del__(self):
        self.Handle.close()
        print 'Closing TCP connection'
    
    def Connect(self):
        identity = self.Model()
        if (identity.find('Model 2611A') != -1):
            print 'Model: '+identity
        else:
            print 'Wrong Model %s' % identity
            self.Handle.close()
            return            
        #self.Reset()
        #self.DisableOutput()
        self.OutputFn('voltage')       

        

    def Beep(self, notes):
        #Beep takes a list of tuples where each tuple consists of
        #two elements (duration in seconds, frequency in hertz)
        #so pass in something like [(0.5, 200), (0.25, 450), ... ]
        cmd = 'beeper.beep({0}, {1})'
        try: 
            for note in notes:
                duration, freq = note
                beepcmd = cmd.format(duration, freq)
                self.Handle.write(beepcmd)
        except Exception as e:
            print 'Beeper failed to work.'

  
        
    def DisableOutput(self):
        self.Handle.write('smua.source.output = smua.OUTPUT_OFF')
    def EnableOutput(self):
        self.Handle.write('smua.source.output = smua.OUTPUT_ON')

    def Reset(self):
        self.Handle.write('smua.reset()')
        self.Config()

    def OutputFn(self, func):
        cmd = 'smua.source.func = {0}'
        if func == 'voltage':
            cmd = cmd.format('smua.OUTPUT_DCVOLTS')
        elif func == 'current':
            cmd = cmd.format('smua.OUTPUT_DCAMPS')
        else:
            print 'bad output function'
            return
        self.Handle.write(cmd)

    def Autorange(self, state):
        #for now only handle current measuring, will change
        #to handle voltage autoranging as well
        cmd = 'smua.measure.autorangei = {0}'
        if state:
            cmd = cmd.format('smua.AUTORANGE_ON')
        else:
            cmd = cmd.format('smua.AUTORANGE_OFF')
        self.Handle.write(cmd)

      
    def SetCurrentLimit(self, current):
        cmd = 'smua.source.limiti = {0}'
        try:
            i = float(current)
            cmd = cmd.format(i)
            self.Handle.write(cmd)
        except ValueError as e:
            print 'bad current in voltageLimit'
            
    def SetVoltageLimit(self, voltage):
        cmd = 'smua.source.limitv = {0}'
        try:
            volt = float(voltage)
            cmd = cmd.format(volt)
            self.Handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in voltageLimit'

    def SetRepeatAverage(self,samples):
        if samples<=1:
            self.Handle.write('smua.measure.filter.enable = smua.FILTER_OFF')
            return
        self.Handle.write('smua.measure.filter.count = {0}'.format(samples))
        self.Handle.write('smua.measure.filter.type = smua.FILTER_REPEAT_AVG')
	self.Handle.write('smua.measure.filter.enable = smua.FILTER_ON')

    def SetSourceDelay(self,delay):
        self.Handle.write('smua.source.delay = {0}'.format(delay))

            
    def SetNPLC(self,nplc=3):
        self.Handle.write('smua.measure.nplc = {0}'.format(nplc))
            
    def Model(self):
        #First clean anything in the buffer out
        self.Handle.clear()
        identity = self.Handle.ask("*IDN?")
        return identity

    def SetVoltage(self, v):
        cmd = 'smua.source.levelv = {0}'
        try:
            voltage = float(v)
            cmd = cmd.format(voltage)
            self.Handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in Set Voltage'
    
    def ReadVIPoint(self,v=None):
        if v != None:
            self.SetVoltage(v) # otherwise use last set voltage
            #set to 1 measurement
        self.Handle.write('smua.measure.count = 1')
        self.EnableOutput()
        self.Handle.write('print(smua.measure.i())')
        measure = self.Handle.read()
        #print 'i-v measure: {0}'.format(measure)
        #self.DisableOutput()
        return measure

    def Discharge(self, n=10):
        print "Discharging cycle, measurements =",n
        self.SetVoltage(0)
        self.EnableOutput()
        for i in range(n):
            self.Handle.write('print(smua.measure.i())')
            measure = self.Handle.read()
            sys.stdout.write(str(i%10))
            sys.stdout.flush()
            time.sleep(1)
        print ""
        self.DisableOutput()

  
    def MeasureIV(self):
        self.Beep([(0.5,200)])
        self.Discharge(self.Discharge0) 
        self.Handle.write('smua.measure.autozero = 1')        
        self.Handle.write('mylist = {}')

        length = len(self.Volts)
        for volt in self.Volts:
            line = 'table.insert(mylist, {0})'.format(volt)
            self.Handle.write(line)

        self.Handle.write('SweepVListMeasureI(smua, mylist, 1,'+str(length)+')')

        self.Handle.timeout = 20000
        time.sleep(0.25)
        opcValue = '0'
        
        print 'recvd %s' % opcValue
    	print 'waiting for opc'
   	while (opcValue.find('1') == -1):
            print "ask OPC"
            try:
                opcValue = self.Handle.ask('*OPC?')
                print 'opc value recvd %s' % opcValue
                time.sleep(10)
	    except vxi11.vxi11.Vxi11Exception as e:
	        print 'timeout? {0}'.format(e)
                continue

        
        self.Handle.write('printbuffer(1,smua.nvbuffer1.n,smua.nvbuffer1.readings)')
        lastMeasure = self.Handle.read()
        self.Current = lastMeasure.strip().split(',')
        self.Discharge(self.Discharge1)
        self.Beep([(0.5,400)])

    def RunScript(self, scriptName, args):


        sargs = ','.join(map(lambda x: '\"{0}\"'.format(x), args))
#        sargs = []
#        for i in range(0, len(args)):
#            sargs.append('a{0}=\"{1}\"'.format(i, args[i]))
        print sargs
        rline = '{0}({1})'.format(scriptName, sargs)
#        rline = '{0}'.format(scriptName)
        
        for arg in sargs:
            print arg
            self.Handle.write(arg)

        print 'Running: {0}'.format(rline)
        self.Handle.write(rline)

        self.Handle.timeout = 20000
        time.sleep(0.25)
        
        l = self.Handle.read()
        while l.find('Done') == -1:
            try:
                print l
                l = self.Handle.read()
            except vxi11.vxi11.Vxi11Exception as e:
                print 'exception {0}'.format(e)
                break

        self.Handle.write('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')
        lastMeasure = self.Handle.read()
        self.Current = lastMeasure.strip().split(',')
        time.sleep(0.25)
        self.Handle.write('printbuffer(1,smua.nvbuffer2.n,smua.nvbuffer2.readings)')
        volts = self.Handle.read()
        self.Volts = volts.strip().split(',')
        
        self.Discharge(self.Discharge0)
        self.Beep([(0.5, 400)])
        self.WriteData()
        
#        for i in range(length):
#            num = self.Handle.ask('print(smua.nvbuffer1.readings['+str(i+1)+']')
#            self.Current.append(num)


            
class Keithley2450(Sourcemeter):
    def __init__(self, host, port):
        Sourcemeter.__init__(self, host, port)
        self.Handle=vxi11.Instrument(self.Host)
        self.Connected = False
        self.ModelName = None
        self.Connect()
        self.Config()

    def Config(self):
        self.SetRepeatAverage(3)  # Average 3 samples / measurement
        self.SetSourceDelay(1.0)  # hold off time before measurements
        self.SetVoltageLimit(-80) # need to improve for Fwd protection
        self.SetCurrentLimit(self.Ilimit)
        self.Autorange(1)

    def UseRearTerm(self):
        self.Handle.write('smu.measure.terminals=smu.TERMINALS_REAR')

        
    def __del__(self):
        self.Handle.close()
        print "Closing TCP connection"
 
    def Connect(self):
        identity = self.Model()
        if (identity.find('MODEL 2450') != -1):
            print 'Model: '+identity
            self.Connected = True
            self.ModelName = identity
        else:
            print 'Wrong Model %s' % identity
            self.Handle.close()
            return            

        
    def Beep(self, notes):
        #Beep takes a list of tuples where each tuple consists of
        #two elements (duration in seconds, frequency in hertz)
        #so pass in something like [(0.5, 200), (0.25, 450), ... ]
        cmd = 'beeper.beep({0}, {1})'
        try: 
            for note in notes:
                duration, freq = note
                beepcmd = cmd.format(duration, freq)
                self.Handle.write(beepcmd)
        except Exception as e:
            print 'Beeper failed to work.'


    def DisableOutput(self):
        self.Handle.write('smu.source.output = smu.OFF')
    def EnableOutput(self):
        self.Handle.write('smu.source.output = smu.ON')

    def Reset(self):
        self.Handle.write('smu.reset()')
        self.Config()

    def OutputFn(self, func=None):
        cmd = 'smu.source.func = {0}'
        if func == 'voltage':
            cmd = cmd.format('smu.FUNC_DC_VOLTAGE')
        elif func == 'current':
            cmd = cmd.format('smu.FUNC_DC_CURRENT')
        else:
            cmd = 'print(smu.source.func)'
            return self.Handle.ask(cmd)
        self.Handle.write(cmd)

    def Autorange(self, state):
        cmd = 'smu.measure.autorange = {0}'
        if state:
            cmd = cmd.format('smu.ON')
        else:
            cmd = cmd.format('smu.OFF')
        self.Handle.write(cmd)
        
    def SetCurrentLimit(self, current):
        cmd = 'smu.source.ilimit.level = {0}'
        try:
            i = float(current)
            cmd = cmd.format(i)
            self.Handle.write(cmd)
        except ValueError as e:
            print 'bad current in CurrentLimit'

    def SetVoltageLimit(self, voltage):
        cmd = 'smu.source.vlimit.level = {0}'
        try:
            v = float(voltage)
            cmd = cmd.format(v)
            self.Handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in voltageLimit'


            
    def SetSMURange(self, limit):
        cmd = 'smu.source.range = {0}'
        try:
            r = float(limit)
            cmd = cmd.format(r)
            self.Handle.write(cmd)
        except ValueError as e:
            print 'bad limit given '

    def SetRepeatAverage(self,samples):
        if samples<=1:
            self.Handle.write('smu.measure.filter.enable = smu.OFF')
            return
        self.Handle.write('smu.measure.filter.count = {0}'.format(samples))
        self.Handle.write('smu.measure.filter.type = smu.FILTER_REPEAT_AVG')
	self.Handle.write('smu.measure.filter.enable = smu.ON')

    def SetSourceDelay(self,delay):
        self.Handle.write('smu.source.delay = {0}'.format(delay))

    def SetNPLC(self,nplc=3):
        self.Handle.write('smu.measure.nplc = {0}'.format(nplc))
        
    def Model(self):
        #First clean anything in the buffer out
        self.Handle.clear()
        identity = self.Handle.ask("*IDN?")
        return identity

    def SetCurrent(self, i):
        cmd = 'smu.source.level = {0}'
        try:
            current = float(i)
            cmd = cmd.format(current)
            self.Handle.write(cmd)
        except ValueError as e:
            print 'bad current in Set Current'


    def SetVoltage(self, v):
        cmd = 'smu.source.level = {0}'
        try:
            voltage = float(v)
            cmd = cmd.format(voltage)
            self.Handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in Set Voltage'
        

    #def ReadUntilStable(self,v=0):
    #    self.SetVoltage(v)
    #    self.Handle.write('smu.measure.count = 1')

    def ReadVIPointTest(self,v=None):
        if v != None:
            self.SetVoltage(v) # otherwise use last set voltage
        #set to 1 measurement
        self.Handle.write('smu.measure.count = 1')
        self.EnableOutput()
        samps=[]
        nave=5
        for i in range(100):
            self.Handle.write('print(smu.measure.read())')
            measure = self.Handle.read()
            samps.append(float(measure))
            if i>=nave-1:
                sum=0; sum2=0
                for n in range(i+1-nave,i+1):
                    sum+=samps[n]; sum2+=samps[n]*samps[n]
                sigma=sqrt(1.0/(nave-1)*(sum2-sum*sum/nave))
                print i,samps[i],sum/nave,sigma
            else:
                print i,samps[i],1,1
        print 'i-v measure: {0}'.format(samps[99])
        self.DisableOutput()
        return measure
            
    def ReadVIPoint(self,v=None):
        if v != None:
            self.SetVoltage(v) # otherwise use last set voltage
        #set to 1 measurement
        self.Handle.write('smu.measure.count = 1')
        self.EnableOutput()
        self.Handle.write('print(smu.measure.read())')
        measure = self.Handle.read()
        #print 'i-v measure: {0}'.format(measure)
        #self.DisableOutput()
        return measure

    def RunScript(self, scriptName, args):


        sargs = ','.join(map(lambda x: '\"{0}\"'.format(x), args))
        rline = '{0}({1})'.format(scriptName, sargs)
        print 'Running: {0}'.format(rline)
        self.Handle.write(rline)

        self.Handle.timeout = 20000
        time.sleep(0.25)
        
        l = self.Handle.read()
        while l.find('Done') == -1:
            try:
                print l
                l = self.Handle.read()
            except vxi11.vxi11.Vxi11Exception as e:
                print 'exception {0}'.format(e)
                break

        self.Handle.write('printbuffer(1, smua.nvbuffer1.n, smua.nvbuffer1.readings)')
        lastMeasure = self.Handle.read()
        self.Current = lastMeasure.strip().split(',')
        time.sleep(0.25)
        self.Handle.write('printbuffer(1,smua.nvbuffer2.n,smua.nvbuffer2.readings)')
        volts = self.Handle.read()
        self.Volts = volts.strip().split(',')
        
        self.Discharge(self.Discharge0)
        self.Beep([(0.5, 400)])
        self.WriteData()

    
    def Discharge(self, n=10):
        print "Discharging cycle, measurements =",n
        self.Handle.write('smu.measure.range = 100e-9')
        self.SetVoltage(0)
        self.EnableOutput()
        for i in range(n):
            self.Handle.write('print(smu.measure.read())')
            measure = self.Handle.read()
            sys.stdout.write(str(i%10))
            sys.stdout.flush()
            time.sleep(1)
        print ""
        self.DisableOutput()
        

    def MeasureIV(self):
        self.Beep([(0.5,200)])
        self.Discharge(self.Discharge0) 
        self.Handle.write('smu.measure.autozero.once()')
        self.Handle.write('smu.source.configlist.create("VoltListSweep")')
        for volt in self.Volts:
            line = 'smu.source.level = {0}'.format(volt)
            #print line
            self.Handle.write(line)
            self.Handle.write('smu.source.configlist.store("VoltListSweep")')
        self.Handle.write('smu.source.sweeplist("VoltListSweep",1)')
        self.Handle.write('trigger.model.setblock(6, trigger.BLOCK_NOP)\n')
        self.Handle.write('trigger.model.setblock(10, trigger.BLOCK_BRANCH_ALWAYS, 11)\n')
        self.Handle.write('trigger.model.initiate()')
        
        #self.Handle.write('waitcomplete()')
        self.Handle.timeout = 20000
        time.sleep(0.25)
        opcValue = '0'

	print 'recvd %s' % opcValue
    	print 'waiting for opc'
   	while (opcValue.find('1') == -1):
            print "ask OPC"
            try:
                opcValue = self.Handle.ask('*OPC?')
                print 'opc value recvd %s' % opcValue
                time.sleep(10)
	    except vxi11.vxi11.Vxi11Exception as e:
	        print 'timeout? {0}'.format(e)
                continue

        self.Handle.write('printbuffer(1,defbuffer1.n,defbuffer1.readings)')
        lastMeasure = self.Handle.read()
        self.Current = lastMeasure.strip().split(',')
        self.Discharge(self.Discharge1)
        self.Beep([(0.5,400)])



    
