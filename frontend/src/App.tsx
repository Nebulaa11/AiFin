import { useState } from "react";
import { useAuth } from "./context/AuthContext";
import { ProfileProvider } from "./context/ProfileContext";
import Layout from "./components/Layout";
import ChatWidget from "./components/ChatWidget";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import AssetsPage from "./pages/AssetsPage";
import DebtsPage from "./pages/DebtsPage";
import StrategyPage from "./pages/StrategyPage";
import type { Tab } from "./types";

function AppShell() {
  const { user, loading } = useAuth();
  const [tab, setTab] = useState<Tab>("dashboard");

  if (loading) {
    return <div className="page-loading full">Loading…</div>;
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <ProfileProvider>
      <Layout active={tab} onNavigate={setTab}>
        {tab === "dashboard" && <DashboardPage />}
        {tab === "assets" && <AssetsPage />}
        {tab === "debts" && <DebtsPage />}
        {tab === "strategy" && <StrategyPage />}
      </Layout>
      <ChatWidget />
    </ProfileProvider>
  );
}

export default function App() {
  return <AppShell />;
}
