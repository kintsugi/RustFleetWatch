import numpy as np 
import os, win32gui, win32ui, win32con, cv2, time, math, logging
from PIL import Image
from BarDetector import *

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
    durabilityBarBoundingBoxes = []
    
    # Matches supplied template, with name imagename, on image, img, and returns true
    # if template is matched with a confidence value greater than the threshold.
    def MatchImage(self, imagename, threshold, img):
    
        # Apply canny edge detecting algorithm to image and template
        # this makes image recognition a lot easier with a noisy background on image
        # and a white background on the template

        cannythresh1 = 200
        cannythresh2 = 250
        templ = cv2.imread(imagename, cv2.IMREAD_COLOR)
        templ_edge = cv2.Canny(templ,cannythresh1, cannythresh2)
        img_edge = cv2.Canny(img,100,  150)
        method = eval('cv2.TM_CCOEFF')
        
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

    def getActionBarSlotBoundingBoxes(self, rustWindow):
    
        # Tries to find the action bar slots with these assumptions:
        #
        # The durability bar is the thinnest bar matching this color contour
        # All bars are always uniform in width
        # Durability bars are 1/15th the width of the action bar slot
        
        # Returns images of the action bar slots
        
        img = convertToOpenCV((getGameScreenImg(rustWindow, 0.25, 0.75, 0.75, 1.0)))
        durabilityContours = self.getDurabilityContours(img)
        self.durabilityBarBoundingBoxes = []
        actionBarSlotBoundingBoxes = []
 
        try:
            for cnt in durabilityContours:
                #thirst bar is a rectangle, len(approx) is the number of edges
                approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt,True),True)
                if len(approx) >= 3:
                    self.durabilityBarBoundingBoxes.append(cv2.boundingRect(cnt))
        except IndexError:
            logging.warning('no durability bounding boxes found')
            logging.error(IndexError)
            self.durabilityBarBoundingBoxes = []

    def getActionBarSlotImages(self, rustWindow):
        img = cv2.cvtColor(convertToOpenCV((getGameScreenImg(rustWindow, 0.25, 0.75, 0.75, 1.0))), cv2.COLOR_HSV2BGR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        actionBarSlotImages = []

        for box in self.durabilityBarBoundingBoxes:
            y1 = ((box[1]+box[3])-box[2]*15)
            y2 = (box[1]+box[3])
            x1 = box[0]+box[2]
            x2 = x1+box[2]*15
            actionBarSlotImages.append(img[y1:y2,x1:x2])
            
        self.actionBarSlotImages = actionBarSlotImages
        #self.actionBarSlotImagesPIL = Image.fromarray(np.concatenate(self.actionBarSlotImages, axis=1))
            
        
