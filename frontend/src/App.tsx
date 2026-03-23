import { useMemo, useState } from "react";
import axios from "axios";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import "./App.css";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

type Loan = { name: string; amount: number; interest_rate: number; emi: number };

type AnalyzeResponse = {
  emergency_fund_target: number;
  recommended_monthly_investment: number;
  best_loan_repayment_order: string[];
  projected_net_worth_best: number;
  strategies: {
    name: string;
    description: string;
    future_net_worth: number;
    risk_score: number;
    cash_flow_stability: number;
    composite_score: number;
    monthly_investment_suggested: number;
    loan_prepayment_monthly: number;
  }[];
  best_strategy_name: string;
  explanation: string;
  engine_summary: {
    monthly_surplus: number;
    months_of_expenses_in_savings: number;
    total_assets: number;
  };
};

const defaultLoan: Loan = { name: "car loan", amount: 500000, interest_rate: 10, emi: 12000 };

export default function App() {
  const [age, setAge] = useState(28);
  const [income, setIncome] = useState(80000);
  const [expenses, setExpenses] = useState(40000);
  const [savings, setSavings] = useState(200000);
  const [risk, setRisk] = useState<"low" | "medium" | "high">("medium");
  const [loans, setLoans] = useState<Loan[]>([defaultLoan]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  const chartData = useMemo(() => {
    if (!result) return null;
    return {
      labels: result.strategies.map((s) => s.name.replace(/_/g, " ")),
      datasets: [
        {
          label: "Projected net worth (model)",
          data: result.strategies.map((s) => Math.round(s.future_net_worth)),
          backgroundColor: "rgba(14, 165, 233, 0.65)",
        },
      ],
    };
  }, [result]);

  async function runAnalyze() {
    setLoading(true);
    setError(null);
    try {
      const { data } = await axios.post<AnalyzeResponse>("/api/v1/analyze", {
        age,
        income_monthly: income,
        expenses_monthly: expenses,
        savings,
        loans,
        assets: [],
        risk_tolerance: risk,
        financial_goals: [],
      });
      setResult(data);
    } catch (e: unknown) {
      if (axios.isAxiosError(e)) {
        setError(String(e.response?.data?.detail ?? e.message));
      } else {
        setError("Request failed");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="hero">
        <h1>AiFin — AI Personal Finance Optimizer</h1>
        <p>
          Enter your profile to get strategy simulations, ranked recommendations, and an explanation
          layer (LLM when configured on the server).
        </p>
      </header>

      <div className="grid">
        <section className="card">
          <h2>Your profile</h2>
          <label>Age</label>
          <input type="number" value={age} onChange={(e) => setAge(+e.target.value)} min={18} />

          <label>Monthly income</label>
          <input type="number" value={income} onChange={(e) => setIncome(+e.target.value)} />

          <label>Monthly expenses</label>
          <input type="number" value={expenses} onChange={(e) => setExpenses(+e.target.value)} />

          <label>Savings / liquid</label>
          <input type="number" value={savings} onChange={(e) => setSavings(+e.target.value)} />

          <label>Risk tolerance</label>
          <select value={risk} onChange={(e) => setRisk(e.target.value as typeof risk)}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>

          <p className="small">Loan (single row for this MVP).</p>
          <label>Loan name</label>
          <input
            value={loans[0]?.name ?? ""}
            onChange={(e) =>
              setLoans((prev) => [{ ...prev[0], name: e.target.value }, ...prev.slice(1)])
            }
          />
          <div className="loan-row">
            <div>
              <label>Principal</label>
              <input
                type="number"
                value={loans[0]?.amount ?? 0}
                onChange={(e) =>
                  setLoans((prev) => [{ ...prev[0], amount: +e.target.value }, ...prev.slice(1)])
                }
              />
            </div>
            <div>
              <label>Rate % p.a.</label>
              <input
                type="number"
                value={loans[0]?.interest_rate ?? 0}
                onChange={(e) =>
                  setLoans((prev) => [{ ...prev[0], interest_rate: +e.target.value }, ...prev.slice(1)])
                }
              />
            </div>
          </div>
          <label>EMI</label>
          <input
            type="number"
            value={loans[0]?.emi ?? 0}
            onChange={(e) =>
              setLoans((prev) => [{ ...prev[0], emi: +e.target.value }, ...prev.slice(1)])
            }
          />

          <button type="button" onClick={runAnalyze} disabled={loading}>
            {loading ? "Analyzing…" : "Run optimizer"}
          </button>
          {error && <div className="error">{String(error)}</div>}
        </section>

        <section className="card">
          <h2>Results</h2>
          {!result && <p className="small">Submit the form to see projections and advice.</p>}
          {result && (
            <>
              <div className="metrics">
                <div className="metric">
                  <strong>Best strategy</strong>
                  <span>{result.best_strategy_name.replace(/_/g, " ")}</span>
                </div>
                <div className="metric">
                  <strong>Emergency fund target (6 mo)</strong>
                  <span>₹ {result.emergency_fund_target.toLocaleString("en-IN")}</span>
                </div>
                <div className="metric">
                  <strong>Recommended monthly investment</strong>
                  <span>₹ {result.recommended_monthly_investment.toLocaleString("en-IN")}</span>
                </div>
                <div className="metric">
                  <strong>Projected net worth (best)</strong>
                  <span>₹ {result.projected_net_worth_best.toLocaleString("en-IN")}</span>
                </div>
                <div className="metric">
                  <strong>Loan payoff order</strong>
                  <span>{result.best_loan_repayment_order.join(" → ") || "—"}</span>
                </div>
              </div>
              {chartData && (
                <div style={{ marginTop: "1rem" }}>
                  <Bar
                    data={chartData}
                    options={{
                      responsive: true,
                      plugins: { legend: { display: false } },
                      scales: { x: { ticks: { maxRotation: 45, minRotation: 0 } } },
                    }}
                  />
                </div>
              )}
              <h3 style={{ marginTop: "1.25rem", fontSize: "1rem" }}>Advisor narrative</h3>
              <div className="explain">{result.explanation}</div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
