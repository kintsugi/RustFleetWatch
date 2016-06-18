from ActionBarDetector import ActionBarDetector
import win32gui
from Tkinter import *
import cv2

class ActionBarDetectorTest(ActionBarDetector):

    METHODS = [
        ("cv2.TM_CCOEFF", eval("cv2.TM_CCOEFF")),
        ("cv2.TM_CCORR", eval("cv2.TM_CCORR")),
        ("cv2.TM_SQDIFF", eval("cv2.TM_SQDIFF")),
    ]

    PREPROC = [
        ("None", 0),
        ("Sobel", 1),
        ("Canny", 2),
        ("Histeq", 3),
    ]

    WEAPONS = [
        ("bolt", "images/bolt"),
        ("AK", "images/AK"),
    ]

    def MatchImage(self, imagename, img):
        templ = cv2.imread(imagename, cv2.IMREAD_GRAYSCALE)

        if self.preproc.get() == 1:
            img = cv2.Sobel(img, 2, 1, 1)
            templ = cv2.Sobel(templ, 2, 1, 1)
        elif self.preproc.get() == 2:
            img = cv2.Canny(img, self.sb_cannymin.get(), self.sb_cannymax.get())
            templ = cv2.Canny(templ, self.sb_cannymin.get(), self.sb_cannymax.get())
        elif self.preproc.get() == 3:
            img = cv2.equalizeHist(img)
            templ = cv2.equalizeHist(templ)

        method = self.method.get()
        res = cv2.matchTemplate(img, templ, method)
        
        #w,h=cv2.cvtColor(templ,cv2.COLOR_BGR2GRAY).shape[::-1]
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        #cv2.rectangle(img, max_loc,(max_loc[0]+w,max_loc[1]+h),255,2)
        
        return (min_val, max_val)

    def __init__(self):
        self.root = Tk()
        self.flag_sobel = False
        self.flag_canny = False
        self.flag_histeq = False

        # Put interface shit here
        # -----------------------

        # Methods Radiobuttons - Use self.method.get() to retrieve method flag

        self.method = IntVar()
        self.method.set(eval("cv2.TM_CCOEFF"))

        self.txt_methods = Label(self.root, text="Method")
        self.txt_methods.pack()

        for text,method in self.METHODS:
            b = Radiobutton(self.root, text=text, variable=self.method, value=method)
            b.pack()

        # Preprocessing Radiobuttons - Use self.preproc.get() to retrieve preproc flag
        #
        # FLAGREF:
        #     1 - Sobel
        #     2 - Canny
        #     3 - Histeq

        self.preproc = IntVar()
        self.preproc.set(1)

        self.txt_preprocessing = Label(self.root, text="Preprocessing")
        self.txt_preprocessing.pack()

        for text,preproc in self.PREPROC:
            b = Radiobutton(self.root, text=text, variable=self.preproc, value=preproc)
            b.pack()

        # Call self.sb_cannymin.get() to get scale  values

        self.txt_cannymin = Label(self.root, text="Minimum Canny Threshold")
        self.sb_cannymin = Scale(self.root, from_=0, to=300, state=DISABLED,
                                 orient=HORIZONTAL)
        self.txt_cannymax = Label(self.root, text="Maximum Canny Threshold")
        self.sb_cannymax = Scale(self.root, from_=0, to=300, state=DISABLED,
                                 orient=HORIZONTAL)

        self.txt_cannymin.pack()
        self.sb_cannymin.pack()
        self.txt_cannymax.pack()
        self.sb_cannymax.pack()

        def canny_scalebar(val,b,trace):
            var = self.preproc.get()
            if var == 2:
                self.sb_cannymin.config(state=NORMAL)
                self.sb_cannymax.config(state=NORMAL)
            else:
                self.sb_cannymin.config(state=DISABLED)
                self.sb_cannymax.config(state=DISABLED)

        self.preproc.trace('w', canny_scalebar)

        # Min/Max Detection Value Output

        self.bt_eval = Button(self.root, text="Evaluate", command=self.evaluate)
        self.bt_eval.pack()

        # -----------------------

        self.root.mainloop()

    def evaluate(self):
        rustWindow = win32gui.FindWindow(None, 'Rust')
        self.getActionBarSlotBoundingBoxes(rustWindow)
        self.getActionBarSlotImages(rustWindow)

        f = open("out.txt", "a")

        f.write("Preproc: {0}\nMethod: {1}\n ".format(self.preproc.get(), self.method.get()))
        
        i = 1

        for slot in self.actionBarSlotImages:
            f.write("---------- Slot {0} ----------\n".format(i))
            for wep in self.WEAPONS:
                (min, max) = self.MatchImage('{0}.jpg'.format(wep[1]),slot)
                f.write("{0}: {1}, {2}\n".format(wep, min, max))

            i+=1

if __name__ == '__main__':
    abd = ActionBarDetectorTest()