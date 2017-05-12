import argparse
import ConfigParser



def buildParser():
    parser = argparse.ArgumentParser(description='Takes I-V Curves')

    ##### Deprecated Args #####
    parser.add_argument('-a','--agilent', action='store_true',
                        help="Use Agilent SMU to take the I-V curve")
    parser.add_argument('-k','--k2611', action='store_true',
                        help="Use Keithley 2611 to take the I-V curve")
    parser.add_argument('-K','--k2450', action='store_true',
                        help="Use Keithley 2450 to take I-V curve")
    parser.add_argument('--script', type=str, nargs='?', default=None,
                        help='Script to upload and run')
    parser.add_argument('-H','--hysteresis', action='store_true', default=False,
                        help="Repeat I-V measurement in reverse for hysteresis curve")
    parser.add_argument('--host', type=str, default=None,
                        help="Host to use")
    parser.add_argument('--port', type=int, default=23,
                        help="Port to use")


    ##### General Arguments #####
    parser.add_argument('-f', '--file', type=str, nargs='?', default=None,
                        help="Input data file that activates list sweep")
    parser.add_argument('-D','--device', type=str, nargs='?', default="noname",
                        help="Device identifier, append _fast for fast collection mode")
    parser.add_argument('-o', '--output', type=str, nargs='?', default="",
                        help="Output file for data")
    parser.add_argument('-g', '--graph', action='store_true',
                        help='Prints the I-V curve graph to the screen')
    parser.add_argument('-B','--BackTerm', action='store_true',
                        help="Use rear terminals on SMU (model 2450 only, for now)")
    parser.add_argument('-c', '--channel', type=int, nargs ='*',
                        help="Take I-V curves at specified channels")
    parser.add_argument('-A', '--all', action='store_true',
                        help="Take I-V curve for all channels")
    parser.add_argument('-i', '--iLED', type=int, nargs = '?', default=None,
                        help="Specifies intensity of LEDs, range is integers 0-4095")
    parser.add_argument('--config', type=str, default=None,
                        help="Specify the configuration file to use")



    ##### I-V Curve Specific Arguments #####
    parser.add_argument('-R','--reverse', action='store_true',
                        help="Takes default reverse bias curve if no data file")
    parser.add_argument('-F','--forward', action='store_true',
                        help="Takes default forward bias I-V curve if no data file")
    parser.add_argument('-l', '--limit', type=float, default = None,
                        help="Set the current limit [0.01 A]")
    parser.add_argument('-s', '--numsteps', type=int, default=100,
                        help="The number of steps in the staircase sweep [100]")
    parser.add_argument('-S', '--stepsize', type=float, default=None,
                        help="Step size for the staircase sweep in units of volts [None]")
    parser.add_argument('-m', '--min', type=float, default=None,
                        help="Voltage at which to start staircase sweep")
    parser.add_argument('-x', '--max', type=float, default=None,
                        help="Voltage at which to stop staircase sweep")


    return parser



def loadSettings(filename):
    settings = {'script':None, 'host':None, 'port':23, 'model':None}

    
    print 'Trying to use {0} for Configuration file'.format(filename)
    try:
        c = ConfigParser.ConfigParser()
        c.readfp(open(filename))

        # Load General Settings first 
        section = 'SMU-Automation-General'
        settings['host'] = c.get(section, 'host')
        settings['port'] = c.getint(section, 'port')
        settings['model'] = c.get(section, 'model')
        settings['currentLimit'] = c.getfloat(section, 'ilimit')
        settings['backterm'] = c.getboolean(section, 'backterm')
        settings['autorange'] = c.getboolean(section, 'autorange')



        try:
            settings['script'] = c.get(section, 'programfile')
        except:
            settings['script'] = None
    
        if c.getboolean(section, 'fastmode'):
            section = 'SMU-Automation-Fast'
        else:
            section = 'SMU-Automation-Slow'

        settings['repeatAvg'] = c.getint(section, 'repeatAvg')
        settings['sourcedelay'] = c.getfloat(section, 'sourcedelay')
        settings['dischargebefore'] = c.getint(section, 'dischargebefore')
        settings['dischargeafter'] = c.getint(section, 'dischargeafter')
        settings['nplc'] = c.getint(section, 'nplc')

        section = 'IV-Curve'
        settings['stepSize'] = c.getfloat(section, 'stepSize')
        settings['min'] = c.getfloat(section, 'min')
        settings['max'] = c.getfloat(section, 'max')
        settings['file'] = c.get(section, 'file')
        settings['led'] = c.getint(section, 'led')
            
    except Exception as e:
        return None
        
    return settings


def processArgs(args, settings):

    if args.limit:
        settings['currentLimit'] = args.limit
    else:
        # use default current limit
        settings['currentLimit'] = 0.01


        
    if not args.host and settings['host'] == None:
        print 'I need a host to connect to, use --host or add it to a config file'
        exit()
    elif args.host:
        settings['host'] = args.host

    if args.port:
        settings['port'] = args.port
    

    if args.k2611:
        settings['model'] = 'k2611'
    elif args.k2450:
        settings['model'] = 'k2450'


    if args.min:
        settings['min'] = args.min

    if args.max:
        settings['max'] = args.max

    if args.stepsize:
        settings['stepSize'] = args.stepsize

    if settings['max'] < settings['min'] and settings['stepSize'] > 0:
        #invert stepSize if we're going to negative values
        settings['stepSize'] = settings['stepSize']*-1
    

    if args.iLED:
        settings['led'] = args.iLED
    elif not settings['script']:
        settings['led'] = 0
        
    

        
    return settings
