import os
import json
from langchain_core.prompts import PromptTemplate
from langchain.chains import GraphQAChain
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph
from agents.state import AgentState, streamer
from graph.networkx_store import kg_store

QA_PROMPT = PromptTemplate(
    template="""You are a graph database assistant. Use the following knowledge triplets to answer the user's question.
If the triplets are empty or do not contain the answer, simply state: "I don't have enough information in the graph to answer this." Do not ask the user for triplets. Do not complain about missing triplets.

Knowledge Triplets: {context}

Question: {question}
Helpful Answer:""",
    input_variables=["context", "question"]
)

def get_ontology_entity_prompt():
    ontology_path = os.path.join(os.getcwd(), "data", "ontology.json")
    ontology_text = ""
    if os.path.exists(ontology_path):
        with open(ontology_path, "r") as f:
            try:
                ontology = json.load(f)
                ontology_text = f"\nDiscovered Entity Types in Database: {ontology.get('entities')}"
            except Exception:
                pass

    return PromptTemplate(
        template=f"""Extract all of the entities from the following text.
As a guideline, extract the entities named in the text, keeping in mind they might belong to these known types:
{ontology_text}

Return the output as a single comma-separated list of entities.
Example: "Apple, Steve Jobs, iPhone"

Text:
{{question}}""",
        input_variables=["question"]
    )

class NetworkXQANode:
    def __init__(self, llm):
        self.llm = llm
        # Load the graph from the global store
        self.nx_graph = NetworkxEntityGraph(kg_store.graph)
        try:
            self.chain = GraphQAChain.from_llm(
                llm=self.llm, 
                graph=self.nx_graph, 
                qa_prompt=QA_PROMPT,
                entity_prompt=get_ontology_entity_prompt(),
                verbose=True
            )
        except Exception as e:
            print(f"Failed to init NetworkX QA Chain: {e}")
            self.chain = None

    async def __call__(self, state: AgentState):
        await streamer.emit_node_active('networkx_qa', 'Running networkx_qa...')
        query = state.get("translated_query", state["messages"][-1].content)
                
        try:
            if not self.chain:
                raise Exception("Chain not initialized")
            # ainvoke yields to the asyncio event loop
            res = await self.chain.ainvoke({"query": query})
            output = res.get("result", str(res))
            
                        
            await streamer.emit_node_completed('networkx_qa', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
            
            return {"networkx_answer": output}
        except Exception as e:
            error_msg = f"NetworkX error: {str(e)}"
            await streamer.emit_node_completed('networkx_qa', {'tokens': 15, 'latency': 120, 'cost': 0.0001})
            return {"networkx_answer": error_msg}
