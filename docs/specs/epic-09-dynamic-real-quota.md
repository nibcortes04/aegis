# Technical Specification: EPIC-09 — Dynamic Real Quota & Live Metrics Integration

**Epic ID:** EPIC-09  
**GitHub Issue:** [#1](https://github.com/nibcortes04/aegis/issues/1)  
**Status:** In Progress (Sprint 2)  
**Architect:** Nicolas Cortes (@nibcortes04)  
**AI Pair Engine:** Gemini 3.8 Flash (High) via Antigravity (AGY)  

---

## 1. Executive Summary & Problem Statement

Line 2 of the Aegis statusline displays mission-critical developer telemetry:
1. **Context Window Utilization:** Graphical 10-block progress bar (`███░░░░░░░ 35%`), active token consumption, and saturation warnings.
2. **Cumulative Spend & Session Duration:** Total cost in USD (`💰 $0.0245`) and active wall-clock time (`⏱ 14m32s`).
3. **Rolling Quotas:** 5-hour rolling tier with localized reset timestamp (`5h:32% (🕦14:30)`) and 7-day weekly tier (`7d:18%`).

### Problem:
In varied environments—such as disconnected development, background subagents, headless CI runs, or when the AGY runtime does not populate the full telemetry payload on `stdin`—the statusline could omit quota metrics or show zeroed context usage.

### Solution:
**EPIC-09** introduces a resilient, multi-tiered telemetry engine:
1. **Live Telemetry Hook Listener:** Extracts usage metrics (`context_window`, `cost`, `quota`) from AGY runtime hook payloads and caches them atomically in `~/.gemini/antigravity-cli/.aegis_live_telemetry.json`.
2. **Sub-millisecond SQLite Fallback:** When live telemetry is absent or incomplete, queries the per-session SQLite database (`conversations/<conv_id>.db` / `conversation_summaries.db`) to compute empirical token count, step volume, elapsed duration, and estimated spend based on model tier.
3. **Visual Threshold Indicators:** Color-coded saturation alarms (Green → Yellow → Red 🚨) for context window (>70%, >90%), spend (> $0.10, > $0.50 💸), and rolling quotas (>50%, >80% 🚨).
4. **CLI & MCP Surface:** Direct inspection via `aegis metrics` / `aegis quota` and the `aegis_get_live_metrics` MCP tool.

---

## 2. Multi-Tier Telemetry Architecture

```
                      +------------------------------------------+
                      |       AGY Runtime / Hook Invocations     |
                      +------------------------------------------+
                                           |
                    [stdin payload or hook event telemetry]
                                           v
                   +-----------------------------------------------+
                   | Tier 1: Live Payload (Runtime Stdin)          |
                   |   • context_window (used_percentage, tokens)  |
                   |   • cost (total_cost_usd, duration_ms)        |
                   |   • quota (gemini-5h, gemini-weekly)          |
                   +-----------------------------------------------+
                                           |
                                [If missing / incomplete]
                                           v
                   +-----------------------------------------------+
                   | Tier 2: Atomic Telemetry Cache File           |
                   |   • ~/.gemini/antigravity-cli/                |
                   |     .aegis_live_telemetry.json                |
                   |   • Ingested by PreToolUse / Stop hooks       |
                   +-----------------------------------------------+
                                           |
                                [If offline / uninitialized]
                                           v
                   +-----------------------------------------------+
                   | Tier 3: Local SQLite Engine Fallback          |
                   |   • conversations/<conv_id>.db                |
                   |     -> gen_metadata (count, sum(size))        |
                   |     -> steps (step count, duration)           |
                   |   • conversation_summaries.db                 |
                   |     -> step_count, last_modified_time         |
                   |   • Empirical pricing: $0.15 / 1M tokens      |
                   +-----------------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |       Formatted 3-Line Statusline        |
                      |   Line 2: [███████░░░ 72% ⚠️]            |
                      |           │ 💰 $0.1420 │ ⏱ 12m40s        |
                      |           │ 5h:64% (🕦22:15) 7d:28%     |
                      +------------------------------------------+
```

---

## 3. Visual Threshold Indicators & Alert Bands

### 3.1 Context Window Saturation
| Range | Visual Indicator | Status / Behavior |
| :--- | :--- | :--- |
| **0% – 69%** | `\033[32m███░░░░░░░ 35%\033[0m` (Green) | Normal operating capacity. |
| **70% – 89%** | `\033[33m███████░░░ 75% ⚠️\033[0m` (Yellow) | Warning threshold; prompt compaction recommended. |
| **90% – 100%+** | `\033[31m█████████░ 94% 🚨\033[0m` (Red) | Critical saturation; session truncation imminent. |

### 3.2 Cumulative Spend
| Range | Visual Indicator | Cost Tier |
| :--- | :--- | :--- |
| **< $0.10** | `\033[32m💰 $0.0340\033[0m` (Green) | Standard low-overhead tier. |
| **$0.10 – $0.49** | `\033[33m💰 $0.2450\033[0m` (Yellow) | Moderate development spend. |
| **>= $0.50** | `\033[35m💸 $0.6210 ⚠️\033[0m` (Magenta) | High investment / complex agent loop alert. |

### 3.3 Rolling Quota (5h / 7d)
| Usage | Color / Icon | Alert Note |
| :--- | :--- | :--- |
| **< 50%** | Green | High availability. |
| **50% – 79%** | Yellow | Moderate depletion. |
| **>= 80%** | Red `🚨` | Critical quota warning; resets at `(🕦HH:MM)`. |

---

## 4. Offline SQLite Estimation Formulae

When live metrics are not supplied by the runtime:
1. **Estimated Tokens:**
   $$\text{Tokens} = \sum (\text{size}_{\text{gen\_metadata}} / 4.0)$$
   Fallback if `gen_metadata` is empty: $\text{Tokens} = \text{step\_count} \times 1200$.
2. **Context Window Percentage:**
   $$\text{Used \%} = \min\left(100.0, \frac{\text{Tokens}}{\text{Max Tokens}} \times 100.0\right)$$
   (Where $\text{Max Tokens} = 200,000$ by default, or $1,000,000$ for Gemini Pro/Flash long-context models).
3. **Estimated Spend:**
   $$\text{Spend (USD)} = \frac{\text{Tokens}}{1,000,000} \times 0.15$$
4. **Estimated Duration:**
   Calculated from file timestamps (`mtime` - `ctime` or SQLite `last_modified_time` - initial step timestamp).

---

## 5. Delivery Checklist & Validation Criteria

- [x] Technical specification authored (`docs/specs/epic-09-dynamic-real-quota.md`).
- [ ] Telemetry cache and hook listener module in `scripts/statusline_formatter.py` and `scripts/agy_hook_handler.py`.
- [ ] Sub-millisecond SQLite fallback engine implemented and benchmarked (< 5ms query time).
- [ ] Visual threshold warning badges integrated into Line 2 formatting.
- [ ] CLI command `aegis metrics` and `aegis quota` exposed in `bin/aegis`.
- [ ] MCP tool `aegis_get_live_metrics` registered in `mcp/mcp_server.py`.
- [ ] Unit test suite in `tests/test_quota_metrics.py` verifying live, cache, and SQLite fallback paths.
- [ ] Autonomous quality gate certified (`scripts/bot_pr_check.py`).
