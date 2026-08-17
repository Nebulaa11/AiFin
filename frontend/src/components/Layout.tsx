import { useAuth } from "../context/AuthContext";
import type { Tab } from "../types";

const tabs: { id: Tab; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "assets", label: "Assets" },
  { id: "debts", label: "Debts" },
  { id: "strategy", label: "Strategy" },
];

type Props = {
  active: Tab;
  onNavigate: (tab: Tab) => void;
  children: React.ReactNode;
};

export default function Layout({ active, onNavigate, children }: Props) {
  const { user, logout } = useAuth();

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden />
          <span className="brand-name">AiFin</span>
        </div>
        <nav className="nav-pills">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              className={`nav-pill ${active === t.id ? "active" : ""}`}
              onClick={() => onNavigate(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
        <div className="topbar-user">
          {user?.picture_url && (
            <img src={user.picture_url} alt="" className="avatar" referrerPolicy="no-referrer" />
          )}
          <button type="button" className="icon-btn" onClick={logout} title="Sign out">
            ↗
          </button>
        </div>
      </header>
      <main className="main-content">{children}</main>
      <footer className="footer">© {new Date().getFullYear()} AiFin · Built with care.</footer>
    </div>
  );
}
