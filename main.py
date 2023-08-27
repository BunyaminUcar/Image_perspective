import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QFileDialog, QWidget
from PyQt6.QtGui import QPixmap, QPainter, QImage
from PyQt6.QtCore import Qt
import cv2
import numpy as np


class ImageDisplayApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle('Image Display')
        self.setGeometry(150, 150, 1200, 600)

        # Create a layout
        layout = QVBoxLayout()

        # Create a QLabel to show the image
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(1000, 500)
        layout.addWidget(self.image_label,
                         alignment=Qt.AlignmentFlag.AlignCenter)

        # Create a button to load the Image-Base
        self.load_image_btn = QPushButton('Load Image-Base', self)
        self.load_image_btn.clicked.connect(self.load_base_image)
        layout.addWidget(self.load_image_btn,
                         alignment=Qt.AlignmentFlag.AlignCenter)

        # Create a button to load the Image-Overlay
        self.load_overlay_btn = QPushButton('Load Image-Overlay', self)
        self.load_overlay_btn.clicked.connect(self.load_overlay_image)
        layout.addWidget(self.load_overlay_btn,
                         alignment=Qt.AlignmentFlag.AlignCenter)

        # Create an 'apply' button
        self.apply_btn = QPushButton(
            'Apply Perspective', self)  # Düğme adı değiştirildi
        # Bağlantı işlevi değiştirildi
        self.apply_btn.clicked.connect(self.apply_perspective)
        layout.addWidget(
            self.apply_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Placeholder to store the images
        self.base_image = None
        self.overlay_image = None

        # Variables for dragging
        self.dragging = False
        self.offset = None
        self.overlay_label = QLabel(self.image_label)
        self.overlay_label.hide()

    def load_base_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Image-Base", "", "Images (*.png *.jpg *.jpeg);;All Files (*)")
        if file_name:
            self.base_image = QPixmap(file_name)
            self.display_image()

    def load_overlay_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Image-Overlay", "", "Images (*.png *.jpg *.jpeg);;All Files (*)")
        if file_name:
            # OpenCV ile görüntüyü yükle
            overlay_cv_image = cv2.imread(file_name)

            # OpenCV görüntüsünü QPixmap'e dönüştür
            height, width, _ = overlay_cv_image.shape
            bytes_per_line = 3 * width
            q_image = QImage(overlay_cv_image.data, width,
                             height, bytes_per_line, QImage.Format.Format_BGR888)
            pixmap = QPixmap.fromImage(q_image)

            self.overlay_image = overlay_cv_image  # OpenCV formatını saklamaya devam et
            self.overlay_label.setPixmap(pixmap)
            # Üste binen imgenin boyutu
            self.overlay_label.setFixedSize(pixmap.size())
            self.overlay_label.move(0, 0)

    def apply_perspective(self):
        if self.overlay_image is None:
            print("Please select a valid Image-Overlay first.")
            return

        A = (170, 90)
        B = (20, 20)
        C = (180, 135)
        D = (0, 150)

        height, width,  _ = self.overlay_image.shape  # Görüntü boyutlarını alma

        src_pts = np.array([
            [0, 0],
            [width - 1, 0],
            [0, height - 1],
            [width - 1, height - 1]
        ], dtype="float32")

        dst_pts = np.array([A, B, C, D], dtype="float32")

    # Perspektif dönüşüm matrisini hesaplama
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        print(M)
        warped = cv2.warpPerspective(
            self.overlay_image, M, (width, height), flags=cv2.INTER_LINEAR)  # Dönüşümü uygulama

    # Siyah bölgeleri tespit etme
        gray_warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        _, thresholded = cv2.threshold(gray_warped, 1, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(
            thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # En büyük konturu seçme
        max_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(max_contour)

    # Siyah bölgeleri kırpma
        cropped_warped = warped[y:y+h, x:x+w]

    # QImage kullanarak görüntüyü QPixmap'e çevirme
        bytes_per_line = 3 * w
        q_image = QImage(
            cropped_warped.data.tobytes(),  # Convert the array to bytes
            w, h,
            bytes_per_line, QImage.Format.Format_BGR888
        )
        pixmap = QPixmap.fromImage(q_image)
        self.overlay_label.setFixedSize(pixmap.size())
        self.overlay_label.setPixmap(pixmap)  # Dönüşüm sonucunu görüntüle

        self.overlay_label.move(0, 0)

    def display_image(self):
        if self.base_image and not self.base_image.isNull():
            # Create a pixmap to hold the base image
            pixmap = QPixmap(self.image_label.width(),
                             self.image_label.height())
            # Fill pixmap with transparency
            pixmap.fill(Qt.GlobalColor.transparent)

            base_painter = QPainter(pixmap)
            scaled_base = self.base_image.scaled(self.image_label.width(
            ), self.image_label.height(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)
            base_painter.drawPixmap(0, 0, scaled_base)
            base_painter.end()

            # Display the combined image on the picture box
            self.image_label.setPixmap(pixmap)
            self.overlay_label.setFixedSize(scaled_base.size())
            self.overlay_label.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageDisplayApp()
    window.show()
    sys.exit(app.exec())
