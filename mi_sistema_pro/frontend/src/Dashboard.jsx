export default function JhonnyEliteDashboard() { const cards = [ { title: "Total partidos", value: 15 }, { title: "Señales publicables", value: 4 }, { title: "Señales observadas", value: 4 }, { title: "Hot matches", value: 4 }, { title: "Strict", value: 0 }, { title: "Flex", value: 4 }, ];

const signals = [ { partido: "Independiente Medellin vs America de Cali", market: "OVER_NEXT_15_DYNAMIC", confidence: 95, rank: "TOP", mode: "INTERNAL_FLEX", minute: 57, reason: "Presion ofensiva real por xG y tiros al arco", }, { partido: "Waterhouse vs Spanish Town", market: "OVER_NEXT_15_DYNAMIC", confidence: 95, rank: "TOP", mode: "INTERNAL_FLEX", minute: 82, reason: "Presion ofensiva fuerte", }, ];

return ( <div className="min-h-screen bg-slate-950 text-white p-6"> <div className="max-w-7xl mx-auto space-y-6"> <div className="flex items-center justify-between gap-4 flex-wrap"> <div> <h1 className="text-3xl font-bold tracking-tight">JHONNY_ELITE V17</h1> <p className="text-slate-400 mt-1">Panel visual de monitoreo de señales en vivo</p> </div> <div className="flex gap-3"> <button className="px-4 py-2 rounded-2xl bg-emerald-500 text-slate-950 font-semibold shadow-lg">Refrescar scan</button> <button className="px-4 py-2 rounded-2xl bg-slate-800 border border-slate-700">Limpiar cache</button> </div> </div>

<div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
      {cards.map((card) => (
        <div key={card.title} className="rounded-2xl bg-slate-900 border border-slate-800 p-5 shadow-lg">
          <div className="text-slate-400 text-sm">{card.title}</div>
          <div className="text-3xl font-bold mt-2">{card.value}</div>
        </div>
      ))}
    </div>

    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <div className="xl:col-span-2 rounded-2xl bg-slate-900 border border-slate-800 p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
          <h2 className="text-xl font-semibold">Señales activas</h2>
          <div className="flex gap-2 flex-wrap">
            <button className="px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-sm">Todas</button>
            <button className="px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-sm">Strict</button>
            <button className="px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-sm">Flex</button>
          </div>
        </div>

        <div className="space-y-4">
          {signals.map((signal, idx) => (
            <div key={idx} className="rounded-2xl bg-slate-950 border border-slate-800 p-4">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                  <div className="text-lg font-semibold">{signal.partido}</div>
                  <div className="text-slate-400 text-sm mt-1">{signal.market}</div>
                </div>
                <span className="px-3 py-1 rounded-full text-sm bg-amber-500/20 border border-amber-500/30">
                  {signal.rank}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-sm">
                <div className="rounded-xl bg-slate-900 p-3 border border-slate-800">
                  <div className="text-slate-400">Confidence</div>
                  <div className="text-xl font-bold mt-1">{signal.confidence}</div>
                </div>
                <div className="rounded-xl bg-slate-900 p-3 border border-slate-800">
                  <div className="text-slate-400">Modo</div>
                  <div className="text-base font-semibold mt-1">{signal.mode}</div>
                </div>
                <div className="rounded-xl bg-slate-900 p-3 border border-slate-800">
                  <div className="text-slate-400">Minuto</div>
                  <div className="text-xl font-bold mt-1">{signal.minute}</div>
                </div>
                <div className="rounded-xl bg-slate-900 p-3 border border-slate-800">
                  <div className="text-slate-400">Estado</div>
                  <div className="text-base font-semibold mt-1">APOSTAR_SUAVE</div>
                </div>
              </div>

              <div className="mt-4 text-sm text-slate-300">
                <span className="text-slate-400">Razón: </span>
                {signal.reason}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5 shadow-lg">
        <h2 className="text-xl font-semibold mb-4">Estado del sistema</h2>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between border-b border-slate-800 pb-2">
            <span className="text-slate-400">Sistema</span>
            <span>JHONNY_ELITE</span>
          </div>
          <div className="flex justify-between border-b border-slate-800 pb-2">
            <span className="text-slate-400">Versión</span>
            <span>V17</span>
          </div>
          <div className="flex justify-between border-b border-slate-800 pb-2">
            <span className="text-slate-400">Cache TTL</span>
            <span>20s</span>
          </div>
          <div className="flex justify-between border-b border-slate-800 pb-2">
            <span className="text-slate-400">Último scan</span>
            <span>Hace 5s</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Estado API</span>
            <span className="text-emerald-400 font-semibold">HEALTHY</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

); }
