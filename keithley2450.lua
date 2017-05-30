function IVRunnerList(vList, ilimit)
   -- Given a list of voltages (vList), step through each voltage
   errorqueue.clear()

   display.clear()
   display.clear()
   display.settext(display.TEXT1, "Running I-V Scan")

   --disable autorange as we'll handle it 
   smu.measure.autorange = smu.OFF

   print(string.format('Passed in %s for the current limit.', ilimit))


      
   smu.measure.range = 1e-6 --10nA is the minimum of the 2450
   print(string.format('Starting with max current limit of %s for low range', smu.measure.range))
   smu.source.ilimit.level = smu.measure.range-(smu.measure.range*0.01)
   
   defbuffer1.clear()   
   defbuffer1.appendmode = 1
   --   defbuffer1.collectsourcevalues = 1
   smu.source.func = smu.FUNC_DC_VOLTAGE
   smu.measure.func = smu.FUNC_DC_CURRENT
   smu.measure.autozero.once()

   smu.source.level = vList[1]
   i = smu.measure.read()
   print(string.format('%s', i))
   i = smu.measure.read()
   print(string.format('%s', i))
   i = smu.measure.read()
   print(string.format('%s', i))
   i = smu.measure.read()
   print(string.format('%s', i))
   defbuffer1.clear()   

   ivBuffer = buffer.make(500)
   ivBuffer.clear()
   ivBuffer.appendmode = 1
   element = 1
   while vList[element] do
      eType = type(vList[element])
      if (eType == 'number') then
	 --print(string.format('Increasing voltage to %.5g V', smu.source.level))
	 smu.source.level = vList[element]
      elseif (eType == 'string') then
	 print('Beginning to settle')
	 -- We use the format v:p to denote a voltage to stop at (v), and a settling percentage to wait for
	 -- where the current measurement is less than p % different than the previous measurement
	 pos = string.find(vList[element], ':')
	 waitV = tonumber(string.sub(vList[element], 1, pos-1))
	 percentage = tonumber(string.sub(vList[element], pos+1))/100


	 smu.source.level = waitV
	 last = smu.measure.read()
	 pdiff = 1

	 while pdiff > percentage do 
	    current = smu.measure.read()
	    deltaI = current - last
	    pdiff = math.abs(deltaI/current)
	    print(string.format('Settling, i: %.3g nA, last I: %.3g nA, dI: %.3g nA, %%diff: %.3g', current, last, deltaI, pdiff*100))
	    last = current
	 end
	    
	 print (string.format('Finished settling at %.5g V', smu.source.level))
      end

      i = smu.measure.read(ivBuffer)

      rangeCheck = math.abs(i) > 0.6*smu.measure.range
      
      if rangeCheck then
      	 print ('Close to range limit, increasing to next level')
      	 smu.measure.range = smu.measure.range*10
      	 print(string.format("New Range: %.3g A", smu.measure.range))
	 --Also update our current limit
	 
	 limitCheck = (smu.source.ilimit.level <= (smu.measure.range*10)) and (smu.measure.range < ilimit)
--	 print (string.format('Limit Check: %s', tostring(limitCheck)))
--	 print (string.format('%s <= %s, %s, %s < %s, %s', smu.source.ilimit.level, smu.measure.range*10, tostring(smu.source.ilimit.level <= smu.measure.range*10), smu.measure.range, ilimit, tostring(smu.measure.range < ilimit)))
	 
	 if (limitCheck) then
	    print (string.format('Increasing current limit to %s - 1%%', smu.measure.range))
	    smu.source.ilimit.level = smu.measure.range-(smu.measure.range*0.01)
	    print(string.format('New Limit at: %s', smu.source.ilimit.level))
	 else
	    print (string.format('Increasing current limit to %s', ilimit))
	    -- We have to stay under the measure range so I'm subtracting 1% from
	    -- our passed in current limit 
	    if (smu.measure.range == ilimit) then
	       smu.source.ilimit.level = ilimit-0.01*ilimit
	    else
	       smu.source.ilimit.level = ilimit
	    end
	    
	    print(string.format('New Limit at: %s', smu.source.ilimit.level))
	 end
      end

      voltage = string.format("%.5g V", smu.source.level)
      current = string.format("%.3g nA", 1e9*i)

      display.settext(display.TEXT1, string.format("%s", current))

      display.settext(display.TEXT2, string.format("%s", voltage))
      print(string.format('%s, %s', voltage, current))
      element = element + 1


      if (smu.source.ilimit.tripped == smu.ON) then
	 if (smu.source.ilimit.level >= ilimit) then
	    print('At or above current limit! Aborting...')
	    display.clear()
	    display.settext('Above current limit!')
	    break
	 end
      end


   end

   print('Done')
   smu.source.level = 0
   smu.source.output = smu.OFF
   display.clear()
   display.settext(display.TEXT1, "Done")
   print('Done')

end






function IVRunner(start, stop, step)
--   errorqueue.clear()
   display.clear()
   display.clear()
   display.settext(display.TEXT1, "Running I-V Scan")

   --disable autorange as we'll handle it 
   smu.measure.autorange = smu.OFF
   smu.measure.range = 10e-9 --10nA is the minimum of the 2450
   
   defbuffer1.clear()   
   defbuffer1.appendmode = 1
--   defbuffer1.collectsourcevalues = 1

   
   smu.source.level = start
   i = smu.measure.read()
   print(string.format('%s', i))
   i = smu.measure.read()
   print(string.format('%s', i))
   i = smu.measure.read()
   print(string.format('%s', i))
   i = smu.measure.read()
   print(string.format('%s', i))
   defbuffer1.clear()   
   for vstep = start, stop, step do
      smu.source.level = vstep

      i = smu.measure.read()

      rangeCheck = math.abs(i) > 0.8*smu.measure.range
      
      if rangeCheck then
      	 print ('Close to range limit, increasing to next level')
      	 smu.measure.range = smu.measure.range*10
      	 print(string.format("New Range: %.3g nA", smu.measure.range))
      end
	    
--      display.clear()
      voltage = string.format("%.5g V", smu.source.level)
      current = string.format("%.3g nA", 1e9*i)
--      display.setcursor(1,1)
      display.settext(display.TEXT1, string.format("%s", current))
--      display.setcursor(2,1)
      display.settext(display.TEXT2, string.format("%s", voltage))
      print(string.format('%s, %s', voltage, current))
      compliance = status.measurement.current_limit.condition
      
      if (bit.bitand(compliance, 2) > 0) then
       	 print('At or above current limit! Aborting...\n')
       	 display.clear()
       	 display.settext('Above current limit!')
       	 break
      end
      
   end
   print('Done')
   smu.source.level = 0
   smu.source.output = smu.OFF
   display.clear()
   display.settext(display.TEXT1, "Done")
   print('Done')
   --Why do I need two Done statements!?@?!

end