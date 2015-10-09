import argparse
import vxi11
from FT232H import *



parser = argparse.ArgumentParser(description='Select a channel')


parser.add_argument('-c', '--channel', type=int,
                    help="Turn on a channel")
parser.add_argument('-v', '--voltage', type=float,
                    help="Set voltage for a channel")

args = parser.parse_args()
ft232Controller = FT232H('spi', False)

if args.channel is None:
    print 'Please give me a channel'
    exit()

print 'Turning on Channel {0}.'.format(args.channel)

ft232Controller.Persist()
ft232Controller.ClearChannel()
ft232Controller.ActivateChannel(args.channel)

host = '128.143.196.77'
port = 23
s = Keithley2450(host, port, args.limit)
if args.voltage is None:
    voltage = 0.0
    s.SetVoltage(voltage)
else:
    voltage = args.voltage
    s.EnableOutput()
    print('measure: {0}'.format(s.ReadVIPoint(v)))
    s.DisableOutput()

    


    

