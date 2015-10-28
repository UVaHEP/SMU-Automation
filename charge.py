import vxi11
from sourcemeter import *
from FT232H import *


host = '192.168.0.2'
port = 23
channel = 11
samples = 25
output = 'charge.dat'

s = Keithley2450(host, port)
hRelay = FT232H('spi')
hRelay.Persist()
hRelay.ClearChannel()
hRelay.ActivateChannel(channel)
s.Reset()
s.SetCurrentLimit(8e-3)


voltage = 0.0
oFile = open(output, 'w+')
while voltage >= -80:
    for i in range(samples):
        current = s.ReadVIPoint(voltage)
        outStr = '{0} {1} {2}'.format(i+1, voltage, current) 
        oFile.write(outStr)
        print '{0}, {1}, {2}'.format(i+1, voltage, current)
    voltage += -0.1
        
