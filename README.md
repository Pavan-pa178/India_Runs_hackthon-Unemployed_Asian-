# Intelligent Candidate Discovery & Ranking

> **Redrob Hackathon Submission** | Team Unemployed_Asians | Senior AI Engineer (Founding Team) Ranking Challenge

A fully transparent, rule-based candidate ranker. No embeddings. No LLM calls. No training step. Every score can be traced to a specific line of code and a specific reason.

---

## Quick Start

```bash
# 1. Place candidates.jsonl in the repo root (or use --candidates flag)
# 2. Run the ranker
python3 rank.py

# 3. Output lands here
#    outputs/submission.csv
```

**With custom paths:**

```bash
python3 rank.py --candidates /path/to/candidates.jsonl --out /path/to/submission.csv
```

**No dependencies required** — Python 3.9+ standard library only. On 100K candidates: ~60s runtime, ~1.7GB RAM, CPU-only, zero network calls.

---

## Pipeline Overview

The system processes candidates through a three-stage pipeline: **Base Scoring** → **Multiplier Adjustments** → **Rank & Output**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA LOADING                                 │
│  candidates.jsonl (or .jsonl.gz) → list of candidate dicts          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 1: BASE SCORING                            │
│                                                                     │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────┐  │
│  │    TITLE      │  │    SKILL     │  │ EXPERIENCE │  │ EVIDENCE │  │
│  │   RELEVANCE   │  │    MATCH     │  │    FIT     │  │  BONUS   │  │
│  │   (×0.40)     │  │   (×0.30)    │  │  (×0.15)   │  │ (×0.15)  │  │
│  │               │  │              │  │            │  │          │  │
│  │ title prior   │  │ skill weight │  │ 5-9yr band │  │ career   │  │
│  │ from taxon.   │  │ × prof mult  │  │ soft score │  │ history  │  │
│  │               │  │ × endorse    │  │            │  │ regex    │  │
│  │               │  │ ÷ MAX (6.0)  │  │            │  │ patterns │  │
│  └──────┬────────┘  └──────┬───────┘  └─────┬──────┘  └────┬─────┘  │
│         │                  │                │              │        │
│         └────────┬─────────┴────────┬───────┘──────────────┘        │
│                  │                  │                               │
│                  ▼                  ▼                               │
│         base_score = 0.40×T + 0.30×S + 0.15×E + 0.15×V              │
│                                                                     │
│  Skill match is discounted by corroboration:                        │
│  buzzwords without career-history evidence → 0.5×–0.9× penalty      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  STAGE 2: MULTIPLIER ADJUSTMENTS                    │
│                                                                     │
│  ┌───────────────────┐  ┌─────────────────┐  ┌──────────────────┐   │
│  │   DISQUALIFIER    │  │    ANOMALY      │  │   AVAILABILITY   │   │
│  │   MULTIPLIER      │  │   MULTIPLIER    │  │   MULTIPLIER     │   │
│  │                   │  │                 │  │                  │   │
│  │ title chasers     │  │ expert count    │  │ last active date │   │
│  │ consulting-only   │  │ honeypot bucket │  │ recruiter resp.  │   │
│  │ CV/speech-only    │  │ skill > career  │  │ open to work     │   │
│  │ architecture-only │  │ zero-duration   │  │ notice period    │   │
│  │ LangChain-only    │  │ overlapping edu │  │ interview rel.   │   │
│  │                   │  │ bait skills     │  │ location/visa    │   │
│  │                   │  │ dupl. desc.     │  │                  │   │
│  └─────────┬─────────┘  └────────┬────────┘  └────────┬─────────┘   │
│            │                     │                    │             │
│            └────────────┬────────┴────────────────────┘             │
│                         │                                           │
│          adjusted = base × D × A × V                                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 3: RANK & OUTPUT                           │
│                                                                     │
│  final_score = adjusted × 100                                       │
│  Sort descending → take top 100 → generate reasoning → write CSV    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
.
├── rank.py                    # Entry point: load → score → rank → write CSV
├── src/
│   ├── __init__.py
│   ├── title_taxonomy.py      # Title → relevance prior (encodes Finding #1)
│   ├── skill_taxonomy.py      # Skill name → relevance weight by tier
│   ├── experience.py          # 5–9 year band scoring (soft, per JD framing)
│   ├── coherence.py           # Career-history evidence + skill corroboration
│   ├── disqualifiers.py       # JD's "things we do NOT want" penalties
│   ├── anomaly.py             # Honeypot defenses (Findings #1 & #2)
│   ├── behavioral.py          # redrob_signals → availability multiplier
│   ├── scorer.py              # Combines all modules into final_score
│   └── reasoning.py           # Per-candidate reasoning text generation
├── sandbox/
│   ├── app.py                 # Streamlit demo (Section 10.5 compliant)
│   └── requirements.txt       # streamlit only
├── submission_metadata.yaml   # Portal metadata mirror
├── requirements.txt           # No third-party deps (stdlib only)
├── README.md                  # This file
└── .gitignore
```

### Module Reference

| Module | Purpose | Key Function | Inputs | Outputs |
|--------|---------|-------------|--------|---------|
| `title_taxonomy.py` | Maps current title to relevance score. 13 honeypot-bucket titles penalized to 0.25. | `title_prior(title)` | `profile.current_title` | `float 0.03–0.78` |
| `skill_taxonomy.py` | Categorizes skills into tiers (core/buzzword/adjacent/data-infra/bait/noise) with empirical weights. | `skill_weight(name)` | skill name | `float 0.0–1.0` |
| `experience.py` | Scores years-of-experience fit. 5–9 year band = 1.0, decays outside. | `experience_fit_score(yoe)` | `profile.years_of_experience` | `float 0.2–1.0` |
| `coherence.py` | Regex scan of career-history text for evidence of ranking/recommendation/search work. Also discounts uncorroborated buzzwords. | `evidence_bonus(history)` | `career_history` | `float 0.0–0.8` + matched categories |
| `disqualifiers.py` | Penalizes title-chasers, consulting-only careers, CV-only backgrounds, architecture-only roles, recent-LangChain-only. | `compute_disqualifier_multiplier(candidate)` | full candidate dict | `float` + flag list |
| `anomaly.py` | Honeypot defenses: expert-count curve, bucket-title penalty, skill-duration impossibilities, zero-duration experts, bait skills, duplicate descriptions. | `compute_anomaly_multiplier(candidate)` | full candidate dict | `float` + flag list |
| `behavioral.py` | Availability signals: recency, responsiveness, open-to-work, notice period, interview reliability, location/visa. | `compute_availability_multiplier(candidate)` | full candidate dict | `float` + flag list |
| `scorer.py` | Orchestrates all modules. Computes base score, applies multipliers, returns final score + breakdown. | `score_candidate(candidate)` | full candidate dict | score dict with all components |
| `reasoning.py` | Generates 1–2 sentence human-readable reasoning per candidate from score flags and matched skills. | `generate_reasoning(candidate, score, rank)` | candidate + score result + rank | reasoning string |

---

## Scoring Formula

```
base_score = 0.40 × title_relevance
           + 0.30 × skill_match (discounted if uncorroborated)
           + 0.15 × experience_fit
           + 0.15 × career_evidence_bonus

adjusted_score = base_score
               × disqualifier_multiplier    (role/culture fit issues)
               × anomaly_multiplier          (honeypot defenses)
               × availability_multiplier     (behavioral signals + location)

final_score = adjusted_score × 100
```

### Weight Breakdown

| Component | Weight | What It Captures |
|-----------|--------|-----------------|
| Title Relevance | 40% | Does the candidate's title match the JD's target profile? |
| Skill Match | 30% | Do listed skills overlap with JD requirements? (discounted without career-history corroboration) |
| Experience Fit | 15% | Is the candidate in the 5–9 year experience band? |
| Career Evidence | 15% | Does career history contain evidence of ranking/recommendation/search work? |

### Multiplier Stages

| Multiplier | Purpose | Range |
|------------|---------|-------|
| Disqualifier | JD's explicit exclusions (title-chasers, consulting-only, CV-only, architecture-only, LangChain-only) | 0.45–1.0 |
| Anomaly | Honeypot detection (expert-count curve, bucket-title penalty, duration impossibilities) | 0.02–1.0 |
| Availability | Behavioral signals (recency, responsiveness, notice period, location/visa) | 0.05–1.0 |

---

## Key Data Findings

Three empirical findings from analyzing `candidates.jsonl` shaped every design decision.

### Finding #1: The "perfect match" titles are honeypots

| Metric | Value |
|--------|-------|
| Honeypot-bucket titles | 13 (Senior AI Engineer, Staff ML Engineer, etc.) |
| Candidates with these titles | 179 |
| % with ≥2 expert skills | **100%** (vs ~0% elsewhere) |
| Real signal candidates | 3,195 with ML-adjacent titles (Data Scientist, ML Engineer, etc.) |

**Conclusion:** A keyword-similarity ranker would put fabricated profiles at the top. Title relevance must be inverted for these 13 titles.

### Finding #2: Intuitive honeypot checks were too aggressive

| Check Tried | Candidates Flagged | Actual Honeypots | Verdict |
|-------------|-------------------|-----------------|---------|
| YOE vs career history mismatch | ~40,000 | ~80 | Too noisy |
| Overlapping education dates | ~30,000 | ~80 | Too noisy |
| Copy-pasted role descriptions | ~25,000 | ~80 | Too noisy |
| Expert skill count (≥2) | 179 | 179 | **Precise signal** |

**Conclusion:** Keep these checks as gentle penalties, not hard filters. The expert-skill-count is the real discriminator.

### Finding #3: Career-history text rarely corroborates skills

The career history descriptions come from a generic, templated pool. Regex evidence patterns (ranking systems, recommendation engines, search/retrieval, embeddings) rarely fire. Most ranking signal comes from the skills list checked for internal consistency, not from free-text evidence.

---

## Honeypot Defense Strategy

The system deploys 7 layered defenses against fabricated profiles:

| # | Defense | Mechanism | Penalty |
|---|---------|-----------|---------|
| 1 | **Honeypot bucket title + expert skills** | Title from the 13 fabricated titles AND ≥2 expert skills | Score × 0.15 |
| 2 | **Expert skill count curve** | General penalty scaling with expert count (outside bucket) | 0.12–0.92× |
| 3 | **Skill duration > career total** | Any skill "used" longer than the person's entire career | 0.35–0.85× |
| 4 | **Zero-duration expert** | "Expert" proficiency with 0 months of use | 0.2–0.5× |
| 5 | **Bait skill vocabulary** | Suspiciously polished skill names found only on fabricated profiles | 0.5–0.88× |
| 6 | **Overlapping education** | Degree dates that overlap impossibly | 0.75–0.97× |
| 7 | **Duplicate role descriptions** | Same description copy-pasted across roles | 0.93× |

**Result:** 0% honeypot rate in top 100, compared to 48–76% on naive reference rankings.

---

## Compute Constraints

| Constraint | Limit | Our Usage |
|------------|-------|-----------|
| Runtime | ≤ 5 minutes | ~60 seconds |
| Memory | ≤ 16 GB | ~1.7 GB |
| Compute | CPU only | ✅ |
| Network | Off | ✅ Zero calls |
| Disk | ≤ 5 GB | Minimal |
| Dependencies | — | Zero (stdlib only) |

---

## Known Limitations

1. **Career-history evidence rarely triggers.** The regex mechanism works correctly but the dataset's templated descriptions don't reliably mention specific skills. Most signal comes from the skills list itself.

2. **Honeypot-bucket title list is dataset-specific.** The 13 fabricated titles were identified from this exact pool. The *method* (clustering suspicious signals by title) generalizes, but the specific list would need re-derivation for a different evaluation set.

3. **No deep NLP on free-text fields.** `profile.summary` and career descriptions are used only for the narrow evidence check. A language model could extract more, but would violate the compute budget.

---

## Reproducing from Scratch

```bash
git clone <this-repo>
cd <this-repo>
cp /path/to/candidates.jsonl .
python3 rank.py
# Output: outputs/submission.csv
```

Or point directly at the data:

```bash
python3 rank.py --candidates /path/to/candidates.jsonl --out submission.csv
```

---

## AI Tools Declaration

**Tools used:** Claude, ChatGPT

**How they were used:**
- **Claude:** Reasoning through scoring logic, assessing code correctness, debugging issues during development, and understanding concepts to develop ideas for the ranking approach.
- **ChatGPT:** Understanding hackathon requirements and constraints, analyzing the job description and Redrob signals, figuring out what needed to be built within the compute limits.

**What was NOT done with AI:** No candidate data was sent to any external LLM API during ranking. The ranker is offline, rule-based, and has zero network calls at ranking time.

---

## Team

| Name | Email |
|------|-------|
| KOTAPROLU PAVAN KUMAR (Primary) | pavan.kotaprolu@gmail.com |
| Mantha Sai Teja | mst4offl@gmail.com |
| Paluri Joseph Roland | josephroland409@gmail.com |
| Niya Sharma | niya93428@gmail.com |
