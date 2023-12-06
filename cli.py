# import cv2
#
# # Load images
# full_screenshot = cv2.imread('screenshot.png')
# button_image = cv2.imread('button.png')
#
# # Template matching
# result = cv2.matchTemplate(full_screenshot, button_image, cv2.TM_CCOEFF_NORMED)
#
# # Locate the button
# _, _, _, max_loc = cv2.minMaxLoc(result)
#
# # Button position and size
# button_x, button_y = max_loc
# button_width, button_height = button_image.shape[1], button_image.shape[0]
#
# # Draw a rectangle around the detected button (Optional)
# cv2.rectangle(full_screenshot, max_loc, (button_x + button_width, button_y + button_height), (255, 0, 0), 2)
# cv2.imshow('Detected Button', full_screenshot)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
from llm import run_web_task

while True:
    task = input("Enter a task: ")
    output = run_web_task(task)
    print("Task Output: " + output)
