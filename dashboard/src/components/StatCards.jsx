export default function StatCards({ stats, loading }) {
  const cards = [
    { label: "Total consultations", value: stats?.total, icon: "📋", sub: "depuis le début", color: "bg-blue-50 border-blue-100" },
    { label: "Aujourd'hui", value: stats?.aujourd_hui, icon: "🗓️", sub: "consultations", color: "bg-emerald-50 border-emerald-100" },
    { label: "Alertes non traitées", value: stats?.alertes_non_traitees, icon: "🔔", sub: "Orange + Rouge", color: "bg-orange-50 border-orange-100" },
    { label: "Cas verts", value: stats?.vert, icon: "🟢", sub: "non urgents", color: "bg-emerald-50 border-emerald-100" },
    { label: "Cas oranges", value: stats?.orange, icon: "🟠", sub: "sous 48h", color: "bg-amber-50 border-amber-100" },
    { label: "Cas rouges", value: stats?.rouge, icon: "🔴", sub: "urgents", color: "bg-red-50 border-red-100" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card, i) => (
        <div
          key={i}
          className={`${card.color} border rounded-2xl p-4 flex flex-col gap-2 hover:shadow-md transition-shadow`}
        >
          <div className="text-2xl">{card.icon}</div>
          <div>
            <div className="text-xs text-slate-500 font-medium">{card.label}</div>
            <div className="text-3xl font-bold text-slate-800 leading-none mt-1">
              {loading ? "—" : (card.value ?? 0)}
            </div>
            <div className="text-xs text-slate-400 mt-1">{card.sub}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
