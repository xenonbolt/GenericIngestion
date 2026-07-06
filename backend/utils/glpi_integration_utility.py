import httpx
import logging
from typing import Dict, Any, List, Callable
from datetime import datetime

logger = logging.getLogger("GLPIIntegrationUtility")

class GLPIClientUtility:
    """
    Self-contained GLPI REST API client with a built-in sandbox mock data simulator.
    decoupled from any specific project database structure.
    """
    def __init__(self, glpi_url: str = "", app_token: str = "", user_token: str = "", use_mock: bool = True):
        self.glpi_url = glpi_url.rstrip("/")
        self.app_token = app_token
        self.user_token = user_token
        self.use_mock = use_mock
        self.session_token = None

    def init_session(self) -> bool:
        if self.use_mock:
            logger.info("[GLPI Utility] Running in local mock sandbox mode.")
            return True

        if not self.glpi_url:
            logger.warning("[GLPI Utility] No URL provided. Defaulting to mock mode.")
            self.use_mock = True
            return True

        url = f"{self.glpi_url}/apirest.php/initSession/"
        headers = {
            "Content-Type": "application/json",
            "App-Token": self.app_token,
            "Authorization": f"user_token {self.user_token}"
        }

        try:
            response = httpx.get(url, headers=headers, timeout=10.0, verify=False)
            if response.status_code == 200:
                data = response.json()
                self.session_token = data.get("session_token")
                return True
            else:
                logger.error(f"[GLPI Utility] Failed to init session (status: {response.status_code}). Falling back to mock sandbox.")
                self.use_mock = True
                return True
        except Exception as e:
            logger.error(f"[GLPI Utility] Connection error: {e}. Falling back to mock sandbox.")
            self.use_mock = True
            return True

    def kill_session(self):
        if self.use_mock or not self.session_token:
            return

        url = f"{self.glpi_url}/apirest.php/killSession/"
        headers = {
            "App-Token": self.app_token,
            "Session-Token": self.session_token
        }
        try:
            httpx.get(url, headers=headers, timeout=5.0, verify=False)
        except Exception as e:
            logger.error(f"[GLPI Utility] Kill session error: {e}")
        finally:
            self.session_token = None

    def fetch_inventory_data(self) -> Dict[str, List[Dict[str, Any]]]:
        if self.use_mock:
            return self._get_sandbox_mock_data()

        headers = {
            "App-Token": self.app_token,
            "Session-Token": self.session_token
        }
        data = {
            "computers": [],
            "software": [],
            "tickets": [],
            "users": [],
            "relations": []
        }

        try:
            # Fetch computer assets
            comp_res = httpx.get(f"{self.glpi_url}/apirest.php/Computer", headers=headers, timeout=10.0, verify=False)
            if comp_res.status_code == 200:
                data["computers"] = comp_res.json()
            
            # Fetch tickets
            ticket_res = httpx.get(f"{self.glpi_url}/apirest.php/Ticket", headers=headers, timeout=10.0, verify=False)
            if ticket_res.status_code == 200:
                data["tickets"] = ticket_res.json()

            # Fetch software packages
            soft_res = httpx.get(f"{self.glpi_url}/apirest.php/Software", headers=headers, timeout=10.0, verify=False)
            if soft_res.status_code == 200:
                data["software"] = soft_res.json()

            # Fetch users
            user_res = httpx.get(f"{self.glpi_url}/apirest.php/User", headers=headers, timeout=10.0, verify=False)
            if user_res.status_code == 200:
                data["users"] = user_res.json()

            # Fallback if no real records returned
            if not data["computers"] and not data["tickets"]:
                return self._get_sandbox_mock_data()

            # Build generic dependency edges from fetched IDs
            for comp in data["computers"]:
                uid = comp.get("users_id")
                if uid:
                    data["relations"].append({
                        "source": f"User-{uid}",
                        "target": comp.get("name", f"Comp-{comp.get('id')}"),
                        "relation": "OWNS"
                    })

            for ticket in data["tickets"]:
                comp_id = ticket.get("items_id")
                if comp_id:
                    comp_name = next((c.get("name") for c in data["computers"] if c.get("id") == comp_id), f"Comp-{comp_id}")
                    data["relations"].append({
                        "source": ticket.get("name", f"Ticket-{ticket.get('id')}"),
                        "target": comp_name,
                        "relation": "ASSOCIATED_WITH"
                    })

            return data

        except Exception as e:
            logger.error(f"[GLPI Utility] Fetch error: {e}. Falling back to mock data.")
            return self._get_sandbox_mock_data()

    def _get_sandbox_mock_data(self) -> Dict[str, List[Dict[str, Any]]]:
        # Rich sandbox dataset representing corporate users, assets, software licenses, and tickets
        computers = [
            {"id": 1, "name": "Comp-01", "os": "Windows 11 Professional", "ram": "32GB", "cpu": "Intel Core i7-13700", "owner": "alice"},
            {"id": 2, "name": "Comp-02", "os": "Ubuntu 22.04 LTS Server", "ram": "64GB", "cpu": "AMD EPYC 7763", "owner": "bob"},
            {"id": 3, "name": "Comp-03", "os": "macOS Sonoma 14.5", "ram": "16GB", "cpu": "Apple M3 Pro", "owner": "charlie"}
        ]

        software = [
            {"id": 10, "name": "VS Code", "version": "1.90.2", "license": "Open Source"},
            {"id": 11, "name": "Docker Desktop", "version": "4.30.0", "license": "Enterprise Subscription"},
            {"id": 12, "name": "PostgreSQL", "version": "16.3", "license": "PostgreSQL License"},
            {"id": 13, "name": "Figma Desktop", "version": "116.15.4", "license": "Commercial SaaS"}
        ]

        users = [
            {"id": 20, "name": "alice", "email": "alice@company.com", "role": "Software Engineer"},
            {"id": 21, "name": "bob", "email": "bob@company.com", "role": "DevOps Architect"},
            {"id": 22, "name": "charlie", "email": "charlie@company.com", "role": "Lead UI Designer"}
        ]

        tickets = [
            {
                "id": 101, 
                "name": "Ticket-101", 
                "title": "Docker Desktop daemon failing to bind to port 2375 after update", 
                "content": "Docker Desktop service failed to launch on Comp-01. Port 2375 is already in use by another process or locked by firewall rule.",
                "status": "New", 
                "urgency": "High", 
                "submitter": "alice", 
                "item_name": "Comp-01"
            },
            {
                "id": 102, 
                "name": "Ticket-102", 
                "title": "VS Code git extension failing to locate gpg key for signing commits", 
                "content": "Cannot commit code on Comp-01. VS Code output: 'gpg: signing failed: No secret key'. Works in terminal, fails in editor extension.",
                "status": "Processing", 
                "urgency": "Medium", 
                "submitter": "alice", 
                "item_name": "Comp-01"
            },
            {
                "id": 103, 
                "name": "Ticket-103", 
                "title": "Out of memory (OOM-killer) error triggered on PostgreSQL database backup", 
                "content": "PostgreSQL database crashed on Comp-02 server. Kernel OOM-killer terminated postmaster process during scheduled database backup.",
                "status": "Closed", 
                "urgency": "Critical", 
                "submitter": "bob", 
                "item_name": "Comp-02"
            },
            {
                "id": 104, 
                "name": "Ticket-104", 
                "title": "Figma application lagging heavily during web render layout", 
                "content": "Figma desktop client has high GPU utilization and UI stuttering on Comp-03 macOS Sonoma during complex vector designs.",
                "status": "New", 
                "urgency": "Low", 
                "submitter": "charlie", 
                "item_name": "Comp-03"
            }
        ]

        relations = [
            {"source": "alice", "target": "Comp-01", "relation": "OWNS"},
            {"source": "bob", "target": "Comp-02", "relation": "OWNS"},
            {"source": "charlie", "target": "Comp-03", "relation": "OWNS"},
            
            {"source": "Comp-01", "target": "VS Code", "relation": "HAS_SOFTWARE"},
            {"source": "Comp-01", "target": "Docker Desktop", "relation": "HAS_SOFTWARE"},
            {"source": "Comp-02", "target": "Docker Desktop", "relation": "HAS_SOFTWARE"},
            {"source": "Comp-02", "target": "PostgreSQL", "relation": "HAS_SOFTWARE"},
            {"source": "Comp-03", "target": "VS Code", "relation": "HAS_SOFTWARE"},
            {"source": "Comp-03", "target": "Figma Desktop", "relation": "HAS_SOFTWARE"},
            
            {"source": "Ticket-101", "target": "Comp-01", "relation": "ASSOCIATED_WITH"},
            {"source": "Ticket-101", "target": "alice", "relation": "REPORTED_BY"},
            
            {"source": "Ticket-102", "target": "Comp-01", "relation": "ASSOCIATED_WITH"},
            {"source": "Ticket-102", "target": "alice", "relation": "REPORTED_BY"},
            
            {"source": "Ticket-103", "target": "Comp-02", "relation": "ASSOCIATED_WITH"},
            {"source": "Ticket-103", "target": "bob", "relation": "REPORTED_BY"},
            
            {"source": "Ticket-104", "target": "Comp-03", "relation": "ASSOCIATED_WITH"},
            {"source": "Ticket-104", "target": "charlie", "relation": "REPORTED_BY"}
        ]

        return {
            "computers": computers,
            "software": software,
            "tickets": tickets,
            "users": users,
            "relations": relations
        }

class GLPIEntityMapper:
    """
    Core mapper decoupling GLPI entity structures from target database drivers.
    Uses callback injectors so it can support NetworkX, Neo4j, ChromaDB, PGVector, etc.
    """
    def __init__(self, raw_data: Dict[str, List[Dict[str, Any]]]):
        self.raw_data = raw_data

    def sync_to_backends(
        self,
        add_node_fn: Callable[[str, Dict[str, Any]], None],
        add_edge_fn: Callable[[str, str, str], None],
        add_vector_doc_fn: Callable[[str, str, Dict[str, Any]], None]
    ) -> Dict[str, int]:
        """
        Parses GLPI objects and pipes them to the target storage engines via callbacks.
        """
        computers = self.raw_data.get("computers", [])
        software = self.raw_data.get("software", [])
        tickets = self.raw_data.get("tickets", [])
        users = self.raw_data.get("users", [])
        relations = self.raw_data.get("relations", [])

        # 1. Map Graph Nodes
        for u in users:
            attrs = {"type": "User", "email": u.get("email", ""), "role": u.get("role", "")}
            add_node_fn(u["name"], attrs)

        for c in computers:
            attrs = {"type": "Computer", "os": c.get("os", ""), "ram": c.get("ram", ""), "cpu": c.get("cpu", "")}
            add_node_fn(c["name"], attrs)

        for s in software:
            attrs = {"type": "Software", "version": s.get("version", ""), "license": s.get("license", "")}
            add_node_fn(s["name"], attrs)

        for t in tickets:
            attrs = {"type": "Ticket", "title": t.get("title", ""), "status": t.get("status", ""), "urgency": t.get("urgency", "")}
            add_node_fn(t["name"], attrs)

        # 2. Map Graph Relationships
        for r in relations:
            add_edge_fn(r["source"], r["target"], r["relation"])

        # 3. Map Vector Documents
        vector_count = 0
        for c in computers:
            doc_id = f"glpi_comp_{c['id']}"
            doc_text = f"Computer workstation specs: Device Name = {c['name']}, OS = {c.get('os')}, RAM = {c.get('ram')}, CPU = {c.get('cpu')}, User Owner = {c.get('owner')}."
            meta = {"file_name": "glpi_inventory.json", "category": "ITAM", "asset_type": "Computer", "name": c["name"]}
            add_vector_doc_fn(doc_id, doc_text, meta)
            vector_count += 1

        for t in tickets:
            doc_id = f"glpi_ticket_{t['id']}"
            doc_text = f"Ticket reference: {t['name']}. Subject: {t['title']}. Urgency priority: {t['urgency']}. Status: {t['status']}. Assigned machine: {t['item_name']}. Submitter: {t['submitter']}.\nLog Content: {t['content']}"
            meta = {"file_name": "glpi_inventory.json", "category": "ITAM", "asset_type": "Ticket", "name": t["name"], "urgency": t["urgency"]}
            add_vector_doc_fn(doc_id, doc_text, meta)
            vector_count += 1

        return {
            "nodes_mapped": len(users) + len(computers) + len(software) + len(tickets),
            "edges_mapped": len(relations),
            "vectors_mapped": vector_count
        }
