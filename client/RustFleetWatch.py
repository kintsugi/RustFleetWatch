import os, sys, win32gui, base64, zlib, tempfile, json
from mtTkinter import *
import tkMessageBox
from PIL import ImageTk
from BarDetector import BarDetector
#from ActionBarDetector import ActionBarDetector
from socketIO_client import SocketIO, LoggingNamespace
import logging
logging.basicConfig(filename='log.txt', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s %(name)s %(filename)s %(module)s.%(funcName)s line:%(lineno)d %(message)s')
logger=logging.getLogger(__name__)

class App:

    debug = True
    host = 'watchlist.ageudum.com'
    port = 80
    defaultHertz = 2
    
    def __init__(self):
        
        try:
            self.socketIO = SocketIO(self.host, self.port, LoggingNamespace, False)
        except Exception as err:
            logger.error(err)
            tkMessageBox.showinfo("Error connecting to server.", "Could not connect to server.\nCheck internet connection or contact server admin with log.txt.")
            return

        self.root = Tk()
        self.root.wm_title("Rust Fleet Watchlist")
        self.root.minsize(width=250, height=425)
        self.root.attributes("-topmost", True)
        
        #Removing default tk icon until a better one is found
        #http://stackoverflow.com/questions/550050/removing-the-tk-icon-on-a-tkinter-window
        ICON = zlib.decompress(base64.b64decode('eJxjYGAEQgEBBiDJwZDBy'
        'sAgxsDAoAHEQCEGBQaIOAg4sDIgACMUj4JRMApGwQgF/ykEAFXxQRc='))
        _, ICON_PATH = tempfile.mkstemp()
        with open(ICON_PATH, 'wb') as icon_file:
            icon_file.write(ICON)
        self.root.iconbitmap(default=ICON_PATH)
        
        self.userName = StringVar(self.root, "")
        if os.path.exists('user.json'):
            with open('user.json') as dataFile:
                user = json.load(dataFile)
                self.userName.set(user['userName'])

        self.hertz = StringVar(self.root, self.defaultHertz)
          
        self.userNameLabel = Label(self.root, text="Username:")
        self.userNameInput = Entry(self.root, textvariable=self.userName, bd =5)
        
        self.healthCalibrationLabel = Label(self.root, text="Current HP:")
        self.healthCalibrationInput = Entry(self.root, bd =5)
        
        self.thirstCalibrationLabel = Label(self.root, text="Current Thirst:")
        self.thirstCalibrationInput = Entry(self.root, bd =5)
        
        self.hungerCalibrationLabel = Label(self.root, text="Current Hunger:")
        self.hungerCalibrationInput = Entry(self.root, bd =5)
        
        self.calibrateButton = Button(self.root, text="Calibrate", command=self.onCalibrateButtonPress)
        
        self.frequencyLabel = Label(self.root, text="Update Frequency (Hertz):")
        self.frequencyInput = Entry(self.root, textvariable=self.hertz, bd =5)
        
        self.userNameLabel.pack()
        self.userNameInput.pack()
        
        self.healthCalibrationLabel.pack()
        self.healthCalibrationInput.pack()
        
        self.thirstCalibrationLabel.pack()
        self.thirstCalibrationInput.pack()
        
        self.hungerCalibrationLabel.pack()
        self.hungerCalibrationInput.pack()
        
        self.calibrateButton.pack()

        

        self.barDetector = BarDetector()
        #self.actionBarDetector = ActionBarDetector()
        if self.barDetector.calibrated:
            self.confLoadedLabel = Label(self.root, text="Previous Calibration Loaded")
            self.confLoadedLabel.pack()
        
        self.frequencyLabel.pack()
        self.frequencyInput.pack()        
        if self.debug:
            self.hpPanel = Label(self.root, image = None)
            self.hpPanel.pack()
            self.hpText = Label(self.root, text="HP")
            self.hpText.pack()
            self.thirstPanel = Label(self.root, image = None)
            self.thirstPanel.pack() 
            self.thirstText = Label(self.root, text="Thirst")
            self.thirstText.pack()
            self.hungerPanel = Label(self.root, image = None)
            self.hungerPanel.pack()
            self.hungerText = Label(self.root, text="Hunger")
            self.hungerText.pack()
            #self.actionBarPanel = Label(self.root, image = None)
            #self.actionBarPanel.pack()
        self.root.after(self.delay(), self.loop)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.mainloop()
    
    def onCalibrateButtonPress(self):
        try:
            rustWindow = win32gui.FindWindow(None, 'Rust')
            if(rustWindow):
                self.barDetector.calibrate(rustWindow, self.healthCalibrationInput.get(), self.thirstCalibrationInput.get(), self.hungerCalibrationInput.get())
        except Exception as err:
            logger.error(err)
            
    def loop(self):
        try:
            self.hertz.set(self.frequencyInput.get())
            rustWindow = win32gui.GetForegroundWindow()
            if win32gui.GetWindowText(rustWindow) == 'Rust' and self.barDetector.calibrated and self.socketIO.connected:
                stats = self.barDetector.getStats(rustWindow)
                #self.actionBarDetector.getActionBarSlots(rustWindow)
                def showBar(value, barImage, imgPanel, textPanel, textPrefix):
                    uiImage = ImageTk.PhotoImage(barImage)
                    imgPanel.configure(image = uiImage)
                    imgPanel.image = uiImage
                    valueStr = textPrefix + str(value) + "%"
                    textPanel.configure(text = valueStr)
                if self.debug:
                    showBar(stats['health'], self.barDetector.hpBarImg, self.hpPanel, self.hpText, "HP: ")
                    showBar(stats['thirst'], self.barDetector.thirstBarImg, self.thirstPanel, self.thirstText, "Thirst: ")
                    showBar(stats['hunger'], self.barDetector.hungerBarImg, self.hungerPanel, self.hungerText, "Hunger: ")
                    #showBar('Actionbar', np.concatenate(self.actionBarDetector.actionBarSlotImages, axis=1), self.actionBarPanel, None, "Actionbar: ")
                self.generatePayload(stats)
        except Exception as err:
            logger.error(err)
        self.root.after(self.delay(), self.loop)
    
    def generatePayload(self, stats):
        stats['username'] = self.userNameInput.get()
        stats['bolt'] = False
        stats['AK'] = False
        stats['pistol'] = False
        stats['pipe'] = False
        self.socketIO.emit('playerupdate', stats)
        
    def quit(self):
        #write username to disk
        user = {}
        user['userName'] = self.userNameInput.get()
        with open('user.json', 'w') as dataFile:
            json.dump(user, dataFile)
        self.socketIO.disconnect()
        self.root.destroy()
        
    def delay(self):
        hertz = self.hertz.get()
        if len(hertz) == 0:
            hertz = self.defaultHertz
        return int(1000 / float(hertz))


if __name__ == '__main__':
    logging.info('Application start')
    app = App()
