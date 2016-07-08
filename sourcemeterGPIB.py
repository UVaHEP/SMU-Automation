import serial
import random
import time,sys
from math import sqrt
from numpy import array


# To do kill other possible conenctions in Connect method before starting

# Sourcemeter base class
class Sourcemeter:
    def __init__(self, host, port):
        # "hardwired" limits
        self.ilimit=1e-3
        self.Vmax=3
        self.Vmin=-80
        self.host = host
        self.port = port
        self.volts = []
        self.current = []
        self.hysteresisScan=False
        self.discharge0=5  # discharge cycles before
        self.discharge1=5  # and after measurement
        
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
        self.discharge0=t0
        self.discharge1=t1
    
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
                self.volts.append(vEnd)
                return
            delta = float(vEnd-vStart)/float(steps)
            for i in range(0,steps+1):
                self.volts.append(i*delta+vStart)
                
            #volts=array(range(steps+1))*1.0/steps*(vEnd-vStart) # fix bug!
            #self.volts=volts.tolist()
        else: # (maximum) step size is set
            volt=vStart
            dV=cmp(vEnd-vStart,0)*dV # get the sign right
            while abs(volt)<abs(vEnd):
                self.volts.append(volt)
                volt=volt+dV
            self.volts.append(vEnd)

    def AddHysteresis(self):
        if self.hysteresisScan: return
	print "Setting backwards hysteresis scan"
        self.hysteresisScan=True
        hst=list(self.volts) # copy the list of voltages
        hst.reverse()
        self.volts.extend(hst) 
            
    def MakeList(self,direction):        
        if direction>0:
            volt = 0.0
            while round(volt,4) <= 3.0:
                self.volts.append(str(round(volt,4)))
                volt += 0.05

        else:
            volt = 0.0
            while round(volt,4)>=(-70.0):
                self.volts.append(str(round(volt,4)))
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
                    self.volts.append(values[3])
            if not self.volts == []:
                print self.volts
                del self.volts[0]
        elif self.volts == []:
            for line in f:
                splitSpace =[]
                newline = line.replace(',',' ')
                splitSpace = newline.split()
                if len(splitSpace) >1:
                    for i in range(len(splitSpace)):
                        self.volts.append(splitSpace[i])
                    else:
                        if not splitSpace == []:
                            self.volts.append(splitSpace[0])
        f.close()

    def MeasureIV(self):
        print 'doing list sweep'
        pass

    # dump the IV curve data to the screen and optionally a file
    def WriteData(self, output=""):
        if output != "":
            print 'Writing SMU data to {0}.'.format(output)
            outputFile = open(output,'w+')
            outputFile.write('Repeat,VAR2,Point,Voltage,Current,Time\n')
        # len(self.volts) possibly > len(self.current)
        for i in range(len(self.current)): # n.b. sample list may be truncated by ilimit
            try:
                current = str(self.current[i]).lstrip('+')
                outputStr = '1,1,1,{0},{1},1\n'.format(self.volts[i], current)
                if outputFile: outputFile.write(outputStr)
                else: 
                    oStr = '%3d %6.2f %6.2e' % (i, float(self.volts[i]), float(current))
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
        self.handle = serial.Serial(host, timeout=2)
        self.handle.write('\n')
        self.handle.write('++read_tmo_ms 1500\n')
        self.handle.write('++auto 0\n')
        self.ClearQueue()
        self.ClearBuffer()
        self.Connect()
        self.Config()
        
    def Config(self):
        self.SetRepeatAverage(3)  # Average 3 samples / measurement
        self.SetSourceDelay(1.0)  # hold off time before measurements
        self.SetVoltageLimit(80) # need to improve for Fwd protection
        self.SetCurrentLimit(self.ilimit)
        self.Autorange(1)
        self.SetNPLC(3)
        #self.handle.write('smu.source.autodelay = smu.ON')
        #self.handle.write('trigger.model.abort()')
                    
    def __del__(self):
        self.handle.close()
        print 'Closing TCP connection'
    
    def Connect(self):
        identity = self.Model()
        if (identity.find('Model 2611A') != -1):
            print 'Model: '+identity
        else:
            print 'Wrong Model %s' % identity
            self.handle.close()
            return            
        #self.Reset()
        #self.DisableOutput()
        self.OutputFn('voltage')       

    def ClearQueue(self):
        self.handle.write('errorqueue.clear()\n')
        
    def ClearBuffer(self):
        self.handle.flush()
        value = random.randint(0,9999)
        self.handle.write('print("{0!s}")\n'.format(value)) 
        try:
            time.sleep(2)
            self.handle.write('++read eoi\n')
	    junk = self.handle.readline() # make sure buffer is clear
            print 'first junk: ' +junk
            while(junk.find('{0!s}'.format(value)) == -1):
                time.sleep(2)
                self.handle.write('++read eoi\n')
                junk = self.handle.readline()
                print 'next junk:'+junk
                if junk == '':
                    self.handle.write('print("{0!s}")\n'.format(value))
        except Exception as e:
            print 'timed out waiting for clear buffer? {0}'.format(e)

    def Beep(self, notes):
        #Beep takes a list of tuples where each tuple consists of
        #two elements (duration in seconds, frequency in hertz)
        #so pass in something like [(0.5, 200), (0.25, 450), ... ]
        cmd = 'beeper.beep({0}, {1})\n'
        try: 
            for note in notes:
                duration, freq = note
                beepcmd = cmd.format(duration, freq)
                self.handle.write(beepcmd)
        except Exception as e:
            print 'Beeper failed to work.'

  
        
    def DisableOutput(self):
        self.handle.write('smua.source.output = smua.OUTPUT_OFF\n')
    def EnableOutput(self):
        self.handle.write('smua.source.output = smua.OUTPUT_ON\n')

    def Reset(self):
        self.handle.write('smua.reset()\n')
        self.Config()

    def OutputFn(self, func):
        cmd = 'smua.source.func = {0}\n'
        if func == 'voltage':
            cmd = cmd.format('smua.OUTPUT_DCVOLTS')
        elif func == 'current':
            cmd = cmd.format('smua.OUTPUT_DCAMPS')
        else:
            print 'bad output function'
            return
        self.handle.write(cmd)

    def Autorange(self, state):
        #for now only handle current measuring, will change
        #to handle voltage autoranging as well
        cmd = 'smua.measure.autorangei = {0}\n'
        if state:
            cmd = cmd.format('smua.AUTORANGE_ON')
        else:
            cmd = cmd.format('smua.AUTORANGE_OFF')
        self.handle.write(cmd)

      
    def SetCurrentLimit(self, current):
        cmd = 'smua.source.limiti = {0}\n'
        try:
            i = float(current)
            cmd = cmd.format(i)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad current in voltageLimit'
            
    def SetVoltageLimit(self, voltage):
        cmd = 'smua.source.limitv = {0}\n'
        try:
            volt = float(voltage)
            cmd = cmd.format(volt)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in voltageLimit'

    def SetRepeatAverage(self,samples):
        if samples<=1:
            self.handle.write('smua.measure.filter.enable = smua.FILTER_OFF\n')
            return
        self.handle.write('smua.measure.filter.count = {0}\n'.format(samples))
        self.handle.write('smua.measure.filter.type = smua.FILTER_REPEAT_AVG\n')
	self.handle.write('smua.measure.filter.enable = smua.FILTER_ON\n')

    def SetSourceDelay(self,delay):
        self.handle.write('smua.source.delay = {0}\n'.format(delay))

            
    def SetNPLC(self,nplc=3):
        self.handle.write('smua.measure.nplc = {0}\n'.format(nplc))
            
    def Model(self):
        self.handle.write("*IDN?\n")
        self.handle.write('++read eoi\n')
        identity = self.handle.readline()
        return identity

    def SetVoltage(self, v):
        cmd = 'smua.source.levelv = {0}\n'
        try:
            voltage = float(v)
            cmd = cmd.format(voltage)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in Set Voltage'
    
    def ReadVIPoint(self,v=None):
        #self.handle.write('testData = smua.makebuffer(100)\n')
        #self.handle.write('smua.testData.collectsourcevalues = 1\n')
        if v != None:
            self.SetVoltage(v) # otherwise use last set voltage
            #set to 1 measurement
        self.handle.write('smua.measure.count = 1\n')
        self.handle.write('smua.measure.interval = 0.1\n')
        self.EnableOutput()
        self.handle.write('print(smua.measure.i())\n')
        #self.handle.write('waitcomplete()\n')
        #self.handle.write('printbuffer(1,3, testData.readings)\n')
        self.handle.write('++read eoi\n')
        datastr = self.handle.readline()
        #print 'original data:'+datastr
        while datastr == '':
            self.handle.write('++read eoi\n')
            datastr = self.handle.readline()
            #print 'datastr:'+datastr
        datacut = datastr.strip().split('\n')
        datalist = datacut[0].strip().split(',')
        data = map(float, datalist)
        current = (data[0])
        self.DisableOutput()
        #self.handle.write('smua.testData.clear()\n')
        #self.handle.write('testData = nil\n')
        return str(v)+'     '+str(current)

    def Discharge(self, n=10):
        print "Discharging cycle, measurements =",n
        self.SetVoltage(0)
        self.EnableOutput()
        for i in range(n):
            self.handle.write('print(smua.measure.i())\n')
            self.handle.write('++read eoi\n')
            measure = self.handle.readline()
            sys.stdout.write(str(i%10))
            sys.stdout.flush()
            time.sleep(1)
        print ""
        self.DisableOutput()
        self.ClearBuffer()

  
    def MeasureIV(self):
        self.Beep([(0.5,200)])
        self.Discharge(self.discharge0)
        time.sleep(5)
        print 'about to measure iv'
        self.handle.write('smua.measure.autozero = 1\n')        
        self.handle.write('mylist = {}\n')

        length = len(self.volts)
        for volt in self.volts:
            line = 'table.insert(mylist, {0})\n'.format(volt)
            self.handle.write(line)

        self.handle.write('SweepVListMeasureI(smua, mylist, 1,'+str(length)+')\n')

        self.handle.timeout = 2
        time.sleep(0.25)
        opcValue = '0'
        
        self.handle.write('*OPC?\n')
    	print 'waiting for opc'
   	while (opcValue.strip() != '1'):
            try:
                #self.handle.write('print("3")\n')
                time.sleep(10)
                self.handle.write('++read eoi\n')
                #bytein = self.handle.inWaiting()
                #byteout = self.handle.outWaiting()
                #print "bytes:"+str(bytein)+', '+str(byteout)
                opcValue = self.handle.readline()
                print 'opc value recvd {0}'.format(opcValue)
                time.sleep(1)
	    except Exception as e:
	        print 'timeout? {0}'.format(e)
                continue
        print 'does it ever get here?'
        self.ClearBuffer()
        self.handle.write('print(smua.nvbuffer1.n)\n')
        self.handle.write('++read eoi\n')
        bufSzread = self.handle.readline()
        #print type(bufSzread)
        #print bufSzread
        bufSzread = bufSzread.strip()
        bufSz = float(bufSzread)
        bufSz = int(bufSz)

        n =1
        nlimit = 15
        Next = n+nlimit-1
        if (Next > bufSz):
            Next = bufSz

        while (n<= bufSz):
            Next = n+nlimit-1
            print ('Reading out from {0} to {1}'.format(n, Next))
            if (Next >= bufSz):
                Next = bufSz
            self.handle.write('printbuffer({0},{1}, smua.nvbuffer1.readings)\n'.format(n,Next))
            self.handle.write('++read eoi\n')
            data = self.handle.readline()
            self.current += map(float, data.strip().split(','))
            n += nlimit

        
        self.Discharge(self.discharge1)
        self.Beep([(0.5,400)])
        return self.current


            
class Keithley2450(Sourcemeter):
    def __init__(self, host, port):
        Sourcemeter.__init__(self, host, port)
        self.handle = serial.Serial(host, timeout=2)
        self.handle.write('++auto 0\r')
        self.ClearBuffer()
        self.Connect()
        #self.Reset()
        self.Config()

    def Config(self):
        self.SetRepeatAverage(3)  # Average 3 samples / measurement
        self.SetSourceDelay(1.0)  # hold off time before measurements
        self.InputFn('voltage')
        self.OutputFn('current')
        self.SetVoltageLimit(80) # need to improve for Fwd protection
        self.SetCurrentLimit(self.ilimit)
        self.Autorange(1)
        self.SetNPLC(3)
        #self.handle.write('smu.source.autodelay = smu.ON')
        #self.handle.write('trigger.model.abort()')
        
    def __del__(self):
        #self.handle.write('*RST')
        self.handle.close()
        print "Closing connection"
 
    def Connect(self):
        pass
        #identity = self.Model()
        #if (identity.find('MODEL 2450') != -1):
            #print 'Model: '+identity
        #else:
            #print 'Wrong Model %s' % identity
            #self.handle.close()
            #return            
        #self.Reset()
        #self.DisableOutput()
        #self.OutputFn('voltage')	

    def ClearBuffer(self):
        self.handle.write('print(1234567890)\n') 
        try:
	    self.handle.write('++read eoi\n')
            junk = self.handle.read(20)
            #print 'first junk:'+junk.strip()
            while(junk.find('123456789') == -1):
                self.handle.write('++read eoi\n')
                junk = self.handle.readline()
                if junk == '':
                    self.handle.write('print(1234567890)\n')
                #print 'next junk:'+junk.strip()
        except serial.SerialTimeoutException as e:
            print 'timed out waiting for clear buffer? {0}'.format(e)

        
    def Beep(self, notes):
        #Beep takes a list of tuples where each tuple consists of
        #two elements (duration in seconds, frequency in hertz)
        #so pass in something like [(0.5, 200), (0.25, 450), ... ]
        cmd = 'beeper.beep({0}, {1})\r'
        try: 
            for note in notes:
                duration, freq = note
                beepcmd = cmd.format(duration, freq)
                self.handle.write(beepcmd)
        except Exception as e:
            print 'Beeper failed to work.'


    def DisableOutput(self):
        self.handle.write('smu.source.output = smu.OFF\n')
    def EnableOutput(self):
        self.handle.write('smu.source.output = smu.ON\n')

    def Reset(self):
        self.handle.write('smu.reset()\n')
        self.Config()

    def OutputFn(self, func):
        cmd = 'smu.measure.func = {0}\n'
        if func == 'voltage':
            cmd = cmd.format('smu.FUNC_DC_VOLTAGE')
        elif func == 'current':
            cmd = cmd.format('smu.FUNC_DC_CURRENT')
        else:
            print 'bad output function'
            return
        self.handle.write(cmd)

    def InputFn(self,func):
        cmd = 'smu.source.func = {0}\n'
        if func == 'voltage':
            cmd = cmd.format('smu.FUNC_DC_VOLTAGE')
        elif func == 'current':
            cmd = cmd.format('smu.FUNC_DC_CURRENT')
        else:
            print 'bad input function'
            return
        self.handle.write(cmd)

    def Autorange(self, state):
        cmd = 'smu.measure.autorange = {0}\n'
        if state:
            cmd = cmd.format('smu.ON')
        else:
            cmd = cmd.format('smu.OFF')
        self.handle.write(cmd)
        
    def SetCurrentLimit(self, current):
        cmd = 'smu.source.ilimit.level = {0}\n'
        try:
            i = float(current)
            cmd = cmd.format(i)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad current in CurrentLimit'
            
    def SetVoltageLimit(self, voltage):
        cmd = 'smu.source.range = {0}\n'
        try:
            volt = float(voltage)
            cmd = cmd.format(volt)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in VoltageLimit'

    def SetRepeatAverage(self,samples):
        if samples<=1:
            self.handle.write('smu.measure.filter.enable = smu.OFF\n')
            return
        self.handle.write('smu.measure.filter.count = {0}\n'.format(samples))
        self.handle.write('smu.measure.filter.type = smu.FILTER_REPEAT_AVG\n')
	self.handle.write('smu.measure.filter.enable = smu.ON\n')

    def SetSourceDelay(self,delay):
        self.handle.write('smu.source.delay = {0}\n'.format(delay))

    def SetNPLC(self,nplc=3):
        self.handle.write('smu.measure.nplc = {0}\n'.format(nplc))
        
    def Model(self):
        self.handle.write('*IDN?\r')
        self.handle.write('++read eoi\n')
        identity = self.handle.read(100)
        return identity

    def SetVoltage(self, v):
        cmd = 'smu.source.level = {0}\r'
        try:
            voltage = float(v)
            cmd = cmd.format(voltage)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in Set Voltage'
        

    #def ReadUntilStable(self,v=0):
    #    self.SetVoltage(v)
    #    self.handle.write('smu.measure.count = 1')

    def ReadVIPointTest(self,v=None):
        if v != None:
            self.SetVoltage(v) # otherwise use last set voltage
        #set to 1 measurement
        self.handle.write('smu.measure.count = 1')
        self.EnableOutput()
        samps=[]
        nave=5
        for i in range(100):
            self.handle.write('print(smu.measure.read())')
            measure = self.handle.read()
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
        self.handle.write('testData = buffer.make(100)\n')
        if v != None:
            self.SetVoltage(v) #otherwise use last set voltage
        self.handle.write('smu.measure.count = 1\n')
        self.EnableOutput()

        self.handle.write('smu.measure.read(testData)\n')

        self.handle.write('printbuffer(1,1, testData.readings, testData.sourcevalues)\n')
        self.handle.write('++read eoi\n')
        datastr = self.handle.readline()
        while datastr == '':
            self.handle.write('++read eoi\n')
            datastr = self.handle.readline()
            print 'datastr:'+datastr
        datacut = datastr.strip().split('\n')
        print 'datacut:'+str(datacut)
        datalist = datacut[0].strip().split(',')
        print 'datalist:'+ str(datalist)
        data = map(float, datalist)
        current = (data[0])
        voltage = (data[1])

        self.DisableOutput()
        self.handle.write('buffer.clearstats(testData)\n')
        self.handle.write('buffer.delete(testData)\n')

        #bytein = self.handle.inWaiting()
        #byteout = self.handle.outWaiting()
        
        #print "bytes:"+str(bytein)+', '+str(byteout)
        return str(voltage)+'    '+ str(current)

    
    def Discharge(self, n=10):
        print "Discharging cycle, measurements =",n
        self.SetVoltage(0)
        self.EnableOutput()
        for i in range(n):
            self.handle.write('print(smu.measure.read())\n')
            self.handle.write('++read eoi\r')
            measure = self.handle.read(300)
            sys.stdout.write(str(i%10))
            sys.stdout.flush()
            time.sleep(1)
        print ""
        self.DisableOutput()
        self.ClearBuffer()
        

    def MeasureIV(self):
        self.Beep([(0.5,200)])
        self.Discharge(self.discharge0)
        self.handle.write('smu.source.highc = smu.ON\n')
        self.handle.write('smu.measure.autozero.once()\n')
        self.handle.write('smu.source.configlist.create("VoltListSweep")\n')
        print 'length:' + str(len(self.volts))
        for volt in self.volts:
            line = 'smu.source.level = {0}\n'.format(volt)
            self.handle.write(line)
            self.handle.write('smu.source.configlist.store("VoltListSweep")\n')
        self.handle.write('smu.source.sweeplist("VoltListSweep",1)\n')
        self.handle.write('trigger.model.setblock(6, trigger.BLOCK_NOP)\n')
        self.handle.write('trigger.model.setblock(10, trigger.BLOCK_BRANCH_ALWAYS, 11)\n')
        self.handle.write('trigger.model.initiate()\n')
        print 'just started'
        
        #self.handle.write('waitcomplete()')
        self.handle.timeout = .5
        time.sleep(0.25)
        opcValue = '0'

        self.handle.write('*OPC?\n')
    	print 'waiting for opc'
   	while (opcValue.strip() != '1'):
            try:
                self.handle.write('++read eoi\n')
                opcValue = self.handle.readline()
                #print 'opc value recvd: {0}'.format(opcValue)
                time.sleep(1)
            except Exception as e:
                print 'Exception: {0}'.format(e)
                continue
        self.ClearBuffer()
        self.handle.write('print(defbuffer1.n)\n')
        self.handle.write('++read eoi\n')
        bufSz = int(self.handle.readline())
        
        n = 1
        nlimit = 15
        Next = n+nlimit-1
        if (Next > bufSz):
            Next = bufSz

        while (n <= bufSz):
            #print 'Next:'+str(Next)+', bufSz:'+str(bufSz)
            Next = n+nlimit-1
            print ('Reading out from {0} to {1}'.format(n, Next))
            if (Next >= bufSz):
                Next = bufSz
            self.handle.write('printbuffer({0},{1}, defbuffer1.readings)\n'.format(n, Next))
            self.handle.write('++read eoi\n')
            data = self.handle.readline()
            #print 'data:'+data
            self.current += map(float, data.strip().split(','))
            n += nlimit

        self.Discharge(self.discharge1)
        self.Beep([(0.5,400)])
        return self.current

    def PrintData(self):
        return self.current

        


        
    
