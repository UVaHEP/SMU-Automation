import mpsse
defaultMap = {
            2 : (1, 0x1),
            3 : (1, 0x2),
            4 : (1, 0x4),
            5 : (1, 0x8),
            6 : (1, 0x10),
            9 : (2, 0x1),
            10 : (2, 0x2),
            11 : (2, 0x4),
            12 : (2, 0x8),
            13 : (2, 0x10)
}


class FT232H:
    def __init__(self, mode, disableOnExit=True, pinMap=defaultMap,  dacAddress='\xC0'):

        self.disableOnExit = disableOnExit
        self.address = dacAddress
        self.DACupdate = '\x40'
        self.ledActive = False
        self.relayActive = False 
        self.debug = False
        
        try:
            if (mode == 'i2c'):
                self.mode = 'i2c'
                self.controller = mpsse.MPSSE(mpsse.I2C, mpsse.ONE_HUNDRED_KHZ, mpsse.MSB)
            elif (mode == 'spi'):
                self.mode = 'spi'
                self.controller = mpsse.MPSSE(mpsse.SPI0, mpsse.ONE_HUNDRED_KHZ, mpsse.MSB)
        except Exception as e:
            print 'Warning! No supported device found.'
            self.controller = None
            self.mode = None 
            #Replace our normal functions with test functions
            self.__install_test_fns()

        self.activeChannel = 0

        self.pinMap = pinMap


    def __pass__(self):
        print 'pass' 
        
    def __del__(self):
        if self.disableOnExit:
            if (self.ledActive):
                print 'Turning off LEDs...good night!'
                self.SetLight(0)
            if (self.relayActive):
                print 'Disabling Relays'
                self.ClearChannel()
        else:
            print 'Leaving Relays and Light Active'
        if (self.controller):
            self.controller.Close()
            self.controller = None 
    

    def __install_test_fns(self):
        self.__del__ = self.__pass__
        self.setCSPins = self.__pass__
        self.Activechannel = self.__pass__
        self.ClearChannel = self.__pass__
        self.EnableChannel = self.__pass__

        
    def Debug(self,flag=True):
        self.debug=flag

        
    def Persist(self,persist=True):
        self.disableOnExit = not persist
        
    def enableMode(self, mode):
        if (self.mode == mode):
            return
        try: 
            if (self.controller):
                self.controller.Close()
                self.controller = None 

            if (mode == 'i2c'):
                self.controller = mpsse.MPSSE(mpsse.I2C, mpsse.ONE_HUNDRED_KHZ, mpsse.MSB)
            elif (mode == 'spi'):
                self.controller = mpsse.MPSSE(mpsse.SPI0, mpsse.ONE_HUNDRED_KHZ, mpsse.MSB)
            else:
                self.controller = None

        except Exception as e:
            print "Couldn't enable mode {0}, because of {1}.".format(mode, e)
        
    def setCSPins(self, n, level):
        if (self.mode != 'spi'):
            self.enableMode('spi')
        
        #Note: We'll want some way to set the cs pins in our class

        if n == 0 and level==0:
            #lower both
            self.controller.PinLow(mpsse.GPIOL0)
            self.controller.PinLow(mpsse.GPIOL2)
        if n == 0 and level==1:
            #raiseboth
            self.controller.PinHigh(mpsse.GPIOL0)
            self.controller.PinHigh(mpsse.GPIOL2)

        elif n == 0 and level==1:
            #raise both
            self.controller.PinHigh(mpsse.GPIOL0)
            self.controller.PinHigh(mpsse.GPIOL2)
        elif n == 1 and level == 0:
            if (self.debug): print 'chip 1 low'
            self.controller.PinLow(mpsse.GPIOL0)
        elif n == 1 and level == 1:
            if (self.debug): print 'chip 1 high'
            self.controller.PinHigh(mpsse.GPIOL0)
        elif n == 2 and level == 0:
            if (self.debug): print 'chip 2 low'
            self.controller.PinLow(mpsse.GPIOL2)
        elif n == 2 and level == 1:
            if (self.debug): print 'chip 2 high'
            self.controller.PinLow(mpsse.GPIOL2)


            
    def ActivateChannel(self, pin):
        if (self.mode != 'spi'):
            self.enableMode('spi')
        
        try:
            (CS,hexCode) = self.pinMap[pin]
        except KeyError  as e:
            print "No channel mapped for pin: {0}".format(pin)
            exit()
            
        self.setCSPins(CS,0)
        self.activeChannel = hexCode
        self.EnableChannel()
        self.relayActive = True 
        

    def ClearChannel(self):
        if (self.mode != 'spi'):
            self.enableMode('spi')

        self.setCSPins(0,0)
        self.controller.Start()
        self.controller.WriteBits(0x0, 8)
        self.controller.Stop()
        self.setCSPins(0,1)
        self.relayActive = False 

    def EnableChannel(self):
        if (self.mode != 'spi'):
            self.enableMode('spi')

        if (self.debug):
            print 'using hex code:{0}'.format(hex(self.activeChannel))
        self.controller.Start()
        self.controller.WriteBits(self.activeChannel, 8)
        self.controller.Stop()
        self.setCSPins(0,1)

    def SetLight(self, light):
        if (self.mode != 'i2c'):
            self.enableMode('i2c')

        self.ledActive = True 
        intensity = light
        vHigh = chr((intensity >> 4))
        vLow = chr((intensity & 0x0f) << 4)

        self.controller.Start()
        self.controller.Write(self.address)
        self.controller.Write(self.DACupdate)
        if intensity == 0:
            self.controller.Write('\x00\x00')
        else:
            self.controller.Write('{0}{1}'.format(vHigh, vLow))
        self.controller.Stop()


if __name__ == '__main__':
    test = FT232Hspi()
    test.Activechannel()
    test.EnableChannel()
    test.ClearChannel()
    test.setCSPins() 
    print test.pinMap
    
    
