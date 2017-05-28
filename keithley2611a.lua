function IVRunnerList(vList, ilimit)
   errorqueue.clear()
   display.clear()
   display.clear()
   display.settext("Running I-V Scan")

   --disable autorange as we'll handle it 
   smua.measure.autorangei = smua.AUTORANGE_OFF
   smua.measure.rangei = 100e-9 --100nA is the minimum on the 2611a and it will default to that when given a lower value

   smua.source.levelv = vList[1]
   i = smua.measure.i()
   print(string.format("%.3g nA", 1e9*i))
   i = smua.measure.i()
   print(string.format("%.3g nA", 1e9*i))
   i = smua.measure.i()
   print(string.format("%.3g nA", 1e9*i))
   i = smua.measure.i()
   print(string.format("%.3g nA", 1e9*i))

   smua.nvbuffer1.clear()   
   smua.nvbuffer1.appendmode = 1
   smua.nvbuffer1.collectsourcevalues = 1

   element = 1
   while vList[element] do
      print(string.format('Increasing voltage to %.5g V', smua.source.levelv))
      smua.source.levelv = vList[element]
      i = smua.measure.i(smua.nvbuffer1)

      rangeCheck = math.abs(i) > 0.8*smua.measure.rangei
      
      if rangeCheck then
	 print ('Close to range limit, increasing to next level')
	 smua.measure.rangei = smua.measure.rangei*10
	 print(string.format("New Range: %.3g nA", smua.measure.rangei))


	 limitCheck = (smua.source.limiti <= (smua.measure.rangei*10)) and (smua.measure.rangei < ilimit)

	 print(limitCheck)

	 if limitCheck == true then
	    print (string.format('Increasing current limit to %s - 1%%', smua.measure.rangei))
	    smua.source.limiti = smua.measure.rangei-(smua.measure.rangei*0.01)
	    print(string.format('New Limit at: %s', smua.source.limiti))
	 else
	    print (string.format('Increasing current limit to %s', ilimit))
	    -- We have to stay under the measure range so I'm subtracting 1% from
	    -- our passed in current limit 
	    if (smua.measure.rangei == ilimit) then
	       smua.source.limiti = ilimit-0.01*ilimit
	    else
	       smua.source.limiti = ilimit
	    end

	    print(string.format('New Limit at: %s', smua.source.limiti))
	 end
      end
      
      display.clear()
      voltage = string.format("%.5g V", smua.source.levelv)
      current = string.format("%.3g nA", 1e9*i)

      display.setcursor(1,1)
      display.settext(string.format("%s", current))
      display.setcursor(2,1)
      display.settext(string.format("%s", voltage))

      compliance = status.measurement.current_limit.condition
      if (bit.bitand(compliance, 2) > 0) then
	 if (i >= limiti) then
	    print('At or above current limit! Aborting...\n')
	    display.clear()
	    display.settext('Above current limit!')
	    break
	 end
      end


      element = element + 1
      
   end


   print("Done")
   smua.source.levelv = 0
   smua.source.output = smua.OUTPUT_OFF
   display.clear()
   display.settext("Done")
   print('Done')
   print('Done')
end



function IVRunner(start, stop, step)
   errorqueue.clear()
   display.clear()
   display.clear()
   display.settext("Running I-V Scan")

   --disable autorange as we'll handle it 
   smua.measure.autorangei = smua.AUTORANGE_OFF
   smua.measure.rangei = 100e-9 --100nA is the minimum on the 2611a and it will default to that when given a lower value
   
   smua.nvbuffer1.clear()   
   smua.nvbuffer1.appendmode = 1
   smua.nvbuffer1.collectsourcevalues = 1

   for vstep = start, stop, step do
      smua.source.levelv = vstep

      i = smua.measure.i(smua.nvbuffer1)

      rangeCheck = math.abs(i) > 0.8*smua.measure.rangei
      
      if rangeCheck then
	 print ('Close to range limit, increasing to next level')
	 smua.measure.rangei = smua.measure.rangei*10
	 print(string.format("New Range: %.3g nA", smua.measure.rangei))
      end
	    
      display.clear()
      voltage = string.format("%.5g V", smua.source.levelv)
      current = string.format("%.3g nA", 1e9*i)
      display.setcursor(1,1)
      display.settext(string.format("%s", current))
      display.setcursor(2,1)
      display.settext(string.format("%s", voltage))
      print(string.format('%s, %s', voltage, current))
      compliance = status.measurement.current_limit.condition
      
      if (bit.bitand(compliance, 2) > 0) then
	 print('At or above current limit! Aborting...\n')
	 display.clear()
	 display.settext('Above current limit!')
	 break
      end
      
   end
   smua.source.levelv = 0
   smua.source.output = smua.OUTPUT_OFF
   display.clear()
   display.settext("Done")
   print('Done')
   print('Done')
   --Why do I need two Done statements!?@?!

end
