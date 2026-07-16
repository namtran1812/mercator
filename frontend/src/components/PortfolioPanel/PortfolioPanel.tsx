import { useState } from "react";
import { fetchPortfolioRisk } from "../../services/market";
import { useMarketStore } from "../../store/useMarketStore";
import type { PortfolioRiskResponse } from "../../types/bond";

function formatUsd(value: number) {
  return value.toLocaleString(
    undefined,
    {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    },
  );
}

export function PortfolioPanel() {
  const bonds = useMarketStore(
    (state) => state.bonds,
  );

  const [faceValue, setFaceValue] =
    useState(1_000_000);

  const [result, setResult] =
    useState<PortfolioRiskResponse | null>(
      null,
    );

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function analyzePortfolio() {
    setLoading(true);
    setError("");

    try {
      const response = await fetchPortfolioRisk(
        bonds
          .slice(0, 25)
          .map((bond) => ({
            instrument_id:
              bond.instrument_id,
            face_value: faceValue,
          })),
      );

      setResult(response);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Portfolio analysis failed",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="portfolio-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">
            Portfolio analytics
          </span>
          <h2>Risk aggregation</h2>
        </div>
      </div>

      <label className="portfolio-input">
        Face value per instrument
        <input
          type="number"
          value={faceValue}
          onChange={(event) =>
            setFaceValue(
              Number(event.target.value),
            )
          }
        />
      </label>

      <button
        type="button"
        onClick={analyzePortfolio}
        disabled={
          loading || bonds.length === 0
        }
      >
        {loading
          ? "Calculating..."
          : "Analyze portfolio"}
      </button>

      {error && (
        <p className="error-text">{error}</p>
      )}

      {result && (
        <>
          <div className="portfolio-metrics">
            <article>
              <span>Market value</span>
              <strong>
                {formatUsd(
                  result.total_market_value,
                )}
              </strong>
            </article>

            <article>
              <span>Total DV01</span>
              <strong>
                {formatUsd(
                  result.total_dv01,
                )}
              </strong>
            </article>

            <article>
              <span>Duration</span>
              <strong>
                {result.weighted_modified_duration.toFixed(
                  3,
                )}
              </strong>
            </article>

            <article>
              <span>Spread</span>
              <strong>
                {result.weighted_g_spread_bps.toFixed(
                  2,
                )}
                bp
              </strong>
            </article>
          </div>

          <div className="portfolio-ranking">
            {result.positions
              .slice(0, 10)
              .map((position) => (
                <div
                  key={position.instrument_id}
                >
                  <span>
                    #{position.instrument_id}
                  </span>

                  <span>
                    {formatUsd(
                      position.market_value,
                    )}
                  </span>

                  <span>
                    {formatUsd(position.dv01)}
                  </span>

                  <strong>
                    {(
                      position.market_value_weight *
                      100
                    ).toFixed(1)}
                    %
                  </strong>
                </div>
              ))}
          </div>
        </>
      )}
    </section>
  );
}
