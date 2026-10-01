# Student 5 RAG context evidence

## Scope

`load_student5_context()` reads the five Student 5 resource lists through the
feature backend API. It creates one `tier_1` chunk for each record and one
totals chunk, all labelled `performance_professional_development`. Chunk IDs
and source IDs identify the resource and record so retrieval results can cite
their source. The staff directory supplies display names when available; a
missing directory leaves staff IDs in the text. Recommendations retain their
decision status and are described as proposals, not completed actions.

The source paths, chunk IDs and fields are documented in
`ai-services/rag-server/tool-contracts.md`. Six benchmark questions covering
all five record types and the totals chunk are in `rag_eval.py`.

## Validation

- The four loader tests passed. They cover chunk fields and IDs, zero progress,
  joined training titles and goal titles, pending recommendations, no staff
  email in context, staff-ID fallback, required API failure, and empty data.
- A local run started the real Student 5 database and backend with their seed
  data. The loader read all five backend APIs and produced 51 unique chunks:
  10 for each resource and one totals chunk.
- A Student 5-only shared RAG refresh indexed all 51 chunks in Chroma with
  `vector_store_status: ready`. All six Student 5 benchmark questions retrieved
  their expected cited chunk within the top five (recall@5: 1.0 for each).

The benchmark run indexed Student 5 chunks only, so it does not measure the
combined group corpus. The backend RAG routes and frontend RAG tab belong to
later steps.
