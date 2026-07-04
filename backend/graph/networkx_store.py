import os
import json
import networkx as nx
import pandas as pd
from typing import List, Dict, Any

class KnowledgeGraphStore:
    def __init__(self):
        self.save_path = os.path.join(os.getcwd(), "data", "knowledge_graph.json")
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        self.graph = nx.MultiDiGraph()
        self._load()

    def _load(self):
        """Loads the graph from disk if it exists."""
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, "r") as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data, directed=True, multigraph=True)
            except Exception as e:
                print(f"Failed to load knowledge graph: {e}")

    def _save(self):
        """Saves the graph to disk."""
        try:
            data = nx.node_link_data(self.graph)
            with open(self.save_path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to save knowledge graph: {e}")

    def add_entity(self, entity_id: str, attributes: Dict[str, Any] = None):
        """Adds an entity node to the graph."""
        if attributes is None:
            attributes = {}
        self.graph.add_node(entity_id, **attributes)
        self._save()

    def add_relationship(self, source_id: str, target_id: str, relation_type: str, attributes: Dict[str, Any] = None):
        """Adds a directed edge representing a relationship."""
        if attributes is None:
            attributes = {}
        self.graph.add_edge(source_id, target_id, key=relation_type, relation=relation_type, **attributes)
        self._save()

    def ingest_csv(self, file_path: str, entity_col: str, relation_col: str, target_col: str):
        """
        Parses a CSV file and loads it into the NetworkX graph.
        Rows should represent: [Entity] --[Relation]--> [Target]
        """
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            source = str(row.get(entity_col))
            target = str(row.get(target_col))
            relation = str(row.get(relation_col))
            
            # Additional columns can be attributes
            attrs = row.drop([entity_col, relation_col, target_col]).to_dict()
            
            if pd.notna(source) and pd.notna(target):
                self.add_entity(source)
                self.add_entity(target)
                self.add_relationship(source, target, relation, attrs)

    def query_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """Finds all relationships connected to an entity."""
        if entity_id not in self.graph:
            return []
        
        results = []
        for src, tgt, key, data in self.graph.edges(entity_id, keys=True, data=True):
            results.append({"source": src, "target": tgt, "relation": key, "attributes": data})
        return results

    def get_graph_data_for_ui(self) -> Dict[str, Any]:
        """Exports graph data to a dictionary format suitable for node-link UI rendering."""
        data = nx.node_link_data(self.graph)
        return data

# Singleton instance
kg_store = KnowledgeGraphStore()
