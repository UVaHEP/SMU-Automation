import vxi11
import time,sys
from numpy import array

# To do kill other possible conenctions in Connect method before starting

# Sourcemeter base class
class Sourcemeter:
    def __init__(self, host, port):
        # "hardwired" limits
        self.ilimit=10e-3
        self.Vmax=3
        self.Vmin=-80
        self.host = host
        self.port = port
        self.volts = []
        self.current = []
        self.hysteresisScan=False
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
            volts=array(range(steps+1))*1.0/steps*(vEnd-vStart) # fix bug!
            self.volts=volts.tolist()
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
            while round(volt,4)>=(-60.0):
                self.volts.append(str(round(volt,4)))
                if round(volt,4) >(-40.0):
                    volt += -0.5
                elif round(volt,4) >(-50.0):
                    volt += -0.1
                else:
                    volt += -0.05

                    
    # Get list of voltages from a text file
    def ReadVfile(self, file):
        f = open(file, 'r')
        if file[-3:] == 'csv':
            for line in f:
                values = line.split(',')
                if len(values) > 4:
                    self.volts.append(values[3])
                if not volts == []:        
                    del volts[0]
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
        self.handle = vxi11.Intrument(self.host)
        self.Connect()

    def __del__(self):
        self.handle.close()
        print 'Closing TCP connection'
    def DisableOutput(self):
        self.handle.write('smua.source.output = smua.OFF')
    def EnableOutput(self):
        self.handle.write('smua.source.output = smua.ON')

    def Reset(self):
        self.handle.write('smua.reset()')

    def OutputFn(self, func):
        cmd = 'smua.source.func = {0}'
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
        cmd = 'smua.measure.autorangei = {0}'
        if state:
            cmd = cmd.format('smua.AUTORANGE_ON')
        else:
            cmd = cmd.format('smua.AUTORANGE_OFF')
        self.handle.write(cmd)
        
    def SetCurrentLimit(self, current):
        cmd = 'smua.source.ilimit.level = {0}'
        try:
            i = float(current)
            cmd = cmd.format(i)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad current in voltageLimit'
            
    def SetVoltageLimit(self, voltage):
        cmd = 'smua.source.limitv = {0}'
        try:
            volt = float(voltage)
            cmd = cmd.format(volt)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in voltageLimit'

    def Model(self):
        identity = self.handle.ask("*IDN?")
        return identity

    def SetVoltage(self, v):
        cmd = 'smua.source.levelv = {0}'
        try:
            voltage = float(v)
            if (voltage < self.Vmin):
                voltage = self.Vmin
            elif (voltage > self.Vmax):
                voltage = self.Vmax
            cmd = cmd.format(voltage)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in Set Voltage'


    
    def Connect(self):
        self.DisableOutput()
        self.OutputFn('voltage')
        self.SetVoltageLimit(-80)
        self.SetCurrentLimit(self.ilimit)
        self.Autorange(1)
        self.EnableOutput()
        self.handle.timeout = 2000000


    def MeasureIV(self):
        self.handle.write('mylist = {}')

        length = len(self.volts)
        for volt in self.volts:
            line = 'table.insert(mylist, {0})'.format(volt)
            self.handle.write(line)

        self.handle.write('SweepVListMeasureI(smua, mylist, 1,'+str(length)+')')

        print length
        self.handle.write('opc()')

        for i in range(length):
            num = self.handle.ask('print(smua.nvbuffer1.readings['+str(i+1)+']')
            self.current.append(num)

class Keithley2450(Sourcemeter):
    def __init__(self, host, port):
        Sourcemeter.__init__(self, host, port)
        self.handle=vxi11.Instrument(self.host)
        self.ClearBuffer()
        self.Connect()
        self.SetRepeatAverage(3)  # Average 3 samples / measurement
        self.handle.write('smu.source.delay = 1.0')
        self.SetVoltageLimit(-80)  # need to improve for Fwd protection
        self.SetCurrentLimit(self.ilimit)
        self.Autorange(1)
        self.handle.write('smu.measure.nplc = 3')
        #self.handle.write('smu.source.autodelay = smu.ON')
        #self.handle.write('trigger.model.abort()')
        
    def __del__(self):
        #self.handle.write('trigger.model.abort()')
        self.handle.close()
        print "Closing TCP connection"
 
    def Connect(self):
        identity = self.Model()
        if (identity.find('MODEL 2450') != -1):
            print 'Model: '+identity
        else:
            print 'Wrong Model %s' % identity
            self.handle.close()
            return            
        self.Reset()
        self.DisableOutput()
        self.OutputFn('voltage')	

    def ClearBuffer(self):
        self.handle.write('print(1234567890)')  #
        try:
	    junk = self.handle.read()               # make sure buffer is clear
            while(junk.find('123456789') == -1):
                junk = self.handle.read()
        except vxi11.vxi11.Vxi11Exception as e:
            print 'timed out waiting for clear buffer? {0}'.format(e)

        
    def Beep(self, notes):
        #Beep takes a list of tuples where each tuple consists of
        #two elements (duration in seconds, frequency in hertz)
        #so pass in something like [(0.5, 200), (0.25, 450), ... ]
        cmd = 'beeper.beep({0}, {1})'
        try: 
            for note in notes:
                duration, freq = note
                beepcmd = cmd.format(duration, freq)
                self.handle.write(beepcmd)
        except Exception as e:
            print 'Beeper failed to work.'


    def DisableOutput(self):
        self.handle.write('smu.source.output = smu.OFF')
    def EnableOutput(self):
        self.handle.write('smu.source.output = smu.ON')

    def Reset(self):
        self.handle.write('smu.reset()')

    def OutputFn(self, func):
        cmd = 'smu.source.func = {0}'
        if func == 'voltage':
            cmd = cmd.format('smu.FUNC_DC_VOLTAGE')
        elif func == 'current':
            cmd = cmd.format('smu.FUNC_DC_CURRENT')
        else:
            print 'bad output function'
            return
        self.handle.write(cmd)

    def Autorange(self, state):
        cmd = 'smu.measure.autorange = {0}'
        if state:
            cmd = cmd.format('smu.ON')
        else:
            cmd = cmd.format('smu.OFF')
        self.handle.write(cmd)
        
    def SetCurrentLimit(self, current):
        cmd = 'smu.source.ilimit.level = {0}'
        try:
            i = float(current)
            cmd = cmd.format(i)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad current in CurrentLimit'
            
    def SetVoltageLimit(self, voltage):
        cmd = 'smu.source.range = {0}'
        try:
            volt = float(voltage)
            cmd = cmd.format(volt)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in VoltageLimit'

    def SetRepeatAverage(self,samples):
        if samples<=1:
            self.handle.write('smu.measure.filter.enable = smu.OFF')
            return
        self.handle.write('smu.measure.filter.count = {0}'.format(samples))
        self.handle.write('smu.measure.filter.type = smu.FILTER_REPEAT_AVG')
	self.handle.write('smu.measure.filter.enable = smu.ON')
            
    def Model(self):
        identity = self.handle.ask("*IDN?")
        return identity

    def SetVoltage(self, v):
        cmd = 'smu.source.level = {0}'
        try:
            voltage = float(v)
            cmd = cmd.format(voltage)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in Set Voltage'

    def ReadVIPoint(self,v=None):
        if v != None:
            self.SetVoltage(v)
        #set to 1 measurement
        self.handle.write('smu.measure.count = 1')
        self.EnableOutput()
        self.handle.write('print(smu.measure.read())')
        measure = self.handle.read()
        print 'i-v measure: {0}'.format(measure)
        self.DisableOutput()
        return measure

    def Discharge(self, n=60):
        print "Discharging cycle, measurements =",n
        self.SetVoltage(0)
        self.handle.write('smu.source.output = smu.ON')
        for i in range(n):
            self.handle.write('print(smu.measure.read())')
            measure = self.handle.read()
            sys.stdout.write(str(i%10))
            sys.stdout.flush()
            time.sleep(1)
        print ""
        self.ClearBuffer()
        self.handle.write('smu.source.output = smu.OFF')
        

    def MeasureIV(self):
        self.Beep([(0.5,200)])
        self.Discharge(10) 
        self.handle.write('smu.measure.autozero.once()')
        self.handle.write('smu.source.configlist.create("VoltListSweep")')
        for volt in self.volts:
            line = 'smu.source.level = {0}'.format(volt)
            self.handle.write(line)
            self.handle.write('smu.source.configlist.store("VoltListSweep")')
        self.handle.write('smu.source.sweeplist("VoltListSweep",1)')
        self.handle.write('trigger.model.initiate()')
#        self.handle.write('waitcomplete()')
        self.handle.timeout = 20000
        time.sleep(0.25)
        opcValue = '0'

	print 'recvd %s' % opcValue
    	print 'waiting for opc'
   	while (opcValue.find('1') == -1):
            try:
                opcValue = self.handle.ask('*OPC?')
                print 'opc value recvd %s' % opcValue
                time.sleep(20)
	    except vxi11.vxi11.Vxi11Exception as e:
	        print 'timeout? {0}'.format(e)
                continue

        self.ClearBuffer()
        self.handle.write('printbuffer(1,defbuffer1.n,defbuffer1.readings)')
        lastMeasure = self.handle.read()
        self.current = lastMeasure.strip().split(',')
        #self.Discharge()
        self.Beep([(0.5,400)])

