import { useState } from "react";

import { queryAgent } from "../../services/agent";

import type {
  AgentQueryResponse,
} from "../../types/bond";

import { useMarketStore } from "../../store/useMarketStore";


const defaultQuestion =
  "Why did this bond move?";


export function AgentPanel() {
  const selectedBondId = useMarketStore(
    (state) => state.selectedBondId,
  );

  const bonds = useMarketStore(
    (state) => state.bonds,
  );

  const selectedBond = bonds.find(
    (bond) =>
      bond.instrument_id === selectedBondId,
  );

  const [question, setQuestion] =
    useState(defaultQuestion);

  const [result, setResult] =
    useState<AgentQueryResponse | null>(
      null,
    );

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function runAnalysis(
    overrideQuestion?: string,
  ) {
    if (selectedBondId === null) {
      setError(
        "Select a bond before running analysis.",
      );

      return;
    }

    const nextQuestion =
      overrideQuestion ?? question;

    if (overrideQuestion) {
      setQuestion(
        overrideQuestion,
      );
    }

    setLoading(true);
    setError("");

    try {
      const response = await queryAgent({
        question: nextQuestion,

        instrument_ids: [
          selectedBondId,
        ],

        maximum_evidence: 5,
      });

      setResult(response);
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


  const attribution =
    result?.price_attribution?.find(
      (item) =>
        item.instrument_id
        === selectedBondId,
    );

  const relativeValue =
    result?.relative_value?.find(
      (item) =>
        item.instrument_id
        === selectedBondId,
    );


  return (
    <aside className="agent-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">
            Mercator Intelligence
          </span>

          <h2>
            {selectedBond
              ? `Bond #${selectedBond.instrument_id}`
              : "Select a bond"}
          </h2>
        </div>

        <span className="status-dot">
          online
        </span>
      </div>


      {selectedBond && (
        <div className="agent-context">
          <span>
            Price{" "}
            {selectedBond.clean_price.toFixed(
              3,
            )}
          </span>

          <span>
            Yield{" "}
            {(
              selectedBond.yield_to_maturity
              * 100
            ).toFixed(2)}
            %
          </span>

          <span>
            Spread{" "}
            {selectedBond.g_spread_bps.toFixed(
              1,
            )}
            bp
          </span>
        </div>
      )}


      <div className="agent-quick-actions">
        <button
          type="button"
          disabled={
            loading
            || selectedBondId === null
          }
          onClick={() =>
            runAnalysis(
              "Why did this bond move?",
            )
          }
        >
          Explain move
        </button>

        <button
          type="button"
          disabled={
            loading
            || selectedBondId === null
          }
          onClick={() =>
            runAnalysis(
              "Is this bond rich or cheap versus peers?",
            )
          }
        >
          Relative value
        </button>

        <button
          type="button"
          disabled={
            loading
            || selectedBondId === null
          }
          onClick={() =>
            runAnalysis(
              "Assess this bond's risk.",
            )
          }
        >
          Risk
        </button>
      </div>


      <textarea
        value={question}
        onChange={(event) =>
          setQuestion(
            event.target.value,
          )
        }
        placeholder={
          selectedBondId === null
            ? "Select a bond first"
            : "Ask about the selected bond"
        }
        disabled={
          selectedBondId === null
        }
      />

      <button
        type="button"
        onClick={() =>
          runAnalysis()
        }
        disabled={
          loading
          || selectedBondId === null
        }
      >
        {loading
          ? "Running analysis..."
          : "Analyze selected bond"}
      </button>


      {error && (
        <p className="error-text">
          {error}
        </p>
      )}


      {relativeValue && (
        <section className="agent-analysis-card">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">
                Relative value
              </span>

              <h3>
                {relativeValue.classification}
              </h3>
            </div>

            <strong>
              {relativeValue.confidence}
            </strong>
          </div>

          <div className="agent-metric-grid">
            <div>
              <span>Spread</span>
              <strong>
                {relativeValue.spread_bps.toFixed(
                  1,
                )}
                bp
              </strong>
            </div>

            <div>
              <span>Peer median</span>
              <strong>
                {relativeValue.peer_median_spread_bps
                  ?.toFixed(1)
                  ?? "—"}
                bp
              </strong>
            </div>

            <div>
              <span>Difference</span>
              <strong>
                {relativeValue.spread_difference_bps
                  >= 0
                  ? "+"
                  : ""}
                {relativeValue.spread_difference_bps.toFixed(
                  1,
                )}
                bp
              </strong>
            </div>

            <div>
              <span>Z-score</span>
              <strong>
                {relativeValue.spread_z_score
                  ?.toFixed(2)
                  ?? "—"}
              </strong>
            </div>

            <div>
              <span>Peers</span>
              <strong>
                {relativeValue.peer_count}
              </strong>
            </div>

            <div>
              <span>Rating</span>
              <strong>
                {relativeValue.rating ?? "—"}
              </strong>
            </div>
          </div>

          <p>
            {relativeValue.interpretation}
          </p>
        </section>
      )}


      {attribution && (
        <section className="agent-analysis-card">
          <span className="eyebrow">
            Price attribution
          </span>

          <h3>
            {attribution.dependency_tenor
              ?? "Curve"}{" "}
            move
          </h3>

          <div className="agent-metric-grid">
            <div>
              <span>Rate shock</span>
              <strong>
                {attribution.rate_change_bps
                  === null
                  ? "—"
                  : `${attribution.rate_change_bps >= 0 ? "+" : ""}${attribution.rate_change_bps.toFixed(2)} bp`}
              </strong>
            </div>

            <div>
              <span>Observed ΔP</span>
              <strong>
                {attribution.observed_price_change
                  === null
                  ? "—"
                  : attribution.observed_price_change.toFixed(
                      4,
                    )}
              </strong>
            </div>

            <div>
              <span>Curve estimate</span>
              <strong>
                {attribution.estimated_curve_price_change
                  === null
                  ? "—"
                  : attribution.estimated_curve_price_change.toFixed(
                      4,
                    )}
              </strong>
            </div>

            <div>
              <span>Residual</span>
              <strong>
                {attribution.residual_price_change
                  === null
                  ? "—"
                  : attribution.residual_price_change.toFixed(
                      4,
                    )}
              </strong>
            </div>
          </div>

          <p>
            {attribution.explanation}
          </p>

          {attribution.source_event_id && (
            <small>
              Event{" "}
              {attribution.source_event_id}
              {" · "}
              curve v
              {attribution.curve_version}
            </small>
          )}
        </section>
      )}


      {result?.brief && (
        <div className="brief-output">
          <h3>
            {result.brief.issuer_name}
          </h3>

          <p>
            {result.brief.summary}
          </p>

          <h4>
            Market observations
          </h4>

          {result.brief.market_observations.map(
            (item) => (
              <p key={item}>
                {item}
              </p>
            ),
          )}

          <h4>
            Risks
          </h4>

          {result.brief.risks.length > 0
            ? result.brief.risks.map(
                (item) => (
                  <p key={item}>
                    {item}
                  </p>
                ),
              )
            : (
              <p>
                No extracted risk flags.
              </p>
            )}

          {result.brief.citations.length > 0 && (
            <>
              <h4>
                Citations
              </h4>

              {result.brief.citations.map(
                (citation) => (
                  <p
                    key={citation}
                    className="citation"
                  >
                    {citation}
                  </p>
                ),
              )}
            </>
          )}
        </div>
      )}


      {result?.errors
        && result.errors.length > 0 && (
          <div>
            {result.errors.map(
              (item) => (
                <p
                  key={item}
                  className="error-text"
                >
                  {item}
                </p>
              ),
            )}
          </div>
        )}
    </aside>
  );
}
