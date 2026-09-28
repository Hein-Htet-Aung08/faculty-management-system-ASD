from mcp.server.fastmcp import FastMCP
from rag_pipeline import refresh_corpus, retrieve_context, answer_question

mcp = FastMCP("research-grant-rag")

@mcp.tool()
def rag_refresh_corpus() -> list:
    """Rebuild the RAG corpus from live database-service data, reports, and repo structure."""
    return refresh_corpus()

@mcp.tool()
def rag_retrieve(query: str, k: int = 5) -> list:
    """Retrieve the top-k most relevant chunks for a query."""
    return retrieve_context(query, k=k)

@mcp.tool()
def rag_answer(query: str) -> dict:
    """Answer a question with grounded, cited context from the RAG corpus."""
    return answer_question(query)

if __name__ == "__main__":
    mcp.run()
