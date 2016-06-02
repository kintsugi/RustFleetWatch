import numpy as np
import cv2
from PIL import Image
from PIL import ImageGrab

#lower upper in BGR
hpLimits = [np.array([50, 100, 100]), np.array([65, 255, 255])]
thirstLimits = [np.array([140, 150, 120]), np.array([150, 255, 255])]
hungerLimits = [np.array([10, 150, 150]), np.array([20, 255, 255])]
calibrationBarHeight = 0
tolerance = 5
lower, upper = (0, 0)

def getKey(item):
    return item[1]

def getMask(image, limits):
    return cv2.inRange(image, limits[0], limits[1])

def getContours(image, limits):
    shapeMask = getMask(image, limits)
    (cnts, _) = cv2.findContours(shapeMask.copy(), cv2.RETR_EXTERNAL,
	cv2.CHAIN_APPROX_SIMPLE)
    return cnts
    
def getBarBBoxes(image):
    #convert to openCV format if necessary
    image = convertToOpenCV(image)
    hpContours = getContours(image, hpLimits)
    thirstContours = getContours(image, thirstLimits)
    hungerContours = getContours(image, hungerLimits)
    #Not set bar height means detection is not calibrated and we must guess
    global calibrationBarHeight
    if calibrationBarHeight == 0:
        return guessAtBarBBox(hpContours, thirstContours, hungerContours)
    else:
        bboxes = []
        for contours in [hpContours, thirstContours, hungerContours]:
            calibratedBBox = getCalibratedBarBBoxes(contours)
            if len(calibratedBBox) == 1:
                print 'Guessing contours'
                return guessAtBarBBox(hpContours, thirstContours, hungerContours) 
            bboxes.append(calibratedBBox)
        return bboxes
        
  
def getCalibratedBarBBoxes(contours):
    global lower, upper
    for cnt in contours:
        (x, y, w, h) = cv2.boundingRect(cnt)
        approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt,True),True)
        if h < upper and h > lower and len(approx) == 4:
            return (x, y, w, h)
    print 'Warning: could not find matching contour in calibrated detection'
    return [0]

def guessAtBarBBox(hpContours, thirstContours, hungerContours):
    #tries to find bars with these assumptions:
    #HP bar is either the second largest contour in area or the only contour
    #thirst contour is the only contour that is a rectangle
    #hunger contour is the only detected contour
    bboxes = [None] * 3
    global calibrationBarHeight
    global tolerance
    global lower, upper

    if len(thirstContours) == 0:
        print "No contour found for thirst bar"
        bboxes[1] = (0, 0, 0, 0)
    for cnt in thirstContours:
        #count the number of edges
        approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt,True),True)
        if len(approx) == 4:
            bboxes[1] = cv2.boundingRect(cnt)
            calibrationBarHeight = bboxes[1][3]
            lower, upper = calibrationBarHeight - tolerance, calibrationBarHeight + tolerance
    try:
        foundBar = False
        for cnt in hungerContours:
            rect = cv2.boundingRect(cnt)
            if rect[3] < upper and rect[3] > lower:
                bboxes[2] = rect
                foundBar = True
        if foundBar == False:
            bboxes[2] = cv2.boundingRect(hungerContours[0])
    except IndexError:
        print "No contour found for hunger bar"
        bboxes[2] = (0, 0, 0, 0)
    try:
        foundBar = False
        for cnt in hpContours:
            rect = cv2.boundingRect(cnt)
            if rect[3] < upper and rect[3] > lower:
                bboxes[0] = rect
                foundBar = True
        if foundBar == False:
            hpAreaTuples = []
            for cnt in hpContours:
                hpAreaTuples.append((cnt, cv2.contourArea(cnt)))
                hpAreaTuples = sorted(hpAreaTuples, key=getKey)
                hpAreaTuples.reverse()
            slice = hpAreaTuples[0: 2]
            if(len(slice) == 2):
                bboxes[0] = cv2.boundingRect(hpAreaTuples[1][0])
            else:
                bboxes[0] = cv2.boundingRect(hpAreaTuples[0][0])
    except IndexError:
        print "No contour found for hunger bar"
        bboxes[0] = (0, 0, 0, 0)
    print bboxes
    return bboxes
    
def convertToOpenCV(pilImage):
    openCvImage = np.array(pilImage.convert('HSV')).astype(np.uint8)
    return openCvImage
    
def calibrateLimits(screen, bboxes):
    hpBarImg = screen.crop((bboxes[0][0], bboxes[0][1], bboxes[0][0] + bboxes[0][2], bboxes[0][1] + bboxes[0][3]))
    thirstBarImg = screen.crop((bboxes[1][0], bboxes[1][1], bboxes[1][0] + bboxes[1][2], bboxes[1][1] + bboxes[1][3]))
    hungerBarImg = screen.crop((bboxes[2][0], bboxes[2][1], bboxes[2][0] + bboxes[2][2], bboxes[2][1] + bboxes[2][3]))
    #setLimits(hpBarImg, hpLimits)
    #setLimits(thirstBarImg, thirstLimits)
    #setLimits(hungerBarImg, hungerLimits)

def setLimits(barImg, limits):
    width, height = barImg.size
    barImg = barImg.load()
    min = [255, 255, 255]
    max = [0, 0, 0]
    for x in range(width):
        for y in range(height):
            currPixel = barImg[x, y]
            for i in range(len(min)):
                if currPixel[i] < min[i]:
                    min[i] = currPixel[i]
            for i in range(len(max)):
                if currPixel[i] > max[i]:
                    max[i] = currPixel[i]
    min.reverse()
    max.reverse()
    limits = [np.array(min), np.array(max)]
