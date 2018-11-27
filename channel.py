#!/usr/bin/python
import argparse
import time
from FT232H import *



parser = argparse.ArgumentParser(description='Select a channel')


parser.add_argument('-c', '--channel', type=int,
                    help="Turn on a channel")
parser.add_argument('-m', '--switcherMap', action='store_true',
                    help="Use Switcher Map")
parser.add_argument('-z', '--zifMap', action='store_true',
                    help="Use zif board map")
parser.add_argument('-t', '--testBeamMap', action='store_true', help="Use Test Beam Map")
parser.add_argument('-s', '--serial', type=str, default = None,
                    help ="Serial number of FT232H Controller to use")
parser.add_argument('-a', '--all', action='store_true', help='Enable all channels for a given pin map')

args = parser.parse_args()
if args.switcherMap:
    ft232Controller = FT232H('spi', pinMap='switcher', serial='00-01')
elif args.zifMap:
    ft232Controller = FT232H('spi', pinMap='zifboard', serial=args.serial)
elif args.serial:
    if args.testBeamMap:
        ft232Controller = FT232H('spi', pinMap='testBeam', serial=args.serial)
    else:
        ft232Controller = FT232H('spi', serial=args.serial)
else:
    ft232Controller = FT232H('spi')
    
    
ft232Controller.Persist()

if args.channel is None and not args.all:
    print 'Please give me a channel'
    exit()



ft232Controller.ClearChannel()
if args.all:
    hexCode = 0x1f
    ft232Controller.ActivateChannel('r1')
    ft232Controller.ActivateChannel('r2')
    
else:
    print 'Turning on Channel {0}.'.format(args.channel)
    ft232Controller.ActivateChannel(args.channel)
#turn off all the channels

