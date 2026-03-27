# SKILL: NotebookLM Paper-to-Implementation

<!--
name: notebooklm-paper-to-implementation
trigger: User wants to replicate a paper AND generate documentation for NotebookLM ingestion, or sync implementation notes with NotebookLM, or query NotebookLM for implementation guidance
depends-on: [paper-replication, project-scaffold, testing-conventions]
applies-to: [all]
-->

## When to Apply

Read when the user wants to go from paper to working code AND use NotebookLM
as the knowledge management layer. This extends `paper-replication` — if the
user just wants to implement a paper without NotebookLM, use that skill instead.
This skill adds the README-for-NotebookLM generation and MCP sync steps.

Trigger phrases: "replicate this paper for NotebookLM", "generate README for
NotebookLM", "build a notebook for this paper", "sync this with NotebookLM",
"query my NotebookLM notebook", or any paper URL/PDF with both implementation
and NotebookLM intent.

## Dependencies

- **paper-replication** — handles ingestion, scaffolding, and implementation (Steps 0-6).
- **project-scaffold** — Poetry + src/ layout for the project structure.
- **testing-conventions** — validation of the implementation before documenting.

## Rules

1. Always follow `paper-replication` for ingestion, scaffolding, and implementation — this skill governs only the README generation, NotebookLM sync, and adaptation steps.
2. The README is the primary deliverable of this skill — structure it for NotebookLM ingestion, not for GitHub display.
3. Every section in the README must be self-contained so NotebookLM can ground answers against individual sections.
4. Key equations must appear as both LaTeX (for precision) and plain-English pseudocode (for NotebookLM Q&A).
5. Design deviations from the paper must be numbered and explained — these are the highest-value sections for NotebookLM queries.
6. If NotebookLM MCP is available, verify the README was ingested correctly by querying back at least one implementation question.
7. If NotebookLM MCP is NOT available, instruct the user to upload the README manually and provide a list of suggested queries to test ingestion quality.
8. The Glossary section is mandatory — NotebookLM answers degrade without domain term definitions.
9. Results vs Paper must be a comparison table, not prose — tables ground better in NotebookLM.
10. After README generation, update CLAUDE.md to record that NotebookLM documentation was generated and which notebook it was uploaded to.

## Patterns

### NotebookLM-Optimised README Template

Generate this at the project root after the implementation is validated
(paper-replication Steps 3-5 complete). Every section is self-contained
so NotebookLM can ground answers against it independently.

```markdown
# [Paper Title] — Implementation Notes

## What This Is
<!-- 2-3 sentences: paper claim, what was implemented, what was NOT implemented.
     NotebookLM uses this as the overview for general queries. -->
[Paper full citation]. This implementation covers [scope].
Not implemented: [list anything skipped and why].

## How the Code Is Organised
<!-- File-by-file breakdown. NotebookLM uses this to answer
     "where is X implemented?" questions. -->
| File | Paper Section | What it does |
|------|--------------|-------------|
| `src/project_name/models/network.py` | Section 4.2 | Neural network architecture |
| `src/project_name/simulation/gbm.py` | Section 3.1 | GBM path generation |
| `notebooks/03_basic_replication.ipynb` | Section 3 | Simplified 1D version |
| `notebooks/04_full_replication.ipynb` | Sections 3-5 | Full implementation |

## Key Equations Implemented
<!-- Each equation in LaTeX AND plain-English pseudocode.
     NotebookLM handles pseudocode better than raw LaTeX for Q&A. -->

### Eq. (3): CVaR Loss
**LaTeX:** $\text{CVaR}_\alpha = \mathbb{E}[X \mid X \leq \text{VaR}_\alpha]$
**Pseudocode:** Sort all P&L outcomes. Take the worst alpha% (e.g. worst 5%).
Average those — that is the CVaR.
**Implemented in:** `src/project_name/losses.py:cvar_loss()`

### Eq. (7): GBM Simulation
**LaTeX:** $S_{t+1} = S_t \exp\left((r - q - \tfrac{1}{2}\sigma^2)\Delta t + \sigma\sqrt{\Delta t}\, Z\right)$
**Pseudocode:** Next price = current price * exp(drift + volatility * random shock).
**Implemented in:** `src/project_name/simulation/gbm.py:simulate_gbm()`

## Design Decisions & Deviations from Paper
<!-- Numbered. These are the highest-value sections for NotebookLM queries.
     Each must explain WHAT changed and WHY. -->
1. **CVaR alpha=0.05 instead of 0.5** — paper uses 0.5 for stability, we use
   0.05 for better tail coverage matching our risk framework.
2. **SPX options from FirstRate instead of simulated data** — paper uses
   synthetic GBM paths, we substitute real market data for validation.
3. [Continue numbering...]

## Data Requirements
<!-- What data is needed, format, where to get it or what was substituted.
     NotebookLM uses this to answer "what data do I need?" questions. -->
- **Spot prices:** Daily SPX from FirstRate Data API (CSV format)
- **Vol surface:** Strike x expiry grid from Marquee API
- **Risk-free rate:** OIS curve from Bloomberg (or interpolated from SOFR)
- **Substitutions:** [list any data you substituted vs the paper]

## How to Run
<!-- Step-by-step from clone to results. -->
```bash
cd project-name
poetry install
cp .env.example .env   # add FirstRate + Marquee credentials
poetry run python scripts/update_data.py init ~/other-project/data/db/data.db
poetry run jupyter notebook notebooks/04_full_replication.ipynb
```

## Results vs Paper
<!-- TABLE, not prose. Tables ground better in NotebookLM. -->
| Metric | Paper | Ours | Match? | Notes |
|--------|-------|------|--------|-------|
| CVaR (5%) | 0.0234 | 0.0241 | ~yes | Within 3%, likely due to data difference |
| Sharpe | 1.45 | 1.38 | ~yes | Paper uses simulated paths |
| Improvement vs BS | 19% | 17% | ~yes | Consistent direction |

## Open Questions / Next Steps
<!-- What still needs work. Useful for NotebookLM queries like
     "what hasn't been implemented yet?" -->
- [ ] Implement Section 5.3 (multi-asset extension)
- [ ] Test with different alpha values for CVaR
- [ ] Compare against Heston paths instead of GBM

## Glossary
<!-- MANDATORY. NotebookLM Q&A degrades without domain term definitions.
     Define every term a non-specialist might not know. -->
- **CVaR (Conditional Value at Risk):** Expected loss in the worst alpha% of outcomes. Also called Expected Shortfall.
- **Reparameterisation trick:** Separate random noise from learnable parameters so gradients can flow through stochastic operations.
- **GBM (Geometric Brownian Motion):** Standard model for stock price dynamics. Assumes log-normal returns with constant drift and volatility.
- **DV01:** Dollar value of one basis point — how much a position's value changes for a 1bp move in spreads.
- **Walk-forward:** Backtesting method that trains on a rolling window and tests on the next period, avoiding look-ahead bias.
```

### NotebookLM MCP Setup

One-time setup to connect Claude Code or Claude Desktop to NotebookLM.

#### Claude Code (simplest)

```bash
# One command — adds NotebookLM MCP to Claude Code
claude mcp add notebooklm npx notebooklm-mcp@latest
```

That's it. Restart Claude Code and the NotebookLM tools are available.

#### Claude Desktop

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["notebooklm-mcp@latest"]
    }
  }
}
```

Restart Claude Desktop after editing.

#### Verify the connection

```
# In Claude Code or Claude Desktop — should show your notebooks
/notebook list
```

#### Troubleshooting

- **Auth prompt:** First run may open a browser for Google sign-in. Follow the prompts.
- **Node version:** Must be 18+. Check with `node --version`
- **npx not found:** Install Node.js from https://nodejs.org/
- **Cowork note:** Cowork runs in a sandboxed VM. MCP must be configured on the host machine for Claude Desktop, or use Claude Code directly.

### MCP Query Workflow

Once connected, query NotebookLM for implementation guidance:

```
# List available notebooks
/notebook list

# Query for implementation guidance
/notebook ask "What does the paper say about the network architecture in Section 4.2?"

# Cross-reference implementation against paper
/notebook ask "Does our CVaR alpha=0.05 deviation match the paper's stated tolerance?"

# Check data requirements
/notebook ask "What data format does the paper specify for input?"
```

#### Fallback when MCP is not available

If MCP is not configured, use this manual workflow:

1. Upload the generated README to a NotebookLM notebook for the paper
2. Test ingestion quality with these queries:
   - "How is [key equation] implemented in the code?"
   - "What deviations were made from the paper and why?"
   - "What data format does the implementation expect?"
   - "What are the open questions for this implementation?"
3. Paste NotebookLM answers back into the Claude Code session for cross-referencing

### Adaptation Step

After replication is validated and README is generated, adapt for the user's
specific context. Ask the user:

- Where does this implementation integrate in your existing codebase?
- Do you need a standalone Jupyter walkthrough in `/notebooks/`?
- Should the README be split into multiple NotebookLM sources for better granularity?

For project-specific integration:
- **vol_pipeline:** Integrate as a new vol model variant
- **rl_hedging_comparison:** Add as a new hedging strategy to compare
- **credit_macro:** Integrate relevant signals into the CDS strategy framework
- **Standalone learning:** Create a Jupyter walkthrough notebook in `/notebooks/`

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Write the README for GitHub audiences (badges, installation for strangers) | Write for NotebookLM ingestion (self-contained sections, glossary, comparison tables) |
| Dump equations as images or screenshots | Write equations in LaTeX AND plain-English pseudocode |
| Skip the Glossary section | Always include Glossary — NotebookLM Q&A degrades without it |
| Write Results vs Paper as prose | Use a comparison table — tables ground better in NotebookLM |
| Assume MCP is available | Always have a manual-upload fallback path |
| Generate README before implementation is tested | README must reflect validated implementation with actual results |
| Put MCP setup instructions in the project README | MCP setup is a one-time environment concern (see env-setup skill) |

## Checklist

- [ ] `paper-replication` skill followed for ingestion, scaffold, and implementation
- [ ] README generated with all 9 sections populated
- [ ] Glossary includes every domain-specific term
- [ ] Key equations have both LaTeX and plain-English pseudocode
- [ ] Results vs Paper table has actual values (not placeholders)
- [ ] README uploaded to NotebookLM (via MCP or manually)
- [ ] At least one query tested against the NotebookLM notebook to verify ingestion quality
- [ ] CLAUDE.md updated with NotebookLM documentation status
- [ ] Jupyter walkthrough notebook created in `/notebooks/` if applicable
