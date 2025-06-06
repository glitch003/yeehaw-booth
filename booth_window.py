import cv2
import os
import datetime
import numpy as np
from PyQt6.QtWidgets import QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QMessageBox, QHBoxLayout, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QObject, QEvent
from PyQt6.QtGui import QImage, QPixmap, QFont, QKeyEvent, QMouseEvent
from photo_capture_thread import PhotoCaptureThread
from photo_effects import MustacheEffect, BoloTieEffect, CowboyHatEffect, BackgroundReplacementEffect, EFFECT_CONFIG
from printer import DNPPrinter

VIDEO_SOURCE_INDEX = 1

class CowboyBooth(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yeehaw Booth")
        self.showFullScreen()
        
        # Add dev mode state
        self.dev_mode = False

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to allow full-screen video

        # Create label to display the webcam feed
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMouseTracking(True)  # Enable mouse tracking for hover effects
        self.image_label.installEventFilter(self)  # Install event filter
        layout.addWidget(self.image_label)

        # Create loading indicator (initially hidden)
        self.loading_widget = QWidget(self)
        self.loading_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
            }
        """)
        loading_layout = QVBoxLayout(self.loading_widget)
        
        self.loading_label = QLabel("Printing photos...\nCollect photos below", self)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                background-color: transparent;
                padding: 20px;
            }
        """)
        loading_layout.addWidget(self.loading_label)
        
        self.loading_progress = QProgressBar(self)
        self.loading_progress.setRange(0, 0)  # Indeterminate progress
        self.loading_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid white;
                border-radius: 5px;
                background-color: transparent;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        loading_layout.addWidget(self.loading_progress)
        
        self.loading_widget.hide()
        self.loading_widget.setParent(self)

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

        # Hide all control buttons by default
        self.capture_button.hide()
        self.mustache_button.hide()
        self.bolo_tie_button.hide()
        self.cowboy_hat_button.hide()
        self.background_button.hide()

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

        # Loading timer for printing indicator
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.hide_loading_indicator)

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

    def show_loading_indicator(self):
        """Show the loading indicator overlay."""
        # Position the loading widget in the center of the main window
        self.loading_widget.resize(300, 150)
        self.loading_widget.move(
            (self.width() - self.loading_widget.width()) // 2,
            (self.height() - self.loading_widget.height()) // 2
        )
        self.loading_widget.show()
        self.loading_widget.raise_()  # Bring to front

    def hide_loading_indicator(self):
        """Hide the loading indicator overlay."""
        self.loading_widget.hide()
        self.loading_timer.stop()

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
        
        # Show loading indicator and start printing
        self.show_loading_indicator()
        
        # Print the strip
        if self.printer.print_strip(panel_path):
            # Start timer to hide loading indicator after 10 seconds
            self.loading_timer.start(10000)  # 10 seconds
        else:
            # Hide loading indicator immediately and show error
            self.hide_loading_indicator()
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
        elif not self.flash_active and self.photo_count == 0:
            # Display tap instruction when idle
            text = "Tap anywhere to start taking photos"
            font_scale = 1.5
            thickness = 3
            font = cv2.FONT_HERSHEY_SIMPLEX
            
            # Get text size to center it
            (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
            text_x = (frame.shape[1] - text_width) // 2
            text_y = (frame.shape[0] + text_height) // 2
            
            # Add a semi-transparent background for better readability
            overlay = frame.copy()
            cv2.rectangle(overlay, 
                         (text_x - 20, text_y - text_height - 20),
                         (text_x + text_width + 20, text_y + 20),
                         (0, 0, 0),
                         -1)
            cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
            
            # Draw the text
            cv2.putText(
                frame,
                text,
                (text_x, text_y),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
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

    def resizeEvent(self, event):
        """Handle window resize to reposition loading indicator."""
        super().resizeEvent(event)
        if hasattr(self, 'loading_widget') and self.loading_widget.isVisible():
            # Reposition loading widget when window is resized
            self.loading_widget.move(
                (self.width() - self.loading_widget.width()) // 2,
                (self.height() - self.loading_widget.height()) // 2
            )

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Event filter to handle mouse clicks on the image label."""
        if obj == self.image_label and event.type() == QEvent.Type.MouseButtonPress:
            # Only start photo capture if we're not in dev mode and not already capturing
            print("Mouse click detected")
            if not self.dev_mode:
                print("Starting photo capture")
                self.start_photo_capture()
                return True  # Event handled
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard events."""
        # Check for Ctrl+D
        if event.key() == Qt.Key.Key_D and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.toggle_dev_mode()
        super().keyPressEvent(event)

    def toggle_dev_mode(self):
        """Toggle dev mode and show/hide effect control buttons."""
        self.dev_mode = not self.dev_mode
        # Show/hide all control buttons
        self.capture_button.setVisible(self.dev_mode)
        self.mustache_button.setVisible(self.dev_mode)
        self.bolo_tie_button.setVisible(self.dev_mode)
        self.cowboy_hat_button.setVisible(self.dev_mode)
        self.background_button.setVisible(self.dev_mode) 