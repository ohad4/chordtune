import "./VolumeMeter.css"

export default function VolumeMeter({ level, listening }) {
  return (
    <div className="volume-meter">
      <span className="volume-meter__status">
        <span className={`volume-meter__dot ${listening ? "volume-meter__dot--active" : ""}`} />
        {listening ? "Listening..." : "Waiting..."}
      </span>

      <div className="volume-meter__bar-wrapper">
        <div className="volume-meter__bar-optimal" />
        <div className="volume-meter__bar-fill" style={{ width: `${level}%` }} />
      </div>

      <span className="volume-meter__value">
        {level > 0 ? `${level.toFixed(1)} dB` : "-- dB"}
      </span>

      <div className="volume-meter__labels">
        {["LOW", "OPTIMAL RANGE", "PEAK"].map(l => (
          <span key={l} className="volume-meter__zone-label">{l}</span>
        ))}
      </div>
    </div>
  )
}
