import { useProfile } from "../context/ProfileContext";
import type { Asset } from "../types";
import { fmt, totalAssets } from "../types";

export default function AssetsPage() {
  const { profile, setProfile } = useProfile();

  function updateAsset(i: number, patch: Partial<Asset>) {
    setProfile((p) => ({
      ...p,
      assets: p.assets.map((a, idx) => (idx === i ? { ...a, ...patch } : a)),
    }));
  }

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Portfolio</p>
        <h1 className="display-heading">Assets</h1>
        <p className="lead compact">
          Everything you own that can grow or be sold. Liquid savings: {fmt(profile.savings)}.
        </p>
      </header>

      <div className="summary-bar">
        <span>Total portfolio value</span>
        <strong>{fmt(totalAssets(profile))}</strong>
      </div>

      <div className="panel">
        <h3 className="panel-title">Liquid savings</h3>
        <label>Cash / savings balance</label>
        <input
          type="number"
          value={profile.savings}
          onChange={(e) => setProfile((p) => ({ ...p, savings: +e.target.value }))}
        />
      </div>

      {profile.assets.map((asset, i) => (
        <div key={i} className="panel item-panel">
          <label>Asset type</label>
          <input value={asset.type} onChange={(e) => updateAsset(i, { type: e.target.value })} />
          <div className="row-2">
            <div>
              <label>Current value (₹)</label>
              <input
                type="number"
                value={asset.value}
                onChange={(e) => updateAsset(i, { value: +e.target.value })}
              />
            </div>
            <div>
              <label>Expected return % p.a.</label>
              <input
                type="number"
                value={asset.expected_return}
                onChange={(e) => updateAsset(i, { expected_return: +e.target.value })}
              />
            </div>
          </div>
          <button
            type="button"
            className="btn-ghost"
            onClick={() => setProfile((p) => ({ ...p, assets: p.assets.filter((_, j) => j !== i) }))}
          >
            Remove asset
          </button>
        </div>
      ))}

      <button
        type="button"
        className="btn-outline"
        onClick={() =>
          setProfile((p) => ({
            ...p,
            assets: [...p.assets, { type: "Mutual fund", value: 100000, expected_return: 10 }],
          }))
        }
      >
        + Add asset
      </button>
    </div>
  );
}
