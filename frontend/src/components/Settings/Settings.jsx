import { useState, useEffect } from "react"
import "./Settings.css"

export default function Settings({ onClose }) {
  const [devices, setDevices] = useState([])
  const [selectedDevice, setSelectedDevice] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("http://localhost:5000/devices")
      .then(r => r.json())
      .then(data => {
        setDevices(data.devices)
        setSelectedDevice(data.current)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const selectDevice = async (index) => {
    setSelectedDevice(index)
    await fetch("http://localhost:5000/devices/select", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ index })
    })
  }

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-modal__header">
          <span className="settings-modal__title">⚙ הגדרות</span>
          <button className="settings-modal__close" onClick={onClose}>✕</button>
        </div>

        <div className="settings-modal__section">
          <div className="settings-modal__section-title">🎤 בחר מיקרופון</div>

          {loading ? (
            <div className="settings-modal__loading">טוען מיקרופונים...</div>
          ) : devices.length === 0 ? (
            <div className="settings-modal__loading">לא נמצאו מיקרופונים</div>
          ) : (
            <div className="settings-modal__devices">
              {devices.map(device => (
                <div
                  key={device.index}
                  className={`settings-modal__device ${selectedDevice === device.index ? "settings-modal__device--active" : ""}`}
                  onClick={() => selectDevice(device.index)}
                >
                  <div className="settings-modal__device-name">{device.name}</div>
                  {selectedDevice === device.index && (
                    <span className="settings-modal__device-check">✓</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
