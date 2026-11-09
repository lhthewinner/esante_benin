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

      {/* HEADER ÉPURÉ */}
      <header className="bg-slate-900/95 backdrop-blur border-b border-slate-800 px-6 py-3 flex items-center justify-between gap-4 shadow-md sticky top-0 z-50">
        
        {/* Branding Gauche */}
        <div className="flex items-center gap-3 shrink-0">
          <img
            src="/esblogo.jpeg"
            alt="E-Santé Bénin"
            className="w-9 h-9 object-cover rounded-full border border-emerald-500/40 shadow-sm shadow-emerald-900/30"
          />
          <div className="flex items-center gap-2.5">
            <h1 className="text-white font-bold text-base tracking-tight whitespace-nowrap">
              E-Santé Bénin
            </h1>
            <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded-md bg-emerald-950/70 border border-emerald-800/40 text-emerald-400 text-[10px] font-medium tracking-wide uppercase">
              Supervision Médicale
            </span>
          </div>
        </div>

        {/* Actions Droite */}
        <div className="flex items-center gap-2.5 shrink-0">
          
          {/* Lien Accéder au bot */}
          <a
            href="http://localhost:8000"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700/90 text-slate-300 hover:text-white border border-slate-700/80 text-xs px-3 py-1.5 rounded-lg transition whitespace-nowrap"
            title="Accéder au bot de consultation"
          >
            <span>Accéder au bot</span>
            <span className="text-slate-500 text-[10px]">↗</span>
          </a>

          {/* Bouton Actualiser */}
          <button
            onClick={chargerTout}
            className="inline-flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700/90 text-slate-300 hover:text-white border border-slate-700/80 text-xs px-3 py-1.5 rounded-lg transition cursor-pointer whitespace-nowrap shadow-sm"
            title="Rafraîchir les flux et alertes"
          >
            <span className="text-sm leading-none">↺</span>
            <span className="hidden sm:inline">Actualiser</span>
          </button>

          {/* Bouton Déconnexion */}
          <button
            onClick={handleLogout}
            className="inline-flex items-center bg-red-950/40 hover:bg-red-900/60 text-red-300 hover:text-red-200 border border-red-800/50 text-xs px-3 py-1.5 rounded-lg transition cursor-pointer whitespace-nowrap shadow-sm"
            title="Fermer la session de supervision"
          >
            Déconnexion
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
