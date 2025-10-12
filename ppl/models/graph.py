"""
Contact graph manager using NetworkX.
"""
import networkx as nx
import pickle
import json
from typing import List, Optional, Dict, Tuple
from pathlib import Path
from .contact import Contact
from .relationship import Relationship


class ContactGraph:
    """
    Core data structure representing contacts and their relationships using NetworkX.
    
    Contacts are stored as nodes with UID as the node identifier.
    Relationships are stored as directed edges with attributes.
    """
    
    def __init__(self):
        """Initialize an empty contact graph."""
        self.graph = nx.DiGraph()  # Directed graph to support directional relationships
        self._contacts: Dict[str, Contact] = {}  # UID -> Contact mapping for quick access
    
    def add_contact(self, contact: Contact) -> None:
        """
        Add a contact to the graph.
        
        Args:
            contact: Contact to add
            
        Raises:
            ValueError: If contact has no UID
        """
        if not contact.uid:
            raise ValueError("Contact must have a UID to be added to graph")
        
        self._contacts[contact.uid] = contact
        self.graph.add_node(contact.uid, contact=contact)
    
    def update_contact(self, contact: Contact) -> None:
        """
        Update an existing contact in the graph.
        
        Args:
            contact: Contact to update
            
        Raises:
            ValueError: If contact has no UID or doesn't exist in graph
        """
        if not contact.uid:
            raise ValueError("Contact must have a UID to be updated")
        
        if contact.uid not in self._contacts:
            raise ValueError(f"Contact with UID {contact.uid} not found in graph")
        
        self._contacts[contact.uid] = contact
        self.graph.nodes[contact.uid]['contact'] = contact
    
    def merge_contact(self, contact: Contact) -> Tuple[bool, str]:
        """
        Intelligently add or merge a contact into the graph.
        
        If contact doesn't exist in graph:
            - Add it as new contact
            - Return (True, "added")
        
        If contact exists in graph:
            - Compare REV timestamps
            - If incoming is newer or equal, merge data
            - Return (True, "updated") if changes made
            - Return (False, "skipped") if incoming is older
        
        Args:
            contact: Contact to add or merge
            
        Returns:
            Tuple of (was_modified, action) where action is "added", "updated", or "skipped"
        """
        if not contact.uid:
            raise ValueError("Contact must have a UID to be merged")
        
        # Check if contact exists in graph
        existing = self.get_contact(contact.uid)
        
        if existing is None:
            # Contact doesn't exist, add it
            self.add_contact(contact)
            return (True, "added")
        
        # Contact exists, compare REV timestamps
        rev_comparison = existing.compare_rev(contact)
        
        if rev_comparison > 0:
            # Existing is newer, skip incoming
            return (False, "skipped")
        
        # Incoming is newer or equal, merge it
        existing.merge_from(contact, prefer_newer=True)
        self.update_contact(existing)
        return (True, "updated")
    
    def get_contact(self, uid: str) -> Optional[Contact]:
        """
        Get a contact by UID.
        
        Args:
            uid: Unique identifier of the contact
            
        Returns:
            Contact if found, None otherwise
        """
        return self._contacts.get(uid)
    
    def remove_contact(self, uid: str) -> None:
        """
        Remove a contact from the graph.
        
        Args:
            uid: Unique identifier of the contact to remove
        """
        if uid in self._contacts:
            del self._contacts[uid]
        
        if self.graph.has_node(uid):
            self.graph.remove_node(uid)
    
    def add_relationship(self, rel: Relationship) -> None:
        """
        Add a relationship (edge) to the graph.
        
        Args:
            rel: Relationship to add
            
        Raises:
            ValueError: If source or target contacts are not in graph
        """
        if not rel.source or not rel.source.uid:
            raise ValueError("Relationship source must have a UID")
        
        if not rel.target or not rel.target.uid:
            raise ValueError("Relationship target must have a UID")
        
        if rel.source.uid not in self._contacts:
            raise ValueError(f"Source contact {rel.source.uid} not in graph")
        
        if rel.target.uid not in self._contacts:
            raise ValueError(f"Target contact {rel.target.uid} not in graph")
        
        # Add edge with relationship data as attributes
        self.graph.add_edge(
            rel.source.uid,
            rel.target.uid,
            types=rel.types,
            directional=rel.directional,
            metadata=rel.metadata
        )
    
    def get_relationships(self, uid: str) -> List[Relationship]:
        """
        Get all relationships for a contact.
        
        Args:
            uid: Unique identifier of the contact
            
        Returns:
            List of Relationship objects where the contact is the source
        """
        relationships = []
        
        if not self.graph.has_node(uid):
            return relationships
        
        source_contact = self._contacts.get(uid)
        if not source_contact:
            return relationships
        
        # Get outgoing edges (where this contact is the source)
        for _, target_uid, edge_data in self.graph.out_edges(uid, data=True):
            target_contact = self._contacts.get(target_uid)
            if target_contact:
                relationships.append(Relationship(
                    source=source_contact,
                    target=target_contact,
                    types=edge_data.get('types', []),
                    directional=edge_data.get('directional', True),
                    metadata=edge_data.get('metadata', {})
                ))
        
        return relationships
    
    def get_all_contacts(self) -> List[Contact]:
        """
        Get all contacts in the graph.
        
        Returns:
            List of all Contact objects
        """
        return list(self._contacts.values())
    
    def get_all_relationships(self) -> List[Relationship]:
        """
        Get all relationships in the graph.
        
        Returns:
            List of all Relationship objects
        """
        relationships = []
        
        for source_uid in self._contacts:
            relationships.extend(self.get_relationships(source_uid))
        
        return relationships
    
    def save(self, file_path: str, format: Optional[str] = None) -> None:
        """
        Save the contact graph to disk.
        
        Supports GraphML and JSON formats. Format is auto-detected from file extension
        if not specified.
        
        Args:
            file_path: Path to save the graph file
            format: Format to use ('graphml' or 'json'). Auto-detected if None.
        """
        # Determine format from extension if not specified
        if format is None:
            ext = Path(file_path).suffix.lower()
            if ext == '.json':
                format = 'json'
            else:
                format = 'graphml'
        
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            self._save_json(file_path)
        else:
            self._save_graphml(file_path)
    
    def _save_graphml(self, file_path: str) -> None:
        """
        Save the contact graph to disk using GraphML format.
        
        The graph structure is saved as GraphML, and Contact objects are serialized
        as JSON in the node attributes.
        
        Args:
            file_path: Path to save the graph file
        """
        # Create a copy of the graph for serialization
        export_graph = nx.DiGraph()
        
        # Add nodes with serialized contact data
        for uid, contact in self._contacts.items():
            # Serialize contact to dict
            contact_data = self._serialize_contact(contact)
            export_graph.add_node(uid, **contact_data)
        
        # Copy all edges with their attributes (serialize lists as JSON)
        for u, v, data in self.graph.edges(data=True):
            edge_data = {}
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    # Serialize complex types as JSON
                    edge_data[key] = json.dumps(value)
                else:
                    edge_data[key] = value
            export_graph.add_edge(u, v, **edge_data)
        
        # Write to GraphML
        nx.write_graphml(export_graph, file_path)
    
    def _save_json(self, file_path: str) -> None:
        """
        Save the contact graph to disk using JSON format.
        
        Uses the graphology JSON schema format:
        {
          "attributes": {"name": "..."},
          "options": {"allowSelfLoops": true, "multi": false, "type": "mixed"},
          "nodes": [{"key": "uid1"}, {"key": "uid2"}],
          "edges": [{"key": "uid1->uid2", "source": "uid1", "target": "uid2", "attributes": {...}}]
        }
        
        Args:
            file_path: Path to save the graph file
        """
        # Build JSON structure
        graph_data = {
            "attributes": {
                "name": "Contact Graph"
            },
            "options": {
                "allowSelfLoops": True,
                "multi": False,
                "type": "directed"
            },
            "nodes": [],
            "edges": []
        }
        
        # Add nodes
        for uid, contact in self._contacts.items():
            node = {
                "key": uid,
                "attributes": self._serialize_contact(contact)
            }
            graph_data["nodes"].append(node)
        
        # Add edges
        for u, v, data in self.graph.edges(data=True):
            edge = {
                "key": f"{u}->{v}",
                "source": u,
                "target": v,
                "attributes": {}
            }
            
            # Copy edge attributes
            for key, value in data.items():
                edge["attributes"][key] = value
            
            graph_data["edges"].append(edge)
        
        # Write to JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
    
    def load(self, file_path: str, format: Optional[str] = None) -> None:
        """
        Load a contact graph from disk.
        
        Supports GraphML and JSON formats. Format is auto-detected from file extension
        if not specified.
        
        Args:
            file_path: Path to the graph file
            format: Format to use ('graphml' or 'json'). Auto-detected if None.
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Graph file not found: {file_path}")
        
        # Determine format from extension if not specified
        if format is None:
            ext = Path(file_path).suffix.lower()
            if ext == '.json':
                format = 'json'
            else:
                format = 'graphml'
        
        if format == 'json':
            self._load_json(file_path)
        else:
            self._load_graphml(file_path)
    
    def _load_graphml(self, file_path: str) -> None:
        """
        Load a contact graph from GraphML format.
        
        Args:
            file_path: Path to the graph file
        """
        # Read GraphML
        import_graph = nx.read_graphml(file_path)
        
        # Clear current graph
        self.graph = nx.DiGraph()
        self._contacts = {}
        
        # Restore contacts from nodes
        for uid in import_graph.nodes():
            node_data = import_graph.nodes[uid]
            contact = self._deserialize_contact(uid, node_data)
            self._contacts[uid] = contact
            self.graph.add_node(uid, contact=contact)
        
        # Restore edges with deserialized attributes
        for u, v, data in import_graph.edges(data=True):
            edge_data = {}
            for key, value in data.items():
                # Try to deserialize JSON strings back to lists/dicts
                if isinstance(value, str):
                    try:
                        edge_data[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        edge_data[key] = value
                else:
                    edge_data[key] = value
            self.graph.add_edge(u, v, **edge_data)
    
    def _load_json(self, file_path: str) -> None:
        """
        Load a contact graph from JSON format.
        
        Expects the graphology JSON schema format.
        
        Args:
            file_path: Path to the graph file
        """
        # Read JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
        
        # Clear current graph
        self.graph = nx.DiGraph()
        self._contacts = {}
        
        # Restore contacts from nodes
        for node in graph_data.get("nodes", []):
            uid = node["key"]
            node_attrs = node.get("attributes", {})
            contact = self._deserialize_contact(uid, node_attrs)
            self._contacts[uid] = contact
            self.graph.add_node(uid, contact=contact)
        
        # Restore edges
        for edge in graph_data.get("edges", []):
            source = edge["source"]
            target = edge["target"]
            edge_attrs = edge.get("attributes", {})
            self.graph.add_edge(source, target, **edge_attrs)
    
    @staticmethod
    def _serialize_contact(contact: Contact) -> Dict[str, str]:
        """
        Serialize a Contact to a dictionary for GraphML storage.
        
        Args:
            contact: Contact to serialize
            
        Returns:
            Dictionary with string values for GraphML compatibility
        """
        data = {
            'fn': contact.fn,
            'version': contact.version,
        }
        
        # Serialize complex fields as JSON strings for GraphML
        if contact.uid:
            data['uid'] = contact.uid
        
        if contact.n:
            data['n'] = contact.n
        
        if contact.rev:
            data['rev'] = contact.rev.isoformat()
        
        if contact.email:
            data['email'] = json.dumps(contact.email)
        
        if contact.tel:
            data['tel'] = json.dumps(contact.tel)
        
        if contact.adr:
            data['adr'] = json.dumps(contact.adr)
        
        if contact.org:
            data['org'] = json.dumps(contact.org)
        
        if contact.title:
            data['title'] = contact.title
        
        if contact.role:
            data['role'] = contact.role
        
        if contact.note:
            data['note'] = contact.note
        
        if contact.categories:
            data['categories'] = json.dumps(contact.categories)
        
        if contact.url:
            data['url'] = json.dumps(contact.url)
        
        if contact.nickname:
            data['nickname'] = json.dumps(contact.nickname)
        
        if contact.bday:
            data['bday'] = contact.bday
        
        if contact.anniversary:
            data['anniversary'] = contact.anniversary
        
        if contact.gender:
            data['gender'] = contact.gender
        
        if contact.photo:
            data['photo'] = contact.photo
        
        if contact.tz:
            data['tz'] = contact.tz
        
        if contact.geo:
            data['geo'] = json.dumps(contact.geo)
        
        if contact.related:
            # Serialize Related objects
            related_data = []
            for rel in contact.related:
                rel_dict = {
                    'uri': rel.uri,
                    'type': rel.type,
                    'text_value': rel.text_value,
                    'pref': rel.pref
                }
                related_data.append(rel_dict)
            data['related'] = json.dumps(related_data)
        
        return data
    
    @staticmethod
    def _deserialize_contact(uid: str, data: Dict[str, str]) -> Contact:
        """
        Deserialize a Contact from GraphML node data.
        
        Args:
            uid: Contact UID
            data: Node data from GraphML
            
        Returns:
            Contact object
        """
        from datetime import datetime
        from .contact import Related
        
        # Create contact with required field
        fn = data.get('fn', '')
        contact = Contact(fn=fn)
        
        # Restore UID
        contact.uid = data.get('uid', uid)
        
        # Restore version
        if 'version' in data:
            contact.version = data['version']
        
        # Restore REV
        if 'rev' in data:
            try:
                contact.rev = datetime.fromisoformat(data['rev'])
            except (ValueError, AttributeError):
                pass
        
        # Restore simple fields
        if 'n' in data:
            contact.n = data['n']
        
        if 'title' in data:
            contact.title = data['title']
        
        if 'role' in data:
            contact.role = data['role']
        
        if 'note' in data:
            contact.note = data['note']
        
        if 'bday' in data:
            contact.bday = data['bday']
        
        if 'anniversary' in data:
            contact.anniversary = data['anniversary']
        
        if 'gender' in data:
            contact.gender = data['gender']
        
        if 'photo' in data:
            contact.photo = data['photo']
        
        if 'tz' in data:
            contact.tz = data['tz']
        
        # Restore JSON-serialized list fields
        if 'email' in data:
            try:
                contact.email = json.loads(data['email'])
            except (json.JSONDecodeError, TypeError):
                contact.email = [data['email']]
        
        if 'tel' in data:
            try:
                contact.tel = json.loads(data['tel'])
            except (json.JSONDecodeError, TypeError):
                contact.tel = [data['tel']]
        
        if 'adr' in data:
            try:
                contact.adr = json.loads(data['adr'])
            except (json.JSONDecodeError, TypeError):
                contact.adr = [data['adr']]
        
        if 'org' in data:
            try:
                contact.org = json.loads(data['org'])
            except (json.JSONDecodeError, TypeError):
                contact.org = [data['org']]
        
        if 'categories' in data:
            try:
                contact.categories = json.loads(data['categories'])
            except (json.JSONDecodeError, TypeError):
                contact.categories = [data['categories']]
        
        if 'url' in data:
            try:
                contact.url = json.loads(data['url'])
            except (json.JSONDecodeError, TypeError):
                contact.url = [data['url']]
        
        if 'nickname' in data:
            try:
                contact.nickname = json.loads(data['nickname'])
            except (json.JSONDecodeError, TypeError):
                contact.nickname = [data['nickname']]
        
        if 'geo' in data:
            try:
                geo_data = json.loads(data['geo'])
                if isinstance(geo_data, list) and len(geo_data) == 2:
                    contact.geo = tuple(geo_data)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Restore Related objects
        if 'related' in data:
            try:
                related_data = json.loads(data['related'])
                for rel_dict in related_data:
                    related = Related(
                        uri=rel_dict.get('uri', ''),
                        type=rel_dict.get('type', []),
                        text_value=rel_dict.get('text_value'),
                        pref=rel_dict.get('pref')
                    )
                    contact.related.append(related)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return contact
