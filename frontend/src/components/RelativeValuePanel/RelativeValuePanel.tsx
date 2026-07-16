import { useQuery } from "@tanstack/react-query";
import { fetchRelativeValue } from "../../services/market";
import { useMarketStore } from "../../store/useMarketStore";

export function RelativeValuePanel() {
  const bonds = useMarketStore(
    (state) => state.bonds,
  );

  const instrumentIds = bonds
    .slice(0, 100)
    .map((bond) => bond.instrument_id);

  const {
    data,
    isLoading,
    isError,
  } = useQuery({
    queryKey: [
      "relative-value",
      instrumentIds.join(","),
    ],
    queryFn: () =>
      fetchRelativeValue(
        instrumentIds,
      ),
    enabled: instrumentIds.length >= 4,
    refetchInterval: 10_000,
  });

  return (
    <section className="relative-value-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">
            Relative value
          </span>
          <h2>Cheap and rich bonds</h2>
        </div>
      </div>

      {isLoading && (
        <p className="muted-text">
          Calculating peer-relative value...
        </p>
      )}

      {isError && (
        <p className="error-text">
          Relative-value analysis unavailable.
        </p>
      )}

      {data && (
        <>
          <div className="relative-value-metrics">
            <article>
              <span>Universe</span>
              <strong>
                {data.instrument_count}
              </strong>
            </article>

            <article>
              <span>Peer-ranked</span>
              <strong>
                {data.opportunity_count}
              </strong>
            </article>

            <article>
              <span>Average spread</span>
              <strong>
                {data.average_spread_bps.toFixed(
                  1,
                )}
                bp
              </strong>
            </article>

            <article>
              <span>Average duration</span>
              <strong>
                {data.average_duration.toFixed(
                  2,
                )}
              </strong>
            </article>
          </div>

          <div className="relative-value-list">
            {data.opportunities
              .slice(0, 15)
              .map((item) => (
                <div key={item.instrument_id}>
                  <span>
                    #{item.instrument_id}
                  </span>

                  <strong
                    className={
                      item.classification
                      === "CHEAP"
                        ? "positive-value"
                        : item.classification
                            === "RICH"
                          ? "negative-value"
                          : ""
                    }
                  >
                    {item.classification}
                  </strong>

                  <span>
                    {item.g_spread_bps.toFixed(
                      1,
                    )}
                    bp
                  </span>

                  <span>
                    {item.spread_difference_bps >= 0
                      ? "+"
                      : ""}
                    {item.spread_difference_bps.toFixed(
                      1,
                    )}
                    bp
                  </span>

                  <span>
                    z{" "}
                    {item.spread_z_score.toFixed(
                      2,
                    )}
                  </span>

                  <span>
                    {item.conviction_score.toFixed(
                      0,
                    )}
                    /100
                  </span>
                </div>
              ))}
          </div>
        </>
      )}
    </section>
  );
}
