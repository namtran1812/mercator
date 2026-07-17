import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchCarryRoll } from "../../services/market";
import { useMarketStore } from "../../store/useMarketStore";

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

export function CarryRollPanel() {
  const bonds = useMarketStore(
    (state) => state.bonds,
  );

  const [horizonMonths, setHorizonMonths] =
    useState(3);

  const instrumentIds = bonds
    .slice(0, 100)
    .map((bond) => bond.instrument_id);

  const {
    data,
    isLoading,
    isError,
  } = useQuery({
    queryKey: [
      "carry-roll",
      instrumentIds.join(","),
      horizonMonths,
    ],
    queryFn: () =>
      fetchCarryRoll(
        instrumentIds,
        horizonMonths,
      ),
    enabled: instrumentIds.length >= 2,
    refetchInterval: 15_000,
  });

  return (
    <section className="carry-roll-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">
            Forward return
          </span>
          <h2>Carry and roll-down</h2>
        </div>

        <select
          value={horizonMonths}
          onChange={(event) =>
            setHorizonMonths(
              Number(event.target.value),
            )
          }
        >
          <option value={1}>1 month</option>
          <option value={3}>3 months</option>
          <option value={6}>6 months</option>
          <option value={12}>12 months</option>
        </select>
      </div>

      {isLoading && (
        <p className="muted-text">
          Calculating expected returns...
        </p>
      )}

      {isError && (
        <p className="error-text">
          Carry and roll-down analysis unavailable.
        </p>
      )}

      {data && (
        <>
          <div className="carry-roll-metrics">
            <article>
              <span>Universe</span>
              <strong>
                {data.instrument_count}
              </strong>
            </article>

            <article>
              <span>Horizon</span>
              <strong>
                {data.horizon_months}M
              </strong>
            </article>

            <article>
              <span>Average return</span>
              <strong>
                {data.average_expected_return_percent.toFixed(
                  2,
                )}
                %
              </strong>
            </article>

            <article>
              <span>Top opportunity</span>
              <strong>
                {data.opportunities[0]
                  ? `#${data.opportunities[0].instrument_id}`
                  : "—"}
              </strong>
            </article>
          </div>

          <div className="carry-roll-list">
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
                      === "ATTRACTIVE"
                        ? "positive-value"
                        : item.classification
                            === "UNATTRACTIVE"
                          ? "negative-value"
                          : ""
                    }
                  >
                    {item.classification}
                  </strong>

                  <span>
                    {item.coupon_carry_return_percent.toFixed(
                      2,
                    )}
                    %
                  </span>

                  <span>
                    {item.treasury_roll_return_percent.toFixed(
                      2,
                    )}
                    %
                  </span>

                  <span>
                    {item.spread_normalization_return_percent.toFixed(
                      2,
                    )}
                    %
                  </span>

                  <strong>
                    {item.expected_total_return_percent.toFixed(
                      2,
                    )}
                    %
                  </strong>

                  <span>
                    {formatUsd(
                      item.expected_pnl_per_million,
                    )}
                  </span>
                </div>
              ))}
          </div>
        </>
      )}
    </section>
  );
}
