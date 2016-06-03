import numpy as np 
from PIL import Image
import os, win32gui, win32ui, win32con, cv2, time, math, json

def getKey(item):
    return item[1]

# Returns a PIL Image containing a screenshot of a region specified by left, top, right, bottom.
# left, top, right, bottom. are specified as a float between 0 and 1 which specify a percentage of
# the maximum screen coordinates.
#
# This might seem like primo autism but it's the most convenient way I could think of in 20 seconds
# to keep this resolution agnostic.

def getGameScreenImg(hwnd, left, top, right, bottom):
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
    screenImg = screenImg.crop((int(width*left), int(height*top), width*right, height*bottom))
    return screenImg
    
def convertToOpenCV(pilImage):
    return np.array(pilImage.convert('HSV')).astype(np.uint8)

def getContours(image, limits):
    shapeMask = cv2.inRange(image, limits[0], limits[1])
    im, cnts, _ = cv2.findContours(shapeMask.copy(), cv2.RETR_EXTERNAL,
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
        screenImg = convertToOpenCV((getGameScreenImg(rustWindow, 0.5, 0.5, 1.0, 1.0)))
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
        screenImg = getGameScreenImg(rustWindow, 0.5, 0.5, 1.0, 1.0)
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
        #Approximate bounding boxes by using the following ruleset:
        #Hunger bar does not have as many similarly saturated images in the screen
        #as thirst/hp. Assuming we have found it, then because the hp and thirst bars
        #are similar in height, we can narrow down the potential detected contours
        
        hpContours, thirstContours, hungerContours = barContours
        self.calibratedBoundingBoxes = [(0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)]
        #approximate hunger bar
        if len(hungerContours) == 0:
            print "No contour found for hunger bar while approximating, aborting approximation"
            return
        for cnt in hungerContours:
            #hunger bar is a rectangle, len(approx) is the number of edges
            approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt,True),True)
            if len(approx) == 4:
                self.calibratedBoundingBoxes[2] = cv2.boundingRect(cnt)
                self.calibrationBarDimensions[1] = self.calibratedBoundingBoxes[2][3]
                self.lower, self.upper = self.calibrationBarDimensions[1] - self.tolerance, self.calibrationBarDimensions[1] + self.tolerance

        #approximate thirst bar
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
        #approximate hp bar
        try:
            foundBar = False
            for cnt in hpContours:
                rect = cv2.boundingRect(cnt)
                if rect[3] < self.upper and rect[3] > self.lower:
                    self.calibratedBoundingBoxes[0] = rect
                    foundBar = True
            if foundBar == False:
                #hp bar will be the second largest bar is building priv bar on screen
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
        
class ActionBarDetector:

    # TODO:
    #
    #   - Get images for all weapons in the game
    #   - Find a solution for other resolutions than 64x64 of action bar slots
    #
    # Example usage:
    #
    # abd = ActionBarDetector()
    # rustWindow = win32gui.FindWindow(None, 'Rust')
    # abs = abd.getActionBarSlots(rustWindow)
    # for slot in abs:
    #      if MatchImage('bolt.jpg',0.3,slot):
    #           stats['bolt'] = True
    # 
    # and so on.
    #
    # Against a reasonably uniform background (rocks, sand, etc.) the templates are matched
    # to a certainty between 0.3 and 0.5. This ~should~ be enough to differentiate every item.
    # The only way to be sure is to go through and hand test each one. So far bolt and AK have
    # passed my tests, although both will fail against a very complicated background, (barbed wire,
    # etc.). The bolt has been the hardest template to match in the past, so this makes me cofident
    # this iteration is pretty solid.
     
    durabilityLimits = [np.array([50, 100, 100]), np.array([65, 255, 255])] # HSV boundaries
    
    # Matches supplied template, with name imagename, on image, img, and returns true
    # if template is matched with a confidence value greater than the threshold.
    def MatchImage(self, imagename, threshold, img):
    
        # Apply canny edge detecting algorithm to image and template
        # this makes image recognition a lot easier with a noisy background on image
        # and a white background on the template
    
        cannythresh1 = 100
        cannythresh2 = 200
        templ = cv2.imread(imagename, cv2.IMREAD_COLOR)
        templ_edge = cv2.Canny(templ,cannythresh1, cannythresh2)
        img_edge = cv2.Canny(img,cannythresh1,  cannythresh2)
        method = eval('cv2.TM_CCOEFF_NORMED')
        
        res = cv2.matchTemplate(img_edge, templ_edge, method)
        
        #w,h=cv2.cvtColor(templ,cv2.COLOR_BGR2GRAY).shape[::-1]
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        #cv2.rectangle(img, max_loc,(max_loc[0]+w,max_loc[1]+h),255,2)
        
        if max_val > threshold:
            return True
        else:
            return False
        
    def getDurabilityContours(self, image):
        return getContours(image, self.durabilityLimits)

    def getActionBarSlots(self, rustWindow):
    
        # Tries to find the action bar slots with these assumptions:
        #
        # The durability bar is the thinnest bar matching this color contour
        # All bars are always uniform in width
        # Durability bars are 1/15th the width of the action bar slot
        
        # Returns images of the action bar slots
        
        img = convertToOpenCV((getGameScreenImg(rustWindow, 0.25, 0.75, 0.75, 1.0)))
        durabilityContours = self.getDurabilityContours(img)
        durabilityBarBoundingBoxes = []
        actionBarSlotBoundingBoxes = []
        actionBarSlotImages = []
        
        for cnt in durabilityContours:
            #thirst bar is a rectangle, len(approx) is the number of edges
            approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt,True),True)
            if len(approx) >= 3:
                durabilityBarBoundingBoxes.append(cv2.boundingRect(cnt))
                
        for box in durabilityBarBoundingBoxes:
            y1 = ((box[1]+box[3])-box[2]*15)
            y2 = (box[1]+box[3])
            x1 = box[0]
            x2 = x1+box[2]*15
            actionBarSlotImages.append(img[y1:y2,x1:x2])
            
        return actionBarSlotImages
            
        
