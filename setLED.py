#!/usr/bin/python
import mpsse
import argparse

parser = argparse.ArgumentParser(description='Takes I-V Curves')

#parser.add_argument('-i', '--iLED', type=int, nargs='?', default = '\xFF\xE0')
parser.add_argument('-i', '--iLED', type=int, nargs='?', default = '0')

args = parser.parse_args()

LightCtl = mpsse.MPSSE(mpsse.I2C, mpsse.ONE_HUNDRED_KHZ, mpsse.MSB)
LightCtl.PinLow(mpsse.GPIOH5)
address = '\xC0'
DACupdate = '\x40'
light  = (0+args.iLED)
vHigh = chr((light >> 4))
vLow = chr((light & 0x0f) << 4)
voltage = str(hex(light)).lstrip('0x')
print hex(light)
LightCtl.PinHigh(mpsse.GPIOL0)
LightCtl.PinHigh(mpsse.GPIOL2)
LightCtl.Start()
LightCtl.Write(address)
LightCtl.Write(DACupdate)
#LightCtl.Write('{0}{1}'.format(voltage[0:2], voltage[-1]))
if light == 0:
    LightCtl.Write('\x00\x00')
else:
    LightCtl.Write('{0}{1}'.format(vHigh, vLow))
LightCtl.Stop()
