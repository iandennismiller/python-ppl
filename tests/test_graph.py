"""
Unit tests for ContactGraph.
"""
import pytest
from ppl.models import Contact, ContactGraph, Relationship


class TestContactGraph:
    """Test cases for ContactGraph class."""
    
    def test_graph_creation(self):
        """Test creating an empty contact graph."""
        graph = ContactGraph()
        assert len(graph.get_all_contacts()) == 0
        assert len(graph.get_all_relationships()) == 0
    
    def test_add_contact(self):
        """Test adding a contact to the graph."""
        graph = ContactGraph()
        contact = Contact(fn="John Doe", uid="john-uid")
        
        graph.add_contact(contact)
        
        assert len(graph.get_all_contacts()) == 1
        assert graph.get_contact("john-uid") == contact
    
    def test_add_contact_without_uid_raises(self):
        """Test that adding a contact without UID raises an error."""
        graph = ContactGraph()
        contact = Contact(fn="John Doe")
        
        with pytest.raises(ValueError, match="UID"):
            graph.add_contact(contact)
    
    def test_update_contact(self):
        """Test updating a contact in the graph."""
        graph = ContactGraph()
        contact = Contact(fn="John Doe", uid="john-uid", email=["john@old.com"])
        graph.add_contact(contact)
        
        # Update contact
        updated_contact = Contact(fn="John Doe", uid="john-uid", email=["john@new.com"])
        graph.update_contact(updated_contact)
        
        retrieved = graph.get_contact("john-uid")
        assert "john@new.com" in retrieved.email
        assert "john@old.com" not in retrieved.email
    
    def test_update_nonexistent_contact_raises(self):
        """Test that updating a non-existent contact raises an error."""
        graph = ContactGraph()
        contact = Contact(fn="John Doe", uid="john-uid")
        
        with pytest.raises(ValueError, match="not found"):
            graph.update_contact(contact)
    
    def test_get_contact_not_found(self):
        """Test getting a contact that doesn't exist."""
        graph = ContactGraph()
        assert graph.get_contact("nonexistent") is None
    
    def test_remove_contact(self):
        """Test removing a contact from the graph."""
        graph = ContactGraph()
        contact = Contact(fn="John Doe", uid="john-uid")
        graph.add_contact(contact)
        
        graph.remove_contact("john-uid")
        
        assert graph.get_contact("john-uid") is None
        assert len(graph.get_all_contacts()) == 0
    
    def test_add_relationship(self):
        """Test adding a relationship between contacts."""
        graph = ContactGraph()
        
        alice = Contact(fn="Alice", uid="alice-uid")
        bob = Contact(fn="Bob", uid="bob-uid")
        
        graph.add_contact(alice)
        graph.add_contact(bob)
        
        rel = Relationship(
            source=alice,
            target=bob,
            types=["friend"],
            directional=False
        )
        
        graph.add_relationship(rel)
        
        relationships = graph.get_relationships("alice-uid")
        assert len(relationships) == 1
        assert relationships[0].target == bob
        assert "friend" in relationships[0].types
    
    def test_add_relationship_missing_source_raises(self):
        """Test that adding a relationship with missing source raises an error."""
        graph = ContactGraph()
        
        alice = Contact(fn="Alice", uid="alice-uid")
        bob = Contact(fn="Bob", uid="bob-uid")
        graph.add_contact(bob)
        
        rel = Relationship(source=alice, target=bob, types=["friend"])
        
        with pytest.raises(ValueError, match="not in graph"):
            graph.add_relationship(rel)
    
    def test_add_relationship_missing_target_raises(self):
        """Test that adding a relationship with missing target raises an error."""
        graph = ContactGraph()
        
        alice = Contact(fn="Alice", uid="alice-uid")
        bob = Contact(fn="Bob", uid="bob-uid")
        graph.add_contact(alice)
        
        rel = Relationship(source=alice, target=bob, types=["friend"])
        
        with pytest.raises(ValueError, match="not in graph"):
            graph.add_relationship(rel)
    
    def test_get_relationships_empty(self):
        """Test getting relationships for a contact with none."""
        graph = ContactGraph()
        alice = Contact(fn="Alice", uid="alice-uid")
        graph.add_contact(alice)
        
        relationships = graph.get_relationships("alice-uid")
        assert len(relationships) == 0
    
    def test_get_all_relationships(self):
        """Test getting all relationships from the graph."""
        graph = ContactGraph()
        
        alice = Contact(fn="Alice", uid="alice-uid")
        bob = Contact(fn="Bob", uid="bob-uid")
        charlie = Contact(fn="Charlie", uid="charlie-uid")
        
        graph.add_contact(alice)
        graph.add_contact(bob)
        graph.add_contact(charlie)
        
        rel1 = Relationship(source=alice, target=bob, types=["friend"])
        rel2 = Relationship(source=alice, target=charlie, types=["colleague"])
        
        graph.add_relationship(rel1)
        graph.add_relationship(rel2)
        
        all_rels = graph.get_all_relationships()
        assert len(all_rels) == 2
