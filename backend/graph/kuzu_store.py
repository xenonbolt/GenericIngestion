import os
import json
import kuzu
from typing import Dict, Any

class KuzuGraphStore:
    def __init__(self):
        db_path = os.path.join(os.getcwd(), "data", "kuzu_db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._init_schema()

    def _init_schema(self):
        """Initializes the generic schema if it doesn't exist."""
        try:
            self.conn.execute("CREATE NODE TABLE Entity (id STRING, attributes STRING, PRIMARY KEY(id))")
        except Exception:
            pass # Already exists
            
        try:
            self.conn.execute("CREATE REL TABLE Relation (FROM Entity TO Entity, relation_type STRING, attributes STRING)")
        except Exception:
            pass # Already exists

    def add_entity(self, entity_id: str, attributes: Dict[str, Any] = None):
        """Adds or updates an entity node in Kuzu."""
        if attributes is None:
            attributes = {}
        
        attrs_json = json.dumps(attributes).replace("'", "''")
        safe_id = entity_id.replace("'", "''")
        
        # Merge-like behavior
        query = f"""
        MERGE (e:Entity {{id: '{safe_id}'}})
        ON MATCH SET e.attributes = '{attrs_json}'
        ON CREATE SET e.attributes = '{attrs_json}'
        """
        try:
            self.conn.execute(query)
        except Exception as e:
            print(f"Kuzu add_entity error: {e}")

    def add_relationship(self, source_id: str, target_id: str, relation_type: str, attributes: Dict[str, Any] = None):
        """Adds a directed edge in Kuzu."""
        if attributes is None:
            attributes = {}
            
        attrs_json = json.dumps(attributes).replace("'", "''")
        safe_src = source_id.replace("'", "''")
        safe_tgt = target_id.replace("'", "''")
        safe_rel = relation_type.replace("'", "''")
        
        # Ensure nodes exist
        self.add_entity(source_id, {})
        self.add_entity(target_id, {})
        
        query = f"""
        MATCH (src:Entity {{id: '{safe_src}'}}), (tgt:Entity {{id: '{safe_tgt}'}})
        CREATE (src)-[:Relation {{relation_type: '{safe_rel}', attributes: '{attrs_json}'}}]->(tgt)
        """
        try:
            self.conn.execute(query)
        except Exception as e:
            print(f"Kuzu add_relationship error: {e}")

    def ingest_csv(self, file_path: str, entity_col: str, relation_col: str, target_col: str):
        """Parses a CSV file and loads it into KuzuDB."""
        import pandas as pd
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            source = str(row.get(entity_col))
            target = str(row.get(target_col))
            relation = str(row.get(relation_col))
            
            attrs = row.drop([entity_col, relation_col, target_col]).to_dict()
            if pd.notna(source) and pd.notna(target):
                self.add_entity(source)
                self.add_entity(target)
                self.add_relationship(source, target, relation, attrs)

# Singleton instance
kuzu_store = KuzuGraphStore()
