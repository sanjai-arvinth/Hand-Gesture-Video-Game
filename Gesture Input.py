import cv2
import mediapipe as mp
import json
import numpy as np
from collections import deque
import pyautogui
import time

# Initialize MediaPipe Hand Detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Load gesture-key mapping
def load_gesture_key_mapping():
    with open("gesture_key_mapping.json", "r") as f:
        return json.load(f)

# Load recorded gestures
def load_recorded_gestures():
    with open("gestures.json", "r") as f:
        return json.load(f)

gesture_key_mapping = load_gesture_key_mapping()
recorded_gestures = load_recorded_gestures()

def calculate_distance(point1, point2):
    return np.sqrt((point1['x'] - point2['x']) ** 2 +
                   (point1['y'] - point2['y']) ** 2 +
                   (point1['z'] - point2['z']) ** 2)

def match_gesture(current_landmarks, recorded_landmarks):
    if len(current_landmarks) != len(recorded_landmarks):
        return float('inf')

    total_distance = 0
    for i in range(len(current_landmarks)):
        distance = calculate_distance(current_landmarks[i], recorded_landmarks[i])
        total_distance += distance

    return total_distance / len(current_landmarks)

def detect_gesture(hand_landmarks):
    current_landmarks = [{"x": lm.x, "y": lm.y, "z": lm.z} for lm in hand_landmarks.landmark]
    
    min_distance = float('inf')
    detected_gesture = None

    for gesture in recorded_gestures:
        distance = match_gesture(current_landmarks, gesture['landmarks'])
        if distance < min_distance:
            min_distance = distance
            detected_gesture = gesture['name']

    if min_distance < 1.5:  # Adjusted threshold for better accuracy
        return detected_gesture
    return None

# Main function to capture and recognize gestures
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# For gesture smoothing
gesture_history = deque(maxlen=10)
gesture_threshold = 7  # Number of consistent detections required

# For managing key states
key_states = {}
last_key_press_time = {}
key_press_cooldown = 0.5  # Cooldown period in seconds

# For left-hand swipe tracking
last_left_hand_position = None
swipe_threshold = 0.001  # Adjust this value to change swipe sensitivity

# Get screen size
screen_width, screen_height = pyautogui.size()

try:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Failed to capture frame.")
            continue

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)

        detected_gestures = set()

        if result.multi_hand_landmarks and result.multi_handedness:
            for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Determine if the hand is left or right
                is_left_hand = handedness.classification[0].label == "Left"
                
                gesture_name = detect_gesture(hand_landmarks)
                gesture_history.append(gesture_name)

                if is_left_hand:
                    # Handle left-hand swiping
                    index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                    
                    # Check if index finger is extended (for swiping)
                    if index_finger_tip.y < thumb_tip.y:
                        screen_x = index_finger_tip.x * screen_width
                        screen_y = index_finger_tip.y * screen_height

                        if last_left_hand_position:
                            dx = screen_x - last_left_hand_position[0]
                            dy = screen_y - last_left_hand_position[1]
                            
                            # Apply swipe threshold
                            if abs(dx) > swipe_threshold * screen_width or abs(dy) > swipe_threshold * screen_height:
                                pyautogui.moveRel(dx, dy)

                        last_left_hand_position = (screen_x, screen_y)
                    else:
                        last_left_hand_position = None

                elif not is_left_hand:
                    # Handle right-hand gestures for other controls
                    if gesture_name and gesture_history.count(gesture_name) >= gesture_threshold:
                        detected_gestures.add(gesture_name)

        # Process detected gestures
        for gesture_name in detected_gestures:
            if gesture_name in gesture_key_mapping['mapping']:
                key = gesture_key_mapping['mapping'][gesture_name]
                action_type = gesture_key_mapping['types'][gesture_name]
                current_time = time.time()

                if action_type == "Press Once":
                    if current_time - last_key_press_time.get(key, 0) > key_press_cooldown:
                        pyautogui.press(key)
                        last_key_press_time[key] = current_time
                        print(f"Pressed key: {key}")
                elif action_type == "Hold":
                    if not key_states.get(key, False):
                        pyautogui.keyDown(key)
                        key_states[key] = True
                        print(f"Holding key: {key}")

        # Release held keys if the gesture is no longer detected
        for key in list(key_states.keys()):
            gesture_for_key = next((g for g, k in gesture_key_mapping['mapping'].items() if k == key), None)
            if key_states[key] and gesture_for_key not in detected_gestures:
                pyautogui.keyUp(key)
                key_states[key] = False
                print(f"Released key: {key}")

        # Reset left-hand position if hand is not detected
        if not result.multi_hand_landmarks:
            last_left_hand_position = None

        cv2.imshow("Hand Gesture Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    for key in key_states:
        if key_states[key]:
            pyautogui.keyUp(key)
    cap.release()
    cv2.destroyAllWindows()
    hands.close()