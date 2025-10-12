"""
Contact graph manager using NetworkX.
"""
import networkx as nx
from typing import List, Optional, Dict
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
