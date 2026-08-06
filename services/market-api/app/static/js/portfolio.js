function renderOptimizerResult(payload) {
      const allocations = payload.allocations || [];

      const allocatedNotional = allocations.reduce(
        (total, allocation) =>
          total + Number(allocation.target_notional || 0),
        0,
      );

      elements.optimizerResultObjective.textContent =
        String(payload.objective || "—")
          .replaceAll("_", " ");

      elements.optimizerResultNotional.textContent =
        currency(payload.total_notional);

      elements.optimizerAllocatedNotional.textContent =
        currency(allocatedNotional);

      elements.optimizerAllocationCount.textContent =
        allocations.length.toLocaleString();

      if (allocations.length === 0) {
        elements.optimizerRows.innerHTML = `
          <tr>
            <td colspan="4" class="empty">
              The optimizer returned no allocations.
            </td>
          </tr>
        `;

        return;
      }

      elements.optimizerRows.innerHTML = allocations
        .map((allocation) => `
          <tr>
            <td>#${instrumentLinkHtml(allocation.instrument_id)}</td>
            <td>
              ${(Number(allocation.weight || 0) * 100)
                .toFixed(2)}%
            </td>
            <td>
              ${currency(allocation.target_notional)}
            </td>
            <td>
              ${number(allocation.expected_score, 6)}
            </td>
          </tr>
        `)
        .join("");
    }

    async function runStandardOptimizer() {

  
      const instrumentIds = parseInstrumentIds();

      if (instrumentIds.length < 2) {
        throw new Error(
          "The optimizer requires at least two instrument IDs.",
        );
      }

      const totalNotional = Number(
        elements.optimizerNotional.value,
      );

      const maxPositionPercent = Number(
        elements.optimizerMaxPosition.value,
      ) / 100;

      if (
        !Number.isFinite(totalNotional)
        || totalNotional <= 0
      ) {
        throw new Error(
          "Total notional must be greater than zero.",
        );
      }

      if (
        !Number.isFinite(maxPositionPercent)
        || maxPositionPercent <= 0
        || maxPositionPercent > 1
      ) {
        throw new Error(
          "Maximum position must be between 0 and 100 percent.",
        );
      }

      elements.runOptimizerButton.disabled = true;
      elements.runOptimizerButton.textContent =
        "Optimizing...";

      try {
        const payload = await request(
          "/portfolio/optimize",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              instrument_ids: instrumentIds,
              total_notional: totalNotional,
              max_position_percent: maxPositionPercent,
              objective:
                elements.optimizerObjective.value,
            }),
          },
        );

        renderOptimizerResult(payload);

        markResultFresh(
          "optimizer",
        );

        log(
          `Optimization completed: `
          + `${payload.allocations.length} allocations, `
          + `${currency(payload.total_notional)} total notional`,
        );
      } finally {
        elements.runOptimizerButton.disabled = false;
        elements.runOptimizerButton.textContent =
          "Run Optimization";
      }
    }


    function renderRiskOptimizerResult(payload) {
      const allocations = payload.allocations || [];

      elements.riskOptimizerInvested.textContent =
        currency(payload.invested_notional);

      elements.riskOptimizerCash.textContent =
        currency(payload.cash_notional);

      elements.riskOptimizerInvestedPercent.textContent =
        `${(Number(payload.invested_percent || 0) * 100)
          .toFixed(2)}%`;

      elements.riskOptimizerPortfolioDv01.textContent =
        number(payload.portfolio_dv01, 2);

      elements.riskOptimizerPortfolioCs01.textContent =
        number(payload.portfolio_cs01, 2);

      elements.riskOptimizerAllocationCount.textContent =
        allocations.length.toLocaleString();

      if (allocations.length === 0) {
        elements.riskOptimizerRows.innerHTML = `
          <tr>
            <td colspan="6" class="empty">
              The risk optimizer returned no allocations.
            </td>
          </tr>
        `;

        return;
      }

      elements.riskOptimizerRows.innerHTML = allocations
        .map((allocation) => `
          <tr>
            <td>#${instrumentLinkHtml(allocation.instrument_id)}</td>
            <td>
              ${(Number(allocation.weight || 0) * 100)
                .toFixed(2)}%
            </td>
            <td>
              ${currency(allocation.target_notional)}
            </td>
            <td>
              ${number(allocation.expected_score, 6)}
            </td>
            <td>
              ${number(allocation.dv01, 2)}
            </td>
            <td>
              ${number(allocation.cs01, 2)}
            </td>
          </tr>
        `)
        .join("");
    }

    async function runRiskBudgetOptimizer() {

  
      const instrumentIds = parseInstrumentIds();

      if (instrumentIds.length < 2) {
        throw new Error(
          "The risk optimizer requires at least two instrument IDs.",
        );
      }

      const totalNotional = Number(
        elements.riskOptimizerNotional.value,
      );

      const maxPositionPercent = Number(
        elements.riskOptimizerMaxPosition.value,
      ) / 100;

      const maxPortfolioDv01 = Number(
        elements.riskOptimizerDv01.value,
      );

      const maxPortfolioCs01 = Number(
        elements.riskOptimizerCs01.value,
      );

      if (
        !Number.isFinite(totalNotional)
        || totalNotional <= 0
      ) {
        throw new Error(
          "Total notional must be greater than zero.",
        );
      }

      if (
        !Number.isFinite(maxPositionPercent)
        || maxPositionPercent <= 0
        || maxPositionPercent > 1
      ) {
        throw new Error(
          "Maximum position must be between 0 and 100 percent.",
        );
      }

      if (
        !Number.isFinite(maxPortfolioDv01)
        || maxPortfolioDv01 <= 0
      ) {
        throw new Error(
          "Maximum portfolio DV01 must be greater than zero.",
        );
      }

      if (
        !Number.isFinite(maxPortfolioCs01)
        || maxPortfolioCs01 <= 0
      ) {
        throw new Error(
          "Maximum portfolio CS01 must be greater than zero.",
        );
      }

      elements.runRiskOptimizerButton.disabled = true;
      elements.runRiskOptimizerButton.textContent =
        "Optimizing...";

      try {
        const payload = await request(
          "/portfolio/optimize-risk",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              instrument_ids: instrumentIds,
              total_notional: totalNotional,
              max_position_percent: maxPositionPercent,
              max_portfolio_dv01: maxPortfolioDv01,
              max_portfolio_cs01: maxPortfolioCs01,
              objective:
                elements.riskOptimizerObjective.value,
            }),
          },
        );

        renderRiskOptimizerResult(payload);

        markResultFresh(
          "riskOptimizer",
        );

        log(
          `Risk optimization completed: `
          + `${allocationsDescription(payload)}, `
          + `DV01 ${number(payload.portfolio_dv01, 2)}, `
          + `CS01 ${number(payload.portfolio_cs01, 2)}`,
        );
      } finally {
        elements.runRiskOptimizerButton.disabled = false;
        elements.runRiskOptimizerButton.textContent =
          "Run Risk Optimization";
      }
    }


    function renderPortfolioRisk(payload) {
  markResultFresh(
    "portfolioRisk",
  );

      const positions =
        payload.positions || [];

      elements
        .portfolioRiskPositionCount
        .textContent =
          Number(
            payload.position_count || 0,
          ).toLocaleString();

      elements
        .portfolioRiskTotalFaceValue
        .textContent =
          currency(
            payload.total_face_value,
          );

      elements
        .portfolioRiskMarketValue
        .textContent =
          currency(
            payload.total_market_value,
          );

      elements
        .portfolioRiskWeightedYield
        .textContent =
          percent(
            payload.weighted_yield_to_maturity,
          );

      elements
        .portfolioRiskWeightedSpread
        .textContent =
          `${number(
            payload.weighted_g_spread_bps,
            2,
          )} bp`;

      elements
        .portfolioRiskWeightedDuration
        .textContent =
          number(
            payload.weighted_modified_duration,
            4,
          );

      elements
        .portfolioRiskWeightedConvexity
        .textContent =
          number(
            payload.weighted_convexity,
            4,
          );

      elements
        .portfolioRiskTotalDv01
        .textContent =
          number(
            payload.total_dv01,
            2,
          );

      elements
        .portfolioRiskConvexityContribution
        .textContent =
          number(
            payload.total_convexity_contribution,
            2,
          );

      if (positions.length === 0) {
        elements
          .portfolioRiskRows
          .innerHTML = `
            <tr>
              <td colspan="11" class="empty">
                No position risk returned.
              </td>
            </tr>
          `;

        return;
      }

      elements
        .portfolioRiskRows
        .innerHTML =
          [...positions]
            .sort(
              (left, right) =>
                Number(
                  right.market_value_weight || 0,
                )
                - Number(
                  left.market_value_weight || 0,
                ),
            )
            .map((item) => {
              const weight =
                Number(
                  item.market_value_weight || 0,
                ) * 100;

              return `
                <tr>
                  <td>
                    #${instrumentLinkHtml(item.instrument_id)}
                  </td>

                  <td>
                    ${currency(
                      item.face_value,
                    )}
                  </td>

                  <td>
                    ${number(
                      item.clean_price,
                      4,
                    )}
                  </td>

                  <td>
                    ${currency(
                      item.market_value,
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

                  <td>
                    ${number(
                      item.dv01,
                      2,
                    )}
                  </td>

                  <td>
                    ${number(
                      item.convexity_contribution,
                      2,
                    )}
                  </td>

                  <td class="
                    ${
                      weight >= 25
                        ? "portfolio-risk-weight-high"
                        : ""
                    }
                  ">
                    ${weight.toFixed(2)}%
                  </td>
                </tr>
              `;
            })
            .join("");
    }

    async function runPortfolioRisk() {

  
      const instrumentIds =
        parseInstrumentIds();

      if (instrumentIds.length < 1) {
        throw new Error(
          "Portfolio risk requires at least one instrument ID.",
        );
      }

      const faceValue = Number(
        elements
          .portfolioRiskFaceValue
          .value,
      );

      if (
        !Number.isFinite(faceValue)
        || faceValue <= 0
        || faceValue > 1000000000
      ) {
        throw new Error(
          "Face value must be greater than zero and no more than $1 billion.",
        );
      }

      elements
        .runPortfolioRiskButton
        .disabled = true;

      elements
        .runPortfolioRiskButton
        .textContent =
          "Calculating...";

      try {
        const payload = await request(
          "/portfolio/risk",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              positions:
                instrumentIds.map(
                  (instrumentId) => ({
                    instrument_id:
                      instrumentId,
                    face_value:
                      faceValue,
                  }),
                ),
            }),
          },
        );

        renderPortfolioRisk(
          payload,
        );

        log(
          `Portfolio risk completed: `
          + `${payload.position_count} positions, `
          + `market value `
          + `${currency(
            payload.total_market_value,
          )}, DV01 `
          + `${number(
            payload.total_dv01,
            2,
          )}`,
        );
      } finally {
        elements
          .runPortfolioRiskButton
          .disabled = false;

        elements
          .runPortfolioRiskButton
          .textContent =
            "Calculate Portfolio Risk";
      }
    }
