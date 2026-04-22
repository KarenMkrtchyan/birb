import { useState, useEffect, useRef } from "react";

const POLL_INTERVAL = 1000;

const MOCK_DETECTIONS = [
  { species: "American Robin", species_confidence: 0.94, timestamp: new Date(Date.now() - 60000).toISOString() },
  { species: "Blue Jay", species_confidence: 0.88, timestamp: new Date(Date.now() - 180000).toISOString() },
  { species: "House Sparrow", species_confidence: 0.76, timestamp: new Date(Date.now() - 360000).toISOString() },
  { species: "Northern Cardinal", species_confidence: 0.91, timestamp: new Date(Date.now() - 600000).toISOString() },
];

function timeAgo(isoString) {
  const diff = Math.floor((Date.now() - new Date(isoString)) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export default function BirdWatchDashboard() {
  const [detections, setDetections] = useState(MOCK_DETECTIONS);
  const [status, setStatus] = useState("connected");
  const [useMock, setUseMock] = useState(true);
  const [flaskUrl, setFlaskUrl] = useState("http://localhost:5000");
  const intervalRef = useRef(null);

  const latest = detections[0];
  const uniqueSpecies = new Set(detections.map((d) => d.species)).size;

  const speciesCount = detections.reduce((acc, d) => {
    acc[d.species] = (acc[d.species] || 0) + 1;
    return acc;
  }, {});
  const topSpecies = Object.entries(speciesCount).sort((a, b) => b[1] - a[1]).slice(0, 4);

  useEffect(() => {
    if (useMock) {
      clearInterval(intervalRef.current);
      return;
    }
    intervalRef.current = setInterval(async () => {
      setStatus("polling");
      try {
        const res = await fetch(`${flaskUrl}/poll`);
        const data = await res.json();
        if (data.status === "new") {
          setDetections((prev) => [data.detection, ...prev].slice(0, 50));
          setStatus("connected");
        } else {
          setStatus("empty");
        }
      } catch {
        setStatus("error");
      }
    }, POLL_INTERVAL);
    return () => clearInterval(intervalRef.current);
  }, [useMock, flaskUrl]);

  const statusDot = {
    connected: "bg-emerald-500",
    polling: "bg-amber-400 animate-pulse",
    empty: "bg-stone-400",
    error: "bg-red-500",
  }[status];

  return (
    <div className="min-h-screen" style={{ background: "#fdf8f3", fontFamily: "'Georgia', serif" }}>
      <div className="max-w-3xl mx-auto px-6 py-12">

        {/* Header */}
        <div className="flex items-center justify-between mb-10">
          <div>
            <h1 className="text-3xl font-bold text-stone-800" style={{ letterSpacing: "-0.02em" }}>
              🪶 BirdWatch
            </h1>
            <p className="text-stone-400 text-sm mt-0.5">Real-time bird detection</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${statusDot}`} />
            <span className="text-stone-400 text-xs font-mono capitalize">{status}</span>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: "Sightings", value: detections.length },
            { label: "Species", value: uniqueSpecies },
            { label: "Latest", value: latest?.species?.split(" ").slice(-1)[0] ?? "—" },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-2xl p-5 text-center" style={{ background: "#f5ede0" }}>
              <p className="text-2xl font-bold text-stone-700">{value}</p>
              <p className="text-xs text-stone-400 mt-0.5 uppercase tracking-wider">{label}</p>
            </div>
          ))}
        </div>

        {/* Latest detection */}
        {latest && (
          <div className="rounded-2xl overflow-hidden mb-8" style={{ background: "#f5ede0" }}>
            {latest.image ? (
              <img
                src={`data:image/jpeg;base64,${latest.image}`}
                alt={latest.species}
                className="w-full h-56 object-cover"
              />
            ) : (
              <div className="w-full h-56 flex items-center justify-center" style={{ background: "#ece0d0" }}>
                <span className="text-7xl opacity-40">🐦</span>
              </div>
            )}
            <div className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xl font-bold text-stone-800">{latest.species}</p>
                  <p className="text-stone-400 text-sm mt-0.5">
                    {Math.round((latest.species_confidence ?? latest.confidence) * 100)}% confidence
                    · {timeAgo(latest.timestamp)}
                  </p>
                </div>
                <span className="text-xs font-semibold uppercase tracking-widest text-amber-700 bg-amber-100 px-3 py-1 rounded-full">
                  Latest
                </span>
              </div>

              {/* confidence bar */}
              <div className="mt-4 h-1.5 rounded-full bg-stone-200">
                <div
                  className="h-1.5 rounded-full bg-amber-500 transition-all duration-700"
                  style={{ width: `${Math.round((latest.species_confidence ?? latest.confidence) * 100)}%` }}
                />
              </div>

              {/* top 3 alternatives */}
              {latest.top_3 && (
                <div className="mt-4 space-y-2">
                  <p className="text-xs uppercase tracking-wider text-stone-400">Other possibilities</p>
                  {latest.top_3.map((r, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-stone-300 text-xs w-3">{i + 1}</span>
                      <span className="text-stone-600 text-sm flex-1">{r.species}</span>
                      <span className="text-stone-400 text-xs font-mono">{Math.round(r.score * 100)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Top species */}
        <div className="mb-8">
          <p className="text-xs uppercase tracking-wider text-stone-400 mb-3">Top Species</p>
          <div className="space-y-2">
            {topSpecies.map(([name, count]) => (
              <div key={name} className="flex items-center gap-4 rounded-xl px-4 py-3" style={{ background: "#f5ede0" }}>
                <span className="text-stone-700 text-sm flex-1">{name}</span>
                <span className="text-amber-700 text-sm font-mono font-semibold">×{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Sighting history */}
        <div className="mb-10">
          <p className="text-xs uppercase tracking-wider text-stone-400 mb-3">Recent Sightings</p>
          <div className="divide-y" style={{ borderColor: "#ece0d0" }}>
            {detections.map((d, i) => (
              <div key={i} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-stone-700 text-sm font-medium">{d.species}</p>
                  <p className="text-stone-400 text-xs mt-0.5">
                    {Math.round((d.species_confidence ?? d.confidence) * 100)}% match
                  </p>
                </div>
                <span className="text-stone-400 text-xs font-mono">{timeAgo(d.timestamp)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Config */}
        <div className="rounded-2xl p-5 space-y-3" style={{ background: "#f5ede0" }}>
          <p className="text-xs uppercase tracking-wider text-stone-400">Connection</p>
          <div className="flex items-center gap-3">
            <input
              value={flaskUrl}
              onChange={(e) => setFlaskUrl(e.target.value)}
              disabled={useMock}
              className="flex-1 text-xs px-3 py-2 rounded-lg bg-white border border-stone-200 text-stone-600 font-mono focus:outline-none focus:border-amber-400"
              placeholder="http://localhost:5000"
            />
            <button
              onClick={() => setUseMock((v) => !v)}
              className="text-xs px-4 py-2 rounded-lg font-medium transition-colors"
              style={{
                background: useMock ? "#d97706" : "#e7ddd3",
                color: useMock ? "white" : "#57534e",
              }}
            >
              {useMock ? "Go Live" : "Use Mock"}
            </button>
          </div>
        </div>

        <p className="text-center text-stone-300 text-xs font-mono mt-8">
          BirdWatch · EE250 · polling every {POLL_INTERVAL / 1000}s
        </p>

      </div>
    </div>
  );
}