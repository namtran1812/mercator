import { useQuery } from "@tanstack/react-query";
import { fetchReplayScenarios } from "../../services/market";

export function ReplayPanel() {
  const {
    data: scenarios = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["replay-scenarios"],
    queryFn: fetchReplayScenarios,
  });

  return (
    <section className="replay-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">
            Historical replay
          </span>
          <h2>Recorded curve sessions</h2>
        </div>
      </div>

      {isLoading && (
        <p className="muted-text">
          Loading replay sessions...
        </p>
      )}

      {isError && (
        <p className="error-text">
          Replay sessions are unavailable.
        </p>
      )}

      <div className="replay-list">
        {scenarios.map((scenario) => (
          <article key={scenario.scenario_name}>
            <div>
              <strong>
                {scenario.scenario_name}
              </strong>

              <span>
                {scenario.event_count} events
              </span>
            </div>

            <small>
              {new Date(
                scenario.first_event_time,
              ).toLocaleString()}
              {" — "}
              {new Date(
                scenario.last_event_time,
              ).toLocaleString()}
            </small>

            <code>
              python services/streaming-pricer/
              scripts/replay_curve_events.py
              {" --scenario-name "}
              {scenario.scenario_name}
              {" --speed 10"}
            </code>
          </article>
        ))}
      </div>
    </section>
  );
}
