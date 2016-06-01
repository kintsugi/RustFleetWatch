import os, sys
from Tkinter import *
from PIL import Image
from PIL import ImageTk
from PIL import ImageGrab
import time
import math
import win32gui
import time
import cvBarDetect

root = Tk()

barLength = [0]
    
def calibrate():
    activeWindow = win32gui.FindWindow(None, 'Rust')
    rect = win32gui.GetWindowRect(activeWindow)
    inGameRect = win32gui.GetClientRect(activeWindow)
    x0, y0 = win32gui.ClientToScreen(activeWindow, (inGameRect[0], inGameRect[1]))
    x1, y1 = win32gui.ClientToScreen(activeWindow, (inGameRect[2], inGameRect[3]))
    screenBox = (x0, y0, x1, y1)
    screen = ImageGrab.grab((x0 + int(float(x1) * 0.5), y0 + int(float(y1) * 0.5), x1, y1))
    bboxes = cvBarDetect.getBarBBoxes(screen)
    cvBarDetect.calibrateLimits(screen, bboxes)
    screen.save('screen.png', 'PNG')
    print bboxes
    barLengths = [bboxes[0][2], bboxes[1][2], bboxes[2][2]]
    if barLengths[0] == barLengths[1] and barLengths[0] == barLengths[2]:
        barLength[0] = barLengths[0]
    else:
        print 'Warning: Calibrated bar lengths are not uniform', barLengths
        barLength[0] = max(barLengths)
    print 'finished calibration'
    
b = Button(root, text="Calibrate", command=calibrate)
b.pack()
hpPanel = Label(root, image = None)
hpPanel.pack()
hpText = Label(root, text="HP")
hpText.pack()
thirstPanel = Label(root, image = None)
thirstPanel.pack() 
thirstText = Label(root, text="Thirst")
thirstText.pack()
hungerPanel = Label(root, image = None)
hungerPanel.pack()
hungerText = Label(root, text="Hunger")
hungerText.pack()

def getGameScreenImg(rustWindow):
    inGameRect = win32gui.GetClientRect(rustWindow)
    x0, y0 = win32gui.ClientToScreen(rustWindow, (inGameRect[0], inGameRect[1]))
    x1, y1 = win32gui.ClientToScreen(rustWindow, (inGameRect[2], inGameRect[3]))
    screenBBox = (x0, y0, x1, y1)
    screen = ImageGrab.grab((x0 + int(float(x1) * 0.5), y0 + int(float(y1) * 0.5), x1, y1))
    return (screen, screenBBox)

def loop():
    rustWindow = win32gui.GetForegroundWindow()
    if win32gui.GetWindowText(rustWindow) == 'Rust' and barLength[0] != 0:
        print "update"
        screenImg, screenBBox = getGameScreenImg(rustWindow)
        bboxes = cvBarDetect.getBarBBoxes(screenImg)
        screenImg.save('screen.png','PNG')
        def showBar(bbox, imgPanel, textPanel, textPrefix):
            x0, y0 = win32gui.ClientToScreen(rustWindow, (int(float(screenBBox[2]) * 0.5) + bbox[0], int(float(screenBBox[3]) * 0.5) + bbox[1]))
            x1, y1 = win32gui.ClientToScreen(rustWindow, (int(float(screenBBox[2]) * 0.5) + bbox[0] + bbox[2], int(float(screenBBox[3]) * 0.5) + bbox[1] + bbox[3]))
            barBBox = (x0, y0, x1, y1)
            barImg = ImageGrab.grab(barBBox)
            uiImage = ImageTk.PhotoImage(barImg)
            imgPanel.configure(image = uiImage)
            imgPanel.image = uiImage
            textStr = textPrefix + str(float(bbox[2]) / barLength[0] * 100) + "%"
            textPanel.configure(text = textStr)
        showBar(bboxes[0], hpPanel, hpText, 'HP: ')
        showBar(bboxes[1], thirstPanel, thirstText, 'Thirst: ')
        showBar(bboxes[2], hungerPanel, hungerText, 'Hunger: ')
    else:
        root.after(500, loop)
root.attributes("-topmost", True)
root.after(500, loop)
root.mainloop()
