import pexpect

def sweepa(output, host, port, limit, args):
    command = 'telnet {0} {1}'.format(host,port)
    
    print 'Connecting to ' +command

    agilent = pexpect.spawn(command)
    agilent.setecho(False)
    fout = file('mytext.txt', 'w')
    agilent.logfile = fout

    agilent.expect('B2900A>')
    agilent.send('*CLS \r')
    agilent.expect('B2900A>')
    #agilent.send(':SENS:CURR:PROT '+ limit +'\r')
    #agilent.expect('B2900A>')
    agilent.send(':FORM:ELEM:SENS VOLT,CURR\r')
    agilent.expect('B2900A>')

    if args.file == None and not args.forward and not args.reverse:
        #this does the staircase sweep
        agilent.send(':VOLT:MODE SWE\r')
        agilent.expect('B2900A>')
        agilent.send(':SOUR:SWE:POIN '+str(args.steps)+'\r')
        agilent.expect('B2900A>')
        agilent.send(':SOUR:VOLT:STAR '+str(args.min)+'\r')
        agilent.expect('B2900A>')
        agilent.send(':SOUR:VOLT:STOP '+str(args.max)+'\r')
        agilent.expect('B2900A>')
        agilent.send(':TRIG:ACQ:COUN '+str(args.steps)+'\r')
        agilent.expect('B2900A>')
        agilent.send(':TRIG:TRAN:COUN '+str(args.steps)+'\r')

    #the rest does a list sweep either with given file or default
    else:
        if not args.file == None:
            f = open(args.file, 'r')
            nums = []
            if args.file[-3:] == 'csv':
                for line in f:
                    values = line.split(',')
                    if len(values) > 4:
                        nums.append(values[3])
                if not nums == []:        
                    strInput = ','.join(nums[1:])
                    length = str(len(nums))
            elif nums == []:
                for line in f:
                    splitSpace =[]
                    newline = line.replace(',',' ')
                    splitSpace = newline.split()
                    if len(splitSpace) >1:
                        for i in range(len(splitSpace)):
                            nums.append(splitSpace[i])
                        else:
                            if not splitSpace == []:
                                nums.append(splitSpace[0])

                strInput = ','.join(nums)
                length = str(len(nums))
            f.close()
        else:
            if args.forward:
                nums = []
                volts = 0.0
                while round(volts,4) <= 3.0:
                    nums.append(str(round(volts,4)))
                    volts += 0.05
                strInput = ','.join(nums)
                length = str(len(nums))
            
            else:
                nums = []
                volts = 0.0
                while round(volts,4)>=(-80.0):
                    nums.append(str(round(volts,4)))
                    if round(volts,4) >(-40.0):
                        volts += -1.0
                    elif round(volts,4) >(-50.0):
                        volts += -0.5
                    elif round(volts,4) >(-60.0):
                        volts += -0.25
                    elif round(volts,4) >(-75.0):
                        volts += -0.05
                    else:
                        volts += -0.1

                    strInput = ','.join(nums)
                    length = str(len(nums))
        
        agilent.send(':VOLT:MODE LIST\r')
        agilent.expect('B2900A>')
        agilent.send(':SOUR:LIST:VOLT '+ strInput + '\r')
        agilent.expect('B2900A>')
        agilent.send(':TRIG:ACQ:COUN ' + length + '\r')
        agilent.expect('B2900A>')
        agilent.send(':TRIG:TRAN:COUN ' + length + '\r')

        
    agilent.expect('B2900A>')
    agilent.send(':TRIG:ACQ:DEL 0.3\r')
    agilent.expect('B2900A>')
    agilent.send(':SENS:CURR:APER 0.4\r')
    agilent.expect('B2900A>')
    agilent.send('INIT:ALL (@1)\r')
    agilent.expect('B2900A>')
    agilent.send('*OPC?\r')
    index = agilent.expect_exact('1', timeout=None)

    agilent.expect('B2900A>')
    agilent.send(':FETC:ARR:VOLT?\r')
    agilent.expect('B2900A>')
    data1 = agilent.before
    agilent.send(':FETC:ARR:CURR?\r')
    agilent.expect('B2900A>')
    data2 = agilent.before
    data1_lines = data1.split('\n')
    data2_lines = data2.split('\n')

    voltage = data1_lines[1].strip().split(',')
    current = data2_lines[1].strip().split(',')

    outputFile = open(output,'w+')
    outputFile.write('Repeat,VAR2,Point,Voltage,Current,Time\n')
    for i in range(len(voltage)):
        outputString = "{0},{1},{2},{3},{4},{5}\n".format(1,1,1,str(voltage[i]).lstrip('+'),str(current[i]).lstrip('+'),1)
        print outputString
        outputFile.write(outputString)

    outputFile.close()
