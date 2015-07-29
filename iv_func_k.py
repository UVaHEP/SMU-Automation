import vxi11

def sweepk(output,args):
    instr = vxi11.Instrument('128.143.196.249')
    try:
        instr.write('smua.reset()')

        instr.write('smua.source.output = smua.OUTPUT_OFF')
        instr.write('smua.source.func = smua.OUTPUT_DCVOLTS')
        instr.write('smua.source.limitv = -80')
        instr.write('smua.source.limiti = 8e-3')
        instr.write('smua.measure.autorangei = smua.AUTORANGE_ON')
        instr.write('smua.source.output = smua.OUTPUT_ON')
        instr.timeout = 2000000

        if args.file == None and not args.forward and not args.reverse:
            #this does the staircase sweep
            instr.write('SweepVLinMeasureI(smua, {0}, {1}, 1, {2})'.format(args.min, args.max, args.steps))
            length = args.steps
            nums=[]
            for i in range(length):
                step = (args.max-args.min)/(args.steps-1)
                volt = args.min+(step*i)
                nums.append(volt)

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
                        del nums[0]
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
                f.close()
            else:
                if args.forward:
                    nums = []
                    volts = 0.0
                    while round(volts,4) <= 3.0:
                        nums.append(str(round(volts,4)))
                        volts += 0.05

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

            instr.write('mylist = {}')

            length = len(nums)
            for volt in nums:
                line = 'table.insert(mylist, {0})'.format(volt)
                instr.write(line)

            instr.write('SweepVListMeasureI(smua, mylist, 1,'+str(length)+')')

        print length
        instr.write('opc()')

        outputFile = open(output, 'w+')
        outputFile.write('Repeat,VAR2, Point,Voltage,Current,Time\n')


        for i in range(length):
            num = instr.ask('print(smua.nvbuffer1.readings['+str(i+1)+'])')
            outputString = "{0},{1},{2},{3},{4},{5}\n".format(1,1,1,str(nums[i]), num, 1)
            print outputString
            outputFile.write(outputString)

        outputFile.close()

    except Exception as e:
        print e

    instr.close()
