import { useState } from "react";
import { agentApi } from "../../services/api";
import type { ClientBrief } from "../../types/bond";

const defaultQuestion =
  "Assess liquidity, debt, refinancing, and interest-rate risks and identify the widest-spread selected bond.";

export function AgentPanel() {
  const [question, setQuestion] = useState(defaultQuestion);
  const [brief, setBrief] = useState<ClientBrief | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function runAnalysis() {
    setLoading(true);
    setError("");

    try {
      const response = await agentApi.post<ClientBrief>(
        "/analyze",
        {
          question,
          issuer: "Apple",
          instrument_ids: [1, 2, 3, 4, 5],
          maximum_evidence: 5,
        },
      );

      setBrief(response.data);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Analysis failed",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <aside className="agent-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Mercator Agent</span>
          <h2>Credit brief</h2>
        </div>
        <span className="status-dot">online</span>
      </div>

      <textarea
        value={question}
        onChange={(event) =>
          setQuestion(event.target.value)
        }
      />

      <button
        type="button"
        onClick={runAnalysis}
        disabled={loading}
      >
        {loading ? "Running analysis..." : "Analyze"}
      </button>

      {error && <p className="error-text">{error}</p>}

      {brief && (
        <div className="brief-output">
          <h3>{brief.issuer_name}</h3>
          <p>{brief.summary}</p>

          <h4>Market observations</h4>
          {brief.market_observations.map((item) => (
            <p key={item}>{item}</p>
          ))}

          <h4>Risks</h4>
          {brief.risks.length > 0 ? (
            brief.risks.map((item) => (
              <p key={item}>{item}</p>
            ))
          ) : (
            <p>No extracted risk flags.</p>
          )}

          <h4>Citations</h4>
          {brief.citations.map((citation) => (
            <p key={citation} className="citation">
              {citation}
            </p>
          ))}
        </div>
      )}
    </aside>
  );
}
