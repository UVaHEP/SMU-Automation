import vxi11
from sourcemeter import *
from FT232H import *


host = '192.168.0.2'
port = 23
channel = 9
samples = 100
output = 'charge.dat'

s = Keithley2450(host, port)
s.SetRepeatAverage(1)  # Average 3 samples / measurement
s.SetSourceDelay(0.0)  # hold off time before measurements
s.SetNPLC(1)

hRelay = FT232H('spi')
hRelay.Persist()
hRelay.ClearChannel()
hRelay.ActivateChannel(channel)
s.Reset()
s.SetCurrentLimit(8e-3)


voltage = -10.0
oFile = open(output, 'w+')
while voltage >= -10.0:
    for i in range(samples):
        current = s.ReadVIPoint(voltage)
        outStr = '{0} {1} {2}\n'.format(i+1, voltage, current) 
        oFile.write(outStr)
        print '{0}, {1}, {2}'.format(i+1, voltage, current)
    voltage += -0.1
        
