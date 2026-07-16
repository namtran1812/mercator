import { useQuery } from "@tanstack/react-query";
import { fetchRfqAnalytics } from "../../services/rfq";

export function RfqAnalyticsPanel() {
  const {
    data,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["rfq-analytics"],
    queryFn: fetchRfqAnalytics,
    refetchInterval: 5_000,
  });

  return (
    <section className="rfq-analytics-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">
            Execution analytics
          </span>
          <h2>RFQ performance</h2>
        </div>
      </div>

      {isLoading && (
        <p className="muted-text">
          Loading RFQ analytics...
        </p>
      )}

      {isError && (
        <p className="error-text">
          RFQ analytics unavailable.
        </p>
      )}

      {data && (
        <>
          <div className="rfq-analytics-metrics">
            <article>
              <span>Execution rate</span>
              <strong>
                {(data.execution_rate * 100).toFixed(1)}%
              </strong>
            </article>

            <article>
              <span>Average latency</span>
              <strong>
                {data.average_dealer_latency_ms.toFixed(1)} ms
              </strong>
            </article>

            <article>
              <span>P95 latency</span>
              <strong>
                {data.p95_dealer_latency_ms.toFixed(1)} ms
              </strong>
            </article>

            <article>
              <span>Executed notional</span>
              <strong>
                ${(
                  data.executed_notional /
                  1_000_000
                ).toFixed(1)}
                MM
              </strong>
            </article>
          </div>

          <div className="dealer-analytics-list">
            {data.dealers.map((dealer) => (
              <div key={dealer.dealer}>
                <span>{dealer.dealer}</span>
                <span>
                  {(dealer.hit_ratio * 100).toFixed(1)}%
                </span>
                <span>
                  {dealer.average_latency_ms.toFixed(1)} ms
                </span>
                <strong>
                  {dealer.average_spread_bps.toFixed(2)} bp
                </strong>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
