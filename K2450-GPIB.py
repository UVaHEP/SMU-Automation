import serial
import time, sys
from math import sqrt
from numpy import array

class K2450GPIB:
    def __init__(self, comport, addr):
        self.ilimit = 1e-3
        self.Vmax = -3
        self.Vmin = 80
        self.comport = comport
        self.addr = addr
        self.volts = []
        self.current = []
        self.discharge0 = 10 #discharge cycles before
        self.discharge1 = 60 #and afrer measurement
        self.handle = serial.Serial(comport, timeout=2)
        self.handle.write('++auto 0\r')
        self.ClearBuffer()
        self.Connect()
        self.Config()

    def Config(self):
        self.SetRepeatAverage(3) #Average 3 samples/measurement
        self.SetSourceDelay(1)# hold off time before measurements
        self.InputFn('voltage')
        self.OutputFn('current')
        self.SetVoltageLimit(80) #need to get Fwd protection
        self.SetCurrentLimit(self.ilimit)
        self.Autorange(1)
        self.SetNPLC(3)
        

    def __del__(self):
        self.handle.close()
        print 'Closing connection'

    def Connect(self):
        pass
    
    def ClearBuffer(self):
        self.handle.write('print(1234567890)\r')
        try:
            self.handle.write('++read\r')
            junk = self.handle.read(20)
            #print 'first junk:'+junk.strip()
            while(junk.find('123456789') == -1):
                self.handle.write('++read\r')
                self.handle.write('print(1234567890)\r')
                junk = self.handle.read(20)
                #print 'next junk:'+junk.strip()
        except serial.SerialTimeoutException as e:
            print 'timed out waiting for clear buffer? {0}'.format(e)

    def Beep(self,notes):
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
        self.handle.write('smu.source.output = smu.OFF\r')

    def EnableOutput(self):
        self.handle.write('smu.source.output = smu.ON\r')

    def Reset(self):
        self.handle.write('smu.reset()\r')
        self.Config()

    def OutputFn(self,func):
        cmd = 'smu.measure.func = {0}\r'
        if func == 'voltage':
            cmd = cmd.format('smu.FUNC_DC_VOLTAGE')
        elif func == 'current':
            cmd = cmd.format('smu.FUNC_DC_CURRENT')
        else:
            print 'bad output function'
            return
        self.handle.write(cmd)
        
    def InputFn(self,func):
        cmd = 'smu.source.func = {0}\r'
        if func == 'voltage':
            cmd = cmd.format('smu.FUNC_DC_VOLTAGE')
        elif func == 'current':
            cmd = cmd.format('smu.FUNC_DC_CURRENT')
        else:
            print 'bad input function'
            return
        self.handle.write(cmd)

    def Autorange(self,state):
        #for now only handles current autoranging
        cmd = 'smu.measure.autorange = {0}\r'
        if state:
            cmd = cmd.format('smu.ON')
        else:
            cmd = cmd.format('smu.OFF')
        self.handle.write(cmd)

    def SetCurrentLimit(self,current):
        cmd = 'smu.measure.limit[1].high.value = {0}\r'
        try:
            i = float(current)
            cmd = cmd.format(i)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad current in currentLimit'

    def SetVoltageLimit(self,voltage):
        cmd = 'smu.source.protect.level = smu.PROTECT_40V\r'
        try:
            volt = float(voltage)
            #cmd = cmd.format(volt)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in voltageLimit'

    def SetRepeatAverage(self,samples):
        if samples<=1:
            self.handle.write('smu.measure.filter.enable = smu.OFF\r')
            return
        self.handle.write('smu.measure.filter.count = {0}\r'.format(samples))
        self.handle.write('smu.measure.filter.type = smu.FILTER_REPEAT_AVG\r')
	self.handle.write('smu.measure.filter.enable = smu.ON\r')


    def SetSourceDelay(self,delay):
        self.handle.write('smu.source.delay = {0}\r'.format(delay))

    def SetNPLC(self, nplc=3):
        self.handle.write('smu.measure.nplc = {0}\r'.format(nplc))

    def Model(self):
        self.handle.write('*IDN?\r')
        self.handle.write('++read\r')
        identity = self.handle.read(100)
        print identity

    def SetVoltage(self,v):
        cmd = 'smu.source.level = {0}\r'
        try:
            voltage = float(v)
            cmd = cmd.format(voltage)
            self.handle.write(cmd)
        except ValueError as e:
            print 'bad voltage in SetVoltage'

    def ReadIVPoint(self, v=None): 
        self.handle.write('testData = buffer.make(100)\r')
        if v != None:
            self.SetVoltage(v) #otherwise use last set voltage
        #self.handle.write('smu.measure.count = 1\r')
        self.EnableOutput()
        self.handle.write('trigger.model.load("SimpleLoop", 3, 0, testData)\r')
        self.handle.write('trigger.model.initiate()\r')

        self.handle.timeout = 5
        opcValue = '0'
        #print 'recvd: {0}'.format(opcValue)
        #print 'waiting for opc'

        while (opcValue.find('1') == -1):
            try:
                self.handle.write('opc()\r')
                self.handle.write('print("1")\r')
                self.handle.write('++read\r')
                opcValue = self.handle.read(20)
                #print 'opc value recvd: {0}'.format(opcValue)
                time.sleep(0.25)
            except Exception as e:
                print 'Exception: {0}'.format(e)
                continue

        self.handle.write('printbuffer(1,3, testData.readings, testData.sourcevalues)\r')
        self.handle.write('++read\r')
        datastr = self.handle.read(100)
        #print 'datastr:'+datastr
        datacut = datastr.strip().split('\n')
        #print 'datacut:'+str(datacut)
        datalist = datacut[0].strip().split(',')
        #print 'datalist:'+ str(datalist)
        data = map(float, datalist)
        current = (data[0]+data[2]+data[4])/3.0
        voltage = (data[1]+data[3]+data[5])/3.0

        self.DisableOutput()
        self.handle.write('buffer.clearstats(testData)\r')
        self.handle.write('buffer.delete(testData)\r')

        bytein = self.handle.inWaiting()
        byteout = self.handle.outWaiting()
        
        #print "bytes:"+str(bytein)+', '+str(byteout)
        return str(voltage)+'    '+ str(current)
        

    def Discharge(self, n=10):
        print "Discharging cycle, measurements =",n
        self.SetVoltage(0)
        self.EnableOutput()
        for i in range(n):
            self.handle.write('print(smu.measure.read())\r')
            self.handle.write('++read\r')
            measure = self.handle.read(1000)
            sys.stdout.write(str(i%10))
            sys.stdout.flush()
            time.sleep(1)
        print ""
        self.DisableOutput()
        self.ClearBuffer()
        

    def MeasureIV(self):
        self.Beep([(0.5,200)])
        self.Discharge(self.discharge0)
        self.handle.write('smu.measure.autozero.once()\r')
        self.handle.write('smu.source.configlist.create("VoltListSweep")\r')
        self.volts = [12,10,8]
        for volt in self.volts:
            line = 'smu.source.level = {0}\r'.format(volt)
            self.handle.write(line)
            self.handle.write('smu.source.configlist.store("VoltListSweep")\r')
        self.handle.write('smu.source.sweeplist("VoltListSweep",1)\r')
        self.handle.write('trigger.model.initiate()\r')

        self.handle.timeout = 20000
        time.sleep(0.25)
        opcValue = '0'

        print 'recvd %s' % opcValue
        print 'waiting for opc'
        while (opcValue.find('1') == -1):
            print "ask OPC"
            try:
                self.handle.write('*OPC?\r')
                self.handle.write('++read\r')
                opcValue = self.handle.read(1000)
                time.sleep(10)
            except serial.SerialTimeoutException as e:
                print 'timeout? {0}'.format(e)
                continue

        self.ClearBuffer()

        self.handle.write('printbuffer(1,defbuffer1.n,defbuffer1.readings)\r')
        self.handle.write('++read\r')
        lastMeasure = self.handle.read(1000)
        self.current = lastMeasure.strip().split(',')
        self.Discharge(self.discharge1)
        self.Beep([(0.5,400)])

    def PrintData(self):
        return self.current
        
        
