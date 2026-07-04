import tiktoken

class TokenManager:
    def __init__(self, model_name: str = "gpt-4o", max_context_window: int = 128000, buffer: int = 2000):
        self.model_name = model_name
        self.max_context_window = max_context_window
        self.buffer = buffer # tokens to reserve for generation
        try:
            self.encoding = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            # Fallback for unmapped models
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
    
    def count_message_tokens(self, messages: list[dict]) -> int:
        """Counts tokens for a list of message dicts (e.g. [{'role': 'user', 'content': 'hello'}])"""
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += self.count_tokens(str(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens -= 1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    def get_headroom(self, current_messages: list[dict]) -> int:
        """Returns the remaining tokens available in the context window."""
        used_tokens = self.count_message_tokens(current_messages)
        return self.max_context_window - used_tokens - self.buffer

    def optimize_messages(self, messages: list[dict]) -> tuple[list[dict], dict]:
        """Truncates or summarizes messages if headroom is negative. Returns (messages, stats)."""
        headroom = self.get_headroom(messages)
        stats = {"messages_dropped": 0, "tokens_saved": 0}
        if headroom >= 0:
            return messages, stats
        
        original_tokens = self.count_message_tokens(messages)
        print(f"Warning: Context window overflow detected. Headroom: {headroom}. Truncating history.")
        # Simple truncation: keep system prompt, drop oldest messages
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        
        original_length = len(other_msgs)
        while self.get_headroom(system_msgs + other_msgs) < 0 and len(other_msgs) > 1:
            other_msgs.pop(0) # drop the oldest non-system message
            
        stats["messages_dropped"] = original_length - len(other_msgs)
        new_tokens = self.count_message_tokens(system_msgs + other_msgs)
        stats["tokens_saved"] = original_tokens - new_tokens
            
        return system_msgs + other_msgs, stats
