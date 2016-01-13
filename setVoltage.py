#!/usr/bin/python
import argparse
import vxi11
from FT232H import *
from sourcemeter import *


parser = argparse.ArgumentParser(description='Select a channel')


parser.add_argument('-c', '--channel', type=int,
                    help="Turn on a channel")
parser.add_argument('-v', '--voltage', type=float,
                    help="Set voltage for a channel")
parser.add_argument('-d', '--duration', type=int, default=10,
                    help="Measurement duration in seconds")  # TBD
parser.add_argument('-k', '--k2611a', action='store_true',
                    help="Use the Keithley 2611a rather than the 2450")
parser.add_argument('-a', '--host', type=str, default='192.168.0.2',
                    help="Specify the host address for the Keithley")
parser.add_argument('-p', '--persist', action='store_true', help='Leave voltage on')

args = parser.parse_args()

if args.channel is None:
    print 'Warning: Using current channel selection' 
else:
    print 'Turning on Channel {0}.'.format(args.channel)

    ft232Controller = FT232H('spi')
    ft232Controller.Persist()
    ft232Controller.ClearChannel()
    ft232Controller.ActivateChannel(args.channel)

#host = '192.168.0.2'
host = args.host
port = 23
if args.k2611a:
    s = Keithley2611(host, port)
else:
    s = Keithley2450(host, port)


if args.voltage is None:
    voltage = 0.0
    print "Resetting voltage to 0"
    for i in range(2):
        s.SetVoltage(voltage)
        print('V: {0}, I measure: {1}'.format(voltage,s.ReadVIPoint(voltage)))
    s.DisableOutput()
else:
    s.Beep([(0.5, 200)])
    voltage = args.voltage
    s.EnableOutput()
    print('V: {0}, I measure: {1}'.format(voltage,s.ReadVIPoint(voltage)))
    if not args.persist:
    	s.DisableOutput()
    else:
        print "Warning: Voltage is persistant! Turn off by hand"

    
