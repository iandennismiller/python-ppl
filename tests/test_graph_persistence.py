"""
Tests for graph persistence functionality.
"""
import pytest
import tempfile
import os
from pathlib import Path

from ppl.models import Contact, ContactGraph, Relationship


class TestGraphPersistence:
    """Test graph save and load functionality."""
    
    def test_save_and_load_empty_graph(self):
        """Test saving and loading an empty graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "empty.graphml")
            
            # Create and save empty graph
            graph = ContactGraph()
            graph.save(graph_file)
            
            # Load and verify
            graph2 = ContactGraph()
            graph2.load(graph_file)
            
            assert len(graph2.get_all_contacts()) == 0
    
    def test_save_and_load_contacts(self):
        """Test saving and loading contacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "contacts.graphml")
            
            # Create contacts
            alice = Contact(fn="Alice", uid="alice-uid", email=["alice@example.com"])
            bob = Contact(fn="Bob", uid="bob-uid", email=["bob@example.com"], tel=["+1-555-0100"])
            
            # Create and populate graph
            graph = ContactGraph()
            graph.add_contact(alice)
            graph.add_contact(bob)
            
            # Save
            graph.save(graph_file)
            
            # Load into new graph
            graph2 = ContactGraph()
            graph2.load(graph_file)
            
            # Verify contacts
            assert len(graph2.get_all_contacts()) == 2
            
            alice2 = graph2.get_contact("alice-uid")
            assert alice2.fn == "Alice"
            assert alice2.email == ["alice@example.com"]
            
            bob2 = graph2.get_contact("bob-uid")
            assert bob2.fn == "Bob"
            assert bob2.tel == ["+1-555-0100"]
    
    def test_save_and_load_relationships(self):
        """Test saving and loading relationships."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "relationships.graphml")
            
            # Create contacts
            alice = Contact(fn="Alice", uid="alice-uid")
            bob = Contact(fn="Bob", uid="bob-uid")
            
            # Create graph with relationship
            graph = ContactGraph()
            graph.add_contact(alice)
            graph.add_contact(bob)
            
            rel = Relationship(source=alice, target=bob, types=["friend"])
            graph.add_relationship(rel)
            
            # Save
            graph.save(graph_file)
            
            # Load into new graph
            graph2 = ContactGraph()
            graph2.load(graph_file)
            
            # Verify relationships
            alice_rels = graph2.get_relationships("alice-uid")
            assert len(alice_rels) == 1
            assert alice_rels[0].types == ["friend"]
            assert alice_rels[0].target.uid == "bob-uid"
    
    def test_save_and_load_complex_contact(self):
        """Test saving and loading contact with all fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "complex.graphml")
            
            from ppl.models import Related
            from datetime import datetime
            
            # Create complex contact
            contact = Contact(
                fn="John Doe",
                uid="john-uid",
                email=["john@example.com", "jdoe@work.com"],
                tel=["+1-555-0100", "+1-555-0101"],
                org=["Tech Corp", "Engineering"],
                title="Software Engineer",
                role="Developer",
                note="Test contact",
                categories=["work", "friend"],
                url=["https://example.com"],
                nickname=["Johnny"],
                gender="M",
                related=[Related(uri="urn:uuid:related-uid", type=["colleague"])]
            )
            contact.rev = datetime.now()
            
            # Create and save graph
            graph = ContactGraph()
            graph.add_contact(contact)
            graph.save(graph_file)
            
            # Load and verify
            graph2 = ContactGraph()
            graph2.load(graph_file)
            
            loaded = graph2.get_contact("john-uid")
            assert loaded.fn == "John Doe"
            assert loaded.email == ["john@example.com", "jdoe@work.com"]
            assert loaded.tel == ["+1-555-0100", "+1-555-0101"]
            assert loaded.org == ["Tech Corp", "Engineering"]
            assert loaded.title == "Software Engineer"
            assert loaded.role == "Developer"
            assert loaded.note == "Test contact"
            assert loaded.categories == ["work", "friend"]
            assert loaded.url == ["https://example.com"]
            assert loaded.nickname == ["Johnny"]
            assert loaded.gender == "M"
            assert len(loaded.related) == 1
            assert loaded.related[0].uri == "urn:uuid:related-uid"
            assert loaded.related[0].type == ["colleague"]
    
    def test_load_nonexistent_file(self):
        """Test loading from non-existent file raises error."""
        graph = ContactGraph()
        
        with pytest.raises(FileNotFoundError):
            graph.load("/nonexistent/file.graphml")
    
    def test_save_creates_directory(self):
        """Test that save creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "subdir", "nested", "graph.graphml")
            
            graph = ContactGraph()
            contact = Contact(fn="Test", uid="test-uid")
            graph.add_contact(contact)
            
            # Should create nested directories
            graph.save(graph_file)
            
            assert os.path.exists(graph_file)
    
    def test_roundtrip_preserves_data(self):
        """Test multiple save/load cycles preserve data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "roundtrip.graphml")
            
            # Create original graph
            original = ContactGraph()
            alice = Contact(fn="Alice", uid="alice-uid", email=["alice@example.com"])
            bob = Contact(fn="Bob", uid="bob-uid", email=["bob@example.com"])
            original.add_contact(alice)
            original.add_contact(bob)
            
            # Save and load multiple times
            for i in range(3):
                graph = ContactGraph()
                if i == 0:
                    graph = original
                else:
                    graph.load(graph_file)
                
                graph.save(graph_file)
            
            # Final load and verify
            final = ContactGraph()
            final.load(graph_file)
            
            assert len(final.get_all_contacts()) == 2
            assert final.get_contact("alice-uid").fn == "Alice"
            assert final.get_contact("bob-uid").fn == "Bob"
    
    def test_update_and_save(self):
        """Test updating contacts and saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "update.graphml")
            
            # Create and save initial graph
            graph = ContactGraph()
            alice = Contact(fn="Alice", uid="alice-uid", email=["old@example.com"])
            graph.add_contact(alice)
            graph.save(graph_file)
            
            # Load, update, and save
            graph2 = ContactGraph()
            graph2.load(graph_file)
            
            alice2 = graph2.get_contact("alice-uid")
            alice2.email = ["new@example.com"]
            graph2.update_contact(alice2)
            graph2.save(graph_file)
            
            # Verify update persisted
            graph3 = ContactGraph()
            graph3.load(graph_file)
            
            alice3 = graph3.get_contact("alice-uid")
            assert alice3.email == ["new@example.com"]
