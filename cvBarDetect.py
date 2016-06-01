import numpy as np
import cv2
from PIL import Image
from PIL import ImageGrab

#lower upper in BGR
hpLimits = [np.array([40, 110, 90]), np.array([80, 200, 160])]
thirstLimits = [np.array([120, 70, 15]), np.array([240, 180, 80])]
hungerLimits = [np.array([30, 90, 175]), np.array([80, 160, 255])]
calibrationBarHeight = 0

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
            bboxes.append(getCalibratedBarBBoxes(contours))
        return bboxes
        
  
def getCalibratedBarBBoxes(contours):
    print 'getting calibrated boxes'
    for cnt in contours:
        (x, y, w, h) = cv2.boundingRect(cnt)
        approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt,True),True)
        print h, calibrationBarHeight
        if h == calibrationBarHeight and len(approx) == 4:
            cv2.drawContours(testImage, [cnt], -1, (0, 255, 0), 2)
            cv2.imwrite('contour' + str(contourNum) + '.png', testImage)
            return (x, y, w, h)
    print 'Warning: could not find matching contour in calibrated detection'
    return (0, 0, 0, 0)

def guessAtBarBBox(hpContours, thirstContours, hungerContours):
    #tries to find bars with these assumptions:
    #HP bar is either the second largest contour in area or the only contour
    #thirst contour is the only contour that is a rectangle
    #hunger contour is the only detected contour
    bboxes = []
    #find hp
    hpAreaTuples = []
    for cnt in hpContours:
        hpAreaTuples.append((cnt, cv2.contourArea(cnt)))
    hpAreaTuples = sorted(hpAreaTuples, key=getKey)
    hpAreaTuples.reverse()
    try:
        slice = hpAreaTuples[0: 2]
        if(len(slice) == 2):
            bboxes.append(cv2.boundingRect(hpAreaTuples[1][0]))
        else:
            bboxes.append(cv2.boundingRect(hpAreaTuples[0][0]))
    except IndexError:
        print "No found area tuple for hp bar"
        bboxes.append((0, 0, 0, 0))

    #find thirst
    if len(thirstContours) == 0:
        print "No contour found for thirst bar"
        bboxes.append((0, 0, 0, 0))
    for cnt in thirstContours:
        #count the number of edges
        approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt,True),True)
        if len(approx) == 4:
            bboxes.append(cv2.boundingRect(cnt))
    #find hunger
    try:
        bboxes.append(cv2.boundingRect(hungerContours[0]))
    except IndexError:
        print "No contour found for hunger bar"
        bboxes.append((0, 0, 0, 0))
    barHeights = [bboxes[0][3], bboxes[1][3], bboxes[2][3]]
    global calibrationBarHeight
    if barHeights[0] == barHeights[1] and barHeights[0] == barHeights[2]:
        calibrationBarHeight = barHeights[0]
    else:
        print 'Warning: Calibrated bar heights are not uniform', barHeights
        calibrationBarHeight = max(barHeights)
    return bboxes
    
def convertToOpenCV(pilImage):
    openCvImage = np.array(pilImage)
    openCvImage = openCvImage[:, :, ::-1].copy()
    return openCvImage
    
def calibrateLimits(screen, bboxes):
    hpBarImg = screen.crop((bboxes[0][0], bboxes[0][1], bboxes[0][0] + bboxes[0][2], bboxes[0][1] + bboxes[0][3]))
    thirstBarImg = screen.crop((bboxes[1][0], bboxes[1][1], bboxes[1][0] + bboxes[1][2], bboxes[1][1] + bboxes[1][3]))
    hungerBarImg = screen.crop((bboxes[2][0], bboxes[2][1], bboxes[2][0] + bboxes[2][2], bboxes[2][1] + bboxes[2][3]))
    setLimits(hpBarImg, hpLimits)
    setLimits(thirstBarImg, thirstLimits)
    setLimits(hungerBarImg, hungerLimits)

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
