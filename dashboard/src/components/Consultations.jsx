function UrgenceBadge({ niveau }) {
  const styles = {
    vert:   "bg-emerald-100 text-emerald-800",
    orange: "bg-amber-100 text-amber-800",
    rouge:  "bg-red-100 text-red-800",
  };
  const icons = { vert: "🟢", orange: "🟠", rouge: "🔴" };
  const n = niveau || "vert";
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${styles[n]}`}>
      {icons[n]} {n.charAt(0).toUpperCase() + n.slice(1)}
    </span>
  );
}

function formatDate(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric" })
    + " " + d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export default function Consultations({ consultations, filtre, setFiltre, onDetail, loading }) {
  const filtres = [
    { key: "tous",   label: "Tous" },
    { key: "vert",   label: "🟢 Vert" },
    { key: "orange", label: "🟠 Orange" },
    { key: "rouge",  label: "🔴 Rouge" },
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">

      {/* HEADER */}
      <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
        <h2 className="font-bold text-slate-800 flex items-center gap-2">
          📋 Consultations
          <span className="bg-slate-800 text-white text-xs px-2 py-0.5 rounded-full">
            {consultations.length}
          </span>
        </h2>
      </div>

      {/* FILTRES */}
      <div className="px-6 py-3 border-b border-slate-100 bg-slate-50 flex gap-2 flex-wrap">
        {filtres.map(f => (
          <button
            key={f.key}
            onClick={() => setFiltre(f.key)}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition
              ${filtre === f.key
                ? "bg-slate-800 text-white border-slate-800"
                : "bg-white text-slate-500 border-slate-200 hover:border-slate-400"
              }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* TABLE */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-slate-50 text-xs text-slate-400 uppercase tracking-wide">
              <th className="px-4 py-3 text-left font-semibold">Patient</th>
              <th className="px-4 py-3 text-left font-semibold">Symptômes</th>
              <th className="px-4 py-3 text-left font-semibold">Durée</th>
              <th className="px-4 py-3 text-left font-semibold">Ville</th>
              <th className="px-4 py-3 text-left font-semibold">Urgence</th>
              <th className="px-4 py-3 text-left font-semibold">Canal</th>
              <th className="px-4 py-3 text-left font-semibold">Date</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-slate-400">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-2 border-slate-200 border-t-blue-500 rounded-full animate-spin"></div>
                    Chargement...
                  </div>
                </td>
              </tr>
            ) : consultations.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-slate-400">
                  <div className="text-4xl mb-3">📭</div>
                  Aucune consultation
                </td>
              </tr>
            ) : (
              consultations.map(c => (
                <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-semibold text-slate-800 text-sm">{c.prenom || "Patient"}</div>
                    <div className="text-xs text-slate-400">
                      {c.age ? `${c.age} ans` : ""} {c.sexe ? `· ${c.sexe}` : ""}
                    </div>
                  </td>
                  <td className="px-4 py-3 max-w-[180px]">
                    <span className="text-sm text-slate-600 line-clamp-2">
                      {c.symptomes ? c.symptomes.substring(0, 50) + (c.symptomes.length > 50 ? "..." : "") : "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600 whitespace-nowrap">{c.duree || "—"}</td>
                  <td className="px-4 py-3 text-sm text-slate-600">{c.localisation || "—"}</td>
                  <td className="px-4 py-3"><UrgenceBadge niveau={c.niveau_urgence} /></td>
                  <td className="px-4 py-3">
                    <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                      {c.canal === "telegram" ? "📱 Telegram" : "🌐 Web"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap">{formatDate(c.timestamp)}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => onDetail(c)}
                      className="bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs px-3 py-1 rounded-lg transition font-medium"
                    >
                      Voir
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
