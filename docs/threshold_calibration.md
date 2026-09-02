# Retrieval threshold calibration

Calibration used the sentence collection's top-1 token-cosine similarity in the
offline deterministic mode, after filtering ordinary stop words and indexing policy
titles alongside text. In-scope probes measured: EMI calculation **0.487**, KYC
documents **0.433**, and joint account mandate **0.387**. Deliberately out-of-scope
probes measured: cricket score **0.000** and tomorrow's weather **0.000**.

The chosen threshold is **0.10**, which lies between the observed clusters rather
than using a tutorial default. `GROUNDING_THRESHOLD` is defined in `src/rag.py`;
queries below it receive the explicit "I don't know" fallback.
