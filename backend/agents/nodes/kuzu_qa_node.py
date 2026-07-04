import os
import json
from langchain_core.prompts import PromptTemplate
from langchain.chains import KuzuQAChain
from langchain_community.graphs import KuzuGraph
from agents.state import AgentState, streamer
from graph.kuzu_store import kuzu_store

QA_PROMPT = PromptTemplate(
    template="""You are a graph database assistant. Use the following knowledge from the graph to answer the user's question.
If the context is empty or does not contain the answer, simply state: "I don't have enough information in the graph to answer this." Do not ask the user for context or knowledge triplets. Do not complain about missing information.

Graph Context: {context}

Question: {question}
Helpful Answer:""",
    input_variables=["context", "question"]
)

def get_ontology_cypher_prompt():
    ontology_path = os.path.join(os.getcwd(), "data", "ontology.json")
    ontology_text = ""
    if os.path.exists(ontology_path):
        with open(ontology_path, "r") as f:
            try:
                ontology = json.load(f)
                ontology_text = f"\nDiscovered Entity Types: {ontology.get('entities')}\nDiscovered Relation Types: {ontology.get('relations')}"
            except Exception:
                pass

    return PromptTemplate(
        template=f"""Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
If you need to search for text chunks, remember that 'Chunk' nodes are linked to entities via 'MENTIONS' relationships.
{ontology_text}

Schema:
{{schema}}

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

The question is:
{{question}}""",
        input_variables=["schema", "question"]
    )

class KuzuQANode:
    def __init__(self, llm):
        self.llm = llm
        try:
            self.kuzu_graph = KuzuGraph(kuzu_store.db)
            self.chain = KuzuQAChain.from_llm(
                llm=self.llm, 
                graph=self.kuzu_graph, 
                qa_prompt=QA_PROMPT,
                cypher_prompt=get_ontology_cypher_prompt(),
                verbose=True
            )
        except Exception as e:
            print(f"Failed to init Kuzu QA Chain: {e}")
            self.chain = None

    async def __call__(self, state: AgentState):
        await streamer.emit_node_active('kuzu_qa', 'Running kuzu_qa...')
        query = state.get("translated_query", state["messages"][-1].content)
                
        try:
            if not self.chain:
                raise Exception("Chain not initialized")
            
            # KuzuGraph wraps it, but the chain generates Cypher from the schema
            self.kuzu_graph.refresh_schema()
            res = await self.chain.ainvoke({"query": query})
            output = res.get("result", str(res))
            
                        
            await streamer.emit_node_completed('kuzu_qa', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
            
            return {"kuzu_answer": output}
        except Exception as e:
            error_msg = f"Kuzu error: {str(e)}"
            await streamer.emit_node_completed('kuzu_qa', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
            return {"kuzu_answer": error_msg}
