const MERCATOR_AGENT_URL =
  "";


function escapeAgentHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function renderAgentList(
  title,
  values,
) {
  if (
    !Array.isArray(values)
    || values.length === 0
  ) {
    return "";
  }

  const items = values
    .map(
      (value) => `
        <li>
          ${escapeAgentHtml(value)}
        </li>
      `,
    )
    .join("");

  return `
    <div class="agent-result-section">
      <h4>${escapeAgentHtml(title)}</h4>

      <ul class="agent-list">
        ${items}
      </ul>
    </div>
  `;
}


function renderAgentSecurity(security) {
  if (!security) {
    return "";
  }

  const ids =
    Array.isArray(
      security.instrument_ids,
    )
      ? security.instrument_ids
      : [];

  const visible =
    ids.slice(0, 12);

  const pills = visible
    .map(
      (id) => `
        <span class="agent-security-pill">
          ${escapeAgentHtml(id)}
        </span>
      `,
    )
    .join("");

  const remaining =
    ids.length - visible.length;

  return `
    <div class="agent-result-section">
      <h4>Resolved Securities</h4>

      <div class="agent-security-summary">
        ${pills}

        ${
          remaining > 0
            ? `
              <span class="agent-security-pill">
                +${remaining} more
              </span>
            `
            : ""
        }
      </div>
    </div>
  `;
}


function renderAgentTools(diagnostics) {
  if (
    !diagnostics
    || typeof diagnostics !== "object"
  ) {
    return "";
  }

  const entries =
    Object.entries(diagnostics)
      .filter(
        ([name]) =>
          name !== "brief",
      );

  if (!entries.length) {
    return "";
  }

  const chips = entries
    .map(
      ([name, details]) => {
        let status =
          details?.status;

        if (
          !status
          && name === "planner"
        ) {
          status =
            "completed";
        }

        status =
          status || "unknown";

        return `
          <div
            class="
              agent-tool-chip
              ${escapeAgentHtml(status)}
            "
          >
            <strong>
              ${escapeAgentHtml(name)}
            </strong>

            <span>
              ${escapeAgentHtml(status)}
            </span>
          </div>
        `;
      },
    )
    .join("");

  return `
    <div class="agent-result-section">
      <h4>Tool Execution</h4>

      <div class="agent-tool-grid">
        ${chips}
      </div>
    </div>
  `;
}



function formatAgentNumber(
  value,
  decimals = 2,
) {
  const number =
    Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  return number.toLocaleString(
    undefined,
    {
      minimumFractionDigits:
        decimals,

      maximumFractionDigits:
        decimals,
    },
  );
}


function formatAgentMoney(
  value,
) {
  const number =
    Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  return number.toLocaleString(
    undefined,
    {
      style: "currency",
      currency: "USD",

      maximumFractionDigits:
        0,
    },
  );
}


function agentMetric(
  label,
  value,
) {
  return `
    <div class="agent-metric">
      <span>
        ${escapeAgentHtml(label)}
      </span>

      <strong>
        ${escapeAgentHtml(value)}
      </strong>
    </div>
  `;
}


function renderAgentEtfAnalytics(
  etf,
) {
  if (!etf) {
    return "";
  }

  const premium =
    Number(
      etf.premium_discount_percent,
    );

  const premiumText =
    Number.isFinite(premium)
      ? `${premium >= 0 ? "+" : ""}${premium.toFixed(3)}%`
      : "—";

  return `
    <div class="agent-result-section">
      <h4>
        ETF Analytics
      </h4>

      <div class="agent-metric-grid">
        ${agentMetric(
          "Reference NAV",
          formatAgentNumber(
            etf.reference_nav,
            4,
          ),
        )}

        ${agentMetric(
          "Mid",
          formatAgentNumber(
            etf.mid,
            4,
          ),
        )}

        ${agentMetric(
          "Premium / Discount",
          premiumText,
        )}

        ${agentMetric(
          "Bid / Ask Spread",
          `${formatAgentNumber(
            etf.bid_ask_spread_bps,
            2,
          )} bp`,
        )}

        ${agentMetric(
          "Basket Coverage",
          `${formatAgentNumber(
            Number(
              etf.priced_weight,
            ) * 100,
            2,
          )}%`,
        )}

        ${agentMetric(
          "Weighted Yield",
          `${formatAgentNumber(
            Number(
              etf.weighted_yield_to_maturity,
            ) * 100,
            2,
          )}%`,
        )}

        ${agentMetric(
          "Weighted Spread",
          `${formatAgentNumber(
            etf.weighted_g_spread_bps,
            1,
          )} bp`,
        )}

        ${agentMetric(
          "Duration",
          formatAgentNumber(
            etf.weighted_modified_duration,
            2,
          ),
        )}
      </div>
    </div>
  `;
}


function renderAgentRisk(
  risk,
) {
  if (!risk) {
    return "";
  }

  const keyRates =
    Array.isArray(
      risk.portfolio_key_rate_dv01,
    )
      ? risk.portfolio_key_rate_dv01
      : [];

  const rows =
    keyRates
      .map(
        (item) => `
          <tr>
            <td>
              ${escapeAgentHtml(
                item.tenor,
              )}
            </td>

            <td>
              ${formatAgentNumber(
                item.tenor_years,
                1,
              )}
            </td>

            <td>
              ${formatAgentNumber(
                item.key_rate_duration,
                2,
              )}
            </td>

            <td>
              ${formatAgentNumber(
                item.key_rate_dv01,
                2,
              )}
            </td>
          </tr>
        `,
      )
      .join("");

  return `
    <div class="agent-result-section">
      <h4>
        Portfolio Risk
      </h4>

      <div class="agent-metric-grid">
        ${agentMetric(
          "Market Value",
          formatAgentMoney(
            risk.total_market_value,
          ),
        )}

        ${agentMetric(
          "DV01",
          formatAgentNumber(
            risk.total_dv01,
            2,
          ),
        )}

        ${agentMetric(
          "CS01",
          formatAgentNumber(
            risk.total_cs01,
            2,
          ),
        )}

        ${agentMetric(
          "Instruments",
          formatAgentNumber(
            risk.instrument_count,
            0,
          ),
        )}
      </div>

      ${
        rows
          ? `
            <div class="agent-table-wrap">
              <table class="agent-table">
                <thead>
                  <tr>
                    <th>Tenor</th>
                    <th>Years</th>
                    <th>KRD</th>
                    <th>DV01</th>
                  </tr>
                </thead>

                <tbody>
                  ${rows}
                </tbody>
              </table>
            </div>
          `
          : ""
      }
    </div>
  `;
}


function renderAgentRelativeValue(
  values,
) {
  if (
    !Array.isArray(values)
    || values.length === 0
  ) {
    return "";
  }

  const rows =
    values
      .slice(
        0,
        10,
      )
      .map(
        (item) => `
          <tr>
            <td>
              <button
                type="button"
                class="agent-instrument-link"
                data-agent-instrument-id="${escapeAgentHtml(
                  item.instrument_id,
                )}"
              >
                ${escapeAgentHtml(
                  item.instrument_id,
                )}
              </button>
            </td>

            <td>
              ${formatAgentNumber(
                item.spread_bps,
                1,
              )}
            </td>

            <td>
              ${formatAgentNumber(
                item.peer_average_spread_bps,
                1,
              )}
            </td>

            <td>
              ${formatAgentNumber(
                item.spread_difference_bps,
                1,
              )}
            </td>

            <td>
              ${escapeAgentHtml(
                item.interpretation,
              )}
            </td>
          </tr>
        `,
      )
      .join("");

  return `
    <div class="agent-result-section">
      <h4>
        Top Relative-Value Opportunities
      </h4>

      <div class="agent-table-wrap">
        <table class="agent-table">
          <thead>
            <tr>
              <th>Instrument</th>
              <th>Spread</th>
              <th>Peer Avg</th>
              <th>Difference</th>
              <th>Signal</th>
            </tr>
          </thead>

          <tbody>
            ${rows}
          </tbody>
        </table>
      </div>
    </div>
  `;
}


function renderAgentHedge(
  hedge,
) {
  if (!hedge) {
    return "";
  }

  const treasury =
    Array.isArray(
      hedge.treasury_hedges,
    )
      ? hedge.treasury_hedges
      : [];

  const rows =
    treasury
      .map(
        (item) => `
          <tr>
            <td>
              ${escapeAgentHtml(
                item.tenor,
              )}
            </td>

            <td>
              ${formatAgentNumber(
                item.portfolio_key_rate_dv01,
                2,
              )}
            </td>

            <td>
              ${formatAgentNumber(
                item.hedge_instrument_dv01_per_million,
                2,
              )}
            </td>

            <td>
              ${formatAgentMoney(
                item.recommended_notional,
              )}
            </td>
          </tr>
        `,
      )
      .join("");

  const credit =
    hedge.credit_hedge;

  return `
    <div class="agent-result-section">
      <h4>
        Hedge Recommendations
      </h4>

      <div class="agent-metric-grid">
        ${agentMetric(
          "Residual DV01",
          formatAgentNumber(
            hedge.residual_dv01,
            2,
          ),
        )}

        ${agentMetric(
          "Residual CS01",
          formatAgentNumber(
            hedge.residual_cs01,
            2,
          ),
        )}

        ${
          credit
            ? agentMetric(
                "Credit Hedge",
                formatAgentMoney(
                  credit.recommended_notional,
                ),
              )
            : ""
        }
      </div>

      ${
        credit
          ? `
            <div class="agent-secondary-text">
              ${escapeAgentHtml(
                credit.hedge_instrument,
              )}
            </div>
          `
          : ""
      }

      ${
        rows
          ? `
            <div class="agent-table-wrap">
              <table class="agent-table">
                <thead>
                  <tr>
                    <th>Tenor</th>
                    <th>Portfolio KRD</th>
                    <th>Hedge DV01 / $1MM</th>
                    <th>Recommended Notional</th>
                  </tr>
                </thead>

                <tbody>
                  ${rows}
                </tbody>
              </table>
            </div>
          `
          : ""
      }
    </div>
  `;
}


function renderAgentStress(
  stress,
) {
  if (!stress) {
    return "";
  }

  const marketValue =
    Number(
      stress.total_market_value,
    );

  const pnl =
    Number(
      stress.total_pnl,
    );

  const pnlPercent =
    marketValue
      ? (
          pnl
          / marketValue
          * 100
        )
      : 0;

  return `
    <div class="agent-result-section">
      <h4>
        Stress Test
      </h4>

      <div class="agent-metric-grid">
        ${agentMetric(
          "Total P&L",
          formatAgentMoney(
            stress.total_pnl,
          ),
        )}

        ${agentMetric(
          "Return",
          `${formatAgentNumber(
            pnlPercent,
            2,
          )}%`,
        )}

        ${agentMetric(
          "Treasury P&L",
          formatAgentMoney(
            stress.total_treasury_pnl,
          ),
        )}

        ${agentMetric(
          "Credit P&L",
          formatAgentMoney(
            stress.total_credit_pnl,
          ),
        )}
      </div>
    </div>
  `;
}

function renderAgentResponse(
  payload,
) {
  const result =
    document.getElementById(
      "agentResult",
    );

  if (!result) {
    return;
  }

  const brief =
    payload?.brief;

  if (!brief) {
    result.innerHTML =
      renderAgentList(
        "Errors",
        payload?.errors
        || [
          "The agent returned no brief.",
        ],
      );

    return;
  }

  result.innerHTML = `
    <div class="agent-result-section">
      <h4>
        Summary
      </h4>

      <div class="agent-summary">
        ${escapeAgentHtml(
          brief.summary,
        )}
      </div>
    </div>

    ${renderAgentEtfAnalytics(
      payload.etf_analytics,
    )}

    ${renderAgentRelativeValue(
      payload.relative_value,
    )}

    ${renderAgentRisk(
      payload.risk,
    )}

    ${renderAgentStress(
      payload.stress,
    )}

    ${renderAgentHedge(
      payload.hedge,
    )}

    ${renderAgentList(
      "Market Observations",
      brief.market_observations,
    )}

    ${renderAgentSecurity(
      payload.security,
    )}

    ${renderAgentTools(
      payload.diagnostics,
    )}

    ${renderAgentList(
      "Evidence",
      brief.evidence_summary,
    )}

    ${renderAgentList(
      "Errors",
      payload.errors,
    )}
  `;
}

async function runMercatorAgent() {
  const question =
    document.getElementById(
      "agentQuestion",
    );

  const button =
    document.getElementById(
      "runAgentButton",
    );

  const status =
    document.getElementById(
      "agentStatus",
    );

  const result =
    document.getElementById(
      "agentResult",
    );

  if (
    !question
    || !button
    || !status
    || !result
  ) {
    return;
  }

  const text =
    question.value.trim();

  if (!text) {
    status.textContent =
      "Enter a question";

    question.focus();

    return;
  }

  button.disabled = true;

  status.textContent =
    "Running agent…";

  result.innerHTML = `
    <div class="empty">
      Mercator is planning and running analytics…
    </div>
  `;

  try {
    const response =
      await fetch(
        `${MERCATOR_AGENT_URL}/agent/query`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify(
            {
              question: text,
            },
          ),
        },
      );

    const raw =
      await response.text();

    let payload;

    try {
      payload =
        JSON.parse(raw);
    }

    catch {
      throw new Error(
        raw
        || `HTTP ${response.status}`,
      );
    }

    if (!response.ok) {
      throw new Error(
        `HTTP ${response.status}`,
      );
    }

    renderAgentResponse(
      payload,
    );

    status.textContent =
      payload.errors?.length
        ? "Completed with warnings"
        : "Completed";
  }

  catch (error) {
    console.error(
      "Mercator agent failed:",
      error,
    );

    status.textContent =
      "Failed";

    result.innerHTML = `
      <div class="agent-result-section">
        <h4>Agent Error</h4>

        <div class="agent-error">
          ${escapeAgentHtml(
            error?.message
            || String(error),
          )}
        </div>
      </div>
    `;
  }

  finally {
    button.disabled =
      false;
  }
}


function initializeMercatorAgent() {
  const button =
    document.getElementById(
      "runAgentButton",
    );

  const question =
    document.getElementById(
      "agentQuestion",
    );

  if (
    !button
    || !question
  ) {
    return;
  }

  button.addEventListener(
    "click",
    runMercatorAgent,
  );

  question.addEventListener(
    "keydown",
    (event) => {
      if (
        event.key === "Enter"
        && (
          event.metaKey
          || event.ctrlKey
        )
      ) {
        event.preventDefault();

        runMercatorAgent();
      }
    },
  );

  document
    .querySelectorAll(
      "[data-agent-question]",
    )
    .forEach(
      (example) => {
        example.addEventListener(
          "click",
          () => {
            question.value =
              example.dataset.agentQuestion
              || "";

            question.focus();
          },
        );
      },
    );
}


if (
  document.readyState === "loading"
) {
  document.addEventListener(
    "DOMContentLoaded",
    initializeMercatorAgent,
  );
}

else {
  initializeMercatorAgent();
}
