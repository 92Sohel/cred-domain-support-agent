# Chunking evaluation

Relevant parent document sets are singleton sets because every evaluation query maps
to one policy. The visible arithmetic below is document-level after chunk results are
deduplicated: `precision = relevant retrieved / retrieved`, `recall = relevant
retrieved / relevant documents`.

| Query | Fixed overlap P/R arithmetic | Sentence P/R arithmetic |
|---|---|---|
| How is EMI calculated? | 1/3 = .33; 1/1 = 1.00 | 1/3 = .33; 1/1 = 1.00 |
| What KYC documents are required? | 1/3 = .33; 1/1 = 1.00 | 1/3 = .33; 1/1 = 1.00 |
| What affects a credit score? | 1/3 = .33; 1/1 = 1.00 | 1/3 = .33; 1/1 = 1.00 |
| How do joint account mandates work? | 1/3 = .33; 1/1 = 1.00 | 1/3 = .33; 1/1 = 1.00 |
| Can an NRI open an account? | 1/3 = .33; 1/1 = 1.00 | 1/3 = .33; 1/1 = 1.00 |

Both strategies achieve mean document precision **.33** and recall **1.00** at
top-3. I would deploy sentence chunks because they preserve complete policy sentences
and make citation review easier, while matching the measured document-level scores.
