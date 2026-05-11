import "./TunerPage.css"

const STRINGS = [
  { note: "E", octave: 2, freq: 82.41,  label: "6TH" },
  { note: "A", octave: 2, freq: 110.0,  label: "5TH" },
  { note: "D", octave: 3, freq: 146.83, label: "4TH" },
  { note: "G", octave: 3, freq: 196.0,  label: "3RD" },
  { note: "B", octave: 3, freq: 246.94, label: "2ND" },
  { note: "e", octave: 4, freq: 329.63, label: "1ST" },
]

function TunerDial({ cents }) {
  const angle = Math.max(-50, Math.min(50, cents)) * 1.4
  const cx = 180, cy = 205

  return (
    <div className="tuner__dial-wrapper">
      <svg width="360" height="220" viewBox="0 0 360 220" style={{ position: "absolute", top: 0 }}>
        <defs>
          <linearGradient id="arcGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%"   stopColor="#00e5ff" stopOpacity="0.15" />
            <stop offset="50%"  stopColor="#00e5ff" stopOpacity="0.05" />
            <stop offset="100%" stopColor="#00e5ff" stopOpacity="0.15" />
          </linearGradient>
        </defs>
        <path d="M 30 200 A 150 150 0 0 1 330 200" fill="none" stroke="url(#arcGrad)" strokeWidth="2" />
        {[-50,-40,-30,-20,-10,0,10,20,30,40,50].map(v => {
          const rad = ((v / 50) * 80 - 90) * (Math.PI / 180)
          const r1 = 145, r2 = v === 0 ? 128 : 136
          return (
            <line key={v}
              x1={cx + r1 * Math.cos(rad)} y1={cy + r1 * Math.sin(rad)}
              x2={cx + r2 * Math.cos(rad)} y2={cy + r2 * Math.sin(rad)}
              stroke={v === 0 ? "#00e5ff" : "rgba(255,255,255,0.25)"}
              strokeWidth={v === 0 ? 2 : 1}
            />
          )
        })}
        {[-50,-25,0,25,50].map(v => {
          const rad = ((v / 50) * 80 - 90) * (Math.PI / 180)
          return (
            <text key={v}
              x={cx + 118 * Math.cos(rad)} y={cy + 118 * Math.sin(rad)}
              fill="rgba(255,255,255,0.3)" fontSize="11"
              textAnchor="middle" dominantBaseline="middle" fontFamily="monospace"
            >
              {v > 0 ? `+${v}` : v}
            </text>
          )
        })}
        <g transform={`rotate(${angle}, ${cx}, ${cy})`}>
          <line x1={cx} y1={cy} x2={cx} y2="70" stroke="#00e5ff" strokeWidth="2" strokeLinecap="round" />
          <circle cx={cx} cy={cy} r="5"  fill="#00e5ff" />
          <circle cx={cx} cy={cy} r="10" fill="none" stroke="#00e5ff" strokeWidth="1" strokeOpacity="0.4" />
        </g>
      </svg>
    </div>
  )
}

export default function TunerPage({ tuning, setTuning, activeString, setActiveString, data }) {
  const hasData = data && data.freq > 0
  const cents = hasData ? data.cents : 0
  const inTune = hasData ? data.inTune : false
  const centsColor = inTune ? "#00e5ff" : cents > 0 ? "#ff6b6b" : "#ffd700"
  const markerLeft = `${50 + (cents / 50) * 48}%`

  return (
    <div className="tuner">
      <div className="tuner__tuning-row">
        {["Standard", "Drop D", "Open G"].map(t => (
          <button
            key={t}
            className={`tuner__tuning-btn ${tuning === t ? "tuner__tuning-btn--active" : ""}`}
            onClick={() => setTuning(t)}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="tuner__dial-area">
        <TunerDial cents={cents} />

        <div className="tuner__note">
          {hasData ? (
            <>
              <div className={`tuner__note-name ${inTune ? "tuner__note-name--in-tune" : "tuner__note-name--out-of-tune"}`}>
                {data.note}{data.octave}
              </div>
              <div className="tuner__note-freq">{data.freq.toFixed(2)} Hz</div>
            </>
          ) : (
            <>
              <div className="tuner__note-name tuner__note-name--waiting">--</div>
              <div className="tuner__note-freq">Play a note to start</div>
            </>
          )}
        </div>

        <div className="tuner__cents-box">
          <div className="tuner__cents-row">
            <span className="tuner__cents-side-label">FLAT</span>
            <div className="tuner__cents-value-wrap">
              <div className="tuner__cents-value" style={{ color: hasData ? centsColor : "rgba(255,255,255,0.2)" }}>
                {hasData ? (cents > 0 ? `+${cents}` : cents) : "0"}
              </div>
              <div className="tuner__cents-label">CENTS</div>
            </div>
            <span className="tuner__cents-side-label">SHARP</span>
          </div>
          <div className="tuner__cents-bar">
            <div className="tuner__cents-bar-center" />
            {hasData && (
              <div
                className="tuner__cents-bar-marker"
                style={{
                  left: markerLeft,
                  background: centsColor,
                  boxShadow: `0 0 8px ${centsColor}`,
                }}
              />
            )}
          </div>
        </div>
      </div>

      <div className="tuner__strings">
        {STRINGS.map((s, i) => (
          <div key={i} className="tuner__string" onClick={() => setActiveString(i)}>
            <div className={`tuner__string-circle ${activeString === i ? "tuner__string-circle--active" : ""}`}>
              {s.note}
            </div>
            {activeString === i && <div className="tuner__string-dot" />}
            <div className="tuner__string-label">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="tuner__footer">
        <span className="tuner__footer-status">
          <span className="tuner__footer-dot">●</span> Playing in 440Hz standard tuning
        </span>
      </div>
    </div>
  )
}
