import os
import re

nodes_dir = "/home/dwijo/Desktop/QuarterFinal/backend/agents/nodes"
files = [f for f in os.listdir(nodes_dir) if f.endswith(".py") and f != "__init__.py"]

helper_code = """
import time
def get_metrics(start_time, resp=None):
    latency_ms = int((time.time() - start_time) * 1000)
    tokens = 0
    if resp:
        if hasattr(resp, "response_metadata") and resp.response_metadata:
            tu = resp.response_metadata.get("token_usage", {})
            if isinstance(tu, dict):
                tokens = tu.get("total_tokens", 0)
        if tokens == 0 and hasattr(resp, "usage_metadata") and resp.usage_metadata:
            tokens = resp.usage_metadata.get("total_tokens", 0)
    cost = round(tokens * 0.00001, 6)
    return {"tokens": tokens, "latency": latency_ms, "cost": cost}
"""

with open(os.path.join(os.path.dirname(nodes_dir), "utils.py"), "w") as f:
    f.write(helper_code)

for file in files:
    filepath = os.path.join(nodes_dir, file)
    with open(filepath, "r") as f:
        content = f.read()
    
    if "from agents.utils import get_metrics" not in content:
        content = "import time\nfrom agents.utils import get_metrics\n" + content
    
    # Inject start_time = time.time() at the beginning of __call__
    content = re.sub(
        r'(async def __call__\(self, state: AgentState\):)',
        r'\1\n        start_time = time.time()',
        content
    )
    
    # Replace hardcoded dict
    # Most have `resp = self.llm.invoke(...)` or similar, except retrieval_node
    if file == "retrieval_node.py":
        content = content.replace(
            "{'tokens': 15, 'latency': 120, 'cost': 0.0001}",
            "get_metrics(start_time)"
        )
    else:
        # Default assume `resp` or `response` is the LLM output.
        # Let's check variable names.
        if "response = await self.llm.ainvoke" in content or "response = self.llm.invoke" in content:
            llm_var = "response"
        elif "resp = await self.llm.ainvoke" in content or "resp = self.llm.invoke" in content:
            llm_var = "resp"
        elif "msg = self.llm.invoke" in content:
            llm_var = "msg"
        elif "self.llm.invoke" in content:
            # Maybe intent_node has a specific variable? Let's assume `resp` or fallback
            llm_var = "resp" # fallback, we will just use regex to find assignment
        else:
            llm_var = "None"
            
        # Let's do a more robust replacement by replacing the exact dict string.
        # We will manually pass the llm variable based on file.
        var_map = {
            "intent_node.py": "resp",
            "graph_judge_node.py": "resp",
            "translator_node.py": "resp",
            "networkx_qa_node.py": "resp",
            "kuzu_qa_node.py": "resp",
            "data_analysis_node.py": "resp",
            "generator_node.py": "response",
            "evaluator_node.py": "resp",
            "decomposer_node.py": "resp"
        }
        v = var_map.get(file, "None")
        content = content.replace(
            "{'tokens': 15, 'latency': 120, 'cost': 0.0001}",
            f"get_metrics(start_time, {v})"
        )
        
    with open(filepath, "w") as f:
        f.write(content)
print("Updated all nodes")
