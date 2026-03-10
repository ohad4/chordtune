import { useState } from "react"
import Settings from "../Settings/Settings"
import "./TopBar.css"

export default function TopBar() {
  const [micOn, setMicOn] = useState(true)
  const [showSettings, setShowSettings] = useState(false)

  const toggleMic = async () => {
    try {
      const endpoint = micOn ? "http://localhost:5000/mic/off" : "http://localhost:5000/mic/on"
      await fetch(endpoint, { method: "POST" })
      setMicOn(!micOn)
    } catch (e) {
      console.error("לא ניתן להתחבר לשרת Python")
    }
  }

  return (
    <>
      <div className="topbar">
        <div className="topbar__right">
          <button
            className={`topbar__mic-btn ${micOn ? "topbar__mic-btn--on" : "topbar__mic-btn--off"}`}
            onClick={toggleMic}
          >
            {micOn ? "🎤 Microphone: ON" : "🔇 Microphone: OFF"}
          </button>
          <button className="topbar__icon-btn" onClick={() => setShowSettings(true)}>⚙</button>
        </div>
      </div>

      {showSettings && <Settings onClose={() => setShowSettings(false)} />}
    </>
  )
}
