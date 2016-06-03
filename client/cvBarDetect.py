import numpy as np 
from PIL import Image
import os, win32gui, win32ui, win32con, cv2, time, math, json

def getKey(item):
    return item[1]

def getGameScreenImg(hwnd):
    # http://stackoverflow.com/questions/3260559/how-to-get-a-window-or-fullscreen-screenshot-in-python-3k-without-pil
    clientOrigin = win32gui.ClientToScreen(hwnd, (0, 0))
    windowRect = win32gui.GetWindowRect(hwnd)
    clientRect = win32gui.GetClientRect(hwnd)
    l,t,r,b=win32gui.GetWindowRect(hwnd)
    h=b-t
    w=r-l
    hDC = win32gui.GetWindowDC(hwnd)
    myDC=win32ui.CreateDCFromHandle(hDC)
    newDC=myDC.CreateCompatibleDC()
    
    myBitMap = win32ui.CreateBitmap()
    myBitMap.CreateCompatibleBitmap(myDC, w, h)
    
    newDC.SelectObject(myBitMap)
    
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.1)
    newDC.BitBlt((0,0),(w, h) , myDC, (0,0), win32con.SRCCOPY)
    myBitMap.Paint(newDC)
    bmpinfo = myBitMap.GetInfo()
    bmpstr = myBitMap.GetBitmapBits(True)
    #converting bmp to PIL image
    screenImg = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)
    #removes window border if not in fullscreen
    screenImg = screenImg.crop((clientOrigin[0] - windowRect[0], clientOrigin[1] - windowRect[1], clientRect[2] + (clientOrigin[0] - windowRect[0]), clientRect[3] + (clientOrigin[1] - windowRect[1])))
    width, height = screenImg.size
    #crop the bottom right quarter of the screen
    screenImg = screenImg.crop((int(width * 0.5), int(height * 0.5), width, height))
    return screenImg
    
def convertToOpenCV(pilImage):
    return np.array(pilImage.convert('HSV')).astype(np.uint8)

def getContours(image, limits):
    shapeMask = cv2.inRange(image, limits[0], limits[1])
    (cnts, _) = cv2.findContours(shapeMask.copy(), cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE)
    return cnts
    
def calcCoords(bbox):
    x0, y0 = bbox[0], bbox[1]
    x1 = bbox[0] + bbox[2]
    y1 = bbox[1] + bbox[3]
    return x0, y0, x1, y1
        
class BarDetector:
    #Limits in HSV credits to @Shantidly
    hpLimits = [np.array([50, 100, 100]), np.array([65, 255, 255])]
    thirstLimits = [np.array([140, 150, 120]), np.array([150, 255, 255])]
    hungerLimits = [np.array([10, 150, 150]), np.array([20, 255, 255])]
    tolerance = 5
    
    def __init__(self):
        self.calibrated = False
        #Width, Height
        self.calibrationBarDimensions = [0, 0]
        self.lower, self.upper = (0, 0)
        #Order is hp, thirst, hunger
        #Bounding box order is x, y, w, h where w, h are not coordinates, but the actual width/length
        self.calibratedBoundingBoxes = [(0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)]
        self.currentBarBoundingBoxes = [(0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)]
        #attempt to read any preexisting calibration
        if os.path.exists('conf.json'):
            with open('conf.json') as dataFile:
                conf = json.load(dataFile)
                self.calibratedBoundingBoxes = conf['calibratedBoundingBoxes']
                self.calibrationBarDimensions =  conf['calibrationBarDimensions']
                self.calibrated = True
    
    #Only call once it is already calibrated
    def getStats(self, rustWindow):
        stats = {}
        health, thirst, hunger = (0, 0, 0)
        self.findBarBoundingBoxes(rustWindow)
        #Measure stat by the current length filled / total length
        health = int(round(float(self.currentBarBoundingBoxes[0][2]) / self.calibrationBarDimensions[0] * 100))
        thirst = int(round(float(self.currentBarBoundingBoxes[1][2]) / self.calibrationBarDimensions[0] * 100))
        hunger = int(round(float(self.currentBarBoundingBoxes[2][2]) / self.calibrationBarDimensions[0] * 100))
        if health > 100 or health < 0:
            print 'Warning: Health is measured to be greater than 100 or less than 0, recalibrate if necessary'
            if health < 0:
                health = 0
            elif health > 100:
                health = 100
        if thirst > 100 or thirst < 0:
            print 'Warning: Thirst is measured to be greater than 100 or less than 0, recalibrate if necessary'
            if thirst < 0:
                thirst = 0
            elif thirst > 100:
                thirst = 100
        if hunger > 100 or hunger < 0:
            print 'Warning: Hunger is measured to be greater than 100 or less than 0, recalibrate if necessary'
            if hunger < 0:
                hunger = 0
            elif hunger > 100:
                hunger = 100
        stats['health'] = health
        stats['thirst'] = thirst
        stats['hunger'] = hunger
        return stats

    def calibrate(self, rustWindow, currentHP, currentThirst, currentHunger):
        if len(currentHP) == 0 or len(currentThirst) == 0 or len(currentHunger) == 0:
            return
        currentHP, currentThirst, currentHunger = int(currentHP), int(currentThirst), int(currentHunger)
        screenImg = convertToOpenCV((getGameScreenImg(rustWindow)))
        self.approximateBoundingBoxes(self.getBarContours(screenImg))
        #Estimates the length of a full bar if currentHP != 100, if it does then
        #the length measured from detection is accurate
        if currentHP < 0:
            currentHP = 0
        elif currentHP > 100:
            currentHP = 100
        if currentThirst < 0:
            currentThirst = 0
        elif currentThirst > 250:
            currentThirst = 250
        if currentHunger < 0:
            currentHunger = 0
        elif currentHunger > 500:
            currentHunger = 500
        hpBarLengthRatio = float(currentHP) / 100
        thirstBarLengthRatio = float(currentThirst) / 250
        hungerBarLengthRatio = float(currentHunger) / 500
        hpLength = int(math.ceil(self.calibratedBoundingBoxes[0][2] / hpBarLengthRatio))
        thirstLength = int(math.ceil(self.calibratedBoundingBoxes[1][2] / thirstBarLengthRatio))
        hungerLength = int(math.ceil(self.calibratedBoundingBoxes[2][2] / hungerBarLengthRatio))
        avgLength = int(round((hpLength + thirstLength + hungerLength) / 3))
        self.calibrationBarDimensions[0] = avgLength
        self.calibratedBoundingBoxes[0] = (self.calibratedBoundingBoxes[0][0], self.calibratedBoundingBoxes[0][1], avgLength, self.calibratedBoundingBoxes[0][3])
        self.calibratedBoundingBoxes[1] = (self.calibratedBoundingBoxes[1][0], self.calibratedBoundingBoxes[1][1], avgLength, self.calibratedBoundingBoxes[1][3])
        self.calibratedBoundingBoxes[2] = (self.calibratedBoundingBoxes[2][0], self.calibratedBoundingBoxes[2][1], avgLength, self.calibratedBoundingBoxes[2][3])
        self.findBarBoundingBoxes(rustWindow)
        self.calibrated = True
        #write values to disk
        conf = {}
        conf['calibratedBoundingBoxes'] = self.calibratedBoundingBoxes
        conf['calibrationBarDimensions'] = self.calibrationBarDimensions
        with open('conf.json', 'w') as dataFile:
            json.dump(conf, dataFile)
            
    #Assuming detection has already been properly calibrated, we only have to look in the
    #bounding box
    def findBarBoundingBoxes(self, rustWindow):
        screenImg = getGameScreenImg(rustWindow)
        self.hpBarImg = screenImg.crop(calcCoords(self.calibratedBoundingBoxes[0]))
        self.thirstBarImg = screenImg.crop(calcCoords(self.calibratedBoundingBoxes[1]))
        self.hungerBarImg = screenImg.crop(calcCoords(self.calibratedBoundingBoxes[2]))
        hpBarImg = convertToOpenCV(self.hpBarImg)
        thirstBarImg = convertToOpenCV(self.thirstBarImg)
        hungerBarImg = convertToOpenCV(self.hungerBarImg)
        
        hpContours = getContours(hpBarImg, self.hpLimits)
        thirstContours = getContours(thirstBarImg, self.thirstLimits)
        hungerContours = getContours(hungerBarImg, self.hungerLimits)
        #is there a sitation where there would be more than one detected contour?
        try:
            self.currentBarBoundingBoxes[0] = cv2.boundingRect(hpContours[0])
            self.currentBarBoundingBoxes[1] = cv2.boundingRect(thirstContours[0])
            self.currentBarBoundingBoxes[2] = cv2.boundingRect(hungerContours[0])
        except IndexError:
            self.currentBarBoundingBoxes = [(0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)]
            
    def approximateBoundingBoxes(self, barContours):
        #tries to find the bars with these assumptions:
        #The thirst bar is the easiest to detect as there are no other bars on the
        #screen that are very similar in color or saturation.
        #testing has shown that the ground is detected when using the hunger bar limits
        #and the HP bar shares limits with the building privelege bar and tool durability bars
        #All bars are always uniform in height, and there is should be no other object that has the
        #same height as the bars. Therefore, if the thirst bar is accurately determined, there is
        #a high probability that a detected contour with similar height to the thirst bar is
        #the hp/hunger bar
        hpContours, thirstContours, hungerContours = barContours
        self.calibratedBoundingBoxes = [(0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)]
        #approximate thirst bar
        if len(hungerContours) == 0:
            print "No contour found for hunger bar while approximating, aborting approximation"
            return
        for cnt in hungerContours:
            #thirst bar is a rectangle, len(approx) is the number of edges
            approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt,True),True)
            if len(approx) == 4:
                self.calibratedBoundingBoxes[2] = cv2.boundingRect(cnt)
                self.calibrationBarDimensions[1] = self.calibratedBoundingBoxes[2][3]
                self.lower, self.upper = self.calibrationBarDimensions[1] - self.tolerance, self.calibrationBarDimensions[1] + self.tolerance
        #approximate hunger bar. If no bar similar in height to thirst bar is found, take the 
        #first detected contour
        try:
            foundBar = False
            for cnt in thirstContours:
                rect = cv2.boundingRect(cnt)
                if rect[3] < self.upper and rect[3] > self.lower:
                    self.calibratedBoundingBoxes[1] = rect
                    foundBar = True
            if foundBar == False:
                self.calibratedBoundingBoxes[1] = cv2.boundingRect(thirstContours[0])
        except IndexError:
            print "No contour found for thirst bar"
            self.calibratedBoundingBoxes[1] = (0, 0, 0, 0)
        #approximate health bar, If no bar similar in height to thirst bar is found, either take the
        #second largest contour in area (e.g. building privilege bar is detected) or the first detected bar
        try:
            foundBar = False
            for cnt in hpContours:
                rect = cv2.boundingRect(cnt)
                if rect[3] < self.upper and rect[3] > self.lower:
                    self.calibratedBoundingBoxes[0] = rect
                    foundBar = True
            if foundBar == False:
                hpAreaTuples = []
                for cnt in hpContours:
                    hpAreaTuples.append((cnt, cv2.contourArea(cnt)))
                    hpAreaTuples = sorted(hpAreaTuples, key=getKey)
                    hpAreaTuples.reverse()
                slice = hpAreaTuples[0: 2]
                if(len(slice) == 2):
                    self.calibratedBoundingBoxes[0] = cv2.boundingRect(hpAreaTuples[1][0])
                else:
                    self.calibratedBoundingBoxes[0] = cv2.boundingRect(hpAreaTuples[0][0])
        except IndexError:
            print "No contour found for hunger bar"
            self.calibratedBoundingBoxes[0] = (0, 0, 0, 0)
    
    def getBarContours(self, image):
        return (getContours(image, self.hpLimits), getContours(image, self.thirstLimits), getContours(image, self.hungerLimits))
        
    
