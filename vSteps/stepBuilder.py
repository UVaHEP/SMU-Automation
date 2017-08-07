import argparse


parser = argparse.ArgumentParser(description='Build Voltage Step List')

parser.add_argument('-S', '--settle', action='store_true', 
               help='Add settling to each step')
parser.add_argument('-s', '--start', type =float, default = 0.0, help='Voltage to start at')
parser.add_argument('-x', '--stop', type =float, default = -40, help ='Voltage to stop at')
parser.add_argument('-d', '--step', type =float, default = 5.0, help='dV per step')
parser.add_argument('-t', '--sTime', type=float, default= 2.0,
               help='Settle time in percent diff')


p = parser.parse_args()


i = p.start
vs = []
if p.stop < p.start:
    #negative dV
    p.step = -1*abs(p.step)
    print 'stop: {0} < start: {1}, step: {2}'.format(p.stop, p.start, p.step)
    while i >= p.stop:
        if p.settle:
            vs.append('{0}:{1}'.format(i, p.sTime))
        else:
            vs.append(i)
        i += p.step
elif p.stop > p.start:
    #positive dV
    p.step = abs(p.step)
    print 'start: {0} > stop: {1}, step: {2}'.format(p.start, p.stop, p.step)

    while i <= p.stop:
        if p.settle:
            vs.append('{0}:{1}'.format(i, p.sTime))
        else:
            vs.append(i)
        i += p.step
else:
    print 'Start and stop equal!'
    exit()

print ','.join(map(str, vs))
