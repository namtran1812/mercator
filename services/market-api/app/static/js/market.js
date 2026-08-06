function relativeValueClassificationClass(value) {
      const classification = String(value || "")
        .trim()
        .toLowerCase();

      if (classification.includes("cheap")) {
        return "cheap";
      }

      if (classification.includes("rich")) {
        return "rich";
      }

      return "fair";
    }

    function signedNumber(value, digits = 2) {
      const numericValue = Number(value || 0);
      const sign = numericValue > 0 ? "+" : "";

      return `${sign}${number(numericValue, digits)}`;
    }

    function renderRelativeValueResult(payload) {
      const opportunities = payload.opportunities || [];

      elements.relativeValueInstrumentCount.textContent =
        Number(payload.instrument_count || 0)
          .toLocaleString();

      elements.relativeValueOpportunityCount.textContent =
        Number(payload.opportunity_count || opportunities.length)
          .toLocaleString();

      elements.relativeValueAverageSpread.textContent =
        `${number(payload.average_spread_bps, 2)} bp`;

      elements.relativeValueAverageDuration.textContent =
        number(payload.average_duration, 3);

      if (opportunities.length === 0) {
        elements.relativeValueRows.innerHTML = `
          <tr>
            <td colspan="11" class="empty">
              No relative-value opportunities were returned.
            </td>
          </tr>
        `;

        return;
      }

      const sortedOpportunities = [...opportunities].sort(
        (left, right) =>
          Number(right.conviction_score || 0)
          - Number(left.conviction_score || 0),
      );

      elements.relativeValueRows.innerHTML =
        sortedOpportunities
          .map((opportunity) => {
            const classification =
              String(opportunity.classification || "Fair");

            const classificationClass =
              relativeValueClassificationClass(
                classification,
              );

            const spreadDifference =
              Number(opportunity.spread_difference_bps || 0);

            const zScore =
              Number(opportunity.spread_z_score || 0);

            const spreadClass =
              spreadDifference > 0
                ? "relative-value-positive"
                : spreadDifference < 0
                  ? "relative-value-negative"
                  : "";

            const zScoreClass =
              zScore > 0
                ? "relative-value-positive"
                : zScore < 0
                  ? "relative-value-negative"
                  : "";

            return `
              <tr>
                <td>#${instrumentLinkHtml(opportunity.instrument_id)}</td>

                <td>
                  ${number(opportunity.clean_price, 4)}
                </td>

                <td>
                  ${percent(opportunity.yield_to_maturity)}
                </td>

                <td>
                  ${number(opportunity.g_spread_bps, 2)} bp
                </td>

                <td>
                  ${number(opportunity.modified_duration, 3)}
                </td>

                <td>
                  ${Number(opportunity.peer_count || 0)
                    .toLocaleString()}
                </td>

                <td>
                  ${number(
                    opportunity.peer_average_spread_bps,
                    2,
                  )} bp
                </td>

                <td class="${spreadClass}">
                  ${signedNumber(
                    opportunity.spread_difference_bps,
                    2,
                  )} bp
                </td>

                <td class="${zScoreClass}">
                  ${signedNumber(
                    opportunity.spread_z_score,
                    3,
                  )}
                </td>

                <td>
                  <span
                    class="
                      relative-value-classification
                      ${classificationClass}
                    "
                  >
                    ${classification}
                  </span>
                </td>

                <td class="relative-value-conviction">
                  ${number(
                    opportunity.conviction_score,
                    4,
                  )}
                </td>
              </tr>
            `;
          })
          .join("");
    }

    async function runRelativeValueScreen() {
      const instrumentIds = parseInstrumentIds();

      if (instrumentIds.length < 2) {
        throw new Error(
          "Relative value analysis requires at least two instrument IDs.",
        );
      }

      const durationBucketWidth = Number(
        elements.relativeValueBucketWidth.value,
      );

      const minimumPeerCount = Number(
        elements.relativeValueMinimumPeers.value,
      );

      if (
        !Number.isFinite(durationBucketWidth)
        || durationBucketWidth <= 0
        || durationBucketWidth > 10
      ) {
        throw new Error(
          "Duration bucket width must be greater than zero and no more than 10.",
        );
      }

      if (
        !Number.isInteger(minimumPeerCount)
        || minimumPeerCount < 2
        || minimumPeerCount > 100
      ) {
        throw new Error(
          "Minimum peer count must be an integer between 2 and 100.",
        );
      }

      elements.runRelativeValueButton.disabled = true;
      elements.runRelativeValueButton.textContent =
        "Screening...";

      try {
        const payload = await request(
          "/relative-value/rank",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              instrument_ids: instrumentIds,
              duration_bucket_width:
                durationBucketWidth,
              minimum_peer_count:
                minimumPeerCount,
            }),
          },
        );

        renderRelativeValueResult(payload);

        log(
          `Relative value screen completed: `
          + `${payload.instrument_count} instruments, `
          + `${payload.opportunity_count} opportunities, `
          + `average spread `
          + `${number(payload.average_spread_bps, 2)} bp`,
        );
      } finally {
        elements.runRelativeValueButton.disabled = false;
        elements.runRelativeValueButton.textContent =
          "Run Relative Value Screen";
      }
    }


    const priceHistoryMetricDefinitions = {
      clean_price: {
        label: "Clean Price",
        formatter: (value) =>
          number(value, 4),
      },
      yield_to_maturity: {
        label: "Yield to Maturity",
        formatter: (value) =>
          percent(value),
      },
      g_spread_bps: {
        label: "G-Spread",
        formatter: (value) =>
          `${number(value, 2)} bp`,
      },
      modified_duration: {
        label: "Modified Duration",
        formatter: (value) =>
          number(value, 4),
      },
      convexity: {
        label: "Convexity",
        formatter: (value) =>
          number(value, 4),
      },
      quality_score: {
        label: "Quality Score",
        formatter: (value) =>
          number(value, 4),
      },
    };

    function formatPriceHistoryTime(value) {
      const date = new Date(value);

      if (Number.isNaN(date.getTime())) {
        return String(value || "—");
      }

      return date.toLocaleString();
    }

    function renderPriceHistoryChart() {
      const metric =
        elements.priceHistoryMetric.value;

      const definition =
        priceHistoryMetricDefinitions[metric];

      elements.priceHistoryChartTitle.textContent =
        definition.label;

      const values = currentPriceHistory
        .map((point) => ({
          value: Number(point[metric]),
          eventTime: point.event_time,
        }))
        .filter((point) =>
          Number.isFinite(point.value)
        );

      if (values.length === 0) {
        elements.priceHistoryChartRange.textContent =
          "No data";

        elements.priceHistoryChart.innerHTML = `
          <div class="price-history-empty">
            No valid observations were returned.
          </div>
        `;

        return;
      }

      const width = 1000;
      const height = 260;
      const left = 70;
      const right = 24;
      const top = 18;
      const bottom = 38;

      const chartWidth =
        width - left - right;

      const chartHeight =
        height - top - bottom;

      const minimum = Math.min(
        ...values.map((item) => item.value),
      );

      const maximum = Math.max(
        ...values.map((item) => item.value),
      );

      const rawRange = maximum - minimum;

      const padding =
        rawRange === 0
          ? Math.max(
              Math.abs(maximum) * 0.01,
              1,
            )
          : rawRange * 0.08;

      const chartMinimum =
        minimum - padding;

      const chartMaximum =
        maximum + padding;

      const chartRange =
        chartMaximum - chartMinimum;

      const xForIndex = (index) =>
        values.length === 1
          ? left + chartWidth / 2
          : left
            + (
              index
              / (values.length - 1)
            ) * chartWidth;

      const yForValue = (value) =>
        top
        + (
          1
          - (
            value - chartMinimum
          ) / chartRange
        ) * chartHeight;

      const points = values
        .map(
          (point, index) =>
            `${xForIndex(index)},`
            + `${yForValue(point.value)}`,
        )
        .join(" ");

      const gridLines = Array.from(
        { length: 5 },
        (_, index) => {
          const fraction = index / 4;

          const y =
            top
            + fraction * chartHeight;

          const value =
            chartMaximum
            - fraction * chartRange;

          return `
            <line
              class="price-history-chart-grid"
              x1="${left}"
              y1="${y}"
              x2="${left + chartWidth}"
              y2="${y}"
            />

            <text
              class="price-history-chart-label"
              x="${left - 10}"
              y="${y + 3}"
              text-anchor="end"
            >
              ${definition.formatter(value)}
            </text>
          `;
        },
      ).join("");

      const baseline =
        top + chartHeight;

      const areaPoints =
        `${left},${baseline} `
        + `${points} `
        + `${left + chartWidth},${baseline}`;

      elements.priceHistoryChartRange.textContent =
        `${definition.formatter(minimum)} – `
        + `${definition.formatter(maximum)}`;

      elements.priceHistoryChart.innerHTML = `
        <svg
          viewBox="0 0 ${width} ${height}"
          preserveAspectRatio="none"
        >
          ${gridLines}

          <polygon
            class="price-history-chart-area"
            points="${areaPoints}"
          />

          <polyline
            class="price-history-chart-line"
            points="${points}"
          />
        </svg>
      `;
    }

    function renderPriceHistory(payload) {
      currentPriceHistory =
        Array.isArray(payload)
          ? [...payload].sort(
              (left, right) =>
                new Date(
                  left.event_time,
                ).getTime()
                - new Date(
                  right.event_time,
                ).getTime(),
            )
          : [];

      elements
        .priceHistoryObservationCount
        .textContent =
          currentPriceHistory.length
            .toLocaleString();

      if (currentPriceHistory.length === 0) {
        elements.priceHistoryRows.innerHTML = `
          <tr>
            <td colspan="12" class="empty">
              No price history was returned.
            </td>
          </tr>
        `;

        renderPriceHistoryChart();

        return;
      }

      const latest =
        currentPriceHistory[
          currentPriceHistory.length - 1
        ];

      elements.priceHistoryLatestPrice.textContent =
        number(latest.clean_price, 4);

      elements.priceHistoryLatestYield.textContent =
        percent(latest.yield_to_maturity);

      elements.priceHistoryLatestSpread.textContent =
        `${number(
          latest.g_spread_bps,
          2,
        )} bp`;

      elements.priceHistoryLatestDuration.textContent =
        number(
          latest.modified_duration,
          4,
        );

      elements.priceHistoryLatestQuality.textContent =
        `${number(
          latest.quality_score,
          4,
        )} (${latest.quality_status})`;

      elements.priceHistoryCurveVersion.textContent =
        String(latest.curve_version);

      elements.priceHistoryModelVersion.textContent =
        String(latest.model_version);

      elements.priceHistoryRows.innerHTML =
        [...currentPriceHistory]
          .reverse()
          .map((point) => `
            <tr>
              <td>
                ${formatPriceHistoryTime(
                  point.event_time,
                )}
              </td>

              <td>
                ${number(
                  point.clean_price,
                  4,
                )}
              </td>

              <td>
                ${number(
                  point.dirty_price,
                  4,
                )}
              </td>

              <td>
                ${percent(
                  point.yield_to_maturity,
                )}
              </td>

              <td>
                ${number(
                  point.g_spread_bps,
                  2,
                )} bp
              </td>

              <td>
                ${number(
                  point.modified_duration,
                  4,
                )}
              </td>

              <td>
                ${number(
                  point.convexity,
                  4,
                )}
              </td>

              <td>
                ${number(
                  point.quality_score,
                  4,
                )}
              </td>

              <td>
                <span class="price-history-status">
                  ${point.quality_status}
                </span>
              </td>

              <td>
                ${point.curve_version}
              </td>

              <td>
                ${point.reference_version}
              </td>

              <td>
                ${point.model_version}
              </td>
            </tr>
          `)
          .join("");

      renderPriceHistoryChart();
    }

    async function runPriceHistory() {

  
      const instrumentId = Number(
        elements
          .priceHistoryInstrumentId
          .value,
      );

      const limit = Number(
        elements.priceHistoryLimit.value,
      );

      if (
        !Number.isInteger(instrumentId)
        || instrumentId < 1
      ) {
        throw new Error(
          "Instrument ID must be a positive integer.",
        );
      }

      if (
        !Number.isInteger(limit)
        || limit < 1
        || limit > 5000
      ) {
        throw new Error(
          "History limit must be between 1 and 5000.",
        );
      }

      elements
        .runPriceHistoryButton
        .disabled = true;

      elements
        .runPriceHistoryButton
        .textContent = "Loading...";

      try {
        const payload = await request(
          `/prices/${instrumentId}/history`
          + `?limit=${limit}`,
        );

        renderPriceHistory(payload);

        markResultFresh(
          "priceHistory",
        );

        log(
          `Loaded ${payload.length} `
          + `price-history observations `
          + `for instrument ${instrumentId}`,
        );
      } finally {
        elements
          .runPriceHistoryButton
          .disabled = false;

        elements
          .runPriceHistoryButton
          .textContent =
            "Load Price History";
      }
    }



    function carryRollValueClass(value) {
      const numeric = Number(value || 0);

      if (numeric > 0) {
        return "carry-roll-positive";
      }

      if (numeric < 0) {
        return "carry-roll-negative";
      }

      return "";
    }

    function carryRollClassificationClass(value) {
      return String(value || "")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9_-]+/g, "-");
    }

    function renderCarryRoll(payload) {
  markResultFresh(
    "carryRoll",
  );

      const opportunities =
        payload.opportunities || [];

      elements
        .carryRollInstrumentCount
        .textContent =
          Number(
            payload.instrument_count || 0,
          ).toLocaleString();

      elements
        .carryRollHorizonResult
        .textContent =
          `${payload.horizon_months || 0}M`;

      elements
        .carryRollAverageReturn
        .textContent =
          `${number(
            payload.average_expected_return_percent,
            3,
          )}%`;

      if (opportunities.length === 0) {
        elements
          .carryRollTopOpportunity
          .textContent = "—";

        elements
          .carryRollRows
          .innerHTML = `
            <tr>
              <td colspan="14" class="empty">
                No carry and roll opportunities returned.
              </td>
            </tr>
          `;

        return;
      }

      const sorted =
        [...opportunities].sort(
          (left, right) =>
            Number(
              right.expected_total_return_percent || 0,
            )
            - Number(
              left.expected_total_return_percent || 0,
            ),
        );

      const top = sorted[0];

      elements
        .carryRollTopOpportunity
        .textContent =
          `#${top.instrument_id} `
          + `(${number(
            top.expected_total_return_percent,
            2,
          )}%)`;

      elements
        .carryRollRows
        .innerHTML =
          sorted
            .map((item) => {
              const classification =
                String(
                  item.classification || "Unknown",
                );

              return `
                <tr>
                  <td>
                    #${instrumentLinkHtml(item.instrument_id)}
                  </td>

                  <td>
                    ${number(
                      item.clean_price,
                      4,
                    )}
                  </td>

                  <td>
                    ${percent(
                      item.yield_to_maturity,
                    )}
                  </td>

                  <td>
                    ${number(
                      item.g_spread_bps,
                      2,
                    )} bp
                  </td>

                  <td>
                    ${number(
                      item.modified_duration,
                      3,
                    )}
                  </td>

                  <td class="
                    ${carryRollValueClass(
                      item.coupon_carry_return_percent,
                    )}
                  ">
                    ${signedNumber(
                      item.coupon_carry_return_percent,
                      3,
                    )}%
                  </td>

                  <td class="
                    ${carryRollValueClass(
                      item.financing_cost_return_percent,
                    )}
                  ">
                    ${signedNumber(
                      item.financing_cost_return_percent,
                      3,
                    )}%
                  </td>

                  <td>
                    ${signedNumber(
                      item.treasury_roll_down_bps,
                      2,
                    )} bp
                  </td>

                  <td class="
                    ${carryRollValueClass(
                      item.treasury_roll_return_percent,
                    )}
                  ">
                    ${signedNumber(
                      item.treasury_roll_return_percent,
                      3,
                    )}%
                  </td>

                  <td class="
                    ${carryRollValueClass(
                      item.spread_normalization_return_percent,
                    )}
                  ">
                    ${signedNumber(
                      item.spread_normalization_return_percent,
                      3,
                    )}%
                  </td>

                  <td class="
                    ${carryRollValueClass(
                      item.expected_total_return_percent,
                    )}
                  ">
                    <strong>
                      ${signedNumber(
                        item.expected_total_return_percent,
                        3,
                      )}%
                    </strong>
                  </td>

                  <td class="
                    ${carryRollValueClass(
                      item.expected_pnl_per_million,
                    )}
                  ">
                    ${signedCurrency(
                      item.expected_pnl_per_million,
                    )}
                  </td>

                  <td>
                    <span
                      class="
                        carry-roll-classification
                        ${carryRollClassificationClass(
                          classification,
                        )}
                      "
                    >
                      ${classification}
                    </span>
                  </td>

                  <td>
                    ${number(
                      item.conviction_score,
                      3,
                    )}
                  </td>
                </tr>
              `;
            })
            .join("");
    }

    async function runCarryRoll() {

  
      const instrumentIds =
        parseInstrumentIds();

      if (instrumentIds.length < 2) {
        throw new Error(
          "Carry & Roll ranking requires at least two instrument IDs.",
        );
      }

      const horizonMonths = Number(
        elements.carryRollHorizon.value,
      );

      const financingRate = Number(
        elements.carryRollFinancingRate.value,
      );

      const normalization = Number(
        elements.carryRollNormalization.value,
      );

      if (
        !Number.isInteger(horizonMonths)
        || horizonMonths < 1
        || horizonMonths > 24
      ) {
        throw new Error(
          "Horizon must be between 1 and 24 months.",
        );
      }

      if (
        !Number.isFinite(financingRate)
        || financingRate < -0.05
        || financingRate > 0.25
      ) {
        throw new Error(
          "Financing rate must be between -5% and 25%.",
        );
      }

      if (
        !Number.isFinite(normalization)
        || normalization < 0
        || normalization > 1
      ) {
        throw new Error(
          "Spread normalization fraction must be between 0 and 1.",
        );
      }

      elements
        .runCarryRollButton
        .disabled = true;

      elements
        .runCarryRollButton
        .textContent =
          "Ranking...";

      try {
        const payload = await request(
          "/carry-roll/rank",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              instrument_ids:
                instrumentIds,
              horizon_months:
                horizonMonths,
              annual_financing_rate:
                financingRate,
              expected_spread_normalization_fraction:
                normalization,
            }),
          },
        );

        renderCarryRoll(
          payload,
        );

        log(
          `Carry & Roll completed: `
          + `${payload.instrument_count} instruments, `
          + `${payload.horizon_months}M horizon, `
          + `average expected return `
          + `${number(
            payload.average_expected_return_percent,
            3,
          )}%`,
        );
      } finally {
        elements
          .runCarryRollButton
          .disabled = false;

        elements
          .runCarryRollButton
          .textContent =
            "Rank Carry & Roll";
      }
    }



    function marketQualityClass(score) {
      const value = Number(score || 0);

      if (value >= 0.9) {
        return "market-quality-good";
      }

      if (value >= 0.8) {
        return "market-quality-warning";
      }

      return "market-quality-bad";
    }

    function renderMarketOverviewRows() {
      const query = String(
        elements.marketOverviewSearch.value || "",
      )
        .trim()
        .toLowerCase();

      const rows = currentMarketOverview.filter(
        (item) => {
          if (!query) {
            return true;
          }

          return [
            item.instrument_id,
            item.quality_status,
            item.curve_version,
            item.reference_version,
          ]
            .map((value) =>
              String(value ?? "")
                .toLowerCase()
            )
            .some((value) =>
              value.includes(query)
            );
        },
      );

      elements
        .marketOverviewVisibleCount
        .textContent =
          rows.length.toLocaleString();

      if (rows.length === 0) {
        elements
          .marketOverviewRows
          .innerHTML = `
            <tr>
              <td colspan="12" class="empty">
                No market rows match the current filter.
              </td>
            </tr>
          `;

        return;
      }

      elements
        .marketOverviewRows
        .innerHTML =
          rows
            .map((item) => `
              <tr>
                <td>
                  #${instrumentLinkHtml(item.instrument_id)}
                </td>

                <td>
                  ${number(
                    item.clean_price,
                    4,
                  )}
                </td>

                <td>
                  ${number(
                    item.dirty_price,
                    4,
                  )}
                </td>

                <td>
                  ${percent(
                    item.yield_to_maturity,
                  )}
                </td>

                <td>
                  ${number(
                    item.g_spread_bps,
                    2,
                  )} bp
                </td>

                <td>
                  ${number(
                    item.modified_duration,
                    4,
                  )}
                </td>

                <td>
                  ${number(
                    item.convexity,
                    4,
                  )}
                </td>

                <td class="
                  ${marketQualityClass(
                    item.quality_score,
                  )}
                ">
                  ${number(
                    item.quality_score,
                    3,
                  )}
                </td>

                <td>
                  ${item.quality_status}
                </td>

                <td>
                  ${item.curve_version}
                </td>

                <td>
                  ${item.reference_version}
                </td>

                <td>
                  ${formatPriceHistoryTime(
                    item.event_time,
                  )}
                </td>
              </tr>
            `)
            .join("");
    }

    function renderMarketSummary(payload) {
  markResultFresh(
    "marketOverview",
  );

      elements
        .marketSummaryInstrumentCount
        .textContent =
          Number(
            payload.instrument_count || 0,
          ).toLocaleString();

      elements
        .marketSummaryAveragePrice
        .textContent =
          number(
            payload.average_clean_price,
            4,
          );

      elements
        .marketSummaryAverageYield
        .textContent =
          percent(
            payload.average_yield_to_maturity,
          );

      elements
        .marketSummaryAverageSpread
        .textContent =
          `${number(
            payload.average_g_spread_bps,
            2,
          )} bp`;

      elements
        .marketSummaryWidestInstrument
        .textContent =
          payload.widest_instrument_id == null
            ? "—"
            : `#${payload.widest_instrument_id}`;

      elements
        .marketSummaryWidestSpread
        .textContent =
          payload.widest_g_spread_bps == null
            ? "—"
            : `${number(
                payload.widest_g_spread_bps,
                2,
              )} bp`;
    }

    async function loadMarketOverview() {

  
      const limit = Number(
        elements.marketOverviewLimit.value,
      );

      const minimumQuality = Number(
        elements.marketOverviewQuality.value,
      );

      if (
        !Number.isInteger(limit)
        || limit < 1
        || limit > 10000
      ) {
        throw new Error(
          "Instrument limit must be between 1 and 10000.",
        );
      }

      if (
        !Number.isFinite(minimumQuality)
        || minimumQuality < 0
        || minimumQuality > 1
      ) {
        throw new Error(
          "Minimum quality score must be between 0 and 1.",
        );
      }

      elements
        .loadMarketOverviewButton
        .disabled = true;

      elements
        .loadMarketOverviewButton
        .textContent =
          "Loading...";

      try {
        const [
          summary,
          latestPrices,
        ] = await Promise.all([
          request(
            "/market/summary",
          ),
          request(
            "/prices/latest"
            + `?limit=${limit}`
            + `&minimum_quality_score=${minimumQuality}`,
          ),
        ]);

        currentMarketOverview =
          Array.isArray(latestPrices)
            ? [...latestPrices].sort(
                (left, right) =>
                  Number(
                    right.g_spread_bps || 0,
                  )
                  - Number(
                    left.g_spread_bps || 0,
                  ),
              )
            : [];

        renderMarketSummary(
          summary,
        );

        renderMarketOverviewRows();

        log(
          `Market overview loaded: `
          + `${summary.instrument_count} instruments, `
          + `${currentMarketOverview.length} latest prices, `
          + `average spread `
          + `${number(
            summary.average_g_spread_bps,
            2,
          )} bp`,
        );
      } finally {
        elements
          .loadMarketOverviewButton
          .disabled = false;

        elements
          .loadMarketOverviewButton
          .textContent =
            "Load Market Overview";
      }
    }


// ============================================================
// Instrument Drill-Down
// ============================================================

let activeInstrumentDrilldownId = null;

function setInstrumentDrawerValue(
  id,
  value,
) {
  const element =
    document.getElementById(id);

  if (!element) {
    return;
  }

  element.textContent =
    value == null
      ? "—"
      : String(value);
}

function openInstrumentDrawerShell(
  instrumentId,
) {
  activeInstrumentDrilldownId =
    Number(instrumentId);

  const drawer =
    document.getElementById(
      "instrumentDrawer",
    );

  const backdrop =
    document.getElementById(
      "instrumentDrawerBackdrop",
    );

  if (!drawer || !backdrop) {
    return;
  }

  setInstrumentDrawerValue(
    "instrumentDrawerTitle",
    `#${instrumentId}`,
  );

  drawer.classList.add(
    "open",
  );

  drawer.setAttribute(
    "aria-hidden",
    "false",
  );

  backdrop.hidden = false;

  document.body.classList.add(
    "instrument-drawer-open",
  );
}

function closeInstrumentDrawer() {
  const drawer =
    document.getElementById(
      "instrumentDrawer",
    );

  const backdrop =
    document.getElementById(
      "instrumentDrawerBackdrop",
    );

  drawer?.classList.remove(
    "open",
  );

  drawer?.setAttribute(
    "aria-hidden",
    "true",
  );

  if (backdrop) {
    backdrop.hidden = true;
  }

  document.body.classList.remove(
    "instrument-drawer-open",
  );
}

function renderInstrumentDrawer(
  instrumentId,
  history,
  risk,
  reference,
) {
  const latest =
    Array.isArray(history)
    && history.length
      ? history[history.length - 1]
      : null;

  const instrumentRisk =
    Array.isArray(
      risk?.instruments,
    )
      ? risk.instruments.find(
          (item) =>
            Number(item.instrument_id)
            === Number(instrumentId),
        )
      : null;

  setInstrumentDrawerValue(
    "instrumentDrawerTitle",
    reference?.issuer_name
      ? `${reference.issuer_name} · #${instrumentId}`
      : `#${instrumentId}`,
  );

  setInstrumentDrawerValue(
    "drawerIssuer",
    reference?.issuer_name ?? "—",
  );

  setInstrumentDrawerValue(
    "drawerCusip",
    reference?.cusip ?? "—",
  );

  setInstrumentDrawerValue(
    "drawerIsin",
    reference?.isin ?? "—",
  );

  setInstrumentDrawerValue(
    "drawerTicker",
    reference?.ticker ?? "—",
  );

  setInstrumentDrawerValue(
    "drawerInstrumentType",
    reference?.instrument_type ?? "—",
  );

  setInstrumentDrawerValue(
    "drawerCoupon",
    reference?.coupon_rate != null
      ? `${number(
          Number(reference.coupon_rate),
          4,
        )}%`
      : "—",
  );

  setInstrumentDrawerValue(
    "drawerMaturity",
    reference?.maturity_date ?? "—",
  );

  setInstrumentDrawerValue(
    "drawerRating",
    reference?.rating ?? "—",
  );

  setInstrumentDrawerValue(
    "drawerSector",
    reference?.sector ?? "—",
  );

  setInstrumentDrawerValue(
    "drawerCurrency",
    reference?.currency ?? "—",
  );

  setInstrumentDrawerValue(
    "drawerReferenceSource",
    reference?.source
      ? `${reference.source} · version ${reference.version_id}`
      : "—",
  );

  setInstrumentDrawerValue(
    "drawerCleanPrice",
    latest
      ? number(
          latest.clean_price,
          4,
        )
      : "—",
  );

  setInstrumentDrawerValue(
    "drawerDirtyPrice",
    latest
      ? number(
          latest.dirty_price,
          4,
        )
      : "—",
  );

  setInstrumentDrawerValue(
    "drawerYield",
    latest
      ? percent(
          latest.yield_to_maturity,
        )
      : "—",
  );

  setInstrumentDrawerValue(
    "drawerSpread",
    latest
      ? `${number(
          latest.g_spread_bps,
          2,
        )} bp`
      : "—",
  );

  setInstrumentDrawerValue(
    "drawerDuration",
    latest
      ? number(
          latest.modified_duration,
          4,
        )
      : "—",
  );

  setInstrumentDrawerValue(
    "drawerConvexity",
    latest
      ? number(
          latest.convexity,
          4,
        )
      : "—",
  );

  setInstrumentDrawerValue(
    "drawerQuality",
    latest
      ? number(
          latest.quality_score,
          3,
        )
      : "—",
  );

  setInstrumentDrawerValue(
    "drawerQualityStatus",
    latest?.quality_status
      ?? "—",
  );

  setInstrumentDrawerValue(
    "drawerCurveVersion",
    latest?.curve_version
      ?? "—",
  );

  setInstrumentDrawerValue(
    "drawerReferenceVersion",
    latest?.reference_version
      ?? "—",
  );

  setInstrumentDrawerValue(
    "drawerModelVersion",
    latest?.model_version
      ?? "—",
  );

  setInstrumentDrawerValue(
    "instrumentDrawerTimestamp",
    latest?.event_time
      ? `Latest observation · ${
          formatPriceHistoryTime(
            latest.event_time,
          )
        }`
      : "No price history",
  );

  setInstrumentDrawerValue(
    "drawerMarketValue",
    instrumentRisk
      ? currency(
          instrumentRisk.market_value,
        )
      : "—",
  );

  setInstrumentDrawerValue(
    "drawerDv01",
    instrumentRisk
      ? number(
          instrumentRisk.aggregate_dv01,
          2,
        )
      : "—",
  );

  setInstrumentDrawerValue(
    "drawerCs01",
    instrumentRisk
      ? number(
          instrumentRisk.cs01,
          2,
        )
      : "—",
  );

  setInstrumentDrawerValue(
    "drawerNotional",
    instrumentRisk
      ? currency(
          instrumentRisk.position_notional,
        )
      : "—",
  );

  const rows =
    document.getElementById(
      "drawerKeyRateRows",
    );

  if (rows) {
    const exposures =
      instrumentRisk
        ?.key_rate_exposures
      || [];

    rows.innerHTML =
      exposures.length
        ? exposures
            .map(
              (exposure) => `
                <tr>
                  <td>
                    ${exposure.tenor}
                  </td>

                  <td>
                    ${number(
                      exposure.key_rate_duration,
                      4,
                    )}
                  </td>

                  <td>
                    ${number(
                      exposure.key_rate_dv01,
                      2,
                    )}
                  </td>
                </tr>
              `,
            )
            .join("")
        : `
            <tr>
              <td
                colspan="3"
                class="empty"
              >
                No key-rate exposure.
              </td>
            </tr>
          `;
  }
}

async function openInstrumentDrilldown(
  instrumentId,
) {
  const id =
    Number(instrumentId);

  if (
    !Number.isInteger(id)
    || id <= 0
  ) {
    return;
  }

  openInstrumentDrawerShell(id);

  const loading =
    document.getElementById(
      "instrumentDrawerLoading",
    );

  if (loading) {
    loading.hidden = false;
  }

  try {
    const notional =
      Number(
        document.getElementById(
          "riskDecompositionNotional",
        )?.value
        || 1000000,
      );

    const [
      history,
      risk,
      reference,
    ] = await Promise.all([
      request(
        `/prices/${id}/history?limit=100`,
      ),

      request(
        "/risk/decomposition",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            instrument_ids: [
              id,
            ],

            position_notional:
              notional,
          }),
        },
      ),

      fetch(
        `http://127.0.0.1:8001/instruments/${id}`,
      ).then(async (response) => {
        if (!response.ok) {
          throw new Error(
            `Reference Data request failed (${response.status})`,
          );
        }

        return response.json();
      }),
    ]);

    if (
      activeInstrumentDrilldownId
      !== id
    ) {
      return;
    }

    renderInstrumentDrawer(
      id,
      history,
      risk,
      reference,
    );
  } catch (error) {
    toastError(
      error?.message
        || String(error),
      `Instrument #${id}`,
    );
  } finally {
    if (loading) {
      loading.hidden = true;
    }
  }
}

function initializeInstrumentDrilldown() {
  const marketRows =
    document.getElementById(
      "marketOverviewRows",
    );

  marketRows?.addEventListener(
    "click",
    (event) => {
      const target =
        event.target;

      if (
        !(target instanceof Element)
      ) {
        return;
      }

      const row =
        target.closest("tr");

      if (!row) {
        return;
      }

      const firstCell =
        row.querySelector("td");

      const match =
        firstCell?.textContent
          ?.match(/\d+/);

      if (!match) {
        return;
      }

      openInstrumentDrilldown(
        Number(match[0]),
      );
    },
  );

  document
    .getElementById(
      "closeInstrumentDrawerButton",
    )
    ?.addEventListener(
      "click",
      closeInstrumentDrawer,
    );

  document
    .getElementById(
      "instrumentDrawerBackdrop",
    )
    ?.addEventListener(
      "click",
      closeInstrumentDrawer,
    );

  document.addEventListener(
    "keydown",
    (event) => {
      if (
        event.key === "Escape"
        && document
          .getElementById(
            "instrumentDrawer",
          )
          ?.classList.contains(
            "open",
          )
      ) {
        closeInstrumentDrawer();
      }
    },
  );

  document
    .getElementById(
      "drawerOpenHistoryButton",
    )
    ?.addEventListener(
      "click",
      () => {
        if (
          !activeInstrumentDrilldownId
        ) {
          return;
        }

        const input =
          document.getElementById(
            "priceHistoryInstrumentId",
          );

        if (input) {
          input.value =
            String(
              activeInstrumentDrilldownId,
            );
        }

        closeInstrumentDrawer();

        document
          .getElementById(
            "history",
          )
          ?.scrollIntoView({
            behavior: "smooth",
          });
      },
    );
}

initializeInstrumentDrilldown();


// ============================================================
// Instrument link helper
// ============================================================

function instrumentLinkHtml(
  instrumentId,
) {
  const id =
    Number(instrumentId);

  if (
    !Number.isInteger(id)
    || id <= 0
  ) {
    return String(
      instrumentId ?? "—",
    );
  }

  return `
    <button
      type="button"
      class="instrument-link"
      data-instrument-id="${id}"
    >
      #${id}
    </button>
  `;
}

document.addEventListener(
  "click",
  (event) => {
    const target =
      event.target;

    if (
      !(target instanceof Element)
    ) {
      return;
    }

    const link =
      target.closest(
        "[data-instrument-id]",
      );

    if (!link) {
      return;
    }

    const instrumentId =
      Number(
        link.getAttribute(
          "data-instrument-id",
        ),
      );

    if (
      !Number.isInteger(
        instrumentId,
      )
      || instrumentId <= 0
    ) {
      return;
    }

    openInstrumentDrilldown(
      instrumentId,
    );
  },
);


// ============================================================
// Instrument Drawer Actions
// ============================================================

function getCurrentInstrumentBasket() {
  const input =
    document.getElementById(
      "instrumentIds",
    );

  if (!input) {
    return [];
  }

  return String(
    input.value || "",
  )
    .split(",")
    .map(
      (value) =>
        Number(
          value.trim(),
        ),
    )
    .filter(
      (value) =>
        Number.isInteger(value)
        && value > 0,
    );
}

function addInstrumentToCurrentBasket(
  instrumentId,
) {
  const id =
    Number(instrumentId);

  if (
    !Number.isInteger(id)
    || id <= 0
  ) {
    return;
  }

  const input =
    document.getElementById(
      "instrumentIds",
    );

  if (!input) {
    toastError(
      "Could not find the shared instrument basket.",
    );

    return;
  }

  const basket =
    getCurrentInstrumentBasket();

  if (
    basket.includes(id)
  ) {
    toastInfo(
      `Instrument #${id} is already in the basket.`,
      "Basket",
    );

    return;
  }

  basket.push(id);

  input.value =
    basket.join(",");

  captureWorkbenchUiState();

  toastSuccess(
    `Instrument #${id} added to the current basket.`,
    "Basket updated",
  );
}

function sendDrawerInstrumentToHistory() {
  if (
    !activeInstrumentDrilldownId
  ) {
    return;
  }

  const input =
    document.getElementById(
      "priceHistoryInstrumentId",
    );

  if (input) {
    input.value =
      String(
        activeInstrumentDrilldownId,
      );
  }

  captureWorkbenchUiState();

  closeInstrumentDrawer();

  document
    .getElementById(
      "history",
    )
    ?.scrollIntoView({
      behavior: "smooth",
    });
}

function sendDrawerInstrumentToRisk() {
  if (
    !activeInstrumentDrilldownId
  ) {
    return;
  }

  const input =
    document.getElementById(
      "instrumentIds",
    );

  if (input) {
    input.value =
      String(
        activeInstrumentDrilldownId,
      );
  }

  captureWorkbenchUiState();

  closeInstrumentDrawer();

  document
    .getElementById(
      "risk",
    )
    ?.scrollIntoView({
      behavior: "smooth",
    });

  toastInfo(
    `Instrument #${activeInstrumentDrilldownId} loaded into the shared basket.`,
    "Risk Decomposition",
  );
}

function sendDrawerInstrumentToStress() {
  if (
    !activeInstrumentDrilldownId
  ) {
    return;
  }

  const input =
    document.getElementById(
      "instrumentIds",
    );

  if (input) {
    input.value =
      String(
        activeInstrumentDrilldownId,
      );
  }

  captureWorkbenchUiState();

  closeInstrumentDrawer();

  document
    .getElementById(
      "risk",
    )
    ?.scrollIntoView({
      behavior: "smooth",
    });

  toastInfo(
    `Instrument #${activeInstrumentDrilldownId} loaded for stress analysis.`,
    "Stress Test",
  );
}

document
  .getElementById(
    "drawerAddToBasketButton",
  )
  ?.addEventListener(
    "click",
    () => {
      if (
        activeInstrumentDrilldownId
      ) {
        addInstrumentToCurrentBasket(
          activeInstrumentDrilldownId,
        );
      }
    },
  );

document
  .getElementById(
    "drawerUseRiskButton",
  )
  ?.addEventListener(
    "click",
    sendDrawerInstrumentToRisk,
  );

document
  .getElementById(
    "drawerUseStressButton",
  )
  ?.addEventListener(
    "click",
    sendDrawerInstrumentToStress,
  );


// ============================================================
// Instrument Search
// ============================================================

let instrumentSearchRequestId = 0;

function renderInstrumentSearchResults(
  results,
) {
  const container =
    document.getElementById(
      "instrumentSearchResults",
    );

  if (!container) {
    return;
  }

  if (
    !Array.isArray(results)
    || results.length === 0
  ) {
    container.innerHTML = `
      <div class="instrument-search-empty">
        No matching instruments.
      </div>
    `;

    container.hidden = false;

    return;
  }

  container.innerHTML =
    results
      .map(
        (instrument) => {
          const metadata = [
            instrument.cusip
              ? `CUSIP ${instrument.cusip}`
              : null,

            instrument.isin
              ? `ISIN ${instrument.isin}`
              : null,

            instrument.rating
              || null,

            instrument.sector
              || null,

            instrument.instrument_type
              || null,
          ]
            .filter(Boolean)
            .map(
              (value) =>
                `<span>${value}</span>`,
            )
            .join("");

          return `
            <button
              type="button"
              class="instrument-search-result"
              data-search-instrument-id="${
                instrument.instrument_id
              }"
            >
              <span
                class="instrument-search-result-main"
              >
                <span
                  class="instrument-search-result-title"
                >
                  ${
                    instrument.issuer_name
                    || "Unknown issuer"
                  }
                </span>

                <span
                  class="instrument-search-result-meta"
                >
                  ${metadata}
                </span>
              </span>

              <span
                class="instrument-search-result-id"
              >
                #${instrument.instrument_id}
              </span>
            </button>
          `;
        },
      )
      .join("");

  container.hidden = false;
}

async function searchInstruments() {
  const input =
    document.getElementById(
      "instrumentSearchInput",
    );

  const button =
    document.getElementById(
      "instrumentSearchButton",
    );

  const container =
    document.getElementById(
      "instrumentSearchResults",
    );

  if (
    !input
    || !container
  ) {
    return;
  }

  const query =
    String(
      input.value || "",
    ).trim();

  if (!query) {
    container.hidden = true;
    return;
  }

  const requestId =
    ++instrumentSearchRequestId;

  if (button) {
    button.disabled = true;
    button.textContent = "Searching...";
  }

  try {
    const response =
      await fetch(
        `http://127.0.0.1:8001/instruments/search?q=${
          encodeURIComponent(query)
        }&limit=8`,
      );

    if (!response.ok) {
      throw new Error(
        `Instrument search failed (${response.status})`,
      );
    }

    const results =
      await response.json();

    if (
      requestId
      !== instrumentSearchRequestId
    ) {
      return;
    }

    renderInstrumentSearchResults(
      results,
    );
  } catch (error) {
    toastError(
      error?.message
        || String(error),
      "Instrument Search",
    );
  } finally {
    if (
      button
      && requestId
        === instrumentSearchRequestId
    ) {
      button.disabled = false;
      button.textContent = "Search";
    }
  }
}

function initializeInstrumentSearch() {
  const input =
    document.getElementById(
      "instrumentSearchInput",
    );

  const button =
    document.getElementById(
      "instrumentSearchButton",
    );

  const results =
    document.getElementById(
      "instrumentSearchResults",
    );

  button?.addEventListener(
    "click",
    () =>
      handleAction(
        searchInstruments,
      ),
  );

  input?.addEventListener(
    "keydown",
    (event) => {
      if (event.key === "Enter") {
        event.preventDefault();

        handleAction(
          searchInstruments,
        );
      }

      if (event.key === "Escape") {
        if (results) {
          results.hidden = true;
        }
      }
    },
  );

  results?.addEventListener(
    "click",
    (event) => {
      const target =
        event.target;

      if (
        !(target instanceof Element)
      ) {
        return;
      }

      const row =
        target.closest(
          "[data-search-instrument-id]",
        );

      if (!row) {
        return;
      }

      const instrumentId =
        Number(
          row.getAttribute(
            "data-search-instrument-id",
          ),
        );

      if (
        !Number.isInteger(
          instrumentId,
        )
      ) {
        return;
      }

      results.hidden = true;

      openInstrumentDrilldown(
        instrumentId,
      );
    },
  );

  document.addEventListener(
    "click",
    (event) => {
      const target =
        event.target;

      if (
        !(target instanceof Element)
      ) {
        return;
      }

      if (
        !target.closest(
          "#instrumentSearch",
        )
        && results
      ) {
        results.hidden = true;
      }
    },
  );
}

initializeInstrumentSearch();
