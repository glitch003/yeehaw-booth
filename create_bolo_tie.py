import cv2
import numpy as np

# Create a transparent image
bolo_tie = np.zeros((200, 100, 4), dtype=np.uint8)

# Draw the main cord (vertical line)
cv2.line(bolo_tie, (50, 0), (50, 200), (40, 30, 20, 255), 4)

# Draw the decorative clasp
# Main clasp body (oval)
cv2.ellipse(bolo_tie, (50, 100), (25, 15), 0, 0, 360, (139, 69, 19, 255), -1)  # Brown
cv2.ellipse(bolo_tie, (50, 100), (20, 10), 0, 0, 360, (184, 134, 11, 255), -1)  # Gold

# Add decorative elements to the clasp
# Center gem
cv2.circle(bolo_tie, (50, 100), 8, (0, 0, 139, 255), -1)  # Dark blue gem
cv2.circle(bolo_tie, (50, 100), 6, (0, 0, 255, 255), -1)  # Bright blue highlight

# Add some shine to the clasp
cv2.ellipse(bolo_tie, (45, 95), (8, 4), 0, 0, 180, (255, 255, 255, 100), -1)

# Add texture to the cord
for y in range(0, 200, 10):
    cv2.line(bolo_tie, (48, y), (52, y), (60, 50, 40, 120), 1)

# Save the bolo tie image
cv2.imwrite('bolo_tie.png', bolo_tie) 