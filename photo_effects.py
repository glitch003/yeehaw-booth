import cv2
import mediapipe as mp
import numpy as np
from abc import ABC, abstractmethod
import math
import random
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Effect configuration
EFFECT_CONFIG = {
    'mustache_enabled': False,
    'bolo_tie_enabled': False,
    'cowboy_hat_enabled': False,
    'background_enabled': True,
    'confetti_dice_enabled': True
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

class ConfettiDiceEffect:
    """Overlay effect for Las Vegas/New Year's theme with confetti and dice."""
    
    def __init__(self):
        self.confetti_particles = []
        self.dice_positions = []
        self.frame_count = 0
        # Las Vegas themed colors - gold, silver, neon, vibrant
        self.confetti_colors = [
            (0, 215, 255),    # Gold (BGR)
            (192, 192, 192),  # Silver
            (0, 255, 255),    # Cyan
            (255, 0, 255),    # Magenta
            (255, 255, 0),    # Yellow
            (0, 255, 0),      # Green
            (255, 0, 0),      # Blue (BGR)
            (0, 0, 255),      # Red (BGR)
            (255, 165, 0),    # Orange
            (255, 192, 203),  # Pink
            (128, 0, 128),    # Purple
            (255, 20, 147),   # Deep Pink
            (0, 191, 255),    # Deep Sky Blue
            (255, 215, 0),    # Gold (alternative)
        ]
        self.initialize_effect()
    
    def is_enabled(self):
        return EFFECT_CONFIG['confetti_dice_enabled']
    
    def initialize_effect(self):
        """Initialize confetti particles and dice positions."""
        # Create confetti particles (will be regenerated per frame for animation)
        self.confetti_particles = []
        self.dice_positions = []
    
    def draw_star(self, frame, center_x, center_y, size, color):
        """Draw a star shape."""
        points = []
        outer_radius = size
        inner_radius = size // 2
        for i in range(10):
            angle = i * np.pi / 5
            if i % 2 == 0:
                radius = outer_radius
            else:
                radius = inner_radius
            x = int(center_x + radius * np.cos(angle))
            y = int(center_y + radius * np.sin(angle))
            points.append([x, y])
        pts = np.array(points, np.int32)
        cv2.fillPoly(frame, [pts], color)
    
    def draw_diamond(self, frame, center_x, center_y, size, color):
        """Draw a diamond shape."""
        points = np.array([
            [center_x, center_y - size],
            [center_x + size, center_y],
            [center_x, center_y + size],
            [center_x - size, center_y]
        ], np.int32)
        cv2.fillPoly(frame, [points], color)
    
    def draw_dice(self, frame, x, y, size):
        """Draw a dice at the specified position."""
        # Dice colors: white background with black dots
        dice_color = (255, 255, 255)  # White
        dot_color = (0, 0, 0)  # Black
        border_color = (100, 100, 100)  # Gray border
        
        # Draw dice square with rounded corners effect
        cv2.rectangle(frame, (x, y), (x + size, y + size), border_color, 2)
        cv2.rectangle(frame, (x + 2, y + 2), (x + size - 2, y + size - 2), dice_color, -1)
        
        # Draw random number of dots (1-6)
        dot_count = random.randint(1, 6)
        dot_radius = max(3, size // 12)
        spacing = size // 4
        
        # Dot patterns for different numbers
        patterns = {
            1: [(size // 2, size // 2)],
            2: [(spacing, spacing), (size - spacing, size - spacing)],
            3: [(spacing, spacing), (size // 2, size // 2), (size - spacing, size - spacing)],
            4: [(spacing, spacing), (size - spacing, spacing), (spacing, size - spacing), (size - spacing, size - spacing)],
            5: [(spacing, spacing), (size - spacing, spacing), (size // 2, size // 2), (spacing, size - spacing), (size - spacing, size - spacing)],
            6: [(spacing, spacing), (spacing, size // 2), (spacing, size - spacing), (size - spacing, spacing), (size - spacing, size // 2), (size - spacing, size - spacing)]
        }
        
        for dot_pos in patterns[dot_count]:
            cv2.circle(frame, (x + dot_pos[0], y + dot_pos[1]), dot_radius, dot_color, -1)
    
    def apply_effect(self, frame):
        """Apply confetti and dice overlay to the frame."""
        if not self.is_enabled():
            return frame
        
        h, w = frame.shape[:2]
        
        # Generate fresh particles distributed across the entire frame
        self.confetti_particles = []
        for _ in range(80):  # Generate particles for the frame
            x = random.randint(0, w)
            y = random.randint(0, h)  # Distribute throughout the frame
            size = random.randint(8, 25)
            color = random.choice(self.confetti_colors)
            shape = random.choice(['circle', 'square', 'diamond', 'star', 'rectangle'])
            rotation = random.uniform(0, 360)
            self.confetti_particles.append({
                'x': x, 'y': y, 'size': size, 'color': color, 'shape': shape,
                'rotation': rotation
            })
        
        # Generate dice positions
        self.dice_positions = []
        num_dice = random.randint(5, 10)
        for _ in range(num_dice):
            x = random.randint(0, w - 80)
            y = random.randint(0, h - 80)
            size = random.randint(40, 70)
            angle = random.randint(0, 360)
            self.dice_positions.append({'x': x, 'y': y, 'size': size, 'angle': angle})
        
        # Draw confetti particles
        for particle in self.confetti_particles:
            # Draw particle based on shape
            x, y = int(particle['x']), int(particle['y'])
            size = particle['size']
            color = particle['color']
            base_color = color
            
            if particle['shape'] == 'circle':
                cv2.circle(frame, (x, y), size, base_color, -1)
                # Add highlight for 3D effect
                if size > 10:
                    highlight_color = tuple(min(255, c + 50) for c in base_color)
                    cv2.circle(frame, (x - size//4, y - size//4), size//3, highlight_color, -1)
            elif particle['shape'] == 'square':
                # Draw rotated square
                half_size = size // 2
                angle_rad = np.radians(particle['rotation'])
                cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
                points = np.array([
                    [x + int(half_size * (cos_a - sin_a)), y + int(half_size * (sin_a + cos_a))],
                    [x + int(half_size * (-cos_a - sin_a)), y + int(half_size * (-sin_a + cos_a))],
                    [x + int(half_size * (-cos_a + sin_a)), y + int(half_size * (-sin_a - cos_a))],
                    [x + int(half_size * (cos_a + sin_a)), y + int(half_size * (sin_a - cos_a))]
                ], np.int32)
                cv2.fillPoly(frame, [points], base_color)
                # Add border for definition
                cv2.polylines(frame, [points], True, tuple(max(0, c - 30) for c in base_color), 1)
            elif particle['shape'] == 'diamond':
                self.draw_diamond(frame, x, y, size, base_color)
                # Add highlight
                if size > 10:
                    highlight_color = tuple(min(255, c + 40) for c in base_color)
                    self.draw_diamond(frame, x - size//4, y - size//4, size//3, highlight_color)
            elif particle['shape'] == 'star':
                self.draw_star(frame, x, y, size, base_color)
                # Add sparkle effect
                if size > 12:
                    sparkle_color = (255, 255, 255)  # White sparkle
                    cv2.circle(frame, (x, y), 2, sparkle_color, -1)
            elif particle['shape'] == 'rectangle':
                # Draw rotated rectangle
                half_w, half_h = size, size // 2
                angle_rad = np.radians(particle['rotation'])
                cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
                points = np.array([
                    [x + int(half_w * cos_a - half_h * sin_a), y + int(half_w * sin_a + half_h * cos_a)],
                    [x + int(-half_w * cos_a - half_h * sin_a), y + int(-half_w * sin_a + half_h * cos_a)],
                    [x + int(-half_w * cos_a + half_h * sin_a), y + int(-half_w * sin_a - half_h * cos_a)],
                    [x + int(half_w * cos_a + half_h * sin_a), y + int(half_w * sin_a - half_h * cos_a)]
                ], np.int32)
                cv2.fillPoly(frame, [points], base_color)
        
        # Draw dice
        for dice in self.dice_positions:
            # Create a temporary image for the dice to allow rotation
            dice_img = np.zeros((dice['size'] + 20, dice['size'] + 20, 3), dtype=np.uint8)
            self.draw_dice(dice_img, 10, 10, dice['size'])
            
            # Rotate the dice
            center = (dice['size'] // 2 + 10, dice['size'] // 2 + 10)
            rot_mat = cv2.getRotationMatrix2D(center, dice['angle'], 1.0)
            rotated_dice = cv2.warpAffine(dice_img, rot_mat, 
                                        (dice['size'] + 20, dice['size'] + 20),
                                        flags=cv2.INTER_LINEAR,
                                        borderMode=cv2.BORDER_CONSTANT,
                                        borderValue=(0, 0, 0))
            
            # Overlay rotated dice on frame
            x, y = dice['x'], dice['y']
            x_end = min(x + dice['size'] + 20, w)
            y_end = min(y + dice['size'] + 20, h)
            dice_w = x_end - x
            dice_h = y_end - y
            
            if dice_w > 0 and dice_h > 0:
                dice_roi = rotated_dice[:dice_h, :dice_w]
                frame_roi = frame[y:y_end, x:x_end]
                
                # Create mask for non-black pixels (dice is white/colored, not black)
                mask = (dice_roi.sum(axis=2) > 50).astype(np.uint8)  # Threshold to ignore black background
                mask_3d = np.stack([mask] * 3, axis=-1)
                
                # Blend dice onto frame
                frame[y:y_end, x:x_end] = np.where(mask_3d, dice_roi, frame_roi)
        
        return frame 