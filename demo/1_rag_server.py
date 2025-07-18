import dotenv
dotenv.load_dotenv(override=True)

import os
from typing import List

from lassie.core.model_loader import ModelLoader
from lassie.core.indices import IndexLoader 
from lassie.core.retriever import RetrieverBuilder

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("RAG")

#initialize embedding model and vector database index (LassieRAG)
## load embedding model 
rag_models = ModelLoader(llm_source = "openailike", embed_model_source = "openailike")
rag_models._embed_model, rag_models._embed_model_tokenizer = rag_models.load_embedding_model(
    base_url = os.getenv("OPENAI_BASE_URL"),
    api_key = os.getenv("OPENAI_API_KEY", "sk-fake-key"),
    model_name = "nomic-embed-text:latest",
    max_length = 512,
    prefix_tokens = ("search_query: ", "search_document: "),
    tokenizer_name = "nomic-ai/nomic-embed-text-v2-moe"
)
retriever_builder = RetrieverBuilder(loaded_models = rag_models, retriever_type = "vector_index")

## load data into index
index_loader = IndexLoader(loaded_models = rag_models, database_type = "opensearch")

fps_rules_index = index_loader.load(
    host = "http://localhost:9200",
    http_auth = ("admin", "admin"),
    index_name = "fps_rules",
    search_pipeline_name = "hybrid_search",
)
icbu_gss_intro_index = index_loader.load(
    host = "http://localhost:9200",
    http_auth = ("admin", "admin"),
    index_name = "icbu_gss_introduction",
    search_pipeline_name = "hybrid_search",
)
nstc_index = index_loader.load(
    host = "http://localhost:9200",
    http_auth = ("admin", "admin"),
    index_name = "nstc",
    search_pipeline_name = "hybrid_search",
)

def turn_node_into_dict(rel_nodes):
    return [
        {
            "score": node.score,
            "text": node.node.text,
        } 
        for node in rel_nodes
    ]

@mcp.tool()
async def retrieve_fps_rules_db(query: str) -> List[dict]:
    """
    Retrieve information relevant to the user's query from a database containing documents about company work rules. 

    Args: 
        query: str. the query from user used to retrieve the relevant information in the vector database
    
    Returns:
        List[dict]: The documents relevant to user's query
    """
    retriever = retriever_builder.build(index = fps_rules_index, similarity_top_k = 5, vector_store_query_mode = "hybrid")
    retrieved_nodes = await retriever.aretrieve(query)
    return turn_node_into_dict(retrieved_nodes)

@mcp.tool()
async def retrieve_company_introduction_db(query: str) -> List[dict]:
    """
    Retrieve information relevant to the user's query from a database containing documents about company notes and introductions. 

    Args: 
        query: str. the query from user used to retrieve the relevant information in the vector database
    
    Returns:
        List[dict]: The documents relevant to user's query
    """
    retriever = retriever_builder.build(index = icbu_gss_intro_index, similarity_top_k = 5, vector_store_query_mode = "hybrid")
    retrieved_nodes = await retriever.aretrieve(query)
    return turn_node_into_dict(retrieved_nodes)

@mcp.tool()
async def retrieve_NSTC_research_project_db(query: str) -> List[dict]:
    """
    Retrieve information relevant to the user's query from a database containing documents about FAQs related to undergraduate student research projects.

    Args: 
        query: str. the query from user used to retrieve the relevant information in the vector database
    
    Returns:
        List[dict]: The documents relevant to user's query
    """
    retriever = retriever_builder.build(index = nstc_index, similarity_top_k = 5, vector_store_query_mode = "hybrid")
    retrieved_nodes = await retriever.aretrieve(query)
    return turn_node_into_dict(retrieved_nodes)

# @mcp.tool()
# def calculate_bmi(weight_kg: float, height_m: float) -> float:
#     """Calculate BMI given weight in kg and height in meters"""
#     return weight_kg / (height_m**2)


if __name__ == "__main__":
    # Run the server
    mcp.run(transport="stdio")