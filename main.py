import sys
import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

# GO ON, BE AS EVIL AS YOU WANT MY FRIEND >:D 
import pyautogui
pyautogui.PAUSE = 0

from PySide6 import QtCore, QtWidgets, QtGui
from pynput import mouse as pymouse
from pynput import keyboard as pykeyboard

widget: TheAmazingDigitalWidget = None

class KeybindButton(QtWidgets.QPushButton):
    def __init__(self, default_key="F8", parent=None):
        super().__init__(default_key, parent)

        self.listening = False
        self.listener = None
        self.clicked.connect(self.startListening)

        self.keySequence: QtGui.QKeySequence = QtGui.QKeySequence(default_key)
        self.updateListener()

        self.heldKeys = []

    def removeListener(self):
        # TODO: ALMOST works, but keyboard requires sudo and i can't figure out how
        # to get the timer to defer onto the main thread

        # seq = self.keySequence.toString().lower()
        # if seq in keyboard._hotkeys:
        #     keyboard.remove_hotkey(seq, self.shortcutActivated)
        if self.listener:
            self.listener.stop()
            self.listener = None

    def updateListener(self):
        # keyboard.add_hotkey(self.keySequence.toString().lower(), self.shortcutActivated)
        if self.listener:
            self.removeListener()
        
        self.listener = pykeyboard.Listener(on_press=self.onKeyPress, on_release=self.onKeyRelease)
        self.listener.start()

    def startListening(self):
        self.removeListener()
        self.listening = True
        
        self.setText("Press a key combination...")
        self.grabKeyboard()

    def onKeyPress(self, key):
        # self.shortcutActivated()

        keys: list[str] = self.keySequence.toString().lower().split("+")
        key = str(key)

        if key.startswith("Key."):
            key = key[4:]
        elif key.startswith("'"):
            key = key[1:-1]
        else:
            print("uhh idk how to format this key: " + key)

        held: int = 0
        if not key in self.heldKeys:
            self.heldKeys.append(key)

        for k in keys:
            if k in self.heldKeys:
                held += 1

        if held == len(keys):
            QtCore.QMetaObject.invokeMethod(self, "shortcutActivated", QtCore.Qt.QueuedConnection)

    def onKeyRelease(self, key):
        key = str(key)

        if key.startswith("Key."):
            key = key[4:]
        elif key.startswith("'"):
            key = key[1:-1]
        else:
            print("uhh idk how to format this key: " + key)
        
        if key in self.heldKeys:
            self.heldKeys.remove(key)

    @QtCore.Slot()
    def shortcutActivated(self):
        parent: TheAmazingDigitalWidget = self.parentWidget()
        parent.running = not parent.running

        parent.totalClicksSinceStart = 0 
        if not parent.clickNumberOfTimesRadioButton.isChecked(): parent.totalButtonsClicksSinceStart = 0
        parent.toggleButton.setText("Stop" if parent.running else "Start")

        if parent.running:
            parent.clickTimer.start()
        else:
            parent.clickTimer.stop()
            
            if not parent.clickNumberOfTimesRadioButton.isChecked():
                parent.testButton.setText("Click me to test!")

        print("Clicking started" if parent.running else "Clicking stopped")

    def keyPressEvent(self, event):
        if not self.listening:
            return super().keyPressEvent(event)
        
        key: QtCore.Qt.Key = event.key()
        if key in (QtCore.Qt.Key_Control, QtCore.Qt.Key_Shift, QtCore.Qt.Key_Alt, QtCore.Qt.Key_Meta):
            return

        modifiers: QtCore.Qt.KeyboardModifier = event.modifiers()

        self.keySequence = QtGui.QKeySequence(key | modifiers.value)
        self.updateListener()
        
        self.listening = False
        self.setText(self.keySequence.toString())
        self.releaseKeyboard()

class TheAmazingDigitalWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.resize(400, 505)
        self.show()

        self.setWindowTitle("The Amazing Digital Autoclicker")

        self.running = False
        self.totalClicksSinceStart = 0
        self.totalButtonsClicksSinceStart = 0

        self.controller = pymouse.Controller()
        self.layout = QtWidgets.QFormLayout(self)

        label = QtWidgets.QLabel("Click Type")
        self.layout.addWidget(label)
        
        font = label.font()
        font.setPixelSize(24)
        label.setFont(font)

        self.layout.addWidget(QtWidgets.QLabel("Mouse Button"))
        self.mouseButtonType = QtWidgets.QComboBox()
        self.mouseButtonType.addItems(["Left Click", "Right Click", "Middle Click"])
        self.layout.addWidget(self.mouseButtonType)

        self.layout.addWidget(QtWidgets.QLabel("Type"))
        self.clickType = QtWidgets.QComboBox()
        self.clickType.addItems(["Single", "Double"])
        self.layout.addWidget(self.clickType)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        self.layout.addWidget(sep)

        #

        label = QtWidgets.QLabel("Repetition")
        self.layout.addWidget(label)
        
        font = label.font()
        font.setPixelSize(24)
        label.setFont(font)

        repetitionGroup = QtWidgets.QButtonGroup(self)

        clickUntilStopped = QtWidgets.QRadioButton("Click until stopped")
        clickUntilStopped.setChecked(True)
        repetitionGroup.addButton(clickUntilStopped)
        self.layout.addWidget(clickUntilStopped)

        repetitionRow = QtWidgets.QWidget()
        rowLayout = QtWidgets.QHBoxLayout(repetitionRow)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(repetitionRow)

        self.clickNumberOfTimesRadioButton = QtWidgets.QRadioButton("Click number of times:")
        self.clickNumberOfTimesRadioButton.toggled.connect(self.numberOfClicksToggled)
        repetitionGroup.addButton(self.clickNumberOfTimesRadioButton)
        rowLayout.addWidget(self.clickNumberOfTimesRadioButton)

        self.clickNumberOfTimesBox = QtWidgets.QLineEdit("1")
        self.clickNumberOfTimesBox.setValidator(QtGui.QIntValidator(top=1))
        self.clickNumberOfTimesBox.setEnabled(False)
        rowLayout.addWidget(self.clickNumberOfTimesBox)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        self.layout.addWidget(sep)

        #

        label = QtWidgets.QLabel("Misc")
        self.layout.addWidget(label)
        
        font = label.font()
        font.setPixelSize(24)
        label.setFont(font)

        self.layout.addWidget(QtWidgets.QLabel("Hotkey"))
        self.hotkeyButton = KeybindButton()
        self.layout.addWidget(self.hotkeyButton)
        
        self.layout.addWidget(QtWidgets.QLabel("Interval (in milliseconds)"))
        intervalBox = QtWidgets.QLineEdit("25")
        intervalBox.setValidator(QtGui.QIntValidator(top=0))
        intervalBox.textChanged.connect(self.intervalChanged)
        self.layout.addWidget(intervalBox)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        self.layout.addWidget(sep)

        #

        self.toggleButton = QtWidgets.QPushButton("Start")
        self.toggleButton.clicked.connect(lambda: self.hotkeyButton.shortcutActivated())
        self.layout.addWidget(self.toggleButton)

        def testButtonClicked():
            self.totalButtonsClicksSinceStart += 1
            self.testButton.setText(f"This button has been clicked {self.totalButtonsClicksSinceStart} times")

        self.testButton = QtWidgets.QPushButton("Click me to test!")
        self.testButton.clicked.connect(testButtonClicked)
        self.layout.addWidget(self.testButton)

        # okay the ui is initialized we can get to the actual Clicker part yay   

        self.clickTimer = QtCore.QTimer()
        self.clickTimer.setInterval(25)       
        self.clickTimer.timeout.connect(self.tryClick)

    def numberOfClicksToggled(self):
        self.clickNumberOfTimesBox.setEnabled(self.clickNumberOfTimesRadioButton.isChecked())

    def intervalChanged(self):
        text = self.sender().text()
        if text == "": text = "0"
        
        interval = int(text)
        self.clickTimer.setInterval(interval)
        
        intervalStr = str(interval)
        print('interval set to ' + intervalStr)

    def tryClick(self):
        if self.clickType.currentText() == "Double":
            match self.mouseButtonType.currentText():
                case "Left Click": self.controller.click(button=pymouse.Button.left, count=2)
                case "Right Click": self.controller.click(button=pymouse.Button.right, count=2)
                case "Middle Click": self.controller.click(button=pymouse.Button.middle, count=2)
        else:
            match self.mouseButtonType.currentText():
                case "Left Click": self.controller.click(button=pymouse.Button.left)
                case "Right Click": self.controller.click(button=pymouse.Button.right)
                case "Middle Click": self.controller.click(button=pymouse.Button.middle)

        self.totalClicksSinceStart += 1
        if self.clickNumberOfTimesRadioButton.isChecked() and self.totalClicksSinceStart >= int(self.clickNumberOfTimesBox.text()):
            self.hotkeyButton.shortcutActivated()

def main():
    app = QtWidgets.QApplication([])

    global widget
    widget = TheAmazingDigitalWidget()

    status: int = app.exec()
    sys.exit(status)

if __name__ == "__main__":
    main()