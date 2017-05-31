#!/usr/bin/python
# Enter a starting voltage and target current value
# this code will setup the SMU and scan the voltage until the
# target current is located.   The voltage setting is returned
# This is a quick/dirty approximation only

import argparse,sys,time,commands
import vxi11
from sourcemeter import *

rootlibs=commands.getoutput("root-config --libdir")
sys.path.append(rootlibs)

# keep ROOT TApplication from grabbing -h flag
from ROOT import PyConfig
PyConfig.IgnoreCommandLineOptions = True
from ROOT import TGraph
from ROOT import TCanvas


parser = argparse.ArgumentParser(description='Select a channel')


parser.add_argument('-c', '--channel', type=int,
                    help="Turn on a channel")
parser.add_argument('-v', '--voltage', type=float, default=0.0,
                    help="Starting voltage for search")
parser.add_argument('-i', '--itarget', type=float, default=0.0,
                    help="target current in abs(nA)")
parser.add_argument('-s', '--vstep', type=float, default=0.02,
                    help="abs(step size) for voltage setting search")
parser.add_argument('-p', '--persist', action='store_true', help='Leave voltage on')
parser.add_argument('-k', '--k2611a', action='store_true',
                    help="Use the Keithley 2611a rather than the 2450")
parser.add_argument('-a', '--host', type=str, default='192.168.0.2',
                    help="Specify the host address for the Keithley")
parser.add_argument('-q', '--quiet', action='store_true', help='No Beeping!')


args = parser.parse_args()
itarget=args.itarget*1e-9

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

if args.voltage == 0:
    print "Enter starting voltage in as [-v VOLTS]"
    sys.exit(1)
if args.itarget == 0:
    print "Enter starting current as [-i TARGET] in nA"
    sys.exit(1)

print "Finding voltage for target current of",args.itarget,"nA"
    
if not args.quiet: s.Beep([(0.5, 200)])
voltage = args.voltage
s.EnableOutput()

# first stablize around the initial current
resol=0.05
current=abs(float(s.ReadVIPoint(voltage)))
delta=1.0
print "Reading current at starting voltage",voltage
while abs(delta) > resol:
    lastVal=current
    current=abs(float(s.ReadVIPoint(voltage)))
    delta=(current-lastVal)/current
    
gIVset=TGraph() ; gIVset.SetTitle("V vs I [A];I;Volts")
gIVset.SetPoint(0,current,voltage)

if voltage>0: step=args.vstep
else: step=-1*args.vstep
sign=-1
if current>itarget:
    step=-1*step
    sign=1
print "step size",step

delta=(current-itarget)*sign
delta0=abs(delta)
while (delta>0):
    voltage=voltage+step
    print "New voltage setting",voltage
    current=abs(float(s.ReadVIPoint(voltage)))
    print "Read current",current
    gIVset.SetPoint(gIVset.GetN(),current,voltage)
    delta=(current-itarget)*sign
    if abs(delta)>delta0:  # we're not converging
        print "Warning voltage search is diverging. Exiting..."
        print "This may be due to a noisy measurement.  Try running again, if no problems are expected."
        sys.exit(1)
    
tc=TCanvas("tc","Search for target current")
tc.cd().SetGridx()
gIVset.GetYaxis().SetTitleOffset(1.4); 
gIVset.Draw("ALP*")
tgtV=gIVset.Eval(itarget)
print "For target current of",args.itarget,"nA, set voltage to",round(tgtV,2)
mark=TGraph()
mark.SetPoint(0,itarget,tgtV)
mark.SetMarkerColor(2)
mark.Draw("P*")

tc.Update()

if not args.persist:
    s.DisableOutput()
else:
    s.ReadVIPoint(tgtV)
    print "setV::Warning: Voltage is persistant! Turn off by hand"

    
print 'Hit return to exit'
sys.stdout.flush() 
raw_input('')
