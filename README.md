# ChordTune

## Requirements

- [Node.js](https://nodejs.org)
- [Python 3.x](https://www.python.org)

---

## Installation

**Frontend:**
```bash
cd frontend
npm install
```

**Backend:**
```bash
cd backend/python
pip install sounddevice numpy scipy flask flask-cors scikit-learn
```

---

## First Time Setup

Train the ML model before running the app:

```bash
cd backend/python
py ml_trainer.py
```

---

## Run the App

Open two terminals:

**Terminal 1:**
```bash
cd backend/python
py audio.py
```

**Terminal 2:**
```bash
cd frontend
npm run electron:dev
```
