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
                    help="Mesaurement duration in seconds")  # TBD

args = parser.parse_args()

if args.channel is None:
    print 'Please give me a channel'
    exit()

print 'Turning on Channel {0}.'.format(args.channel)

ft232Controller = FT232H('spi')
ft232Controller.Persist()
ft232Controller.ClearChannel()
ft232Controller.ActivateChannel(args.channel)

host = '192.168.0.2'
port = 23
s = Keithley2450(host, port)
if args.voltage is None:
    voltage = 0.0
    s.SetVoltage(voltage)
else:
    voltage = args.voltage
    s.EnableOutput()
    print('measure: {0}'.format(s.ReadVIPoint(voltage)))
    s.DisableOutput()

    


    

