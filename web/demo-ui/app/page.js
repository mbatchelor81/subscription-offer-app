"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PLAN_OPTIONS = ["Basic", "Standard", "Standard Plus", "Premium", "Premium Plus", "Unlimited"];

const SCENARIOS = [
  {
    label: "High-Value at Risk",
    data: { subscriber_id: "SUB-10421", tenure_months: "36", avg_monthly_spend: "120", churn_risk: "0.82", current_plan: "Premium" },
  },
  {
    label: "Budget Churner",
    data: { subscriber_id: "SUB-29087", tenure_months: "8", avg_monthly_spend: "35", churn_risk: "0.75", current_plan: "Basic" },
  },
  {
    label: "Loyal Low-Spender",
    data: { subscriber_id: "SUB-55310", tenure_months: "48", avg_monthly_spend: "30", churn_risk: "0.20", current_plan: "Standard" },
  },
  {
    label: "New Subscriber",
    data: { subscriber_id: "SUB-88214", tenure_months: "2", avg_monthly_spend: "55", churn_risk: "0.30", current_plan: "Basic" },
  },
  {
    label: "Stable Premium",
    data: { subscriber_id: "SUB-40072", tenure_months: "18", avg_monthly_spend: "95", churn_risk: "0.15", current_plan: "Unlimited" },
  },
];

const INITIAL = {
  subscriber_id: "",
  tenure_months: "",
  avg_monthly_spend: "",
  churn_risk: "",
  current_plan: "Basic",
};

export default function Home() {
  const [form, setForm] = useState(INITIAL);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showJson, setShowJson] = useState(false);

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const applyScenario = (scenario) => {
    setForm(scenario.data);
    setResult(null);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setShowJson(false);
    setLoading(true);

    try {
      const resp = await fetch(`${API_URL}/api/v1/offer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subscriber_id: form.subscriber_id,
          tenure_months: parseInt(form.tenure_months, 10),
          avg_monthly_spend: parseFloat(form.avg_monthly_spend),
          churn_risk: parseFloat(form.churn_risk),
          current_plan: form.current_plan,
        }),
      });

      if (!resp.ok) {
        const detail = await resp.json().catch(() => null);
        throw new Error(detail?.detail?.[0]?.msg || `Request failed (${resp.status})`);
      }

      setResult(await resp.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page">
      {/* ── Header ──────────────────────── */}
      <header className="page-header">
        <h1 className="page-title">Subscriber Offer Decisioning</h1>
        <p className="page-subtitle">
          Enter subscriber attributes to receive a personalized offer recommendation.
        </p>
      </header>

      {/* ── Scenario Quick-Fill ─────────── */}
      <div className="scenarios">
        {SCENARIOS.map((s) => (
          <button
            key={s.label}
            type="button"
            className="scenario-btn"
            onClick={() => applyScenario(s)}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* ── Input Form ─────────────────── */}
      <form className="card" onSubmit={handleSubmit}>
        <div className="card-title">Subscriber Attributes</div>
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label" htmlFor="subscriber_id">Subscriber ID</label>
            <input
              id="subscriber_id"
              className="form-input"
              required
              placeholder="e.g. SUB-42910"
              value={form.subscriber_id}
              onChange={set("subscriber_id")}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="tenure_months">Tenure (months)</label>
            <input
              id="tenure_months"
              className="form-input"
              type="number"
              required
              min="0"
              placeholder="e.g. 24"
              value={form.tenure_months}
              onChange={set("tenure_months")}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="avg_monthly_spend">Avg Monthly Spend ($)</label>
            <input
              id="avg_monthly_spend"
              className="form-input"
              type="number"
              required
              min="0"
              step="0.01"
              placeholder="e.g. 75.00"
              value={form.avg_monthly_spend}
              onChange={set("avg_monthly_spend")}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="churn_risk">Churn Risk (0 – 1)</label>
            <input
              id="churn_risk"
              className="form-input"
              type="number"
              required
              min="0"
              max="1"
              step="0.01"
              placeholder="e.g. 0.65"
              value={form.churn_risk}
              onChange={set("churn_risk")}
            />
          </div>

          <div className="form-group full-width">
            <label className="form-label" htmlFor="current_plan">Current Plan</label>
            <select
              id="current_plan"
              className="form-select"
              value={form.current_plan}
              onChange={set("current_plan")}
            >
              {PLAN_OPTIONS.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
        </div>

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? (
            <><span className="spinner" /> Evaluating…</>
          ) : (
            "Decide Offer"
          )}
        </button>
      </form>

      {/* ── Error ──────────────────────── */}
      {error && (
        <div className="error-banner">
          <svg className="error-icon" width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* ── Result Card ────────────────── */}
      {result && (
        <div className="result-card">
          {/* Header with offer name + discount badge */}
          <div className="result-header">
            <span className="result-offer-name">{result.recommended_offer}</span>
            {result.discount_pct > 0 && (
              <span className="discount-badge">{result.discount_pct}% off</span>
            )}
          </div>

          <div className="result-body">
            {/* Meta row */}
            <div className="result-meta">
              <div className="result-meta-item">
                <span className="result-meta-label">Subscriber</span>
                <span className="result-meta-value">{result.subscriber_id}</span>
              </div>
              <div className="result-meta-item">
                <span className="result-meta-label">Discount</span>
                <span className="result-meta-value">{result.discount_pct}%</span>
              </div>
            </div>

            {/* AI-enhanced explanation */}
            {result.ai_explanation && (
              <div className="explanation-section ai">
                <div className="explanation-label ai">
                  <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"/></svg>
                  AI-Enhanced Explanation
                </div>
                <p className="explanation-text">{result.ai_explanation}</p>
              </div>
            )}

            {/* Policy explanation */}
            <div className="explanation-section policy">
              <div className="explanation-label policy">Policy Explanation</div>
              <p className="explanation-text">{result.explanation}</p>
            </div>

            {/* Collapsible raw JSON */}
            <button
              type="button"
              className="json-toggle"
              onClick={() => setShowJson(!showJson)}
            >
              <span className={`json-toggle-arrow ${showJson ? "open" : ""}`}>&#9654;</span>
              Raw JSON Response
            </button>
            {showJson && (
              <pre className="json-block">{JSON.stringify(result, null, 2)}</pre>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
