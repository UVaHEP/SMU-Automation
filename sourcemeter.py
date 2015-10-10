import vxi11
import time
from numpy import array

# Sourcemeter base class
class Sourcemeter:
    def __init__(self, host, port, limit=2e-3):
        self.host = host
        self.port = port
        self.limit = limit  # default current limit set above
        self.volts = []
        self.current = []
        self.Vmax=3   # "hardwired" voltage limits
        self.Vmin=-80
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
            volts=array(range(steps+1))*1.0/steps*(vEnd-vStart)
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
        self.hysteresisScan=True
        hst=list(self.volts)
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
            print 'Writing to {0}.'.format(output)
            outputFile = open(output,'w+')
            outputFile.write('Repeat,VAR2,Point,Voltage,Current,Time\n')
        print len(self.current)
        print 'voltage:'
        print len(self.volts)
        for i in range(len(self.current)):
            try:
                current = str(self.current[i]).lstrip('+')
                outputStr = '1,1,1,{0},{1},1\n'.format(self.volts[i], current)
                if outputFile:
                    outputFile.write(outputStr)
                formattedStr = '%3d %6.2f %6.2e' % (i, float(self.volts[i]), float(current))
                print formattedStr
            except Exception as e:
                print 'something went wrong when writing: {0}.'.format(e)

        if output != "":
             outputFile.close()
         
                #print "%3d %6.2f %6.2e" % (i,self.volts[i],float(self.current[i].lstrip('+')))          
#            outputString = "{0},{1},{2},{3},{4},{5}\n".format(1,1,1,str(self.volts[i]),str(self.current[i]).lstrip('+'),1)
#            print "%3d %6.2f %6.2e" % (i,self.volts[i],float(self.current[i].lstrip('+')))
 #           if output != "": outputFile.write(outputString)



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
    def VoltageLimit(self, voltage):
        pass
    def CurrentLimit(self, current):
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

    def __init__(self, host, port, limit):
        Sourcemeter.__init__(self, host, port, limit)
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
        
    def CurrentLimit(self, current):
        cmd = 'smua.source.ilimit.level = {0}'
        try:
            i = float(current)
            cmd = cmd.format(i)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad current in voltageLimit'
            
    def VoltageLimit(self, voltage):
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
        self.VoltageLimit(-80)
        self.CurrentLimit(self.limit)
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
    def __init__(self, host, port, limit):
        Sourcemeter.__init__(self, host, port, limit)
        self.handle=vxi11.Instrument(self.host)
        self.Connect()
        self.handle.write('smu.source.delay = 1.0')
        #self.handle.write('smu.source.autodelay = smu.ON')
        self.handle.write('smu.model.abort()')
        
    def __del__(self):
        self.handle.write('smu.model.abort()')
        self.handle.close()
        print "Closing TCP connection"
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
        
    def CurrentLimit(self, current):
        cmd = 'smu.source.ilimit.level = {0}'
        try:
            i = float(current)
            cmd = cmd.format(i)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad current in CurrentLimit'
            
    def VoltageLimit(self, voltage):
        cmd = 'smu.source.range = {0}'
        try:
            volt = float(voltage)
            cmd = cmd.format(volt)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in VoltageLimit'

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
    
    def Connect(self):
        
        identity = self.Model()
        if (identity.find('MODEL 2450') != -1):
            print 'Model: '+identity
        else:
            print 'Wrong Model %s' % identity
            self.handle.close()
            return
            

        self.Reset()
        #Set output limits and range 
        self.DisableOutput()
        self.OutputFn('voltage')
        self.VoltageLimit(-80)
        self.CurrentLimit(self.limit)
        self.Autorange(1)
        self.EnableOutput()
        self.DisableOutput()


    def MeasureIV(self):
        self.Beep([(0.5,200)])
        self.handle.write('smu.measure.autozero.once()')
        self.handle.write('smu.source.configlist.create("VoltListSweep")')
        for volt in self.volts:
            line = 'smu.source.level = {0}'.format(volt)
            self.handle.write(line)
            self.handle.write('smu.source.configlist.store("VoltListSweep")')
        self.handle.write('smu.source.sweeplist("VoltListSweep",1,0.2)')
        self.handle.write('trigger.model.initiate()')
        self.handle.write('waitcomplete()')
        self.handle.timeout = 2000000
        time.sleep(0.25)
        opcValue = self.handle.ask('*OPC?')
        print 'recvd %s' % opcValue
        print 'waiting for opc'
        while (opcValue.find('1') == -1):
            print 'opc not found'
            opcValue = self.handle.ask('*OPC?')
            print 'recvd %s' % opcValue
            
        print 'Found opc'
            
        self.handle.write('printbuffer(1,defbuffer1.n,defbuffer1.readings)')
        lastMeasure = self.handle.read()
        #print (lastMeasure)

        self.current = lastMeasure.strip().split(',')
        self.Beep([(0.5,400)])

