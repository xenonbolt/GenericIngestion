
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
