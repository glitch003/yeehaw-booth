import cv2
import mediapipe as mp
import numpy as np
from abc import ABC, abstractmethod
import math
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Effect configuration
EFFECT_CONFIG = {
    'mustache_enabled': True,
    'bolo_tie_enabled': True,
    'cowboy_hat_enabled': True,
    'background_enabled': True
}

class BodyEffect(ABC):
    def __init__(self):
        model_path = './pose_landmarker_lite.task'

        BaseOptions = mp.tasks.BaseOptions
        PoseLandmarker = mp.tasks.vision.PoseLandmarker
        PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode
        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.IMAGE,
            num_poses=10)

        self.landmarker = PoseLandmarker.create_from_options(options)
        self.effect_image = None
        self.load_effect_image()

    @abstractmethod
    def load_effect_image(self):
        """Load the effect image. Should be implemented by subclasses."""
        pass

    @abstractmethod
    def get_effect_position(self, pose_landmarks, frame_shape):
        """Calculate the position for the effect. Should be implemented by subclasses."""
        pass

    @abstractmethod
    def is_enabled(self):
        """Check if this effect is enabled in the configuration."""
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
        """Apply the effect to detected pose in the frame."""
        if not self.is_enabled():
            return frame
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert the frame received from OpenCV to a MediaPipe’s Image object.
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = self.landmarker.detect(mp_image)
        pose_landmarks_list = results.pose_landmarks

        # Loop through the detected poses to visualize.
        for idx in range(len(pose_landmarks_list)):
            pose_landmarks = pose_landmarks_list[idx]

            h, w, _ = frame.shape
            x, y, width, height, angle = self.get_effect_position(pose_landmarks, (h, w))
            
            # Ensure coordinates are within frame bounds
            x = max(0, min(x, w - width))
            y = max(0, min(y, h - height))
            
            frame = self.overlay_effect(frame, x, y, width, height, angle)
        return frame

class MustacheEffect(BodyEffect):
    def is_enabled(self):
        return EFFECT_CONFIG['mustache_enabled']

    def load_effect_image(self):
        self.effect_image = cv2.imread('mustache.png', cv2.IMREAD_UNCHANGED)
        if self.effect_image is None:
            # Create a simple mustache if image not found
            self.effect_image = np.zeros((50, 100, 4), dtype=np.uint8)
            cv2.ellipse(self.effect_image, (50, 25), (40, 20), 0, 0, 180, (0, 0, 0, 255), -1)

    def get_effect_position(self, pose_landmarks, frame_shape):
        h, w = frame_shape
        # Use nose position for mustache placement (landmark 0)
        nose = pose_landmarks[mp.solutions.pose.PoseLandmark.NOSE]
        
        # Use shoulder width to estimate face size for better scaling at distance
        left_shoulder = pose_landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = pose_landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
        
        # Calculate shoulder distance to estimate body size
        shoulder_distance = math.hypot(
            (right_shoulder.x - left_shoulder.x) * w,
            (right_shoulder.y - left_shoulder.y) * h
        )
        
        # Scale mustache size based on shoulder width (face is roughly 1/3 of shoulder width)
        width = int(shoulder_distance * 0.25)  # Adjusted for better mustache size
        height = int(width * self.effect_image.shape[0] / self.effect_image.shape[1])
        
        # Set angle to 0 to keep effects right-side up
        angle = 0
        
        # Position mustache slightly below nose
        cx = int(nose.x * w)
        cy = int(nose.y * h) + int(height * 0.5)  # Below nose
        
        x = cx - width // 2
        y = cy - height // 2
        
        return x, y, width, height, angle

class BoloTieEffect(BodyEffect):
    def is_enabled(self):
        return EFFECT_CONFIG['bolo_tie_enabled']

    def load_effect_image(self):
        self.effect_image = cv2.imread('bolo_tie.png', cv2.IMREAD_UNCHANGED)
        if self.effect_image is None:
            # Create a simple bolo tie if image not found
            self.effect_image = np.zeros((100, 50, 4), dtype=np.uint8)
            cv2.rectangle(self.effect_image, (20, 0), (30, 100), (0, 0, 0, 255), -1)
            cv2.circle(self.effect_image, (25, 50), 15, (0, 0, 0, 255), -1)

    def get_effect_position(self, pose_landmarks, frame_shape):
        h, w = frame_shape
        # Use neck area for bolo tie placement
        left_shoulder = pose_landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = pose_landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
        
        # Calculate shoulder distance for sizing
        shoulder_distance = math.hypot(
            (right_shoulder.x - left_shoulder.x) * w,
            (right_shoulder.y - left_shoulder.y) * h
        )
        
        # Scale bolo tie size based on shoulder width
        width = int(shoulder_distance * 0.6)  # Increased from 0.4 to make it bigger
        height = int(width * self.effect_image.shape[0] / self.effect_image.shape[1])
        
        # Set angle to 0 to keep effects right-side up
        angle = 0
        
        # Position bolo tie at neck area (between shoulders, slightly below)
        cx = int((left_shoulder.x + right_shoulder.x) / 2 * w)
        cy = int((left_shoulder.y + right_shoulder.y) / 2 * h) + int(shoulder_distance * 0.2)
        
        x = cx - width // 2
        y = cy - height // 2
        
        return x, y, width, height, angle

class CowboyHatEffect(BodyEffect):
    def is_enabled(self):
        return EFFECT_CONFIG['cowboy_hat_enabled']

    def load_effect_image(self):
        self.effect_image = cv2.imread('cowboy_hat.png', cv2.IMREAD_UNCHANGED)
        if self.effect_image is None:
            # Create a simple cowboy hat if image not found
            self.effect_image = np.zeros((100, 150, 4), dtype=np.uint8)
            cv2.ellipse(self.effect_image, (75, 50), (60, 30), 0, 0, 180, (0, 0, 0, 255), -1)
            cv2.rectangle(self.effect_image, (50, 50), (100, 100), (0, 0, 0, 255), -1)

    def get_effect_position(self, pose_landmarks, frame_shape):
        h, w = frame_shape
        # Use nose and ear positions for hat placement
        nose = pose_landmarks[mp.solutions.pose.PoseLandmark.NOSE]
        left_ear = pose_landmarks[mp.solutions.pose.PoseLandmark.LEFT_EAR]
        right_ear = pose_landmarks[mp.solutions.pose.PoseLandmark.RIGHT_EAR]
        
        # Use shoulder width for sizing reference
        left_shoulder = pose_landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = pose_landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
        
        shoulder_distance = math.hypot(
            (right_shoulder.x - left_shoulder.x) * w,
            (right_shoulder.y - left_shoulder.y) * h
        )
        
        # Calculate ear distance for hat width
        ear_distance = math.hypot(
            (right_ear.x - left_ear.x) * w,
            (right_ear.y - left_ear.y) * h
        )
        
        # Use the larger of ear distance or proportion of shoulder distance for hat width
        width = int(max(ear_distance * 2.0, shoulder_distance * 0.6))
        height = int(width * self.effect_image.shape[0] / self.effect_image.shape[1])
        
        # Set angle to 0 to keep effects right-side up
        angle = 0
        
        # Position hat above the head (using nose as reference, moving up)
        cx = int(nose.x * w)
        cy = int(nose.y * h) - int(height * 0.9)  # Increased from 0.6 to 0.9 to move hat higher
        
        x = cx - width // 2
        y = cy - height // 2
        
        return x, y, width, height, angle

class BackgroundReplacementEffect:
    def __init__(self):
        # Initialize MediaPipe Selfie Segmentation
        self.mp_selfie_segmentation = mp.solutions.selfie_segmentation
        self.selfie_segmentation = self.mp_selfie_segmentation.SelfieSegmentation(model_selection=1)
        self.background_image = None
        self.load_effect_image()

    def is_enabled(self):
        return EFFECT_CONFIG['background_enabled']

    def load_effect_image(self):
        """Load the background image."""
        self.background_image = cv2.imread('background.png')
        if self.background_image is None:
            raise FileNotFoundError("background.png not found. Please ensure the file exists.")

    def apply_effect(self, frame):
        """Replace the background with the loaded background image."""
        if not self.is_enabled():
            return frame
            
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