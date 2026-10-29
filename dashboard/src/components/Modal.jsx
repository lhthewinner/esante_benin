function UrgenceBadge({ niveau }) {
  const styles = {
    vert:   "bg-emerald-100 text-emerald-800",
    orange: "bg-amber-100 text-amber-800",
    rouge:  "bg-red-100 text-red-800",
  };
  const icons = { vert: "🟢", orange: "🟠", rouge: "🔴" };
  const n = niveau || "vert";
  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-semibold ${styles[n]}`}>
      {icons[n]} {n.charAt(0).toUpperCase() + n.slice(1)}
    </span>
  );
}

function formatDate(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  return d.toLocaleDateString("fr-FR", {
    day: "2-digit", month: "long", year: "numeric",
    hour: "2-digit", minute: "2-digit"
  });
}

function Row({ label, value }) {
  return (
    <div className="flex gap-4 py-3 border-b border-slate-100 last:border-0">
      <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide w-28 flex-shrink-0 mt-0.5">
        {label}
      </div>
      <div className="text-sm text-slate-700 flex-1">{value || "—"}</div>
    </div>
  );
}

export default function Modal({ consultation: c, onClose }) {
  return (
    <div
      className="fixed inset-0 bg-slate-900/70 z-50 flex items-center justify-center p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto animate-in">

        {/* HEADER */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white rounded-t-2xl">
          <div>
            <h3 className="font-bold text-slate-800 text-lg">
              Consultation — {c.prenom || "Patient"}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">{formatDate(c.timestamp)}</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-red-100 hover:text-red-600 flex items-center justify-center transition text-slate-500"
          >
            ✕
          </button>
        </div>

        {/* CONTENU */}
        <div className="px-6 py-4">

          {/* Badge urgence */}
          <div className="mb-4">
            <UrgenceBadge niveau={c.niveau_urgence} />
          </div>

          <Row label="Patient"      value={`${c.prenom || "—"} · ${c.age ? c.age + " ans" : "—"} · ${c.sexe || "—"}`} />
          <Row label="Canal"        value={c.canal === "telegram" ? "📱 Telegram" : "🌐 Web"} />
          <Row label="Symptômes"    value={c.symptomes} />
          <Row label="Durée"        value={c.duree} />
          <Row label="Localisation" value={c.localisation} />
          <Row label="Hôpital"      value={c.hopital} />
          <Row label="Conseils"     value={c.conseils} />

          {/* Statut alerte */}
          <div className="mt-4 flex items-center gap-2">
            {c.alerte_traitee
              ? <span className="text-emerald-600 text-sm font-semibold">✅ Alerte traitée</span>
              : <span className="text-amber-600 text-sm font-semibold">⏳ En attente de traitement</span>
            }
          </div>
        </div>

        {/* FOOTER */}
        <div className="px-6 py-4 border-t border-slate-100">
          <button
            onClick={onClose}
            className="w-full bg-slate-800 hover:bg-slate-700 text-white py-2.5 rounded-xl text-sm font-semibold transition"
          >
            Fermer
          </button>
        </div>

      </div>
    </div>
  );
}
