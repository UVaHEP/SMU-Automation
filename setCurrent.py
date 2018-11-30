#!/usr/bin/python
import argparse
import vxi11
from sourcemeter import *


parser = argparse.ArgumentParser(description='Select a channel')


parser.add_argument('-c', '--channel', type=int,
                    help="Turn on a channel")
parser.add_argument('--continuous', action='store_true',
                    help="Take continuous measurements after setting voltage")
parser.add_argument('-i', '--current', type=float, default=0.0,
                    help="Set current for a channel")
parser.add_argument('-d', '--duration', type=int, default=10,
                    help="Measurement duration in seconds")  # TBD
parser.add_argument('-k', '--k2611a', action='store_true',
                    help="Use the Keithley 2611a rather than the 2450")
parser.add_argument('-a', '--host', type=str, default='192.168.0.2',
                    help="Specify the host address for the Keithley")
parser.add_argument('-v', '--voltage_limit', type=float, default=0.1,
                    help="Set Voltage Limit, default 0.1 V")
parser.add_argument('-p', '--persist', action='store_true', help='Leave Current on')
parser.add_argument('-q', '--quiet', action='store_true', help='No Beeping!')

args = parser.parse_args()

if args.channel is None:
    print 'setI::Warning: Using current channel selection' 
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


if not s.Connected:
    print 'Failed to connect....quitting'
    exit(-1)

print 'Successfully connected to the {0} sourcemeter'.format(s.ModelName)

try:
    # First find out what mode we're in
    # This will get moved into our source meter class eventually 
    mode = s.OutputFn()
    if mode.find('DC_VOLTAGE') != -1:
        #disable the output and switch modes
        print 'Switching to Current mode'
        s.DisableOutput()
        s.Handle.write('smu.measure.func = smu.FUNC_DC_VOLTAGE')
        s.OutputFn('current')
        
        mode = s.OutputFn()
        print 'Now in mode {0}'.format(mode)

    print 'Setting Voltage Limit to: {0}'.format(args.voltage_limit)
    s.SetVoltageLimit(args.voltage_limit)
    s.SetCurrent(args.current)
    s.EnableOutput()
    print 'Current Values: {0}'.format(s.ReadVIPoint(None))

    if not args.persist:
        s.DisableOutput()
    
except Exception as e:
        print '{0}'.format(e)
finally:
    pass
    #Kill the connection, not necessary as it's done in the sourcemeter class
#    s = None
    
        
