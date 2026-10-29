function formatDate(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" })
    + " " + d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export default function Alertes({ alertes, onTraiter, loading }) {
  const nonTraitees = alertes.filter(a => !a.traitee);
  const traitees    = alertes.filter(a => a.traitee);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">

      {/* HEADER */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <h2 className="font-bold text-slate-800 flex items-center gap-2">
          🚨 Alertes
          {nonTraitees.length > 0 && (
            <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full animate-pulse">
              {nonTraitees.length}
            </span>
          )}
        </h2>
      </div>

      {/* LISTE */}
      <div className="divide-y divide-slate-100 max-h-[600px] overflow-y-auto">
        {loading ? (
          <div className="flex flex-col items-center gap-3 py-12 text-slate-400">
            <div className="w-8 h-8 border-2 border-slate-200 border-t-red-500 rounded-full animate-spin"></div>
            Chargement...
          </div>
        ) : alertes.length === 0 ? (
          <div className="py-12 text-center text-slate-400">
            <div className="text-4xl mb-3">✅</div>
            <div className="text-sm">Aucune alerte</div>
          </div>
        ) : (
          <>
            {/* Non traitées */}
            {nonTraitees.map(a => (
              <div
                key={a.id}
                className={`p-4 ${a.niveau_urgence === "rouge"
                  ? "bg-red-50 border-l-4 border-red-500"
                  : "bg-amber-50 border-l-4 border-amber-500"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="font-semibold text-slate-800 text-sm">
                    {a.niveau_urgence === "rouge" ? "🔴" : "🟠"} {a.prenom || "Patient"}
                  </div>
                  <div className="text-xs text-slate-400">{formatDate(a.timestamp)}</div>
                </div>

                <div className="text-xs text-slate-500 mb-1 line-clamp-2">
                  {a.symptomes ? a.symptomes.substring(0, 80) + "..." : "—"}
                </div>

                <div className="text-xs text-blue-600 mb-3 flex items-center gap-1">
                  🏥 {a.hopital || "Hôpital non précisé"}
                </div>

                <button
                  onClick={() => onTraiter(a.id)}
                  className={`w-full py-1.5 rounded-lg text-xs font-semibold transition
                    ${a.niveau_urgence === "rouge"
                      ? "bg-red-100 hover:bg-red-500 text-red-700 hover:text-white"
                      : "bg-amber-100 hover:bg-amber-500 text-amber-700 hover:text-white"
                    }`}
                >
                  ✓ Marquer comme traitée
                </button>
              </div>
            ))}

            {/* Traitées */}
            {traitees.map(a => (
              <div key={a.id} className="p-4 opacity-50">
                <div className="flex items-center justify-between mb-1">
                  <div className="font-semibold text-slate-600 text-sm">
                    {a.niveau_urgence === "rouge" ? "🔴" : "🟠"} {a.prenom || "Patient"}
                  </div>
                  <div className="text-xs text-slate-400">{formatDate(a.timestamp)}</div>
                </div>
                <div className="text-xs text-emerald-600 font-semibold">✅ Traitée</div>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
