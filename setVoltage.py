#!/usr/bin/python
import argparse
import vxi11
from sourcemeter import *


parser = argparse.ArgumentParser(description='Select a channel')


parser.add_argument('-c', '--channel', type=int,
                    help="Turn on a channel")
parser.add_argument('--continuous', action='store_true',
                    help="Take continuous measurements after setting voltage")
parser.add_argument('-v', '--voltage', type=float, default=0.0,
                    help="Set voltage for a channel")
parser.add_argument('-d', '--duration', type=int, default=10,
                    help="Measurement duration in seconds")  # TBD
parser.add_argument('-k', '--k2611a', action='store_true',
                    help="Use the Keithley 2611a rather than the 2450")
parser.add_argument('-a', '--host', type=str, default='192.168.0.2',
                    help="Specify the host address for the Keithley")
parser.add_argument('-i', '--current_limit', type=float, default='0.001',
                    help="move current limit up for SiPMs")
parser.add_argument('-p', '--persist', action='store_true', help='Leave voltage on')
parser.add_argument('-q', '--quiet', action='store_true', help='No Beeping!')

args = parser.parse_args()

if args.channel is None:
    print 'setV::Warning: Using current channel selection' 
else:
    from FT232H import *
    print 'setV::Info: Turning on Channel {0}.'.format(args.channel)
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

#s.Reset()
s.handle.write('trigger.model.abort()')
s.SetCurrentLimit(args.current_limit)
s.Autorange(True)
if args.voltage == 0:
    print "Setting voltage to 0"

if not args.quiet: s.Beep([(0.5, 200)])
voltage = args.voltage

s.EnableOutput()
current=s.ReadVIPoint(voltage)
try:
    print('V: {0}, I measure: {1}'.format(voltage,s.ReadVIPoint(voltage)))
    #Read a few more points to get the meter to settle if we have
    #some excess capacitance
    #s.handle.write('smu.measure.range = 100e-6')
    s.ReadVIPoint(voltage)
    if args.continuous:
        s.handle.write('trigger.model.load("SimpleLoop", 500)')
        s.handle.write('trigger.model.initiate()')
        
except:
    print "Error reading returned current msg",current
if not args.persist:
    s.DisableOutput()
else:
    print "setV::Warning: Voltage is persistant! Turn off by hand"

    
