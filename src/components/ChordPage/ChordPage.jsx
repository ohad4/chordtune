import "./ChordPage.css"

const NOTE_NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

// מיפוי אקורדים לפוזיציות על הגיטרה
const FRET_POSITIONS = {
  "C":     [{ string: 1, fret: 3 }, { string: 2, fret: 2 }, { string: 4, fret: 2 }],
  "D":     [{ string: 0, fret: 2 }, { string: 1, fret: 3 }, { string: 2, fret: 2 }],
  "E":     [{ string: 1, fret: 2 }, { string: 2, fret: 2 }, { string: 3, fret: 1 }],
  "F":     [{ string: 1, fret: 3 }, { string: 2, fret: 3 }, { string: 3, fret: 2 }],
  "G":     [{ string: 0, fret: 3 }, { string: 1, fret: 2 }, { string: 5, fret: 3 }],
  "A":     [{ string: 1, fret: 2 }, { string: 2, fret: 2 }, { string: 3, fret: 2 }],
  "B":     [{ string: 1, fret: 4 }, { string: 2, fret: 4 }, { string: 3, fret: 4 }],
  "C#":    [{ string: 1, fret: 4 }, { string: 2, fret: 3 }, { string: 3, fret: 1 }],
  "D#":    [{ string: 1, fret: 4 }, { string: 2, fret: 4 }, { string: 3, fret: 3 }],
  "F#":    [{ string: 1, fret: 4 }, { string: 2, fret: 4 }, { string: 3, fret: 3 }],
  "G#":    [{ string: 1, fret: 1 }, { string: 2, fret: 1 }, { string: 3, fret: 1 }],
  "A#":    [{ string: 1, fret: 3 }, { string: 2, fret: 3 }, { string: 3, fret: 3 }],
}

// מיפוי אקורדים למקשי פסנתר
const CHORD_KEYS = {
  "Major":  [0, 4, 7],
  "Minor":  [0, 3, 7],
  "7":      [0, 4, 7, 10],
  "maj7":   [0, 4, 7, 11],
  "m7":     [0, 3, 7, 10],
  "dim":    [0, 3, 6],
  "aug":    [0, 4, 8],
  "sus2":   [0, 2, 7],
  "sus4":   [0, 5, 7],
  "dim7":   [0, 3, 6, 9],
}

function getChordData(chord) {
  if (!chord || chord.name === "--") {
    return { frets: [], keys: [] }
  }

  // חילוץ תו בסיס וסוג אקורד
  const root = chord.root || "--"
  const chordName = chord.name || "--"
  const chordType = chordName.replace(root, "").trim() || "Major"

  // פוזיציות גיטרה
  const frets = FRET_POSITIONS[root] || []

  // מקשי פסנתר - חישוב לפי תו הבסיס
  const rootIndex = NOTE_NAMES.indexOf(root)
  const intervals = CHORD_KEYS[chordType] || CHORD_KEYS["Major"]
  const keys = rootIndex >= 0 ? intervals.map(i => (rootIndex + i) % 12) : []

  return { frets, keys }
}

function WaveformBg() {
  const points = Array.from({ length: 80 }, (_, i) => {
    const x = (i / 79) * 100
    const y = 50 + Math.sin(i * 0.4) * 12 + Math.sin(i * 0.9) * 6
    return `${x},${y}`
  }).join(" ")

  return (
    <svg className="chord__waveform" preserveAspectRatio="none">
      <polyline points={points} fill="none" stroke="#00e5ff" strokeWidth="1.5" />
    </svg>
  )
}

function Fretboard({ dots }) {
  const strings = 6, frets = 5
  const sw = 260, sh = 120
  const fretW = sw / frets
  const stringH = sh / (strings - 1)

  return (
    <svg width={sw} height={sh + 10} style={{ display: "block" }}>
      {Array.from({ length: frets + 1 }).map((_, i) => (
        <line key={i}
          x1={i * fretW} y1={0} x2={i * fretW} y2={sh}
          stroke={i === 0 ? "rgba(255,255,255,0.6)" : "rgba(255,255,255,0.15)"}
          strokeWidth={i === 0 ? 3 : 1}
        />
      ))}
      {Array.from({ length: strings }).map((_, i) => (
        <line key={i}
          x1={0} y1={i * stringH} x2={sw} y2={i * stringH}
          stroke="rgba(255,255,255,0.2)" strokeWidth={1}
        />
      ))}
      {dots.map((d, i) => {
        const x = (d.fret - 0.5) * fretW
        const y = d.string * stringH
        return (
          <g key={i}>
            <circle cx={x} cy={y} r={10} fill="#00e5ff" opacity={0.9} />
            <circle cx={x} cy={y} r={5} fill="#001a1a" />
          </g>
        )
      })}
    </svg>
  )
}

function PianoKeys({ activeKeys }) {
  const whites = [0, 2, 4, 5, 7, 9, 11, 12]
  const blackPositions = [1, 2, 4, 5, 6]
  const blackNotes = [1, 3, 6, 8, 10]
  const keyW = 42, keyH = 90
  const totalW = whites.length * keyW

  return (
    <svg width={totalW} height={keyH + 10} style={{ display: "block" }}>
      {whites.map((note, i) => (
        <rect key={i}
          x={i * keyW + 1} y={0} width={keyW - 2} height={keyH} rx={3}
          fill={activeKeys.includes(note % 12) ? "#00e5ff" : "rgba(255,255,255,0.08)"}
          stroke="rgba(255,255,255,0.1)" strokeWidth={1}
        />
      ))}
      {blackPositions.map((pos, i) => (
        <rect key={i}
          x={pos * keyW - 13} y={0} width={26} height={keyH * 0.6} rx={2}
          fill={activeKeys.includes(blackNotes[i] % 12) ? "#005f6b" : "rgba(0,0,0,0.75)"}
        />
      ))}
      {whites.map((note, i) => (
        <text key={i}
          x={i * keyW + keyW / 2} y={keyH - 8}
          fill={activeKeys.includes(note % 12) ? "#001a1a" : "rgba(255,255,255,0.3)"}
          fontSize={10} textAnchor="middle" fontFamily="monospace"
        >
          {NOTE_NAMES[note % 12]}
        </text>
      ))}
    </svg>
  )
}

export default function ChordPage({ chord }) {
  const { frets, keys } = getChordData(chord)
  const hasChord = chord && chord.name !== "--"

  return (
    <div className="chord">
      {/* Main chord display */}
      <div className="chord__display">
        <WaveformBg />
        <div className="chord__detected-label">DETECTED CHORD</div>
        <div className="chord__name">
          {hasChord ? chord.name : "--"}
        </div>
        <div className="chord__tags">
          <span className="chord__tag">ROOT: {chord?.root || "--"}</span>
          <span className="chord__tag">INTERVALS: {chord?.intervals || "--"}</span>
        </div>
      </div>

      {/* Bottom panels */}
      <div className="chord__panels">
        <div className="chord__panel">
          <div className="chord__panel-header">
            <span className="chord__panel-title">🎸 Guitar Fretboard</span>
          </div>
          <Fretboard dots={frets} />
        </div>

        <div className="chord__panel">
          <div className="chord__panel-header">
            <span className="chord__panel-title">🎹 Piano Keys</span>
          </div>
          <PianoKeys activeKeys={keys} />
        </div>
      </div>

      {/* Footer */}
      <div className="chord__footer">
        <span className="chord__footer-status">
          <span className="chord__footer-dot">●</span> Playing in 440Hz standard tuning
        </span>
      </div>
    </div>
  )
}
