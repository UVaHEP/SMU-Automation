import argparse
from FT232H import *



parser = argparse.ArgumentParser(description='Select a channel')


parser.add_argument('-c', '--channel', type=int,
                    help="Turn on a channel")

args = parser.parse_args()
ft232Controller = FT232H('spi', False)

if args.channel is None:
    print 'Please give me a channel'
    exit()

print 'Turning on Channel {0}.'.format(args.channel)

ft232Controller.ClearChannel()
ft232Controller.ActivateChannel(args.channel)
#turn off all the channels

