# main.py

import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, Qt

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.open_frontend)
        self.timer.start(10000)  # 10 seconds

    def init_ui(self):
        self.setWindowTitle("Select Application")
        self.setFixedSize(1245, 440)  # Set fixed window size

        # Set the background image using QLabel
        self.set_background_image()

        # Create a transparent widget to hold the buttons and label
        content_widget = QWidget(self)
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignCenter)

        label = QLabel("Select an option:")
        label.setStyleSheet("font-size: 24px; color: white;")
        label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(label)

        frontend_button = QPushButton("Open Frontend")
        frontend_button.setStyleSheet(
            "font-size: 18px; padding: 10px; background-color: rgba(0, 0, 0, 0.5); color: white;"
        )
        frontend_button.clicked.connect(self.open_frontend)
        content_layout.addWidget(frontend_button)

        admin_button = QPushButton("Open Admin Portal")
        admin_button.setStyleSheet(
            "font-size: 18px; padding: 10px; background-color: rgba(0, 0, 0, 0.5); color: white;"
        )
        admin_button.clicked.connect(self.open_admin)
        content_layout.addWidget(admin_button)

        content_widget.setLayout(content_layout)

        # Position the content widget over the background label
        content_widget.setGeometry(0, 0, 645, 340)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.background_label)
        main_layout.addWidget(content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self.show()

    def set_background_image(self):
        # Get the absolute path of the image
        image_path = os.path.join(os.path.dirname(__file__), 'Images', 'Rada.jpg')
        # Check if the image exists
        if not os.path.exists(image_path):
            print(f"Background image not found at {image_path}")
            return

        # Create a QLabel to display the background image
        self.background_label = QLabel(self)
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print(f"Failed to load image at {image_path}")
            return

        # Get the size of the original image
        image_width = pixmap.width()
        image_height = pixmap.height()

        # Define the offsets to move the image
        x_offset = 200  # Adjust this value to move the image horizontally
        y_offset = 300  # Adjust this value to move the image vertically

        # Define the size of the display area (same as window size)
        display_width = 1245
        display_height = 940

        # Ensure the region is within the bounds of the original image
        if x_offset + display_width > image_width:
            x_offset = image_width - display_width
        if y_offset + display_height > image_height:
            y_offset = image_height - display_height
        if x_offset < 0:
            x_offset = 0
        if y_offset < 0:
            y_offset = 0

        # Crop the image to the specified region
        cropped_pixmap = pixmap.copy(x_offset, y_offset, display_width, display_height)

        self.background_label.setPixmap(cropped_pixmap)
        self.background_label.setGeometry(0, 0, display_width, display_height)
        self.background_label.setScaledContents(False)
        self.background_label.lower()

    def open_frontend(self):
        self.timer.stop()
        self.hide()
        subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), 'frontend.py')])
        QApplication.instance().quit()

    def open_admin(self):
        self.timer.stop()
        self.hide()
        subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), 'admin.py')])
        QApplication.instance().quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
