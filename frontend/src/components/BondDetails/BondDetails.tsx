import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchPriceHistory } from "../../services/market";
import { useMarketStore } from "../../store/useMarketStore";

function formatTime(value: string) {
  return new Date(value).toLocaleTimeString();
}

export function BondDetails() {
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

  const {
    data: history = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: [
      "price-history",
      selectedBondId,
    ],
    queryFn: () =>
      fetchPriceHistory(
        selectedBondId as number,
        200,
      ),
    enabled: selectedBondId !== null,
    refetchInterval: 5_000,
  });

  if (!selectedBond) {
    return (
      <section className="details-panel empty-panel">
        Select a bond to inspect pricing history and provenance.
      </section>
    );
  }

  const chartData = [...history]
    .reverse()
    .map((point) => ({
      ...point,
      time: formatTime(point.event_time),
      yield_percent:
        point.yield_to_maturity * 100,
    }));

  const latest = history[0];

  return (
    <section className="details-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">
            Instrument details
          </span>
          <h2>
            Bond #{selectedBond.instrument_id}
          </h2>
        </div>

        <span>
          {selectedBond.quality_status}
        </span>
      </div>

      <div className="details-metrics">
        <article>
          <span>Clean price</span>
          <strong>
            {selectedBond.clean_price.toFixed(4)}
          </strong>
        </article>

        <article>
          <span>Yield</span>
          <strong>
            {(
              selectedBond.yield_to_maturity *
              100
            ).toFixed(3)}
            %
          </strong>
        </article>

        <article>
          <span>G-spread</span>
          <strong>
            {selectedBond.g_spread_bps.toFixed(2)}
            bp
          </strong>
        </article>

        <article>
          <span>Duration</span>
          <strong>
            {selectedBond.modified_duration.toFixed(3)}
          </strong>
        </article>
      </div>

      {isLoading && (
        <p className="muted-text">
          Loading history...
        </p>
      )}

      {isError && (
        <p className="error-text">
          Could not load price history.
        </p>
      )}

      {chartData.length > 0 && (
        <>
          <div className="chart-card">
            <div className="chart-heading">
              <span>Clean price history</span>
              <small>
                {chartData.length} observations
              </small>
            </div>

            <ResponsiveContainer
              width="100%"
              height={210}
            >
              <LineChart data={chartData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />
                <XAxis
                  dataKey="time"
                  minTickGap={30}
                />
                <YAxis
                  domain={["auto", "auto"]}
                  width={55}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="clean_price"
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <div className="chart-heading">
              <span>Spread history</span>
              <small>basis points</small>
            </div>

            <ResponsiveContainer
              width="100%"
              height={210}
            >
              <LineChart data={chartData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />
                <XAxis
                  dataKey="time"
                  minTickGap={30}
                />
                <YAxis
                  domain={["auto", "auto"]}
                  width={55}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="g_spread_bps"
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {latest && (
        <div className="provenance-card">
          <span className="eyebrow">
            Pricing provenance
          </span>

          <dl>
            <div>
              <dt>Curve version</dt>
              <dd>{latest.curve_version}</dd>
            </div>

            <div>
              <dt>Reference version</dt>
              <dd>{latest.reference_version}</dd>
            </div>

            <div>
              <dt>Model version</dt>
              <dd>{latest.model_version}</dd>
            </div>

            <div>
              <dt>Trace ID</dt>
              <dd>
                {latest.calculation_trace_id}
              </dd>
            </div>

            <div>
              <dt>Source event</dt>
              <dd>{latest.source_event_id}</dd>
            </div>

            <div>
              <dt>Quality score</dt>
              <dd>
                {latest.quality_score.toFixed(3)}
              </dd>
            </div>
          </dl>
        </div>
      )}
    </section>
  );
}
