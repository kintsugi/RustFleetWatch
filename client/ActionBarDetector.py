import numpy as np 
import os, win32gui, win32ui, win32con, cv2, time, math, logging, collections
from PIL import Image
from BarDetector import *

class ActionBarDetector:

    # USAGE:    
    #
    #   - Usage is as simple as:
    #
    #       abd = ActionBarDetector()
    #       items = abd.getMatches()
    #
    #     which sets items to be a list containing tuples for each item with the first value being the name of
    #     the item in the bar e.g.
    #
    #     [('bolt', 8275823.0), ('ak', 98029345.0)]

    TEMPLATES = {"bolt" : "images/bolt.jpg",
                 "AK"   : "images/AK.jpg",
                 "eoka_pistol" : "images/eoka.jpg",
                 "flame" : "images/flame.jpg",
                 "semi_pistol" : "images/pistol.jpg",
                 "pump_shotgun" : "images/pump.jpg",
                 "waterpipe_shotgun" : "images/pipe.jpg",
                 "rocket_launcher" : "images/rocket.jpg",
                 "salvaged_cleaver" : "images/cleaver.jpg",
                 "thompson" : "images/thompson.jpg",
                 #"salvaged_sword" : "images/ssword.jpg",
                 "revolver" : "images/revolver.jpg",
                 "machete"  : "images/machete.jpg",
                 "bone_club" : "images/bone_club.jpg",
                 "bone_knife" : "images/bone_knife.jpg",
                 "custom_smg" : "images/custom_smg.jpg",
                 "crossbow" : "images/crossbow.jpg",
                 "spear" : "images/spear.jpg",
                 "semi_rifle" : "images/semi_rifle.jpg",
                 "mace" : "images/mace.jpg",
                 "longsword" : "images/longsword.jpg",
                 "hunting_bow" : "images/hunting_bow.jpg",
                 "salvaged_icepick" : "images/salvaged_icepick.jpg",
                 "stone_hatchet" : "images/stone_hatchet.jpg",
                 "salvaged_hammer" : "images/salvaged_hammer.jpg",
                 "salvaged_axe" : "images/salvaged_axe.jpg",
                 "pickaxe" : "images/pickaxe.jpg",
                 "hatchet" : "images/hatchet.jpg",
                 "torch" : "images/torch.jpg",
                 "stone_pickaxe" : "images/stone_pickaxe.jpg",
                 "water_bucket" : "images/bucket.jpg"
    } # etc, need to add all items with durability bars

    durabilityLimits = [np.array([50, 100, 100]), np.array([65, 255, 255])] # HSV boundaries
    durabilityBarBoundingBoxes = []
    
    # Matches supplied template, with name imagename, on image, img, and returns true
    # if template is matched with a confidence value greater than the threshold.
    def MatchImage(self, imagename, img):
    
        # Apply canny edge detecting algorithm to image and template
        # this makes image recognition a lot easier with a noisy background on image
        # and a white background on the template

        cannythresh1 = 130
        cannythresh2 = 180

        templ = cv2.imread(imagename, cv2.IMREAD_COLOR)
        sf = self.getScaleFactor()
        print sf
        
        print templ.shape
        templ = cv2.resize(templ,dsize=(0,0),fx=sf, fy=sf)
        print templ.shape
        cv2.waitKey(0)
        kernel = np.ones((2,2),np.uint8)

        templ_edge = cv2.Canny(templ,cannythresh1,cannythresh2)
        templ_edge = cv2.dilate(templ_edge,kernel,iterations=1)
        img_edge = cv2.Canny(img,cannythresh1,cannythresh2)
        img_edge = cv2.dilate(img_edge,kernel,iterations=1)

        method = eval('cv2.TM_CCOEFF')
        
        res = cv2.matchTemplate(img_edge, templ_edge, method)
        
        #w,h=cv2.cvtColor(templ,cv2.COLOR_BGR2GRAY).shape[::-1]
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        #cv2.rectangle(img, max_loc,(max_loc[0]+w,max_loc[1]+h),255,2)
        return max_val
        
    def getDurabilityContours(self, image):
        return getContours(image, self.durabilityLimits)

    def getScaleFactor(self):
        # 90.0 is a magic number representing the width of the action bar slot at 1080p
        return (self.actionBarSlotImages[0].shape[1] / (90.0))
    
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
        self.actionBarSlotNumber = len(actionBarSlotImages)
        #self.actionBarSlotImagesPIL = Image.fromarray(np.concatenate(self.actionBarSlotImages, axis=1))

    def getActionBarSlotImageCat(self):
        return cv2.hconcat(self.actionBarSlotImages)
    
    # This is where the meme dream occurs. Match every image with durability in game to concatenated slot images
    # and return the n (n = self.actionBarSlotNumber) best matches. For the items we want to track (probably just
    # guns) we can just check if the returned tuple contains the item.
    #
    # Returns a tuple of strings representing the detected items

    def getMatches(self):
        rustWindow = win32gui.FindWindow(None, 'Rust')

        self.getActionBarSlotBoundingBoxes(rustWindow)
        self.getActionBarSlotImages(rustWindow)
        actionBar = self.getActionBarSlotImageCat()

        b = 0
        vals = {}
        res = []

        for k,v in self.TEMPLATES.iteritems():
            a = self.MatchImage(v,actionBar)
            vals[k] = a

        vals_sorted = collections.OrderedDict(sorted(vals.items(), key=lambda t: t[1]))
        
        for i in range(0,self.actionBarSlotNumber):
            res.append(vals_sorted.popitem(last=True))

        return res

            

