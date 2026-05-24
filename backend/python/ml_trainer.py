import numpy as np
import json
import os
import pickle

# Machine Learning libraries from scikit-learn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ---------------------------------------------------------
# Load chord templates and setup constants
# ---------------------------------------------------------
_json_path = os.path.join(os.path.dirname(__file__), "chords.json")
with open(_json_path, "r") as f:
    _chord_data = json.load(f)

# The musical intervals that make up each chord type (e.g., Major = [0, 4, 7])
CHORD_TEMPLATES = _chord_data["templates"]

# List of musical note names in chromatic order
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def make_realistic_sample_v2(root, chord_type):
    """
    Simulates a realistic acoustic guitar chord strike.
    Instead of training the model on "perfect" mathematical data, we introduce
    controlled randomness to make the model robust against real-world playing conditions.
    """
    template = CHORD_TEMPLATES[chord_type]
    notes = [0.0] * 12

    # 1. Base Note Strength: Each note in the chord is played at a slightly different volume
    for interval in template:
        note_idx = (root + interval) % 12
        # Randomize volume between 60% and 100%
        strength = np.random.uniform(0.6, 1.0)
        notes[note_idx] = strength

    # 2. Muted/Weak Strings: Simulate a human player not pressing a string perfectly (20% chance)
    if np.random.random() < 0.2:
        weak_note = (root + template[np.random.randint(len(template))]) % 12
        notes[weak_note] *= np.random.uniform(0.1, 0.4) # Drop the volume of this specific note

    # 3. Background Noise: Add tiny amounts of noise to all 12 notes (simulating room noise or harmonics)
    # The noise is kept very low (0 to 0.02) because we now use a Noise Gate in chord.py
    noise = [np.random.uniform(0, 0.02) for _ in range(12)]
    notes = [min(1.0, n + noise[i]) for i, n in enumerate(notes)]

    # 4. Root Note One-Hot Encoding: Creates an array where only the root note's index is 1.0
    root_vec = [0.0] * 12
    root_vec[root] = 1.0

    # Return a single 24-value feature vector (12 notes + 12 root indicators)
    return notes + root_vec 

def generate_dataset():
    """
    Generates a massive synthetic dataset for the machine learning model to learn from.
    Creates 300 unique variations for every single chord.
    Total samples = 12 roots * 10 chord types * 300 = 36,000 data points.
    """
    X = [] # Features (the 24-value arrays)
    y = [] # Labels (the chord names, e.g., "C_Major")

    chord_types = list(CHORD_TEMPLATES.keys())

    for root in range(12):
        for chord_type in chord_types:
            label = f"{NOTE_NAMES[root]}_{chord_type}"
            for _ in range(300):
                X.append(make_realistic_sample_v2(root, chord_type))
                y.append(label)

    return np.array(X), np.array(y)

def train_model():
    """
    The main pipeline to generate data, train the Random Forest model, 
    evaluate its accuracy, and save it to the disk.
    """
    print("Generating improved dataset (V2)...")
    X, y = generate_dataset()
    print(f"Created {len(X)} samples for {len(set(y))} chords")

    # Split the dataset: 80% for training the model, 20% for testing its accuracy
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training Random Forest model...")
    # Initialize a Random Forest with 250 decision trees for high accuracy and stability
    model = RandomForestClassifier(n_estimators=250, random_state=42)
    
    # Train the model on the 80% training data
    model.fit(X_train, y_train)

    # Test the model on the remaining 20% unseen data to calculate real accuracy
    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    print(f"Model accuracy: {acc * 100:.1f}%")

    # Serialize (save) the trained model to a .pkl file so the Flask server can load and use it
    # We save it as 'ml_model.pkl' to maintain compatibility with chord.py
    model_path = os.path.join(os.path.dirname(__file__), "ml_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print("Model saved successfully: ml_model.pkl")

if __name__ == "__main__":
    # Execute the training pipeline when the script is run
    train_model()