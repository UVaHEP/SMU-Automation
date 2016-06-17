import threading
import time, sys
import serial
from K2450GPIB import *



def IVmeasure():
    t = threading.currentThread()
    comport = '/dev/ttyUSB0'
    addr = 18
    voltage = 7

    s = K2450GPIB(comport, addr)
    
    while getattr(t, "do_run", True):
        data = s.ReadIVPoint(voltage)
        s.ClearBuffer()
        print data

        time.sleep(0.5)
    print "Ok, I'm done now."


print "Press enter to stop measurements"
print "Voltage          Current"
thread = threading.Thread(target=IVmeasure)
thread.start()
button = 'nothing'
while button != '':
    button = raw_input('')
    if button == '':
        thread.do_run = False
        thread.join()
    

        
