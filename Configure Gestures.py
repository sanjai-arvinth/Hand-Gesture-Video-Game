import tkinter as tk
from tkinter import ttk, messagebox
import json

# Load the gestures from the gestures.json file
def load_gestures():
    try:
        with open("gestures.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Gesture file not found.")
        return []

# Load existing gesture-key mappings from the gesture_key_mapping.json file
def load_mapping():
    try:
        with open("gesture_key_mapping.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Mapping file not found. Starting with empty mappings.")
        return {'mapping': {}, 'types': {}}

# Save the gesture-key mapping to a JSON file
def save_mapping(gesture_key_mapping):
    try:
        with open("gesture_key_mapping.json", "w") as f:
            json.dump(gesture_key_mapping, f)
        messagebox.showinfo("Success", "Gesture-key mapping saved successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Error saving mapping: {e}")

# Create the Tkinter window
def create_configuration_window(gestures, existing_mapping):
    window = tk.Tk()
    window.title("Gesture to Key Configuration")
    window.geometry("400x400")

    gesture_key_mapping = existing_mapping['mapping']
    gesture_types = existing_mapping['types']

    # Create labels and dropdowns for each gesture
    for idx, gesture in enumerate(gestures):
        gesture_name = gesture['name']
        tk.Label(window, text=f"Gesture: {gesture_name}").grid(row=idx, column=0, padx=10, pady=5)

        # Entry for key assignment
        key_var = tk.StringVar()
        entry = ttk.Entry(window, textvariable=key_var)
        entry.grid(row=idx, column=1, padx=10, pady=5)

        # Initialize entry with existing mapping if available
        if gesture_name in gesture_key_mapping:
            key_var.set(gesture_key_mapping[gesture_name])

        # Dropdown for action type (hold or press)
        action_var = tk.StringVar(value=gesture_types.get(gesture_name, 'Press Once'))
        action_dropdown = ttk.Combobox(window, textvariable=action_var, values=['Press Once', 'Hold'])
        action_dropdown.grid(row=idx, column=2, padx=10, pady=5)

        # Save the mapping when the user changes the key entry
        def save_entry(gesture_name, key_var):
            gesture_key_mapping[gesture_name] = key_var.get()
            gesture_types[gesture_name] = action_var.get()  # Store the action type

        # Attach an event handler to track changes in the entry
        entry.bind('<FocusOut>', lambda e, g=gesture_name, k=key_var: save_entry(g, k))

        # Attach an event handler to track changes in the action type dropdown
        action_dropdown.bind("<<ComboboxSelected>>", lambda e, g=gesture_name, k=key_var: save_entry(g, k))

    # Save button
    save_button = tk.Button(window, text="Save", command=lambda: save_mapping({'mapping': gesture_key_mapping, 'types': gesture_types}))
    save_button.grid(row=len(gestures) + 1, column=0, columnspan=3, pady=20)

    window.mainloop()

# Load gestures and existing mappings, then create the configuration window
gestures = load_gestures()
existing_mapping = load_mapping()
if gestures:
    create_configuration_window(gestures, existing_mapping)
else:
    print("No gestures found.")
