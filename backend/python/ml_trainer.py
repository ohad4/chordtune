import numpy as np
import json
import os
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load chord data from JSON
_json_path = os.path.join(os.path.dirname(__file__), "chords.json")
with open(_json_path, "r") as f:
    _chord_data = json.load(f)

CHORD_TEMPLATES = _chord_data["templates"]
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def make_realistic_sample(root, chord_type):
    """
    Simulates a realistic guitar sound:
    1. Not all notes sound at equal volume
    2. Sometimes one note is weaker (string not played hard)
    3. Sometimes an extra note is heard (harmonic)
    4. Small background noise
    """
    template = CHORD_TEMPLATES[chord_type]
    notes = [0.0] * 12

    # Each note at a slightly different strength - like a real guitar
    for interval in template:
        note_idx = (root + interval) % 12
        strength = np.random.uniform(0.6, 1.0)
        notes[note_idx] = strength

    # Sometimes one note is weak (string played softly)
    if np.random.random() < 0.3:
        weak_note = (root + template[np.random.randint(len(template))]) % 12
        notes[weak_note] *= np.random.uniform(0.1, 0.4)

    # Sometimes a harmonic - a neighboring note heard faintly
    if np.random.random() < 0.4:
        extra_note = np.random.randint(12)
        if notes[extra_note] == 0:
            notes[extra_note] = np.random.uniform(0.05, 0.2)

    # Small background noise
    noise = [np.random.uniform(0, 0.05) for _ in range(12)]
    notes = [n + noise[i] for i, n in enumerate(notes)]

    # Root note vector
    root_vec = [0.0] * 12
    root_vec[root] = 1.0

    return notes + root_vec  # 24 features total

def generate_dataset():
    """
    Generates a realistic dataset of guitar chords.
    Creates 200 samples per chord.
    """
    X = []
    y = []

    chord_types = list(CHORD_TEMPLATES.keys())

    for root in range(12):
        for chord_type in chord_types:
            label = f"{NOTE_NAMES[root]}_{chord_type}"
            for _ in range(200):
                X.append(make_realistic_sample(root, chord_type))
                y.append(label)

    return np.array(X), np.array(y)

def train_model():
    print("Generating dataset...")
    X, y = generate_dataset()
    print(f"Created {len(X)} samples for {len(set(y))} chords")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training Random Forest model...")
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    print(f"Model accuracy: {acc * 100:.1f}%")

    model_path = os.path.join(os.path.dirname(__file__), "ml_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"Model saved: ml_model.pkl")

if __name__ == "__main__":
    train_model()
