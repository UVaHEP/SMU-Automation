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
    # Features to add
    #################

    def Beep(self):
        #Bring the noise
        pass
    def Arm(self):
        pass
    def DisArm(self):
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

    def Connect(self):
        self.handle.write('smua.reset()')

        self.handle.write('smua.source.output = smua.OUTPUT_OFF')
        self.handle.write('smua.source.func = smua.OUTPUT_DCVOLTS')
        self.handle.write('smua.source.limitv = -80')
        self.handle.write('smua.source.limiti = '+str(self.limit))
        self.handle.write('smua.measure.autorangei = smua.AUTORANGE_ON')
        self.handle.write('smua.source.output = smua.OUTPUT_ON')
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
        
    def __del__(self):
        self.handle.close()
        print "Closing TCP connection"
        
    def Connect(self):
        identity = self.handle.ask("*IDN?")
        if (identity.find('MODEL 2450') != -1):
            print 'Model: '+identity
        else:
            print 'Wrong Model %s' % identity
            self.handle.close()
            return
            

        self.handle.write('smu.reset()')
        #Set output limits and range 
        self.handle.write('smu.source.output = smu.OFF')
        self.handle.write('smu.source.func = smu.FUNC_DC_VOLTAGE')
        
        self.handle.write('smu.source.autorange = smu.ON')
       
        self.handle.write('smu.measure.autorange = smu.ON')
      #  self.handle.write('smu.source.range = -80')
        self.handle.write('smu.source.output = smu.ON')
        self.handle.write('smu.source.output = smu.OFF')
        print 'limit:'+str(self.limit)
        self.handle.write('smu.source.ilimit.level = {0}'.format(self.limit))

    def MeasureIV(self):
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


