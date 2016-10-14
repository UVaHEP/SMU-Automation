import vxi11
import time, sys
from math import sqrt



outputMap = {
    'sine' : 'SIN',
    'square' : 'SQU',
    'ramp' : 'RAMP',
    'pulse' : 'PULS'
    }


class FunctionGenerator:
    def __init__(self, host):
        pass

    def setFrequency(self, frequency):
        pass

    def setVoltage(self, V):
        pass

    def enableOutput(self):
        pass

    def disableOutput(self):
        pass

    def outputType(self, sigType):
        pass

    def runSweep(self, fStart, fStop, holdTime, steps): 
        pass
    
    
        

        
class AFG3252(FunctionGenerator):
    def __init__(self, host):
        try:
            self.conn = vxi11.Instrument(host)
            self.dType = self.conn.ask('*IDN?')
            print self.dType
        except Exception as e:
            print e


    def setFrequency(self, frequency):
        print 'Setting fixed frequency to {0}'.format(frequency)
        self.conn.write('SOUR:FREQ:FIX {0} Hz'.format(frequency))

    def setVoltage(self, V):
        pass

    
    def enableOutput(self, ch):
        if ch == 1:
            self.conn.write('OUTP1:STAT ON')
        elif ch == 2:
            self.conn.write('OUTP2:STAT ON')
        else:
            print 'I don\'t have channel {0}'.format(ch)

    def disableOutput(self, ch):
        if ch == 1:
            self.conn.write('OUTP1:STAT OFF')
        elif ch == 2:
            self.conn.write('OUTP2:STAT OFF')
        else:
            print 'I don\'t have channel {0}'.format(ch)
        
    def outputType(self, sigType):
        try:
            sig = outputMap[sigType]
            self.conn.write('SOUR:FUNC:SHAP {0}'.format(sig))

        except Exception as e:
            print e

    def sweep(self, start, stop, step, wait):
        
        self.setFrequency(start)
        delta = round((float(stop)-start)/step)
        f = start
        for i in range(0, step-1):
            time.sleep(wait)
            f += delta
            self.setFrequency(f)
                        
        self.setFrequency(stop)
        time.sleep(wait)


        

