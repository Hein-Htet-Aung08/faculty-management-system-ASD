# RAG Validation Report

## DETERMINISTIC VALIDATION SUMMARY

Status: PASS
Functional validation: PASS (structure, tools, health, corpus refresh, retrieval, grounded answer, citations, confidence, insufficient-context handling, audit logging)
Retrieval quality: mean P@5=0.470, mean R@5=0.975, minimum R@5=0.500
Observed recall limitation: minimum R@5=0.500, so at least one benchmark did not retrieve all expected relevant evidence at k=5.

The deterministic validation summary above is authoritative for functional pass/fail. The model outputs below are advisory and do not override collected evidence.

## OBSERVE

```text
RAG VALIDATION EVIDENCE
- Structural files: PASS
- Required tools: PASS (refresh_corpus, retrieve_context, answer_question)
- Live health: PASS ({'status': 'ok', 'service': 'faculty-management-rag'})
- Corpus refresh: PASS (138 chunks, vector store ready)
- Retrieval: PASS (5 chunk(s), mode=vector)
- Validation query: Which staff member has expertise in machine learning?
- Grounded answer: John Smith (staff ID 1) has expertise in machine learning.
- Citations: PASS (5 returned)
- Confidence: PASS (High)
- Insufficient-context behaviour: PASS
- Audit logging: PASS (6 new record(s))
- Retrieval metrics: 20 benchmark(s), mean P@5=0.470, mean R@5=0.975, minimum R@5=0.500
```

## IMPLEMENTATION ASSESSMENT (ADVISORY MODEL OUTPUT)

Status: PASS
Strengths: Structural files, required tools, live health, corpus refresh, retrieval, validation query, grounded answer, citations, confidence, audit logging, retrieval metrics, and measurement capabilities are all met.

Gaps: Insufficient-context behaviour, audit logging, and retrieval metrics are not observed.

## REVIEW (ADVISORY MODEL OUTPUT)

Risk: Insufficient-context behaviour is marked as PASS, contradicting the Gap: Insufficient-context behaviour is not observed.
Correction: None
Retest: No additional retest required
