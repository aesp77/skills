# SKILL: Paper Replication

<!--
name: paper-replication
trigger: Reading an academic paper, replicating its findings, or adapting a published method to a specific problem
depends-on: [notebook-workflow, experiment-logging]
applies-to: [all]
-->

## When to Apply

Read before starting work on an academic paper — whether replicating results,
implementing a method, or adapting a published approach to your own problem.

## Dependencies

- **notebook-workflow** — notebooks follow numbering and cell conventions.
- **experiment-logging** — all replication results are logged.

## Rules

1. Always start by extracting the paper's **claims, data, method, and evaluation** before writing any code.
2. Replicate the paper's results first — only then adapt to your problem.
3. Each paper gets its own directory: `papers/<short-name>/`
4. PDFs live in `papers/<short-name>/paper.pdf` — never rename the original.
5. One notebook per stage — notebooks evolve from simple to complex.
6. **Paper notebooks stay as notebooks** — they are study material, not production code.
7. When something is worth keeping, extract it to `src/` **in the main project** — not in the paper directory.
8. Log replication results and compare against the paper's reported numbers.

## Patterns

### Directory Structure

Paper work lives in its own directory. It stays there for study and reference.
Production code graduates to the main project's `src/`.

```
project-root/
├── src/                                    # production code (main project)
│   └── project_name/
│       └── models/
│           └── deep_hedging.py             # ← extracted from paper notebooks
│
├── papers/                                 # study material (stays here)
│   └── deep-hedging-buehler-2019/
│       ├── paper.pdf                       # original paper
│       ├── notes.md                        # extracted summary
│       └── notebooks/
│           ├── 01_paper_breakdown.ipynb    # read & understand
│           ├── 02_data_setup.ipynb         # prepare data
│           ├── 03_basic_replication.ipynb  # simplest version first
│           ├── 04_full_replication.ipynb   # complete implementation
│           ├── 05_validation.ipynb         # compare vs paper's numbers
│           └── 06_my_adaptation.ipynb      # apply to my problem
```

### Notebook Evolution — Simple to Complex

The key principle: **start with the simplest possible version and build up**.
Each notebook is more complex than the previous one.

```
01_paper_breakdown    — no code, just reading and extracting
02_data_setup         — get the data working, nothing else
03_basic_replication  — simplest version of the method (toy example, 1D, small data)
04_full_replication   — full version matching the paper's setup
05_validation         — compare numbers, document differences
06_my_adaptation      — modify for your use case
```

This progression means:
- You can stop at any notebook and still have something useful
- Each notebook can be studied independently
- A reader can follow your thinking from simple to complex
- If notebook 04 breaks, you still have 03 as a working baseline

### Step 1 — Paper Breakdown (notes.md)

Do this before writing any code.

```markdown
# Paper: [Title]
**Authors:** [names]
**Year:** [year]
**Link:** [url if available]

## Core Claim
[1-2 sentences: what does this paper claim to show?]

## Method
[Numbered steps of the algorithm/approach]
1. ...
2. ...
3. ...

## Key Equations
[The equations you'll need to implement, with equation numbers from the paper]
- Eq. (3): ...
- Eq. (7): ...

## Data Used
[What data did they use? Can you access it or simulate it?]

## Reported Results
[The numbers you're trying to replicate — tables, figures, metrics]
- Table 1: ...
- Figure 3: ...

## Assumptions & Limitations
[What did they assume? What might not hold for your use case?]

## Relevance to My Work
[Why are you reading this? What would you apply it to?]

## Dependencies on Other Skills
[Which skills will be needed for implementation?]
```

### Step 2 — Data Setup (Notebook 02)

Just get the data working. No method implementation yet.

```python
# Cell 1: Setup
import os
os.environ["KERAS_BACKEND"] = "torch"

# Cell 2: What data the paper uses
"""
Paper uses: [describe]
My approach: [same data / synthetic / my market data]
"""

# Cell 3+: Load or generate data, verify it looks right

# Last cell:
"""
FINDINGS:
- Data matches paper's Section [X]
- Differences: [list]
- Ready for replication: YES/NO
"""
```

### Step 3 — Basic Replication (Notebook 03)

The simplest possible version. Toy example, small data, 1D if possible.
Prove the core idea works before scaling up.

```python
# Cell 1: Setup

# Cell 2: What we're implementing
"""
Implementing the CORE of Section [X] — simplified version:
- [simplification 1: e.g. 1D instead of multi-dimensional]
- [simplification 2: e.g. 100 paths instead of 100,000]
- [simplification 3: e.g. constant vol instead of stochastic]

Goal: verify the basic mechanism works before adding complexity.
"""

# Cell 3+: Implement step by step, referencing equation numbers
def core_method(x):
    """Eq. (3) from [Author] ([Year]) — simplified version."""
    ...

# Cell: Quick sanity check
# "With these simple inputs, I expect roughly [X] based on the paper"

# Last cell:
"""
FINDINGS:
- Basic version works / doesn't work
- Output looks reasonable / unexpected because [reason]
- Ready to scale up: YES/NO
"""
```

### Step 4 — Full Replication (Notebook 04)

Full implementation matching the paper's setup.

```python
# Cell 2: What changed from basic version
"""
Upgrading from notebook 03:
- [added: stochastic vol instead of constant]
- [added: full 100,000 paths]
- [added: transaction costs]
- [matches paper's Section [X] setup exactly]
"""

# Cell 3+: Full implementation

# Last cell:
"""
FINDINGS:
- Full replication complete
- Key results: [list metrics]
- Ready for validation: YES
"""
```

### Step 5 — Validation (Notebook 05)

Compare your numbers against the paper.

```python
paper_results = {
    "table_1_metric_a": 0.0234,
    "table_1_metric_b": 0.0189,
}

my_results = {
    "table_1_metric_a": ...,
    "table_1_metric_b": ...,
}

def compare_results(paper, mine, tolerance=0.1):
    for key in paper:
        if isinstance(paper[key], (int, float)):
            diff = abs(paper[key] - mine[key]) / abs(paper[key])
            status = "MATCH" if diff < tolerance else "DIFFERS"
            print(f"  {key}: paper={paper[key]:.4f}, mine={mine[key]:.4f}, "
                  f"diff={diff*100:.1f}% [{status}]")

# Last cell:
"""
REPLICATION RESULTS:
- Table 1: [MATCH/DIFFERS] — [explanation]
- Differences caused by: [list reasons]
"""
```

### Step 5b — NotebookLM README (Optional)

After validation, generate a README structured for NotebookLM ingestion.
Upload it to a NotebookLM notebook so you can query the paper's concepts
and your implementation interactively.

```markdown
# [Paper Title] — Implementation Notes

## What This Is
[2-3 sentences: paper claim, what we implemented, what we didn't]

## Key Equations Implemented
[For each major equation: the equation, which file/function implements it]
- Eq. (3): CVaR loss → `src/losses.py:cvar_loss()`
- Eq. (7): GBM simulation → `src/simulation.py:simulate_gbm()`

## How the Code Is Organised
[File-by-file: what each file does, which paper section it implements]
| File | Paper Section | What it does |
|------|--------------|-------------|
| `notebooks/03_basic_replication.ipynb` | Section 3 | Simplified 1D version |
| `notebooks/04_full_replication.ipynb` | Sections 3-5 | Full implementation |
| `src/models/hedging_network.py` | Section 4.2 | Neural network architecture |

## Design Decisions & Deviations
[Numbered: where we diverged and why]
1. Used CVaR alpha=0.05 instead of 0.5 — better tail coverage for our data
2. Substituted SPX options from FirstRate for paper's simulated data

## Results vs Paper
| Metric | Paper | Ours | Match? |
|--------|-------|------|--------|
| CVaR | 0.0234 | 0.0241 | ~yes |

## Glossary
[Domain terms — especially useful for NotebookLM Q&A]
- **CVaR**: Conditional Value at Risk — expected loss in worst alpha% of outcomes
- **Reparameterisation trick**: Separate noise from parameters so gradients flow
```

**After generating:** upload this README to a NotebookLM notebook for that paper.
Then you can ask NotebookLM source-grounded questions like:
- "What does the paper say about handling missing data?"
- "Does our deviation in Step 3 match the paper's stated tolerance?"
- "Explain the reparameterisation trick as used in this paper"

**If NotebookLM MCP is configured** (see env-setup skill), you can query
directly from Claude Desktop without switching apps.

### Step 6 — Adaptation (Notebook 06)

Apply to your problem. Document every change.

```python
# Cell 2: Adaptation plan
"""
Paper method: [what it does]
My problem: [what I need]

Changes:
1. [replaced simulated data with my SPX data]
2. [modified loss function for my risk preferences]
3. [added features from my market data]
"""

# Last cell:
"""
FINDINGS:
- Method [works/doesn't work] for my problem because [reason]
- Performance: [metrics vs my existing approach]

EXTRACT TO src/: [YES/NO]
- [function_a() — worth keeping because ...]
- [class_b — adapts well to my pipeline]
"""
```

### Extracting to Production

When a paper produces useful code, it moves to the **main project's** `src/`.
The paper notebooks stay as-is for future reference.

```python
# In src/project_name/models/deep_hedging.py
# Extracted from papers/deep-hedging-buehler-2019/notebooks/04_full_replication.ipynb

"""Deep hedging implementation based on Buehler et al. (2019).

Adapted for our use case:
- Uses our market data schema (market-data skill)
- Modified loss function (CVaR alpha=0.05 instead of 0.5)
- Added vol surface features from our interpolator

Original paper: papers/deep-hedging-buehler-2019/paper.pdf
Replication notebooks: papers/deep-hedging-buehler-2019/notebooks/
"""
```

### When a Paper Isn't Worth Replicating

After Step 1 (breakdown), check:

- **Data**: Can you access or simulate their data?
- **Complexity vs payoff**: Is the method complex but the improvement marginal?
- **Assumptions**: Do their assumptions hold for your use case?
- **Already solved**: Does your existing toolkit already handle this?

If unfavourable, document why in `notes.md` and move on.

## Banned Patterns

| Do NOT do | Do instead |
|---|---|
| Start coding before reading the full paper | Complete notes.md first |
| Jump straight to full implementation | Start simple (notebook 03), then scale up (04) |
| Replicate and adapt at the same time | Replicate first (03-05), adapt second (06) |
| Skip validation against paper's numbers | Always compare in notebook 05 |
| Move paper notebooks to `src/` | Paper notebooks stay as study material |
| Extract to `src/` inside the paper directory | Extract to main project's `src/` |
| Put everything in one massive notebook | One notebook per stage, simple to complex |

## Checklist

- [ ] `notes.md` completed — claims, method, equations, data, reported results
- [ ] Notebooks progress from simple (03) to complex (04)
- [ ] Basic replication works before attempting full replication
- [ ] Results compared against paper's reported numbers (notebook 05)
- [ ] Differences documented with hypotheses
- [ ] Adaptation notebook (06) documents every change from original
- [ ] Useful code extracted to main project's `src/`, not paper directory
- [ ] Paper notebooks preserved as study material
- [ ] NotebookLM README generated and uploaded (if using NotebookLM)
