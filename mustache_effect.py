import cv2
import mediapipe as mp
import numpy as np

class MustacheEffect:
    def __init__(self):
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=10,  # Allow up to 10 faces
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Load mustache image
        self.mustache = cv2.imread('mustache.png', cv2.IMREAD_UNCHANGED)
        if self.mustache is None:
            # Create a simple mustache if image not found
            self.mustache = np.zeros((50, 100, 4), dtype=np.uint8)
            cv2.ellipse(self.mustache, (50, 25), (40, 20), 0, 0, 180, (0, 0, 0, 255), -1)

    def apply_mustache(self, frame):
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                h, w, _ = frame.shape
                # Get mouth landmarks
                mouth_top = face_landmarks.landmark[13]  # Upper lip
                mouth_bottom = face_landmarks.landmark[14]  # Lower lip

                # Calculate mustache position
                mustache_width = int(w * 0.3)  # 30% of frame width
                mustache_height = int(mustache_width * self.mustache.shape[0] / self.mustache.shape[1])
                mustache_x = int(mouth_top.x * w) - mustache_width // 2
                mustache_y = int(mouth_top.y * h) - mustache_height

                # Ensure coordinates are within frame bounds
                mustache_x = max(0, min(mustache_x, w - mustache_width))
                mustache_y = max(0, min(mustache_y, h - mustache_height))

                # Resize mustache
                resized_mustache = cv2.resize(self.mustache, (mustache_width, mustache_height))

                # Overlay mustache
                if mustache_width > 0 and mustache_height > 0:
                    alpha = resized_mustache[:, :, 3] / 255.0
                    for c in range(3):
                        frame[mustache_y:mustache_y + mustache_height, 
                              mustache_x:mustache_x + mustache_width, c] = \
                            frame[mustache_y:mustache_y + mustache_height, 
                                  mustache_x:mustache_x + mustache_width, c] * (1 - alpha) + \
                            resized_mustache[:, :, c] * alpha
        return frame 