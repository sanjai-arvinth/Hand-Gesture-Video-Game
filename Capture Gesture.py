import cv2
import mediapipe as mp
import json

# Initialize MediaPipe Hand Detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()


# List to store gestures
stored_gestures = []

def save_gesture(landmarks, gesture_name):
    # Convert landmarks to a list of (x, y, z) coordinates
    gesture_data = [{"x": lm.x, "y": lm.y, "z": lm.z} for lm in landmarks]
    stored_gestures.append({"name": gesture_name, "landmarks": gesture_data})

    # Save to a JSON file
    with open("gestures.json", "w") as f:
        json.dump(stored_gestures, f)
    print(f"Gesture '{gesture_name}' saved!")

try:
    while cap.isOpened():
        # Capture frames from the webcam
        success, frame = cap.read()
        if not success:
            print("Failed to capture frame.")
            continue


        # Flip the frame horizontally for a selfie-view display
        frame = cv2.flip(frame, 1)

        # Convert the frame color to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame and detect hands
        result = hands.process(rgb_frame)

        # Draw hand landmarks
        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Example: Press 's' to save the current gesture with a given name
                key = cv2.waitKey(1) & 0xFF
                if key == ord('s'):
                    gesture_name = input("Enter gesture name: ")
                    save_gesture(hand_landmarks.landmark, gesture_name)

        # Display the frame
        cv2.imshow("Hand Gesture Capture", frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    hands.close()
