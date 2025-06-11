import dotenv
dotenv.load_dotenv(override=True)

import os
import json
from typing import List
from llama_index.core.schema import TextNode
from lassie.core.model_loader import ModelLoader
from lassie.core.indices import IndexLoader


def convert_chunk_data_into_nodes(chunk_data: List[TextNode]):
    nodes = []
    for doc_chunks in chunk_data:
        nodes += [
            TextNode(text=chunk, metadata={"file_name": doc_chunks["source"]})
            for chunk in doc_chunks["chunk"]
        ]
    return nodes

## search pipeline setting
search_pipeline_config = {
  "description": "Post processor for hybrid search",
  "phase_results_processors": [
    {
      "normalization-processor": {
        "normalization": {
          "technique": "min_max"
        },
        "combination": {
          "technique": "arithmetic_mean",
          "parameters": {
            "weights": [
              0.3,
              0.7
            ]
          }
        }
      }
    }
  ]
}

if __name__=="__main__":
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
    ## load data into index
    index_loader = IndexLoader(loaded_models = rag_models, database_type = "opensearch")
    for dataset_name in ["FPS_rules", "ICBU_gss_introduction", "NSTC"]:
        chunk_data_path = f"{os.getcwd()}/../dataset/{dataset_name}/chunk_data.json"
        
        with open(chunk_data_path, "r", encoding="utf-8") as f:
            chunk_data = json.load(f)
        index_name = dataset_name.lower()
        
        # initialize index
        index = index_loader.load(
            data_source=(
                convert_chunk_data_into_nodes(chunk_data) 
                if index_name != "nstc" 
                else []
            ),
            host = "http://localhost:9200",
            http_auth = ("admin", "admin"),
            index_name = index_name,
            search_pipeline_name = "hybrid_search",
            search_pipeline_config = search_pipeline_config,
        )