from ActionBarDetector import *
from Tkinter import *
import win32gui
import cv2

j = 0

def getSlots():
    global j
    abd = ActionBarDetector()

    rustWindow = win32gui.FindWindow(None, "Rust")

    abd.getActionBarSlotBoundingBoxes(rustWindow)
    abd.getActionBarSlotImages(rustWindow)

    for im in abd.actionBarSlotImages:
        cv2.imwrite('images/{0}.jpg'.format(j),im)
        j+=1


if __name__ == '__main__':

    root = Tk()
    bt_getSlots = Button(root, text="Get Slots", command=getSlots)
    bt_getSlots.pack()

    root.mainloop()
    