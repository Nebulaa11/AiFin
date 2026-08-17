import { useProfile } from "../context/ProfileContext";
import type { Loan } from "../types";
import { fmt, totalDebt } from "../types";

export default function DebtsPage() {
  const { profile, setProfile } = useProfile();

  function updateLoan(i: number, patch: Partial<Loan>) {
    setProfile((p) => ({
      ...p,
      loans: p.loans.map((l, idx) => (idx === i ? { ...l, ...patch } : l)),
    }));
  }

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Liabilities</p>
        <h1 className="display-heading">Debts</h1>
        <p className="lead compact">Every loan you carry — ranked by interest so you know what to attack first.</p>
      </header>

      <div className="summary-bar">
        <span>Total outstanding</span>
        <strong className="debt">{fmt(totalDebt(profile))}</strong>
      </div>

      {[...profile.loans]
        .sort((a, b) => b.interest_rate - a.interest_rate)
        .map((loan) => {
          const i = profile.loans.indexOf(loan);
          return (
            <div key={i} className="panel item-panel">
              <div className="loan-badge">{(loan.interest_rate).toFixed(1)}% p.a.</div>
              <label>Loan name</label>
              <input value={loan.name} onChange={(e) => updateLoan(i, { name: e.target.value })} />
              <div className="row-3">
                <div>
                  <label>Principal (₹)</label>
                  <input
                    type="number"
                    value={loan.amount}
                    onChange={(e) => updateLoan(i, { amount: +e.target.value })}
                  />
                </div>
                <div>
                  <label>Rate %</label>
                  <input
                    type="number"
                    value={loan.interest_rate}
                    onChange={(e) => updateLoan(i, { interest_rate: +e.target.value })}
                  />
                </div>
                <div>
                  <label>EMI (₹)</label>
                  <input
                    type="number"
                    value={loan.emi}
                    onChange={(e) => updateLoan(i, { emi: +e.target.value })}
                  />
                </div>
              </div>
              {profile.loans.length > 1 && (
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={() => setProfile((p) => ({ ...p, loans: p.loans.filter((_, j) => j !== i) }))}
                >
                  Remove loan
                </button>
              )}
            </div>
          );
        })}

      <button
        type="button"
        className="btn-outline"
        onClick={() =>
          setProfile((p) => ({
            ...p,
            loans: [...p.loans, { name: "Personal loan", amount: 200000, interest_rate: 14, emi: 6500 }],
          }))
        }
      >
        + Add loan
      </button>
    </div>
  );
}
