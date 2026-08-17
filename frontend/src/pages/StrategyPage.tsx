import { useMemo, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar, Line } from "react-chartjs-2";
import { api } from "../api/client";
import { useProfile } from "../context/ProfileContext";
import type { Goal } from "../types";

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

type StrategyMode = "avalanche" | "snowball" | "balanced";

const modeLabels: Record<StrategyMode, string> = {
  avalanche: "Avalanche",
  snowball: "Snowball",
  balanced: "Balanced",
};

const modeDesc: Record<StrategyMode, string> = {
  avalanche: "Pay highest interest rate first — saves the most money over time.",
  snowball: "Pay smallest balance first — builds momentum and quick wins.",
  balanced: "Split surplus between investing and debt reduction evenly.",
};

export default function StrategyPage() {
  const { profile, setProfile, analysis, runAnalyze, analyzing } = useProfile();
  const [mode, setMode] = useState<StrategyMode>("avalanche");
  const [extraPay, setExtraPay] = useState(0);
  const [whatIfTimeline, setWhatIfTimeline] = useState<typeof analysis extends null ? never : NonNullable<typeof analysis>["timeline"] | null>(null);

  const surplus = Math.max(0, profile.income_monthly - profile.expenses_monthly);

  const chartData = useMemo(() => {
    if (!analysis) return null;
    return {
      labels: analysis.strategies.map((s) => s.name.replace(/_/g, " ")),
      datasets: [
        {
          label: "Projected net worth",
          data: analysis.strategies.map((s) => Math.round(s.future_net_worth)),
          backgroundColor: "rgba(26, 26, 26, 0.75)",
          borderRadius: 8,
        },
      ],
    };
  }, [analysis]);

  const timelineData = useMemo(() => {
    const tl = whatIfTimeline ?? analysis?.timeline;
    if (!tl?.length) return null;
    return {
      labels: tl.map((p) => `${Math.round(p.month / 12)}y`),
      datasets: [
        {
          label: "Net worth",
          data: tl.map((p) => Math.round(p.net_worth)),
          borderColor: "#1a1a1a",
          backgroundColor: "rgba(26,26,26,0.06)",
          fill: true,
          tension: 0.35,
        },
        {
          label: "Debt",
          data: tl.map((p) => Math.round(p.total_debt)),
          borderColor: "#b45309",
          tension: 0.35,
        },
      ],
    };
  }, [analysis, whatIfTimeline]);

  function updateGoal(i: number, patch: Partial<Goal>) {
    setProfile((p) => ({
      ...p,
      financial_goals: p.financial_goals.map((g, idx) => (idx === i ? { ...g, ...patch } : g)),
    }));
  }

  async function computePlan() {
    await runAnalyze();
    setWhatIfTimeline(null);
  }

  async function runWhatIf() {
    const prepay = mode === "avalanche" ? extraPay : mode === "snowball" ? extraPay * 0.8 : extraPay * 0.5;
    const invest = mode === "balanced" ? (surplus - prepay) * 0.5 : surplus - prepay;
    const { data } = await api.post<{ timeline: NonNullable<typeof analysis>["timeline"] }>("/what-if", {
      profile,
      monthly_investment: Math.max(0, invest),
      loan_prepayment_monthly: prepay,
      lump_sum_prepayment: 0,
    });
    setWhatIfTimeline(data.timeline);
  }

  return (
    <div className="page strategy-page">
      <div className="strategy-grid">
        <div className="panel strategy-panel">
          <p className="eyebrow">Choose your approach</p>
          <h2 className="display-heading sm">Strategy</h2>

          <div className="segmented">
            {(Object.keys(modeLabels) as StrategyMode[]).map((m) => (
              <button
                key={m}
                type="button"
                className={mode === m ? "active" : ""}
                onClick={() => setMode(m)}
              >
                {modeLabels[m]}
              </button>
            ))}
          </div>
          <p className="muted">{modeDesc[mode]}</p>

          <div className="row-2">
            <div>
              <label>Age</label>
              <input
                type="number"
                value={profile.age}
                onChange={(e) => setProfile((p) => ({ ...p, age: +e.target.value }))}
              />
            </div>
            <div>
              <label>Dependents</label>
              <input
                type="number"
                value={profile.dependents}
                onChange={(e) => setProfile((p) => ({ ...p, dependents: +e.target.value }))}
              />
            </div>
          </div>
          <label>Monthly income (₹)</label>
          <input
            type="number"
            value={profile.income_monthly}
            onChange={(e) => setProfile((p) => ({ ...p, income_monthly: +e.target.value }))}
          />
          <label>Monthly expenses (₹)</label>
          <input
            type="number"
            value={profile.expenses_monthly}
            onChange={(e) => setProfile((p) => ({ ...p, expenses_monthly: +e.target.value }))}
          />
          <label>Risk tolerance</label>
          <select
            value={profile.risk_tolerance}
            onChange={(e) =>
              setProfile((p) => ({ ...p, risk_tolerance: e.target.value as typeof profile.risk_tolerance }))
            }
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>

          <label>Extra you can pay each month (₹)</label>
          <input
            type="number"
            value={extraPay}
            onChange={(e) => setExtraPay(+e.target.value)}
            max={surplus}
          />

          <h3 className="panel-title">Goals</h3>
          {profile.financial_goals.map((goal, i) => (
            <div key={i} className="goal-inline">
              <input value={goal.name} onChange={(e) => updateGoal(i, { name: e.target.value })} />
              <input
                type="number"
                value={goal.target_amount}
                onChange={(e) => updateGoal(i, { target_amount: +e.target.value })}
                placeholder="Target ₹"
              />
            </div>
          ))}

          <button type="button" className="btn-primary" onClick={computePlan} disabled={analyzing}>
            {analyzing ? "Computing…" : "✦ Compute my plan"}
          </button>
        </div>

        <div className="panel timeline-panel">
          <p className="eyebrow">Debt timeline</p>
          <h2 className="display-heading sm">Path to zero</h2>
          {analysis ? (
            <>
              <div className="timeline-badge">
                {analysis.timeline.find((p) => p.total_debt <= 0)
                  ? `${Math.ceil((analysis.timeline.find((p) => p.total_debt <= 0)!.month) / 12)} years`
                  : "10+ years"}
              </div>
              {timelineData && (
                <Line
                  data={timelineData}
                  options={{
                    responsive: true,
                    plugins: { legend: { position: "bottom", labels: { boxWidth: 12 } } },
                    scales: { y: { ticks: { callback: (v) => `₹${Number(v) / 100000}L` } } },
                  }}
                />
              )}
              {chartData && (
                <div className="chart-mini">
                  <Bar
                    data={chartData}
                    options={{
                      responsive: true,
                      plugins: { legend: { display: false } },
                    }}
                  />
                </div>
              )}
              <button type="button" className="btn-outline" onClick={runWhatIf}>
                Simulate with extra ₹{extraPay.toLocaleString("en-IN")}/mo
              </button>
              {analysis.debt_vs_invest && (
                <div className="advice-inline">
                  <strong>{analysis.debt_vs_invest.recommendation.replace(/_/g, " ")}</strong>
                  <p>{analysis.debt_vs_invest.rationale}</p>
                </div>
              )}
            </>
          ) : (
            <p className="empty-state">Add debts and compute a plan to see your timeline.</p>
          )}
        </div>
      </div>
    </div>
  );
}
