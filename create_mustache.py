import cv2
import numpy as np

# Create a transparent image
mustache = np.zeros((120, 300, 4), dtype=np.uint8)

# Main body (thicker, with a curve)
cv2.ellipse(mustache, (150, 70), (90, 30), 0, 0, 180, (40, 30, 20, 255), -1)

# Left twirl
cv2.ellipse(mustache, (60, 70), (40, 18), 0, 20, 200, (40, 30, 20, 255), -1)
cv2.ellipse(mustache, (40, 70), (18, 10), 0, 60, 220, (40, 30, 20, 255), -1)

# Right twirl
cv2.ellipse(mustache, (240, 70), (40, 18), 0, -20, 160, (40, 30, 20, 255), -1)
cv2.ellipse(mustache, (260, 70), (18, 10), 0, -40, 120, (40, 30, 20, 255), -1)

# Add a highlight for a bit of shine
cv2.ellipse(mustache, (150, 80), (70, 10), 0, 0, 180, (80, 80, 80, 80), -1)

# Add some texture lines
for i in range(-60, 61, 20):
    cv2.line(mustache, (150 + i, 70), (150 + i, 90), (60, 50, 40, 120), 2)

# Save the mustache image
cv2.imwrite('mustache.png', mustache) 