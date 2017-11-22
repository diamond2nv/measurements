import pylab as py
import time
#import sys
import datetime
import os.path
from AttocubeANC300 import AttocubeANC300
from measurement.instruments.pylonWeetabixTrigger import trigSender, trigReceiver, voltOut
from Keithley import Keithley

class SpectroCtrl ():

	def __init__(self, work_folder):
		self._wfolder = work_folder

	def init_spectro (self):
		pass

	def readout (self):
		pass

	def wait_for_ready (self):
		pass

	def test_for_ready (self):
		pass

	def first_point (self):
		pass

class Scanner ():

	def __init__(self):
		pass

	def moveX (self, value):
		pass

	def moveY (self, value):
		pass

	def getX (self):
		pass

	def getY (self):
		pass

	def goSmoothlyToPos(self, xPos, yPos, smoothStep=1., smoothDelay=SMOOTH_DELAY):
		# go smoothly to a position
		currentX = self.getX()
		currentY = self.getY()
		xSmoothNbOfSteps = int(abs(py.floor((currentX - xPos) / float(smoothStep))) + 1)
		ySmoothNbOfSteps = int(abs(py.floor((currentY - yPos) / float(smoothStep))) + 1)
		totalSmoothNbOfSteps = max((xSmoothNbOfSteps, ySmoothNbOfSteps))
		xSmoothPositions = py.append(py.linspace(currentX, xPos, xSmoothNbOfSteps), 
						py.zeros(totalSmoothNbOfSteps - xSmoothNbOfSteps) + xPos)
		ySmoothPositions = py.append(py.linspace(currentY, yPos, ySmoothNbOfSteps),
						py.zeros(totalSmoothNbOfSteps - ySmoothNbOfSteps) + yPos)

	    for x, y in zip(xSmoothPositions, ySmoothPositions):
	        self.moveX(x)
	        self.moveY(y)
	        time.sleep(smoothDelay)

class AttocubeNI (Scanner):

	def __init__ (self, chX = 'ao0', chY = 'ao1', conversion_factor=1/15.):
		self.scanners_volt_drive_X = voltOut("/Weetabix/"+chX)
		self.scanners_volt_drive_Y = voltOut("/Weetabix/"+chY)
		self.conversion_factor = conversion_factor

	def moveX (self, value):
		self.scanners_volt_drive_X.write(conversion_factor * value)

	def moveY (self, value):
		self.scanners_volt_drive_Y.write(conversion_factor * value)


class PylonNICtrl (SpectroCtrl):

	def __init__(self, work_folder, sender_port="/Weetabix/port1/line3",
						 receiver_port = "/Weetabix/port1/line2"):
		self._wfolder = work_folder
		self._sender_port = sender_port
		self._receiver_port = receiver_port
		self.senderTask = trigSender(self._sender_port)
		self.senderTask.StartTask()
        self.receiverTask = trigReceiver(self._receiver_port)
        self.receiverTask.StartTask()

    def wait_for_ready (self):
    	CCDready = 0
    	while CCDready == 0:
    		CCDready = self.receiverTask.listen()

    def readout (self):
    	self.senderTask.emit()

class LockinCtrl (SpectroCtrl):
	def __init__(self, work_folder, lockinVisaAddress):
		self._wfolder = work_folder
		self._lockin = LockIn7265(lockinVisaAddress)

	def first_point (self):
		self.lockin.sendPulse()
		time.sleep(0.1)
		if lockin.readADCdigital():
			break

    def wait_for_ready (self):
    	while True:
    		if not lockin.readADCdigital():
    			break
    		time.sleep(0.1)

    def readout (self):
    	self.lockin.sendPulse()




class XYScan ():

	def __init__(self, scanner = None, detector = None):
		self._scanner = scanner
		self._detector = detector
		self._spectro = None
		self._ctr = None

		self.delayBetweenPoints = 1
		self.delayBetweenRows = 0.5

	def set_detection (self, value):
		if (value=='spectro'):
			self._spectro = True
		elif (value == 'APD'):
			self._ctr = True

	def set_range (self, xLim, xStep, yLim, yStep):

		self.xNbOfSteps = int(abs(py.floor((float(xLims[1]) - float(xLims[0])) / float(xStep))) + 1)
		self.xPositions = py.linspace(xLims[0], xLims[1], xNbOfSteps)
		self.yNbOfSteps = int(abs(py.floor((float(yLims[1]) - float(yLims[0])) / float(yStep))) + 1)
		self.yPositions = py.linspace(yLims[0], yLims[1], yNbOfSteps)
		self.totalNbOfSteps = self.xNbOfSteps * self.yNbOfSteps		

	def secondsInHMS(self, nbOfSeconds):
		hours = py.floor(nbOfSeconds / 3600)
		minutes = py.floor(nbOfSeconds % 3600) / 60
		seconds = nbOfSeconds - minutes*60 - hours*3600
		return hours, minutes, seconds

    def print_elapsed_time (self):
        if startTime == 0:
            startTime = time.time()
            if currentIndex % 20 == 0:
                elapsedTime = float(time.time() - startTime)
                remainingTime = elapsedTime / currentIndex * (totalNbOfSteps - (currentIndex-1))

                hoursE, minutesE, secondsE = secondsInHMS(elapsedTime)
                hoursR, minutesR, secondsR = secondsInHMS(remainingTime)

                print 'Elapsed time: {:.0f} h {:.0f} min {:.0f} s\tRemaining time: {:.0f} h {:.0f} min {:.0f} s'.format(hoursE, minutesE, secondsE, hoursR, minutesR, secondsR)


	def run_scan (self):

        try:
            startTime = 0
            firstPoint = True

            for y in self.yPositions:
                firstInRow = True
                for x in self.xPositions:
                    currentIndex = currentIndex + 1
                    self._scanner.moveX(x)
                    self._scanner.moveY(y)
             
                    # display update
                    print '{}/{} \t{:.1f} \t{:.1f}'.format(currentIndex, 
                                    self.xNbOfSteps*self.yNbOfSteps, x, y)
        
                    # For first point wait for a reaction (when acquisition is launched in WinSpec)
                    while firstPoint:
                        self._detector.first_point()

                    # elapsed time?
                    self.print_elapsed_time()

                    # delay between rows
                    if firstInRow:
                        time.sleep(delayBetweenRows)
                        firstInRow = False
                
                    # delay between points
                    time.sleep(delayBetweenPoints)
                
                    # trigger exposure
                    if firstPoint:
                        firstPoint = False
                    else:
                        self._detector.readout()            
                    
                    time.sleep(0.5)
                
                    #powerInVolts.append(voltmeter.read())
                    
                    # wait for CCD 'NOT SCAN' signal
                    self._detector.wait_for_ready()

                # move back to 0 smoothly
                for x in xPositions[::-1]:
                    self._scanner.moveX(x)
                    time.sleep(SMOOTH_DELAY)          

                # go smoothly to start position
                if backToZero:
                    goSmoothlyToPos(xPos=0, yPos=0, SxAxis=SxAxis, SyAxis=SyAxis)
        except:
            raise

        finally:
            self._scanner.close()
            self._detector.close()





		

