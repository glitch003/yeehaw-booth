import cv2
import os
import datetime
import numpy as np
from PyQt6.QtWidgets import QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QMessageBox, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from photo_capture_thread import PhotoCaptureThread
from photo_effects import MustacheEffect, BoloTieEffect, CowboyHatEffect, BackgroundReplacementEffect, EFFECT_CONFIG
from printer import DNPPrinter

VIDEO_SOURCE_INDEX = 1

class CowboyBooth(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yeehaw Booth")
        self.setGeometry(100, 100, 1280, 720)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create label to display the webcam feed
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        # Create button layout
        button_layout = QHBoxLayout()
        
        # Create button to take photos
        self.capture_button = QPushButton("Take Photos", self)
        self.capture_button.clicked.connect(self.start_photo_capture)
        button_layout.addWidget(self.capture_button)

        # Create buttons to toggle effects
        self.mustache_button = QPushButton("Mustache", self)
        self.mustache_button.clicked.connect(lambda: self.toggle_effect('mustache_enabled'))
        self.mustache_button.setCheckable(True)
        self.mustache_button.setChecked(EFFECT_CONFIG['mustache_enabled'])
        button_layout.addWidget(self.mustache_button)

        self.bolo_tie_button = QPushButton("Bolo Tie", self)
        self.bolo_tie_button.clicked.connect(lambda: self.toggle_effect('bolo_tie_enabled'))
        self.bolo_tie_button.setCheckable(True)
        self.bolo_tie_button.setChecked(EFFECT_CONFIG['bolo_tie_enabled'])
        button_layout.addWidget(self.bolo_tie_button)

        self.cowboy_hat_button = QPushButton("Cowboy Hat", self)
        self.cowboy_hat_button.clicked.connect(lambda: self.toggle_effect('cowboy_hat_enabled'))
        self.cowboy_hat_button.setCheckable(True)
        self.cowboy_hat_button.setChecked(EFFECT_CONFIG['cowboy_hat_enabled'])
        button_layout.addWidget(self.cowboy_hat_button)

        self.background_button = QPushButton("Background", self)
        self.background_button.clicked.connect(lambda: self.toggle_effect('background_enabled'))
        self.background_button.setCheckable(True)
        self.background_button.setChecked(EFFECT_CONFIG['background_enabled'])
        button_layout.addWidget(self.background_button)

        layout.addLayout(button_layout)

        # Initialize effects
        self.mustache_effect = MustacheEffect()
        self.bolo_tie_effect = BoloTieEffect()
        self.cowboy_hat_effect = CowboyHatEffect()
        self.background_effect = BackgroundReplacementEffect()

        # Initialize printer
        self.printer = DNPPrinter()

        # Initialize webcam
        self.cap = cv2.VideoCapture(VIDEO_SOURCE_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # Set up timer for webcam updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 30ms = ~33fps

        # Photo capture variables
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown = 0
        self.captured_frames = []
        self.photo_capture_thread = None
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.end_flash)
        self.flash_active = False
        self.photo_count = 0

        # Create photos directory if it doesn't exist
        self.photos_dir = "photos"
        if not os.path.exists(self.photos_dir):
            os.makedirs(self.photos_dir)

    def toggle_effect(self, effect_name):
        """Toggle an effect on/off and update the button state."""
        EFFECT_CONFIG[effect_name] = not EFFECT_CONFIG[effect_name]
        # Convert effect_name to button name (e.g., 'cowboy_hat_enabled' -> 'cowboy_hat_button')
        button_name = effect_name.replace('_enabled', '_button')
        button = getattr(self, button_name)
        button.setChecked(EFFECT_CONFIG[effect_name])

    def start_photo_capture(self):
        self.capture_button.setEnabled(False)
        self.countdown = 3
        self.captured_frames = []
        self.photo_count = 0
        # Store the timestamp for this set
        self.photo_set_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.countdown_timer.start(1000)  # 1 second intervals

    def update_countdown(self):
        if self.countdown > 0:
            self.capture_button.setText(f"Taking photo {self.photo_count + 1}/4 in {self.countdown}...")
            self.countdown -= 1
        else:
            self.countdown_timer.stop()
            self.capture_button.setText("Taking Photos...")
            # Start flash and capture photo at the same time
            self.start_flash()
            self.capture_photo()

    def capture_photo(self):
        ret, frame = self.cap.read()
        if ret:
            # Apply all effects to the saved photo
            frame_with_effects = frame.copy()
            frame_with_effects = self.background_effect.apply_effect(frame_with_effects)
            frame_with_effects = self.mustache_effect.apply_effect(frame_with_effects)
            frame_with_effects = self.bolo_tie_effect.apply_effect(frame_with_effects)
            frame_with_effects = self.cowboy_hat_effect.apply_effect(frame_with_effects)
            self.captured_frames.append(frame_with_effects)
            self.photo_count += 1
            # Start flash, but do NOT start the next countdown here
            self.start_flash()
            # The next countdown will be started in end_flash()

    def start_flash(self):
        self.flash_active = True
        self.flash_timer.start(500)  # Flash for 500ms

    def end_flash(self):
        self.flash_active = False
        self.flash_timer.stop()
        # Now start the next countdown or save photos
        if len(self.captured_frames) < 4:
            self.countdown = 3
            self.countdown_timer.start(1000)
        else:
            self.save_photos()

    def save_photos(self):
        self.photo_capture_thread = PhotoCaptureThread(self.captured_frames)
        self.photo_capture_thread.finished.connect(self.on_photos_saved)
        self.photo_capture_thread.start()

    def on_photos_saved(self, frames):
        # Create vertical strip of 4 photos
        # Assuming all frames are the same size
        h, w = frames[0].shape[:2]
        
        # Create a panel that's 4 photos tall and 2 photos wide (for two identical strips)
        panel = np.zeros((h * 4, w * 2, 3), dtype=np.uint8)
        
        # Create the first strip (left side)
        panel[0:h, 0:w] = frames[0]  # Top
        panel[h:h*2, 0:w] = frames[1]  # Second
        panel[h*2:h*3, 0:w] = frames[2]  # Third
        panel[h*3:h*4, 0:w] = frames[3]  # Bottom
        
        # Duplicate the strip for the right side
        panel[0:h, w:w*2] = frames[0]  # Top
        panel[h:h*2, w:w*2] = frames[1]  # Second
        panel[h*2:h*3, w:w*2] = frames[2]  # Third
        panel[h*3:h*4, w:w*2] = frames[3]  # Bottom
        
        # Save the panel
        panel_filename = f"strip_{self.photo_set_timestamp}.jpg"
        panel_path = os.path.join(self.photos_dir, panel_filename)
        cv2.imwrite(panel_path, panel)
        
        # Print the strip
        if self.printer.print_strip(panel_path):
            QMessageBox.information(self, "Success", "Photo strips printed successfully!")
        else:
            QMessageBox.warning(self, "Print Error", "Failed to print photo strips. Please check printer connection.")
        
        self.capture_button.setText("Take Photos")
        self.capture_button.setEnabled(True)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Apply all effects to the preview
        frame = self.background_effect.apply_effect(frame)
        frame = self.mustache_effect.apply_effect(frame)
        frame = self.bolo_tie_effect.apply_effect(frame)
        frame = self.cowboy_hat_effect.apply_effect(frame)

        # Display countdown and photo count on the frame
        if self.countdown > 0:
            # Photo count in top-right corner
            cv2.putText(
                frame,
                f"{self.photo_count + 1}/4",
                (frame.shape[1] - 180, 80),  # Top-right, with some padding
                cv2.FONT_HERSHEY_SIMPLEX,
                2,  # Smaller font
                (255, 255, 255),
                3,
                cv2.LINE_AA
            )
            # Countdown in the center
            cv2.putText(
                frame,
                str(self.countdown),
                (frame.shape[1] // 2 - 40, frame.shape[0] // 2 + 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                5,  # Large font
                (255, 255, 255),
                8,
                cv2.LINE_AA
            )

        # Apply flash effect
        if self.flash_active:
            frame = cv2.addWeighted(frame, 2.0, frame, 0, 0)  # Increased brightness multiplier

        # Convert frame to QImage and display
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
            self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio))

    def closeEvent(self, event):
        self.cap.release()
        event.accept() 