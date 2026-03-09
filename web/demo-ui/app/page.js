"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SCENARIOS = [
  {
    label: "High-Value at Risk",
    data: { subscriber_id: "SUB-1001", tenure_months: 36, monthly_spend: 150, churn_risk: 0.9, current_plan: "Premium" },
  },
  {
    label: "New & Unhappy",
    data: { subscriber_id: "SUB-1002", tenure_months: 4, monthly_spend: 30, churn_risk: 0.85, current_plan: "Basic" },
  },
  {
    label: "Loyal Mid-Risk",
    data: { subscriber_id: "SUB-1003", tenure_months: 30, monthly_spend: 60, churn_risk: 0.6, current_plan: "Basic" },
  },
  {
    label: "Upsell Candidate",
    data: { subscriber_id: "SUB-1004", tenure_months: 12, monthly_spend: 75, churn_risk: 0.1, current_plan: "Basic" },
  },
];

const INITIAL_FORM = {
  subscriber_id: "",
  tenure_months: "",
  monthly_spend: "",
  churn_risk: "",
  current_plan: "",
};

export default function Home() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function loadScenario(scenario) {
    setForm({
      subscriber_id: scenario.data.subscriber_id,
      tenure_months: String(scenario.data.tenure_months),
      monthly_spend: String(scenario.data.monthly_spend),
      churn_risk: String(scenario.data.churn_risk),
      current_plan: scenario.data.current_plan,
    });
    setResult(null);
    setError(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);

    const payload = {
      subscriber_id: form.subscriber_id,
      tenure_months: parseInt(form.tenure_months, 10),
      monthly_spend: parseFloat(form.monthly_spend),
      churn_risk: parseFloat(form.churn_risk),
      current_plan: form.current_plan,
    };

    try {
      const res = await fetch(`${API_URL}/decide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        throw new Error(detail?.detail?.[0]?.msg || `Server error (${res.status})`);
      }

      setResult(await res.json());
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-wrapper">
      <h1 className="page-title">Subscriber Offer Decisioning</h1>
      <p className="page-subtitle">
        Enter subscriber attributes to receive a personalized offer recommendation.
      </p>

      {/* ── Input Card ────────────────────────────────── */}
      <div className="card">
        <h2 className="card-title">Subscriber Inputs</h2>

        <div className="scenario-row">
          {SCENARIOS.map((s) => (
            <button
              key={s.label}
              type="button"
              className="scenario-btn"
              onClick={() => loadScenario(s)}
            >
              {s.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label" htmlFor="subscriber_id">Subscriber ID</label>
              <input
                className="form-input"
                id="subscriber_id"
                name="subscriber_id"
                value={form.subscriber_id}
                onChange={handleChange}
                placeholder="e.g. SUB-1001"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="current_plan">Current Plan</label>
              <input
                className="form-input"
                id="current_plan"
                name="current_plan"
                value={form.current_plan}
                onChange={handleChange}
                placeholder="e.g. Basic, Premium"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="tenure_months">Tenure (months)</label>
              <input
                className="form-input"
                id="tenure_months"
                name="tenure_months"
                type="number"
                min="0"
                value={form.tenure_months}
                onChange={handleChange}
                placeholder="e.g. 24"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="monthly_spend">Avg Monthly Spend ($)</label>
              <input
                className="form-input"
                id="monthly_spend"
                name="monthly_spend"
                type="number"
                min="0"
                step="0.01"
                value={form.monthly_spend}
                onChange={handleChange}
                placeholder="e.g. 75.00"
                required
              />
            </div>

            <div className="form-group full-width">
              <label className="form-label" htmlFor="churn_risk">Churn Risk Score (0 – 1)</label>
              <input
                className="form-input"
                id="churn_risk"
                name="churn_risk"
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={form.churn_risk}
                onChange={handleChange}
                placeholder="e.g. 0.75"
                required
              />
            </div>
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Deciding…" : "Decide Offer"}
          </button>
        </form>
      </div>

      {/* ── Error ─────────────────────────────────────── */}
      {error && <div className="error-msg">{error}</div>}

      {/* ── Result Card ───────────────────────────────── */}
      {result && (
        <div className="card">
          <h2 className="card-title">Recommendation</h2>

          <div className="result-header">
            <span className="offer-name">{result.offer_name}</span>
            {result.discount_pct > 0 && (
              <span className="discount-badge">{result.discount_pct}% off</span>
            )}
          </div>

          {result.ai_explanation ? (
            <>
              <p className="explanation-text">{result.ai_explanation}</p>
              <p className="explanation-label">AI-enhanced</p>
              <details className="original-explanation">
                <summary>View original explanation</summary>
                <p className="explanation-text muted">{result.explanation}</p>
              </details>
            </>
          ) : (
            <p className="explanation-text">{result.explanation}</p>
          )}

          <span className="subscriber-id-label">
            Subscriber: {result.subscriber_id}
          </span>
        </div>
      )}
    </main>
  );
}
