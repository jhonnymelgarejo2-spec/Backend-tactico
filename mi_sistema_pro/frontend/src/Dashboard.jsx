import { useEffect, useState } from "react";

const API = "https://jhonny-elite-backend.onrender.com";

export default function JhonnyEliteDashboard() {
  const [data, setData] = useState(null);
  const [filter, setFilter] = useState("ALL");

  const fetchData = async () => {
    try {
      const res = await fetch(`${API}/dashboard-data`);
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error("Error cargando dashboard:", err);
    }
  };

  const refreshScan = async () => {
    await fetch(`${API}/scan/refresh`);
    fetchData();
  };

  const clearCache = async () => {
    await fetch(`${API}/scan/cache-clear`);
    fetchData();
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // auto refresh cada 10s
    return () => clearInterval(interval);
  }, []);

  if (!data) {
    return <div className="text-white p-10">Cargando...</div>;
  }

  const signals =
    filter === "STRICT"
      ? data.strict_signals
      : filter === "FLEX"
      ? data.flex_signals
      : [...data.strict_signals, ...data.flex_signals];

  const cards = [
    { title: "Total partidos", value: data.stats.total_matches },
    { title: "Señales publicables", value: data.stats.total_signals },
    { title: "Señales observadas", value: data.stats.observed_signals },
    { title: "Hot matches", value: data.stats.total_hot_matches },
    { title: "Strict", value: data.stats.strict_signals },
    { title: "Flex", value: data.stats.flex_signals },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* HEADER */}
        <div className="flex justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold">JHONNY_ELITE V17</h1>
            <p className="text-slate-400">Sistema de señales en vivo</p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={refreshScan}
              className="px-4 py-2 bg-emerald-500 text-black rounded-xl font-bold"
            >
              Refrescar
            </button>

            <button
              onClick={clearCache}
              className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl"
            >
              Limpiar cache
            </button>
          </div>
        </div>

        {/* CARDS */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {cards.map((c) => (
            <div key={c.title} className="bg-slate-900 p-4 rounded-xl">
              <div className="text-slate-400 text-sm">{c.title}</div>
              <div className="text-2xl font-bold">{c.value}</div>
            </div>
          ))}
        </div>

        {/* FILTROS */}
        <div className="flex gap-2">
          <button onClick={() => setFilter("ALL")} className="btn">Todas</button>
          <button onClick={() => setFilter("STRICT")} className="btn">Strict</button>
          <button onClick={() => setFilter("FLEX")} className="btn">Flex</button>
        </div>

        {/* SEÑALES */}
        <div className="space-y-4">
          {signals.length === 0 && (
            <div className="text-slate-400">No hay señales</div>
          )}

          {signals.map((s, i) => (
            <div key={i} className="bg-slate-900 p-4 rounded-xl">
              <div className="flex justify-between">
                <div>
                  <div className="font-bold">{s.partido}</div>
                  <div className="text-slate-400 text-sm">{s.market}</div>
                </div>

                <span className="bg-yellow-500/20 px-2 rounded">
                  {s.signal_rank}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3">
                <div>Conf: {s.confidence}</div>
                <div>Modo: {s.publication_mode}</div>
                <div>Min: {s.minute}</div>
                <div>{s.recomendacion_final}</div>
              </div>

              <div className="text-sm text-slate-400 mt-2">
                {s.reason}
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
         }
