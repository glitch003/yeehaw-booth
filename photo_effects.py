import cv2
import mediapipe as mp
import numpy as np
from abc import ABC, abstractmethod
import math
import os
import random
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Effect configuration
EFFECT_CONFIG = {
    'mustache_enabled': False,
    'bolo_tie_enabled': False,
    'cowboy_hat_enabled': False,
    'background_enabled': False,
    'darren_enabled': True
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

class DarrenFaceSwapEffect:
    def __init__(self):
        # Initialize MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,  # Full range model
            min_detection_confidence=0.5
        )
        
        # Initialize MediaPipe Face Mesh for better face alignment
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.darren_face = None
        self.darren_landmarks = None
        self.load_darren_face()

    def is_enabled(self):
        return EFFECT_CONFIG['darren_enabled']

    def load_darren_face(self):
        """Load Darren's face from one of the photos in the darren folder."""
        darren_folder = 'darren'
        if not os.path.exists(darren_folder):
            print(f"Warning: {darren_folder} folder not found")
            return
        
        # Get all jpg files in the darren folder
        darren_files = [f for f in os.listdir(darren_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not darren_files:
            print(f"Warning: No image files found in {darren_folder} folder")
            return
        
        # randomize the order of the files
        random.shuffle(darren_files)
        
        # Try to load a face from one of Darren's photos
        for darren_file in darren_files:
            darren_path = os.path.join(darren_folder, darren_file)
            darren_image = cv2.imread(darren_path)
            if darren_image is None:
                continue
            
            # Convert to RGB for MediaPipe
            darren_rgb = cv2.cvtColor(darren_image, cv2.COLOR_BGR2RGB)
            
            # Try to detect face in Darren's photo
            face_results = self.face_detection.process(darren_rgb)
            if face_results.detections:
                # Get the first detected face
                detection = face_results.detections[0]
                bbox = detection.location_data.relative_bounding_box
                h, w, _ = darren_image.shape
                
                # Extract face region with padding
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                face_w = int(bbox.width * w)
                face_h = int(bbox.height * h)
                
                # Add padding
                padding = 50
                x = max(0, x - padding)
                y = max(0, y - padding)
                face_w = min(w - x, face_w + 2 * padding)
                face_h = min(h - y, face_h + 2 * padding)
                
                # Extract and store Darren's face
                self.darren_face = darren_image[y:y+face_h, x:x+face_w].copy()
                
                # Get face landmarks for Darren's face
                mesh_results = self.face_mesh.process(darren_rgb)
                if mesh_results.multi_face_landmarks:
                    self.darren_landmarks = mesh_results.multi_face_landmarks[0]
                    print(f"Successfully loaded Darren's face from {darren_file}")
                    return
        
        print("Warning: Could not detect face in any Darren photos")

    def get_face_mask(self, landmarks, bbox, img_shape):
        """Create a mask for the face region using landmarks and bounding box."""
        h, w = img_shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # Get face outline points from MediaPipe face mesh
        # These are the indices for the face oval contour
        face_oval_indices = [
            10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
            397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
            172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109
        ]
        
        points = []
        for idx in face_oval_indices:
            if idx < len(landmarks.landmark):
                landmark = landmarks.landmark[idx]
                points.append([int(landmark.x * w), int(landmark.y * h)])
        
        if len(points) > 2:
            points = np.array(points, dtype=np.int32)
            cv2.fillPoly(mask, [points], 255)
        else:
            # Fallback: use elliptical mask based on bounding box
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            face_w = int(bbox.width * w)
            face_h = int(bbox.height * h)
            center = (x + face_w // 2, y + face_h // 2)
            axes = (face_w // 2, int(face_h * 0.9))
            cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        
        # Apply Gaussian blur for smoother edges
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        
        return mask

    def apply_effect(self, frame):
        """Apply face swap effect to replace detected faces with Darren's face."""
        if not self.is_enabled() or self.darren_face is None:
            return frame
        
        # Convert frame to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces in the frame
        face_results = self.face_detection.process(rgb_frame)
        
        if not face_results.detections:
            return frame
        
        # Get face mesh landmarks for better alignment
        mesh_results = self.face_mesh.process(rgb_frame)
        
        if not mesh_results.multi_face_landmarks:
            return frame
        
        # Process each detected face (use the first one if multiple detected)
        if len(face_results.detections) > 0 and len(mesh_results.multi_face_landmarks) > 0:
            detection = face_results.detections[0]
            landmarks = mesh_results.multi_face_landmarks[0]
            
            # Get bounding box
            bbox = detection.location_data.relative_bounding_box
            h, w, _ = frame.shape
            
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            face_w = int(bbox.width * w)
            face_h = int(bbox.height * h)
            
            # Ensure coordinates are within bounds
            x = max(0, x)
            y = max(0, y)
            face_w = min(w - x, face_w)
            face_h = min(h - y, face_h)
            
            if face_w > 0 and face_h > 0:
                # Resize Darren's face to match detected face size
                darren_resized = cv2.resize(self.darren_face, (face_w, face_h), interpolation=cv2.INTER_LINEAR)
                
                # Create a mask for blending
                mask = self.get_face_mask(landmarks, bbox, frame.shape)
                
                # Extract the mask region for the face
                face_mask = mask[y:y+face_h, x:x+face_w]
                
                # Normalize mask to 0-1 range
                if face_mask.max() > 0:
                    face_mask = face_mask.astype(np.float32) / 255.0
                else:
                    # Fallback: use elliptical mask if landmark mask fails
                    face_mask = np.ones((face_h, face_w), dtype=np.float32)
                    cv2.ellipse(face_mask, (face_w//2, face_h//2), (face_w//2, int(face_h*0.9)), 0, 0, 360, 1.0, -1)
                    face_mask = cv2.GaussianBlur(face_mask, (21, 21), 0)
                
                # Expand mask to 3 channels
                face_mask_3d = np.stack([face_mask] * 3, axis=-1)
                
                # Blend Darren's face into the frame
                frame[y:y+face_h, x:x+face_w] = (
                    frame[y:y+face_h, x:x+face_w] * (1 - face_mask_3d) +
                    darren_resized * face_mask_3d
                ).astype(np.uint8)
        
        return frame 