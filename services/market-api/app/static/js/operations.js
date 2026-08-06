function renderMarketStreamStatus(payload) {
  updateFreshnessFromStreamStatus(
    payload,
  );

      const running =
        Boolean(payload.running);

      elements
        .streamStatusRunning
        .textContent =
          running
            ? "Running"
            : "Stopped";

      elements
        .streamStatusRunning
        .className =
          running
            ? "stream-running"
            : "stream-stopped";

      elements
        .streamStatusClients
        .textContent =
          Number(
            payload.client_count || 0,
          ).toLocaleString();

      elements
        .streamStatusInstruments
        .textContent =
          Number(
            payload.instrument_count || 0,
          ).toLocaleString();

      elements
        .streamStatusInterval
        .textContent =
          payload.interval_ms == null
            ? "—"
            : `${payload.interval_ms} ms`;

      elements
        .streamStatusSequence
        .textContent =
          Number(
            payload.sequence || 0,
          ).toLocaleString();
    }

    async function refreshMarketStreamStatus() {
      const payload = await request(
        "/stream/status",
      );

      renderMarketStreamStatus(
        payload,
      );

      return payload;
    }

    async function startMarketStream() {
      const instrumentIds =
        parseInstrumentIds();

      if (instrumentIds.length < 1) {
        throw new Error(
          "Starting the market stream requires at least one instrument ID.",
        );
      }

      const intervalMs = Number(
        elements.streamIntervalMs.value,
      );

      const volatilityBps = Number(
        elements.streamVolatilityBps.value,
      );

      if (
        !Number.isInteger(intervalMs)
        || intervalMs < 100
        || intervalMs > 60000
      ) {
        throw new Error(
          "Stream interval must be between 100 and 60000 ms.",
        );
      }

      if (
        !Number.isFinite(volatilityBps)
        || volatilityBps < 0
        || volatilityBps > 100
      ) {
        throw new Error(
          "Stream volatility must be between 0 and 100 bp.",
        );
      }

      elements
        .startMarketStreamButton
        .disabled = true;

      elements
        .startMarketStreamButton
        .textContent =
          "Starting...";

      try {
        const payload = await request(
          "/stream/start",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              instrument_ids:
                instrumentIds,
              interval_ms:
                intervalMs,
              volatility_bps:
                volatilityBps,
            }),
          },
        );

        renderMarketStreamStatus(
          payload,
        );

        log(
          `Market stream started: `
          + `${payload.instrument_count} instruments, `
          + `${payload.interval_ms} ms interval`,
        );
      } finally {
        elements
          .startMarketStreamButton
          .disabled = false;

        elements
          .startMarketStreamButton
          .textContent =
            "Start Stream";
      }
    }

    async function stopMarketStream() {
      elements
        .stopMarketStreamButton
        .disabled = true;

      elements
        .stopMarketStreamButton
        .textContent =
          "Stopping...";

      try {
        const payload = await request(
          "/stream/stop",
          {
            method: "POST",
          },
        );

        renderMarketStreamStatus(
          payload,
        );

        log(
          "Market stream stopped.",
        );
      } finally {
        elements
          .stopMarketStreamButton
          .disabled = false;

        elements
          .stopMarketStreamButton
          .textContent =
            "Stop Stream";
      }
    }

    function formatReplayDuration(
      firstEventTime,
      lastEventTime,
    ) {
      const first =
        new Date(firstEventTime);

      const last =
        new Date(lastEventTime);

      if (
        Number.isNaN(first.getTime())
        || Number.isNaN(last.getTime())
      ) {
        return "—";
      }

      const seconds =
        Math.max(
          0,
          (
            last.getTime()
            - first.getTime()
          ) / 1000,
        );

      if (seconds < 60) {
        return `${seconds.toFixed(1)} sec`;
      }

      if (seconds < 3600) {
        return `${(seconds / 60).toFixed(1)} min`;
      }

      return `${(seconds / 3600).toFixed(2)} hr`;
    }

    async function loadReplayScenarios() {
      elements
        .loadReplayScenariosButton
        .disabled = true;

      elements
        .loadReplayScenariosButton
        .textContent =
          "Loading...";

      try {
        const payload = await request(
          "/replay/scenarios",
        );

        const scenarios =
          Array.isArray(payload)
            ? payload
            : [];

        if (scenarios.length === 0) {
          elements
            .replayScenarioRows
            .innerHTML = `
              <tr>
                <td colspan="5" class="empty">
                  No replay scenarios are currently available.
                </td>
              </tr>
            `;

          return;
        }

        elements
          .replayScenarioRows
          .innerHTML =
            scenarios
              .sort(
                (left, right) =>
                  Number(
                    right.event_count || 0,
                  )
                  - Number(
                    left.event_count || 0,
                  ),
              )
              .map((scenario) => `
                <tr>
                  <td>
                    ${scenario.scenario_name}
                  </td>

                  <td>
                    ${Number(
                      scenario.event_count || 0,
                    ).toLocaleString()}
                  </td>

                  <td>
                    ${formatPriceHistoryTime(
                      scenario.first_event_time,
                    )}
                  </td>

                  <td>
                    ${formatPriceHistoryTime(
                      scenario.last_event_time,
                    )}
                  </td>

                  <td>
                    ${formatReplayDuration(
                      scenario.first_event_time,
                      scenario.last_event_time,
                    )}
                  </td>
                </tr>
              `)
              .join("");

        log(
          `Loaded ${scenarios.length} replay scenarios.`,
        );
      } finally {
        elements
          .loadReplayScenariosButton
          .disabled = false;

        elements
          .loadReplayScenariosButton
          .textContent =
            "Load Replay Scenarios";
      }
    }
