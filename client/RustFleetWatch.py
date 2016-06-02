import os, sys
from Tkinter import *
from PIL import Image
from PIL import ImageTk
from PIL import ImageGrab
import time
import math
import win32gui
import win32ui
import win32con
import time
import cvBarDetect
from socketIO_client import SocketIO, LoggingNamespace

root = Tk()
barLength = 0
debug = True
host = 'watchlist.ageudum.com'
port = 80
socketIO = SocketIO(host, port, LoggingNamespace)
    
def calibrate():
    global barLength
    rustWindow = win32gui.FindWindow(None, 'Rust')

    screenImg = getGameScreenImg(rustWindow)
    bboxes = cvBarDetect.getBarBBoxes(screenImg)
    cvBarDetect.calibrateLimits(screenImg, bboxes)
    barLengths = [bboxes[0][2], bboxes[1][2], bboxes[2][2]]
    if barLengths[0] == barLengths[1] and barLengths[0] == barLengths[2]:
        barLength = barLengths[0]
    else:
        print 'Warning: Calibrated bar lengths are not uniform', barLengths
        barLength = barLengths[0]
        hpRatio = float(healthCalibrationInput.get()) / 100
        barLength = barLength / hpRatio
    print 'finished calibration'

userNameLabel = Label(root, text="Username:")
userNameLabel.pack()
userNameInput = Entry(root, bd =5)
userNameInput.pack()
healthCalibrationLabel = Label(root, text="Current HP:")
healthCalibrationLabel.pack()
healthCalibrationInput = Entry(root, bd =5)
healthCalibrationInput.pack()
b = Button(root, text="Calibrate", command=calibrate)
b.pack()
hpPanel = None
hpText = None
thirstPanel = None
thirstText = None
hungerPanel = None
hungerText = None
if debug:
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

def getGameScreenImg(hwnd):
    hwnd = win32gui.FindWindow(None, 'Rust')
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
    screenImg = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)
    screenImg = screenImg.crop((clientOrigin[0] - windowRect[0], clientOrigin[1] - windowRect[1], clientRect[2] + (clientOrigin[0] - windowRect[0]), clientRect[3] + (clientOrigin[1] - windowRect[1])))
    width, height = screenImg.size
    screenImg = screenImg.crop((int(width * 0.5), int(height * 0.5), width, height))
    screenImg.save('test.png', 'PNG')
    return screenImg

def generatePayload(stats):
    print stats
    stats['username'] = userNameInput.get()
    stats['bolt'] = False
    stats['AK'] = False
    stats['pistol'] = False
    stats['pipe'] = False
    socketIO.emit('playerupdate', stats)
    
    
def loop():
    global barLength
    global debug
    rustWindow = win32gui.GetForegroundWindow()
    if win32gui.GetWindowText(rustWindow) == 'Rust' and barLength != 0:
        screenImg = getGameScreenImg(rustWindow)
        bboxes = cvBarDetect.getBarBBoxes(screenImg)
        
        stats = {}
        stats['health'] = int(float(bboxes[0][2]) / barLength * 100)
        stats['thirst'] = int(float(bboxes[1][2]) / barLength * 100)
        stats['hunger'] = int(float(bboxes[2][2]) / barLength * 100)
        #print hp, thirst, hunger
        generatePayload(stats)

        def showBar(bbox, imgPanel, textPanel, textPrefix):
            x0, y0 = (bbox[0], bbox[1])
            x1, y1 = (bbox[0] + bbox[2], bbox[1] + bbox[3])
            barBBox = (x0, y0, x1, y1)
            barImg = screenImg.crop(barBBox)
            uiImage = ImageTk.PhotoImage(barImg)
            imgPanel.configure(image = uiImage)
            imgPanel.image = uiImage
            textStr = textPrefix + str(float(bbox[2]) / barLength * 100) + "%"
            textPanel.configure(text = textStr)
        if debug:
            showBar(bboxes[0], hpPanel, hpText, "HP: ")
            showBar(bboxes[1], thirstPanel, thirstText, "Thirst: ")
            showBar(bboxes[2], hungerPanel, hungerText, "Hunger: ")
        
    root.after(100, loop)
root.attributes("-topmost", True)
root.after(100, loop)
root.mainloop()
