import { useAuth } from "../context/AuthContext";
import { useProfile } from "../context/ProfileContext";
import { fmt, netWorth, totalAssets, totalDebt } from "../types";

export default function DashboardPage() {
  const { user } = useAuth();
  const { profile, analysis, profileLoading } = useProfile();

  const firstName = user?.name?.split(" ")[0] ?? "there";
  const today = new Date().toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  const debtFreeMonths = analysis?.timeline?.find((p) => p.total_debt <= 0)?.month;
  const coachText =
    analysis?.next_actions?.[0]?.replace(/\*\*/g, "") ??
    analysis?.explanation?.slice(0, 280) ??
    "Add your assets and debts, then compute a plan on the Strategy page to see your personalized path.";

  if (profileLoading) {
    return <div className="page-loading">Loading your profile…</div>;
  }

  return (
    <div className="page dashboard-page">
      <header className="page-header">
        <p className="eyebrow">{today.toUpperCase()}</p>
        <h1 className="display-heading">Hello, {firstName}.</h1>
        <p className="lead compact">
          Here is the calmest, shortest path to becoming debt-free — recalculated every time you
          change anything.
        </p>
      </header>

      <div className="metric-row">
        <div className="metric-card">
          <span className="metric-label">Net worth</span>
          <span className="metric-value">{fmt(netWorth(profile))}</span>
          <span className="metric-sub">assets minus debts</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Total assets</span>
          <span className="metric-value">{fmt(totalAssets(profile))}</span>
          <span className="metric-sub">{profile.assets.length + 1} items</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Total debt</span>
          <span className="metric-value debt">{fmt(totalDebt(profile))}</span>
          <span className="metric-sub">{profile.loans.length} loans</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Debt-free in</span>
          <span className="metric-value accent">
            {debtFreeMonths != null ? `${Math.ceil(debtFreeMonths / 12)} yr` : "—"}
          </span>
          <span className="metric-sub">
            {analysis ? "based on best strategy" : "compute a plan to see"}
          </span>
        </div>
      </div>

      <section className="coach-card">
        <div className="coach-header">
          <span className="spark">✦</span>
          <span className="eyebrow">Your coach says</span>
        </div>
        <p className="coach-body">{coachText}</p>
        {analysis && (
          <div className="coach-meta">
            <span>Best: {analysis.best_strategy_name.replace(/_/g, " ")}</span>
            <span>Emergency fund: {fmt(analysis.emergency_fund_target)}</span>
          </div>
        )}
      </section>

      {analysis && (
        <section className="panel-grid">
          <div className="panel">
            <h3 className="panel-title">Next actions</h3>
            <ol className="actions-list">
              {analysis.next_actions.map((a, i) => (
                <li key={i}>{a.replace(/\*\*/g, "")}</li>
              ))}
            </ol>
          </div>
          <div className="panel">
            <h3 className="panel-title">Goal progress</h3>
            {analysis.goal_progress.length === 0 ? (
              <p className="muted">Add goals in Strategy to track progress.</p>
            ) : (
              analysis.goal_progress.map((g) => (
                <div key={g.name} className={`goal-row ${g.on_track ? "ok" : "warn"}`}>
                  <strong>{g.name}</strong>
                  <span>
                    {fmt(g.projected_amount)} / {fmt(g.target_amount)}
                  </span>
                </div>
              ))
            )}
          </div>
        </section>
      )}
    </div>
  );
}
