import { useState, useEffect } from "react"
import Sidebar from "./components/Sidebar/Sidebar"
import TopBar from "./components/TopBar/TopBar"
import VolumeMeter from "./components/VolumeMeter/VolumeMeter"
import TunerPage from "./components/TunerPage/TunerPage"
import ChordPage from "./components/ChordPage/ChordPage"
import "./App.css"

export default function App() {
  const [page, setPage] = useState("tuner")
  const [tuning, setTuning] = useState("Standard")
  const [activeString, setActiveString] = useState(0)

  const [tunerData, setTunerData] = useState({
    note: null, octave: null, freq: 0, cents: 0, inTune: false,
  })
  const [chordData, setChordData] = useState({
    name: "--", root: "--", intervals: "--", accuracy: 0,
  })
  const [volume, setVolume] = useState(0)
  const [listening, setListening] = useState(false)

  // Connect to Python API
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch("http://localhost:5000/data")
        const data = await res.json()
        setTunerData(data.tuner)
        setChordData(data.chord)
        setVolume(data.volume)
        setListening(data.listening)
      } catch (e) {
        setListening(false)
      }
    }, 100)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app">
      <Sidebar
        page={page}
        setPage={setPage}
        chordName={chordData.name}
        onReset={() => {
          setTunerData({ note: null, octave: null, freq: 0, cents: 0, inTune: false })
          setChordData({ name: "--", root: "--", intervals: "--", accuracy: 0 })
          setVolume(0)
          setListening(false)
        }}
      />
      <div className="app__main">
        <TopBar />
        <VolumeMeter level={volume} listening={listening} />
        {page === "tuner" ? (
          <TunerPage
            tuning={tuning}
            setTuning={setTuning}
            activeString={activeString}
            setActiveString={setActiveString}
            data={tunerData}
          />
        ) : (
          <ChordPage chord={chordData} />
        )}
      </div>
    </div>
  )
}
