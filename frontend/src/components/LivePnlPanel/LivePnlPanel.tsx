import { useQuery } from "@tanstack/react-query";
import { fetchLiveAccountRisk } from "../../services/rfq";

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

export function LivePnlPanel() {
  const {
    data,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["live-account-risk"],
    queryFn: fetchLiveAccountRisk,
    refetchInterval: 2_000,
  });

  return (
    <section className="live-pnl-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">
            Live account risk
          </span>
          <h2>Portfolio P&amp;L</h2>
        </div>

        <span className="status-dot">
          2s refresh
        </span>
      </div>

      {isLoading && (
        <p className="muted-text">
          Loading live risk...
        </p>
      )}

      {isError && (
        <p className="error-text">
          Live account risk is unavailable.
        </p>
      )}

      {data && (
        <>
          <div className="live-pnl-total">
            <span>Total P&amp;L</span>

            <strong
              className={
                data.total_pnl >= 0
                  ? "positive-value"
                  : "negative-value"
              }
            >
              {formatUsd(data.total_pnl)}
            </strong>

            <small>
              NLV{" "}
              {formatUsd(
                data.net_liquidation_value,
              )}
            </small>
          </div>

          <div className="live-risk-metrics">
            <article>
              <span>Market value</span>
              <strong>
                {formatUsd(
                  data.total_market_value,
                )}
              </strong>
            </article>

            <article>
              <span>Unrealized</span>
              <strong>
                {formatUsd(
                  data.total_unrealized_pnl,
                )}
              </strong>
            </article>

            <article>
              <span>Realized</span>
              <strong>
                {formatUsd(
                  data.total_realized_pnl,
                )}
              </strong>
            </article>

            <article>
              <span>DV01</span>
              <strong>
                {formatUsd(
                  data.total_dv01,
                )}
              </strong>
            </article>
          </div>

          <div className="live-position-list">
            {data.positions.map(
              (position) => (
                <div
                  key={
                    position.instrument_id
                  }
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
                    {position.g_spread_bps.toFixed(
                      1,
                    )}
                    bp
                  </span>

                  <strong
                    className={
                      position.total_pnl >= 0
                        ? "positive-value"
                        : "negative-value"
                    }
                  >
                    {formatUsd(
                      position.total_pnl,
                    )}
                  </strong>
                </div>
              ),
            )}
          </div>
        </>
      )}
    </section>
  );
}
