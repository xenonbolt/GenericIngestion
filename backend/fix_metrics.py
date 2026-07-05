import os
import re

nodes_dir = "/home/dwijo/Desktop/QuarterFinal/backend/agents/nodes"
files = [f for f in os.listdir(nodes_dir) if f.endswith(".py") and f != "__init__.py"]

for file in files:
    filepath = os.path.join(nodes_dir, file)
    with open(filepath, "r") as f:
        content = f.read()
    
    # Replace get_metrics(start_time, resp) and get_metrics(start_time, response)
    # with get_metrics(start_time, locals().get('resp') or locals().get('response') or locals().get('res'))
    
    content = re.sub(
        r'get_metrics\(start_time, [a-zA-Z0-9_]+\)',
        r"get_metrics(start_time, locals().get('resp') or locals().get('response') or locals().get('res'))",
        content
    )
    
    with open(filepath, "w") as f:
        f.write(content)
print("Fixed UnboundLocalError in all nodes")
