import "./Sidebar.css"

export default function Sidebar({ page, setPage, chordName, onReset }) {
  return (
    <div className="sidebar">
      <div className="sidebar__logo">
        <div className="sidebar__logo-icon">♪</div>
        <div className="sidebar__logo-text">ChordTune</div>
      </div>

      {[
        { id: "tuner", icon: "♬", label: "Tuner" },
        { id: "chord", icon: "⬡", label: "Chord Detector" },
      ].map(item => (
        <div
          key={item.id}
          className={`sidebar__nav-item ${page === item.id ? "sidebar__nav-item--active" : ""}`}
          onClick={() => setPage(item.id)}
        >
          <span className="sidebar__nav-icon">{item.icon}</span>
          {item.label}
        </div>
      ))}

      <div className="sidebar__currently-playing">
        <div className="sidebar__playing-label">CURRENTLY PLAYING</div>
        <div className="sidebar__playing-name">{chordName}</div>
        <button className="sidebar__reset-btn" onClick={onReset}>
          Reset Session
        </button>
      </div>
    </div>
  )
}
