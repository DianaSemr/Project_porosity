from uibd_ui import Ui_Dialog
from PyQt5.QtWidgets import QMainWindow


class Dialog(QMainWindow, Ui_Dialog):
    def __init__(self, parent = None):
        super(Dialog, self).__init__(parent)
        self.setupUi(self)
        self.mainWindow = parent
        self.btnAddRow.clicked.connect(self.update_cb)
        self.btnDeleteRow.clicked.connect(self.update_cb)
        self.btnOK.clicked.connect(self.update_and_close)

    def update_cb(self):
        self.mainWindow.load_materials()

    def update_and_close(self):
        self.mainWindow.load_materials()
        self.close()
