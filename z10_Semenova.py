import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QFileDialog
from PyQt5 import QtGui, QtCore, QtWidgets
import sqlite3, sys
from uisppr_ui import Ui_MainWindow
from dialog import *
from PIL import Image, ImageEnhance, ImageQt
import numpy as np


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.contrast_slider.setRange(0, 200)
        self.contrast_slider.setObjectName("contrast_slider")
        self.contrast_slider.setValue(10)

        self.brightness_slider.setRange(0, 50)
        self.brightness_slider.setObjectName("brightness_slider")
        self.brightness_slider.setValue(10)

        self.sharpness_slider.setRange(0, 200)
        self.sharpness_slider.setObjectName("sharpness_slider")
        self.sharpness_slider.setValue(10)

        self.load_materials()
        self.set_material_values()
        self.cmbxMaterialName.currentIndexChanged.connect(self.set_material_values)
        self.btnChange.clicked.connect(self.open_dialog)
        self.actionOpen.triggered.connect(self.open_image)

        self.contrast_slider.valueChanged.connect(self.set_transformed_image)
        self.brightness_slider.valueChanged.connect(self.set_transformed_image)
        self.sharpness_slider.valueChanged.connect(self.set_transformed_image)

    # обработка изменений значения контрастности, яркости и резкости
    def set_transformed_image(self):
        try:
            image = Image.open(self.tranform_img).convert('L')
            mode = image.mode
            image = ImageEnhance.Contrast(image).enhance(self.contrast_slider.value() / 10)
            image = ImageEnhance.Brightness(image).enhance(self.brightness_slider.value() / 10)
            image = ImageEnhance.Sharpness(image).enhance(self.sharpness_slider.value() / 10)
            image = np.array(image)
            if mode == "RGB":
                image = QtGui.QImage(image.data, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888)
            else:
                image = QtGui.QImage(image.data, image.shape[1], image.shape[0], QtGui.QImage.Format_Indexed8)
            pixmap = QtGui.QPixmap.fromImage(image)
            self.transformed_frame.setPixmap(pixmap)
            self.transformed_frame.setScaledContents(True)
            self.explore()
        except Exception as e:
            print(e)


    def open_image(self):
        img = QFileDialog.getOpenFileName(self, "Open image",
                                          "C:\\Users\\Диана\\Desktop\\Введение в анализ изображений",
                                          "Image files (*.jpg *.jpeg *.png *.webp)")
        imgPath = img[0]
        self.tranform_img = imgPath
        pixmap = QtGui.QPixmap(imgPath)
        self.current_frame.setPixmap(QtGui.QPixmap(pixmap))
        self.current_frame.setScaledContents(True)

        self.current_frame.setPixmap(pixmap)
        self.current_frame.setScaledContents(True)

        image = Image.open(self.tranform_img)
        # image = Image.fromarray(image)
        mode = image.mode
        image = np.array(image)
        if mode == "RGB":
            image = QtGui.QImage(image.data, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888)
        else:
            image = QtGui.QImage(image.data, image.shape[1], image.shape[0], QtGui.QImage.Format_Indexed8)
        # image = ImageQt(image)
        pixmap = QtGui.QPixmap.fromImage(image)
        self.current_frame.setPixmap(pixmap)
        self.current_frame.setScaledContents(True)

        self.set_transformed_image()

        self.explore()


    def open_dialog(self):
        db = Dialog(self)
        db.show()

    def load_materials(self):
        conn = sqlite3.connect("my_database.db")
        cur = conn.cursor()
        materials = cur.execute("SELECT * FROM Materials;").fetchall()
        conn.close()
        self.cmbxMaterialName.clear()
        for row in materials:
            self.cmbxMaterialName.addItem(row[1])

    def set_material_values(self):
        conn = sqlite3.connect("my_database.db")
        cur = conn.cursor()
        materials = cur.execute("SELECT * FROM Materials;").fetchall()
        conn.close()
        currentMaterial = self.cmbxMaterialName.currentText()
        for material in materials:
            if material[1] == currentMaterial:
                self.label_pore_area.setText(str(material[2]))
                self.label_pore_area_std.setText(str(material[3]))
                self.label_porous.setText(str(material[5]))
                self.label_porous_std.setText(str(material[4]))

    def explore(self):
        try:
            incomingImage = self.transformed_frame.pixmap().toImage()
            width = incomingImage.width()
            height = incomingImage.height()
            ptr = incomingImage.bits()
            ptr.setsize(incomingImage.byteCount())
            arr = np.array(ptr).reshape(height, width, 4)

            image = Image.fromarray(arr.astype(np.uint8))
            image = arr
            # дополнительная обработка шумов
            blured = cv2.GaussianBlur(np.float32(image), (5, 5), 0)
            # конвертация BGR формата в формат HSV
            hsv = cv2.cvtColor(np.float32(blured), cv2.COLOR_BGR2HSV)
            lower_black = np.array([0, 0, 0])
            upper_black = np.array([120, 120, 120])
            # определяем маску для обнаружения контуров пор.
            # будут выделены поры в заданном диапозоне
            mask = cv2.inRange(hsv, lower_black, upper_black)
            # получаем массив конутров
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            good_contours = []
            bad_contours = []
            area_c = 0
            # находим поры, не превышающие нормативную площадь
            for contour in contours:
                # также подсчитываем общую площадь пор
                area_c += cv2.contourArea(contour)
                if float(self.label_pore_area.text()) - float(self.label_pore_area_std.text()) <= cv2.contourArea(contour) \
                        <= float(self.label_pore_area.text()) + float(self.label_pore_area_std.text()):
                    good_contours.append(contour)
                else:
                    bad_contours.append(contour)
            area_c = area_c / (image.shape[0] * image.shape[1])
            # выделяем 'хорошие' поры зеленым цветом
            image = cv2.drawContours(image, good_contours, -1, (0, 255, 0), 2, cv2.LINE_AA)  #########
            # выделяем 'плохие' поры красным цветом
            image = cv2.drawContours(image, bad_contours, -1, (255, 0, 0), 2, cv2.LINE_AA)  #######

            image = Image.fromarray(image.astype(np.uint8))
            image.save("C:\\Users\\Диана\\Desktop\\Введение в анализ изображений\\new_image.png")

            img = Image.open("C:\\Users\\Диана\\Desktop\\Введение в анализ изображений\\new_image.png")
            img = img.convert("RGB")
            img = img.resize((width, height))
            img = np.array(img)
            image = QtGui.QImage(img.data, img.shape[1], img.shape[0], QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(image)
            self.porous_frame.setPixmap(pixmap)
            self.porous_frame.setScaledContents(True)

            self.label_24.setText(str(round(area_c, 5)))
            self.label_24.setStyleSheet("color: black; ")
            self.label_25.setStyleSheet("color: black; ")
            self.label_20.setStyleSheet("color: black; ")
            if float(self.label_porous_std.text()) - float(self.label_porous.text()) <= round(area_c, 4) \
                    <= float(self.label_porous.text()) + float(self.label_porous_std.text()):
                self.label_25.setText('в норме')
                self.label_25.setStyleSheet("color: green; ")
            elif float(self.label_porous_std.text()) - float(self.label_porous.text()) > round(area_c, 4):
                self.label_25.setText('ниже нормы')
                self.label_25.setStyleSheet("color: red; ")
            elif float(self.label_porous.text()) + float(self.label_porous_std.text()) < round(area_c, 4):
                self.label_25.setText('выше нормы')
                self.label_25.setStyleSheet("color: red; ")
            self.label_20.setText(str(len(bad_contours)))
            #self.ui.Save.setEnabled(True)


        except Exception as e:
            print(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()
