import { useState, useEffect, useCallback } from "react";
import StatCards from "./components/StatCards";
import Consultations from "./components/Consultations";
import Alertes from "./components/Alertes";
import Modal from "./components/Modal";
import Login from "./components/Login";

const API = "http://localhost:8000";

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("esante_token"));
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("esante_user") || "null");
    } catch {
      return null;
    }
  });

  const [stats, setStats] = useState(null);
  const [consultations, setConsultations] = useState([]);
  const [alertes, setAlertes] = useState([]);
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [filtre, setFiltre] = useState("tous");
  const [loading, setLoading] = useState(true);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("esante_token");
    localStorage.removeItem("esante_user");
    setToken(null);
    setUser(null);
  }, []);

  const chargerTout = useCallback(async () => {
    if (!token) return;

    try {
      const headers = { Authorization: `Bearer ${token}` };

      const [statsRes, consultRes, alertesRes] = await Promise.all([
        fetch(`${API}/stats`, { headers }),
        fetch(`${API}/consultations`, { headers }),
        fetch(`${API}/alertes`, { headers }),
      ]);

      // Si le jeton est expiré ou invalide (401), retour écran login
      if (statsRes.status === 401 || consultRes.status === 401 || alertesRes.status === 401) {
        handleLogout();
        return;
      }

      const statsData   = await statsRes.json();
      const consultData = await consultRes.json();
      const alertesData = await alertesRes.json();

      setStats(statsData);
      setConsultations(consultData.consultations || []);
      setAlertes(alertesData.alertes || []);
    } catch (e) {
      console.error("Erreur chargement données dashboard:", e);
    } finally {
      setLoading(false);
    }
  }, [token, handleLogout]);

  const traiterAlerte = async (id) => {
    try {
      const res = await fetch(`${API}/alertes/${id}/traiter`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.status === 401) {
        handleLogout();
        return;
      }
      await chargerTout();
    } catch (e) {
      console.error("Erreur traitement alerte:", e);
    }
  };

  useEffect(() => {
    if (token) {
      chargerTout();
      const interval = setInterval(chargerTout, 30000);
      return () => clearInterval(interval);
    }
  }, [token, chargerTout]);

  // Si non authentifié, afficher l'écran de connexion médical
  if (!token) {
    return (
      <Login
        onLoginSuccess={(newToken, newUser) => {
          setToken(newToken);
          setUser(newUser);
        }}
      />
    );
  }

  const consultationsFiltrees = filtre === "tous"
    ? consultations
    : consultations.filter(c => c.niveau_urgence === filtre);

  return (
    <div className="min-h-screen bg-slate-50">

      {/* HEADER */}
      <header className="bg-slate-900 px-8 py-4 flex items-center gap-4 shadow-lg sticky top-0 z-50">
        <img src="/esblogo.jpeg" alt="E-Santé Bénin" className="w-10 h-10 object-cover rounded-full" />
        <div>
          <h1 className="text-white font-bold text-lg font-serif">E-Santé Bénin</h1>
          <p className="text-slate-400 text-xs">Dashboard médical · Supervision des flux sanitaires</p>
        </div>

        <div className="ml-auto flex items-center gap-3">
          
          {/* Badge Médecin Connecté */}
          <div className="hidden sm:flex items-center gap-2 bg-slate-800/80 border border-slate-700 px-3 py-1.5 rounded-full text-xs text-slate-300">
            <span className="text-emerald-400">👨‍⚕️</span>
            <span>{user?.nom || "Personnel Médical"}</span>
            <span className="text-slate-500 font-mono text-[10px]">({user?.username || "admin"})</span>
          </div>

          <div className="flex items-center gap-2 bg-emerald-900/30 border border-emerald-700/40 px-3 py-1.5 rounded-full">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-emerald-400 text-xs font-medium">Session Active</span>
          </div>

          <a
            href="http://localhost:8000"
            target="_blank"
            rel="noopener"
            className="bg-slate-700 hover:bg-slate-600 text-white text-xs px-3 py-1.5 rounded-full transition"
          >
            🤖 Ouvrir le bot
          </a>

          <button
            onClick={chargerTout}
            className="bg-slate-700 hover:bg-slate-600 text-white text-xs px-3 py-1.5 rounded-full transition cursor-pointer"
            title="Rafraîchir les données"
          >
            ↺ Actualiser
          </button>

          {/* Bouton Déconnexion */}
          <button
            onClick={handleLogout}
            className="bg-red-950/60 hover:bg-red-900/80 text-red-300 border border-red-800/50 text-xs px-3 py-1.5 rounded-full transition cursor-pointer flex items-center gap-1"
            title="Fermer la session"
          >
            <span>Quitter</span>
            <span>🚪</span>
          </button>
        </div>
      </header>

      <div className="max-w-screen-xl mx-auto px-6 py-8">

        {/* STATS */}
        <StatCards stats={stats} loading={loading} />

        {/* GRILLE PRINCIPALE */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mt-8">

          {/* CONSULTATIONS */}
          <div className="xl:col-span-2">
            <Consultations
              consultations={consultationsFiltrees}
              filtre={filtre}
              setFiltre={setFiltre}
              onDetail={setSelectedConsultation}
              loading={loading}
            />
          </div>

          {/* ALERTES */}
          <div>
            <Alertes
              alertes={alertes}
              onTraiter={traiterAlerte}
              loading={loading}
            />
          </div>

        </div>
      </div>

      {/* MODAL */}
      {selectedConsultation && (
        <Modal
          consultation={selectedConsultation}
          onClose={() => setSelectedConsultation(null)}
        />
      )}

    </div>
  );
}
