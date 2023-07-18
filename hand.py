import cv2
import numpy as np
import threading
import queue




cap = cv2.VideoCapture(0)
lower_skin = np.array([0, 20, 70], dtype=np.uint8)
upper_skin = np.array([20, 255, 255], dtype=np.uint8)



hand_position = 0
hand_position_queue = queue.Queue()
current_frame = None
frame_lock = threading.Lock()
hand_position_updated = threading.Event()



def track_hand():

    global hand_position, current_frame, frame_lock, hand_position_queue, hand_position_updated
    while True:
        ret, frame = cap.read()
        #preprocessing

        #convert the frame to HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        #frame to get only skin color
        mask = cv2.inRange(hsv, lower_skin, upper_skin)

        mask = cv2.GaussianBlur(mask, (5, 5), 0)


        #remove noise
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        #convert unnecessary objects to black
        result = cv2.bitwise_and(frame, frame, mask=mask)

        #convert to grayscale
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)

        #threshold the grayscale image to obtain a binary image
        _, threshold = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

        #find contours of the binary image
        contours, _ = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            #find the largest contour
            hand_contour = max(contours, key=cv2.contourArea)

            #compute the centroid of the contour
            M = cv2.moments(hand_contour)
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # Draw the centroid on the frame
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            with frame_lock:
                hand_position = cx
                hand_position_queue.put(cx)
                hand_position_updated.set()        

        with frame_lock:
            current_frame = frame

        #exit when q pressed
        if cv2.waitKey(1) &  0xFF == ord('q'):
            break



    cap.release()
    cv2.destroyAllWindows()