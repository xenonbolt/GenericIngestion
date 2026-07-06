import os
import json
import logging
from typing import Dict, Any
from datetime import datetime
from utils.glpi_integration_utility import GLPIClientUtility, GLPIEntityMapper
from graph.networkx_store import kg_store
from graph.kuzu_store import kuzu_store
from ingestion.pipeline import pipeline

logger = logging.getLogger("GLPISync")

class GLPISyncManager:
    def __init__(self):
        self.master_metadata_path = os.path.join(os.getcwd(), "data", "master_chunk_metadata.json")
        self.status_path = os.path.join(os.getcwd(), "data", "glpi_status.json")

    def run_sync(self, glpi_url: str = "", app_token: str = "", user_token: str = "", use_mock: bool = True) -> Dict[str, Any]:
        logger.info("Executing GLPI Sync via decoupled GLPIIntegrationUtility...")
        
        # 1. Fetch raw data from client utility
        client = GLPIClientUtility(glpi_url=glpi_url, app_token=app_token, user_token=user_token, use_mock=use_mock)
        if not client.init_session():
            return {"status": "error", "message": "Failed to connect to GLPI API."}
            
        try:
            raw_data = client.fetch_inventory_data()
        finally:
            client.kill_session()

        # 2. Clear application memory cache
        try:
            from memory.cache_manager import cache_manager
            cache_manager.clear_cache()
        except Exception as e:
            logger.warning(f"Cache clear warning during GLPI Sync: {e}")

        # 3. Initialize Mapper Utility
        mapper = GLPIEntityMapper(raw_data)

        # 4. Define Database Callbacks (Linking utility to our stack)
        def add_node_callback(node_id: str, attributes: Dict[str, Any]):
            kg_store.add_entity(node_id, attributes)
            kuzu_store.add_entity(node_id, attributes)

        def add_edge_callback(source: str, target: str, relation: str):
            kg_store.add_relationship(source, target, relation)
            kuzu_store.add_relationship(source, target, relation)

        def add_vector_callback(doc_id: str, text: str, metadata: Dict[str, Any]):
            pipeline.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )

        # 5. Execute Mapping Action
        mapping_result = mapper.sync_to_backends(
            add_node_fn=add_node_callback,
            add_edge_fn=add_edge_callback,
            add_vector_doc_fn=add_vector_callback
        )

        # 6. Save Sync Status & Telemetry Metadata
        status_payload = {
            "status": "success",
            "computers_synced": len(raw_data.get("computers", [])),
            "software_synced": len(raw_data.get("software", [])),
            "tickets_synced": len(raw_data.get("tickets", [])),
            "users_synced": len(raw_data.get("users", [])),
            "relations_synced": mapping_result["edges_mapped"],
            "use_mock": client.use_mock,
            "last_synced_at": datetime.utcnow().isoformat()
        }

        try:
            with open(self.status_path, "w") as f:
                json.dump(status_payload, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save GLPI status file: {e}")

        # 7. Update Graph Librarian Table of Contents
        self._update_librarian_toc(raw_data.get("tickets", []))

        return status_payload

    def _update_librarian_toc(self, tickets: list):
        master_metadata = {}
        if os.path.exists(self.master_metadata_path):
            with open(self.master_metadata_path, "r") as f:
                try:
                    master_metadata = json.load(f)
                except Exception:
                    pass

        # Clear old glpi keys
        for key in list(master_metadata.keys()):
            if key.startswith("glpi_"):
                del master_metadata[key]

        # Register library entries so Agent knows it can search it
        master_metadata["glpi_inventory"] = {
            "type": "unstructured",
            "file_name": "glpi_inventory.json",
            "summary": "Synchronized GLPI IT inventory database including computers, users, software installations, and service tickets.",
            "category": "ITAM",
            "keywords": [
                "computer", "software", "ticket", "user", "workstation", "server", 
                "vscode", "docker", "postgresql", "figma", "alice", "bob", "charlie",
                "ram", "os", "cpu", "urgency", "crash", "lagging", "memory", "error"
            ]
        }

        for t in tickets:
            master_metadata[f"glpi_ticket_{t['id']}"] = {
                "type": "unstructured",
                "file_name": "glpi_inventory.json",
                "summary": f"Service ticket {t['name']} regarding {t['title']} submitted by {t['submitter']}.",
                "category": "ITAM",
                "keywords": [
                    t["name"].lower(), t["submitter"].lower(), t["item_name"].lower(), 
                    t["urgency"].lower(), t["status"].lower(), "ticket"
                ]
            }

        with open(self.master_metadata_path, "w") as f:
            json.dump(master_metadata, f, indent=2)

glpi_sync_manager = GLPISyncManager()
