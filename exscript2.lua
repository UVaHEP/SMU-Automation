function IVRunner(start, stop, step)
   errorqueue.clear()
   display.clear()
   display.clear()
   display.settext("Running I-V Scan")

   for vstep = start, stop, step do
         smua.source.levelv = vstep
	 i = smua.measure.i()
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



