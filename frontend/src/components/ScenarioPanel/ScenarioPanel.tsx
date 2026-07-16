import { useState } from "react";
import { runScenario } from "../../services/market";
import { useMarketStore } from "../../store/useMarketStore";
import type { ScenarioResponse } from "../../types/bond";

export function ScenarioPanel() {
  const bonds = useMarketStore((state) => state.bonds);

  const [treasuryShock, setTreasuryShock] =
    useState(50);

  const [spreadShock, setSpreadShock] =
    useState(0);

  const [faceValue, setFaceValue] =
    useState(1_000_000);

  const [result, setResult] =
    useState<ScenarioResponse | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function submitScenario() {
    setLoading(true);
    setError("");

    try {
      const response = await runScenario({
        instrument_ids: bonds
          .slice(0, 50)
          .map((bond) => bond.instrument_id),
        treasury_shock_bps: treasuryShock,
        credit_spread_shock_bps: spreadShock,
        position_face_value: faceValue,
      });

      setResult(response);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Scenario failed",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="scenario-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">
            Scenario engine
          </span>
          <h2>Rates and spread shocks</h2>
        </div>
      </div>

      <div className="scenario-inputs">
        <label>
          Treasury shock
          <input
            type="number"
            value={treasuryShock}
            onChange={(event) =>
              setTreasuryShock(
                Number(event.target.value),
              )
            }
          />
          <span>bp</span>
        </label>

        <label>
          Credit spread shock
          <input
            type="number"
            value={spreadShock}
            onChange={(event) =>
              setSpreadShock(
                Number(event.target.value),
              )
            }
          />
          <span>bp</span>
        </label>

        <label>
          Position face value
          <input
            type="number"
            value={faceValue}
            onChange={(event) =>
              setFaceValue(
                Number(event.target.value),
              )
            }
          />
          <span>USD</span>
        </label>
      </div>

      <button
        type="button"
        onClick={submitScenario}
        disabled={loading || bonds.length === 0}
      >
        {loading
          ? "Running scenario..."
          : "Run scenario"}
      </button>

      {error && (
        <p className="error-text">{error}</p>
      )}

      {result && (
        <div className="scenario-results">
          <article className="scenario-total">
            <span>Total estimated P&L</span>
            <strong>
              {result.total_estimated_pnl.toLocaleString(
                undefined,
                {
                  style: "currency",
                  currency: "USD",
                  maximumFractionDigits: 0,
                },
              )}
            </strong>
            <small>
              {result.instrument_count} instruments
            </small>
          </article>

          <div className="scenario-ranking">
            {result.results.slice(0, 10).map(
              (item) => (
                <div key={item.instrument_id}>
                  <span>
                    #{item.instrument_id}
                  </span>

                  <span>
                    {item.shocked_clean_price.toFixed(2)}
                  </span>

                  <strong
                    className={
                      item.estimated_pnl >= 0
                        ? "positive-value"
                        : "negative-value"
                    }
                  >
                    {item.estimated_pnl.toLocaleString(
                      undefined,
                      {
                        style: "currency",
                        currency: "USD",
                        maximumFractionDigits: 0,
                      },
                    )}
                  </strong>
                </div>
              ),
            )}
          </div>
        </div>
      )}
    </section>
  );
}
