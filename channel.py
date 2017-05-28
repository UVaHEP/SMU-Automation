#!/usr/bin/python
import argparse
from FT232H import *



parser = argparse.ArgumentParser(description='Select a channel')


parser.add_argument('-c', '--channel', type=int,
                    help="Turn on a channel")
parser.add_argument('-m', '--switcherMap', action='store_true',
                    help="Use Switcher Map")
parser.add_argument('-s', '--serial', type=str, default = None,
                    help ="Serial number of FT232H Controller to use")

args = parser.parse_args()
if args.switcherMap:
    ft232Controller = FT232H('spi', pinMap=switcherMap, serial='00-01')
elif args.serial:
    ft232Controller = FT232H('spi', serial=args.serial)
    
ft232Controller.Persist()

if args.channel is None:
    print 'Please give me a channel'
    exit()

print 'Turning on Channel {0}.'.format(args.channel)

ft232Controller.ClearChannel()
ft232Controller.ActivateChannel(args.channel)
#turn off all the channels

