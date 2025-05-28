import cv2
import numpy as np

# Create a transparent image
cowboy_hat = np.zeros((200, 300, 4), dtype=np.uint8)

# Draw the main hat body (top part)
cv2.ellipse(cowboy_hat, (150, 100), (80, 60), 0, 0, 180, (40, 30, 20, 255), -1)  # Brown
cv2.ellipse(cowboy_hat, (150, 100), (70, 50), 0, 0, 180, (60, 40, 20, 255), -1)  # Lighter brown

# Draw the wide brim
cv2.ellipse(cowboy_hat, (150, 120), (120, 20), 0, 0, 180, (40, 30, 20, 255), -1)  # Brown
cv2.ellipse(cowboy_hat, (150, 120), (110, 15), 0, 0, 180, (60, 40, 20, 255), -1)  # Lighter brown

# Add decorative band
cv2.ellipse(cowboy_hat, (150, 100), (75, 10), 0, 0, 180, (139, 69, 19, 255), -1)  # Brown band
cv2.ellipse(cowboy_hat, (150, 100), (70, 5), 0, 0, 180, (184, 134, 11, 255), -1)  # Gold trim

# Add some texture to the hat
for i in range(-60, 61, 20):
    cv2.line(cowboy_hat, (150 + i, 80), (150 + i, 120), (60, 50, 40, 120), 2)

# Add a highlight for a bit of shine
cv2.ellipse(cowboy_hat, (150, 90), (50, 10), 0, 0, 180, (80, 80, 80, 80), -1)

# Add some decorative stitching on the brim
for i in range(-100, 101, 20):
    cv2.line(cowboy_hat, (150 + i, 120), (150 + i, 130), (60, 50, 40, 120), 1)

# Save the cowboy hat image
cv2.imwrite('cowboy_hat.png', cowboy_hat) 