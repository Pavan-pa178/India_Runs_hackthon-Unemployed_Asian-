"""
Streamlit sandbox app -- satisfies submission_spec.md Section 10.5.

Accepts a small candidate sample (<=100 candidates) as a JSONL upload,
runs the same ranking pipeline used for the full submission, and displays
the ranked output as a table plus a downloadable CSV.

Deploy on Streamlit Community Cloud (free tier):
  1. Push this repo to GitHub.
  2. https://share.streamlit.io -> New app -> point at this repo,
     entry point: sandbox/app.py
  3. No secrets/env vars needed -- the app has zero external dependencies
     beyond streamlit itself.

Run locally:
  pip install streamlit
  streamlit run sandbox/app.py
"""

import sys
import json
import csv
import io
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.scorer import score_candidate
from src.reasoning import generate_reasoning

st.set_page_config(page_title="Redrob Ranker Sandbox", layout="wide")

st.title("Redrob Candidate Ranker — Sandbox")
st.markdown(
    "Upload a small sample of candidates (JSONL, one JSON object per line, "
    "matching `candidate_schema.json`) to see the ranking pipeline run "
    "end-to-end. This sandbox is for **reproducibility verification only** "
    "(per submission_spec.md Section 10.5) — the full 100K-candidate "
    "submission is produced by `rank.py` directly, not through this UI."
)

uploaded = st.file_uploader("Candidate sample (.jsonl)", type=["jsonl", "json", "txt"])

if uploaded is not None:
    raw_text = uploaded.read().decode("utf-8")
    candidates = []
    errors = []
    for i, line in enumerate(raw_text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            candidates.append(json.loads(line))
        except json.JSONDecodeError as e:
            errors.append(f"Line {i+1}: {e}")

    if errors:
        st.error(f"{len(errors)} line(s) failed to parse:")
        for e in errors[:10]:
            st.text(e)

    if candidates:
        if len(candidates) > 100:
            st.warning(f"Sample has {len(candidates)} candidates; sandbox is intended for <=100. Proceeding anyway.")

        with st.spinner(f"Scoring {len(candidates)} candidates..."):
            results = []
            for c in candidates:
                try:
                    r = score_candidate(c)
                    results.append((c, r))
                except (KeyError, TypeError) as e:
                    st.error(f"Candidate {c.get('candidate_id', '?')} failed to score: {e}")

            results.sort(key=lambda x: (-x[1]["final_score"], x[1]["candidate_id"]))

            rows = []
            for rank, (c, r) in enumerate(results, start=1):
                reasoning = generate_reasoning(c, r, rank)
                rows.append({
                    "candidate_id": r["candidate_id"],
                    "rank": rank,
                    "score": r["final_score"],
                    "reasoning": reasoning,
                })

        st.success(f"Ranked {len(rows)} candidates.")
        st.dataframe(rows, use_container_width=True)

        # Downloadable CSV
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        writer.writerows(rows)
        st.download_button(
            "Download ranked CSV",
            data=buf.getvalue(),
            file_name="sandbox_ranking.csv",
            mime="text/csv",
        )
    else:
        st.info("No valid candidate rows found in the upload.")
else:
    st.info("Upload a .jsonl sample to run the ranker. You can extract a small "
            "sample from the full candidates.jsonl with: `head -n 20 candidates.jsonl > sample.jsonl`")
