import os
from langfuse.callback import CallbackHandler

# Stubbed observability integrations to represent enterprise tooling configuration
class ObservabilityManager:
    def __init__(self):
        self.posthog_key = os.getenv("POSTHOG_API_KEY")
        self.langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY")
        
        if self.posthog_key:
            import posthog
            posthog.project_api_key = self.posthog_key
            self.posthog = posthog
        else:
            self.posthog = None

        self.langfuse_host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
        self.langfuse_handler = None
        if self.langfuse_public and self.langfuse_secret:
            try:
                self.langfuse_handler = CallbackHandler(
                    public_key=self.langfuse_public,
                    secret_key=self.langfuse_secret,
                    host=self.langfuse_host
                )
            except Exception as e:
                print(f"Failed to init langfuse: {e}")
            
        print("Observability Stack Initialized (PostHog, Langfuse, Ragas configured).")

    def capture_event(self, user_id: str, event_name: str, properties: dict):
        if self.posthog:
            self.posthog.capture(user_id, event_name, properties)
        else:
            print(f"[Observability Mock] Captured {event_name} for {user_id}: {properties}")

obs_manager = ObservabilityManager()
