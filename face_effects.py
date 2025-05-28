import cv2
import mediapipe as mp
import numpy as np
from abc import ABC, abstractmethod
import math

class FaceEffect(ABC):
    def __init__(self):
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=10,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.effect_image = None
        self.load_effect_image()

    @abstractmethod
    def load_effect_image(self):
        """Load the effect image. Should be implemented by subclasses."""
        pass

    @abstractmethod
    def get_effect_position(self, face_landmarks, frame_shape):
        """Calculate the position for the effect. Should be implemented by subclasses."""
        pass

    def overlay_effect(self, frame, x, y, width, height, angle=0):
        """Overlay the effect image on the frame at the specified position."""
        if width <= 0 or height <= 0:
            return frame

        resized_effect = cv2.resize(self.effect_image, (width, height), interpolation=cv2.INTER_AREA)
        rot_mat = cv2.getRotationMatrix2D((width // 2, height // 2), angle, 1.0)
        rotated_effect = cv2.warpAffine(resized_effect, rot_mat, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
        alpha = rotated_effect[:, :, 3] / 255.0
        
        for c in range(3):
            frame[y:y + height, x:x + width, c] = \
                frame[y:y + height, x:x + width, c] * (1 - alpha) + \
                rotated_effect[:, :, c] * alpha
        return frame

    def apply_effect(self, frame):
        """Apply the effect to all detected faces in the frame."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                h, w, _ = frame.shape
                x, y, width, height, angle = self.get_effect_position(face_landmarks, (h, w))
                
                # Ensure coordinates are within frame bounds
                x = max(0, min(x, w - width))
                y = max(0, min(y, h - height))
                
                frame = self.overlay_effect(frame, x, y, width, height, angle)
        return frame

class MustacheEffect(FaceEffect):
    def load_effect_image(self):
        self.effect_image = cv2.imread('mustache.png', cv2.IMREAD_UNCHANGED)
        if self.effect_image is None:
            # Create a simple mustache if image not found
            self.effect_image = np.zeros((50, 100, 4), dtype=np.uint8)
            cv2.ellipse(self.effect_image, (50, 25), (40, 20), 0, 0, 180, (0, 0, 0, 255), -1)

    def get_effect_position(self, face_landmarks, frame_shape):
        h, w = frame_shape
        # Mouth corners
        left = face_landmarks.landmark[61]
        right = face_landmarks.landmark[291]
        upper_lip = face_landmarks.landmark[13]
        # Calculate width and angle
        x1, y1 = int(left.x * w), int(left.y * h)
        x2, y2 = int(right.x * w), int(right.y * h)
        width = int(1.3 * math.hypot(x2 - x1, y2 - y1))  # Slightly wider
        height = int(width * self.effect_image.shape[0] / self.effect_image.shape[1])
        angle = -math.degrees(math.atan2(y2 - y1, x2 - x1))
        # Center between mouth corners, slightly above upper lip
        cx = (x1 + x2) // 2
        cy = int(upper_lip.y * h) - height // 3  # Move mustache even higher
        x = cx - width // 2
        y = cy - height // 2
        return x, y, width, height, angle

class BoloTieEffect(FaceEffect):
    def load_effect_image(self):
        self.effect_image = cv2.imread('bolo_tie.png', cv2.IMREAD_UNCHANGED)
        if self.effect_image is None:
            # Create a simple bolo tie if image not found
            self.effect_image = np.zeros((100, 50, 4), dtype=np.uint8)
            cv2.rectangle(self.effect_image, (20, 0), (30, 100), (0, 0, 0, 255), -1)
            cv2.circle(self.effect_image, (25, 50), 15, (0, 0, 0, 255), -1)

    def get_effect_position(self, face_landmarks, frame_shape):
        h, w = frame_shape
        chin = face_landmarks.landmark[152]
        jaw_left = face_landmarks.landmark[234]
        jaw_right = face_landmarks.landmark[454]
        x1, y1 = int(jaw_left.x * w), int(jaw_left.y * h)
        x2, y2 = int(jaw_right.x * w), int(jaw_right.y * h)
        width = int(0.45 * math.hypot(x2 - x1, y2 - y1))  # Larger bolo tie
        height = int(width * self.effect_image.shape[0] / self.effect_image.shape[1])
        angle = -math.degrees(math.atan2(y2 - y1, x2 - x1))
        cx = int(chin.x * w)
        cy = int(chin.y * h) + height // 1  # Move bolo tie lower
        x = cx - width // 2
        y = cy - height // 2
        return x, y, width, height, angle

class CowboyHatEffect(FaceEffect):
    def load_effect_image(self):
        self.effect_image = cv2.imread('cowboy_hat.png', cv2.IMREAD_UNCHANGED)
        if self.effect_image is None:
            # Create a simple cowboy hat if image not found
            self.effect_image = np.zeros((100, 150, 4), dtype=np.uint8)
            cv2.ellipse(self.effect_image, (75, 50), (60, 30), 0, 0, 180, (0, 0, 0, 255), -1)
            cv2.rectangle(self.effect_image, (50, 50), (100, 100), (0, 0, 0, 255), -1)

    def get_effect_position(self, face_landmarks, frame_shape):
        h, w = frame_shape
        # Use left and right forehead for width/angle, top of forehead for y
        left = face_landmarks.landmark[234]
        right = face_landmarks.landmark[454]
        top = face_landmarks.landmark[10]
        x1, y1 = int(left.x * w), int(left.y * h)
        x2, y2 = int(right.x * w), int(right.y * h)
        width = int(1.6 * math.hypot(x2 - x1, y2 - y1))  # Increased width
        height = int(width * self.effect_image.shape[0] / self.effect_image.shape[1])
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))  # Flip sign to fix upside down hat
        cx = int(top.x * w)
        cy = int(top.y * h) - height // 1  # Move hat higher
        x = cx - width // 2
        y = cy - height // 2
        return x, y, width, height, angle

class BackgroundReplacementEffect(FaceEffect):
    def __init__(self):
        super().__init__()
        # Initialize MediaPipe Selfie Segmentation
        self.mp_selfie_segmentation = mp.solutions.selfie_segmentation
        self.selfie_segmentation = self.mp_selfie_segmentation.SelfieSegmentation(model_selection=1)
        self.background_image = None
        self.load_effect_image()

    def load_effect_image(self):
        """Load the background image."""
        self.background_image = cv2.imread('background.jpg')
        if self.background_image is None:
            raise FileNotFoundError("background.jpg not found. Please ensure the file exists.")

    def get_effect_position(self, face_landmarks, frame_shape):
        """Not used for background replacement."""
        return 0, 0, 0, 0, 0

    def apply_effect(self, frame):
        """Replace the background with the loaded background image."""
        # Convert frame to RGB for processing
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get segmentation results
        results = self.selfie_segmentation.process(rgb_frame)
        
        # Create a mask from the segmentation results
        mask = results.segmentation_mask > 0.1
        
        # Resize background to match frame size
        background = cv2.resize(self.background_image, (frame.shape[1], frame.shape[0]))
        
        # Create a 3-channel mask
        mask_3d = np.stack([mask] * 3, axis=-1)
        
        # Combine the frame and background using the mask
        output = np.where(mask_3d, frame, background)
        
        return output.astype(np.uint8) 