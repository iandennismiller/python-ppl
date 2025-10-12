"""
Tests for JSON graph format support.
"""
import pytest
import tempfile
import os
import json
from datetime import datetime
from ppl.models import Contact, ContactGraph, Relationship


class TestJSONGraphFormat:
    """Test JSON graph export/import functionality."""
    
    def test_save_and_load_json_format(self):
        """Test saving and loading graph in JSON format."""
        graph = ContactGraph()
        
        # Add contacts
        contact1 = Contact(
            fn="Alice Johnson",
            uid="alice-uid",
            email=["alice@example.com"],
            tel=["+1-555-0001"],
            title="Engineer"
        )
        
        contact2 = Contact(
            fn="Bob Smith",
            uid="bob-uid",
            email=["bob@example.com"],
            title="Manager"
        )
        
        graph.add_contact(contact1)
        graph.add_contact(contact2)
        
        # Add relationship
        rel = Relationship(
            source=contact1,
            target=contact2,
            types=["colleague", "friend"],
            directional=True
        )
        graph.add_relationship(rel)
        
        # Save to JSON
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "graph.json")
            graph.save(json_file, format='json')
            
            # Verify file exists and is valid JSON
            assert os.path.exists(json_file)
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Verify JSON structure
            assert "attributes" in data
            assert "options" in data
            assert "nodes" in data
            assert "edges" in data
            
            # Verify options
            assert data["options"]["type"] == "directed"
            assert data["options"]["allowSelfLoops"] is True
            assert data["options"]["multi"] is False
            
            # Verify nodes
            assert len(data["nodes"]) == 2
            node_keys = {node["key"] for node in data["nodes"]}
            assert "alice-uid" in node_keys
            assert "bob-uid" in node_keys
            
            # Verify edges
            assert len(data["edges"]) == 1
            edge = data["edges"][0]
            assert edge["source"] == "alice-uid"
            assert edge["target"] == "bob-uid"
            assert "key" in edge
            
            # Load from JSON
            graph2 = ContactGraph()
            graph2.load(json_file, format='json')
            
            # Verify loaded contacts
            loaded_alice = graph2.get_contact("alice-uid")
            assert loaded_alice is not None
            assert loaded_alice.fn == "Alice Johnson"
            assert loaded_alice.email == ["alice@example.com"]
            assert loaded_alice.title == "Engineer"
            
            loaded_bob = graph2.get_contact("bob-uid")
            assert loaded_bob is not None
            assert loaded_bob.fn == "Bob Smith"
            
            # Verify relationships
            rels = graph2.get_relationships("alice-uid")
            assert len(rels) == 1
            assert rels[0].target.uid == "bob-uid"
    
    def test_auto_detect_json_extension(self):
        """Test that JSON format is auto-detected from .json extension."""
        graph = ContactGraph()
        contact = Contact(fn="Test", uid="test-uid")
        graph.add_contact(contact)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "contacts.json")
            
            # Save without specifying format
            graph.save(json_file)
            
            # Verify it's JSON
            with open(json_file, 'r') as f:
                data = json.load(f)
            assert "nodes" in data
            assert "edges" in data
            
            # Load without specifying format
            graph2 = ContactGraph()
            graph2.load(json_file)
            
            loaded = graph2.get_contact("test-uid")
            assert loaded is not None
            assert loaded.fn == "Test"
    
    def test_auto_detect_graphml_extension(self):
        """Test that GraphML format is auto-detected from .graphml extension."""
        graph = ContactGraph()
        contact = Contact(fn="Test", uid="test-uid")
        graph.add_contact(contact)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            graphml_file = os.path.join(tmpdir, "contacts.graphml")
            
            # Save without specifying format
            graph.save(graphml_file)
            
            # Verify it's GraphML (XML)
            with open(graphml_file, 'r') as f:
                content = f.read()
            assert '<?xml' in content or '<graphml' in content
            
            # Load without specifying format
            graph2 = ContactGraph()
            graph2.load(graphml_file)
            
            loaded = graph2.get_contact("test-uid")
            assert loaded is not None
            assert loaded.fn == "Test"
    
    def test_json_preserves_all_contact_fields(self):
        """Test that JSON format preserves all contact fields."""
        graph = ContactGraph()
        
        contact = Contact(
            fn="Complex Contact",
            uid="complex-uid",
            n="Doe;John;MiddleName;Dr.;Jr.",
            email=["john@example.com", "john@work.com"],
            tel=["+1-555-0001", "+1-555-0002"],
            adr=[";;123 Main St;City;State;12345;Country"],
            org=["Company Inc"],
            title="Senior Engineer",
            role="Developer",
            note="Important person",
            categories=["work", "vip"],
            url=["https://example.com"],
            bday="1990-01-01",
            rev=datetime(2024, 10, 12, 19, 0, 0)
        )
        
        graph.add_contact(contact)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "complex.json")
            graph.save(json_file, format='json')
            
            # Load and verify
            graph2 = ContactGraph()
            graph2.load(json_file, format='json')
            
            loaded = graph2.get_contact("complex-uid")
            assert loaded.fn == "Complex Contact"
            assert loaded.n == "Doe;John;MiddleName;Dr.;Jr."
            assert loaded.email == ["john@example.com", "john@work.com"]
            assert loaded.tel == ["+1-555-0001", "+1-555-0002"]
            assert loaded.title == "Senior Engineer"
            assert loaded.role == "Developer"
            assert loaded.note == "Important person"
            assert loaded.categories == ["work", "vip"]
            assert loaded.bday == "1990-01-01"
            assert loaded.rev == datetime(2024, 10, 12, 19, 0, 0)
    
    def test_json_preserves_edge_attributes(self):
        """Test that JSON format preserves edge attributes."""
        graph = ContactGraph()
        
        contact1 = Contact(fn="Person 1", uid="uid-1")
        contact2 = Contact(fn="Person 2", uid="uid-2")
        
        graph.add_contact(contact1)
        graph.add_contact(contact2)
        
        # Add relationship with metadata
        rel = Relationship(
            source=contact1,
            target=contact2,
            types=["friend", "colleague"],
            directional=True,
            metadata={"strength": "strong", "since": "2020"}
        )
        graph.add_relationship(rel)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "edges.json")
            graph.save(json_file, format='json')
            
            # Verify JSON structure
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            edge = data["edges"][0]
            assert edge["attributes"]["types"] == ["friend", "colleague"]
            assert edge["attributes"]["directional"] is True
            assert edge["attributes"]["metadata"]["strength"] == "strong"
            
            # Load and verify
            graph2 = ContactGraph()
            graph2.load(json_file, format='json')
            
            rels = graph2.get_relationships("uid-1")
            assert len(rels) == 1
            assert rels[0].types == ["friend", "colleague"]
            assert rels[0].directional is True
            assert rels[0].metadata["strength"] == "strong"
    
    def test_json_empty_graph(self):
        """Test saving and loading an empty graph in JSON format."""
        graph = ContactGraph()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "empty.json")
            graph.save(json_file, format='json')
            
            # Verify structure
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            assert data["nodes"] == []
            assert data["edges"] == []
            
            # Load and verify
            graph2 = ContactGraph()
            graph2.load(json_file, format='json')
            
            assert len(graph2.get_all_contacts()) == 0
    
    def test_json_format_explicit(self):
        """Test explicitly specifying JSON format."""
        graph = ContactGraph()
        contact = Contact(fn="Test", uid="test-uid")
        graph.add_contact(contact)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save with .txt extension but explicit JSON format
            file_path = os.path.join(tmpdir, "graph.txt")
            graph.save(file_path, format='json')
            
            # Verify it's JSON
            with open(file_path, 'r') as f:
                data = json.load(f)
            assert "nodes" in data
            
            # Load with explicit format
            graph2 = ContactGraph()
            graph2.load(file_path, format='json')
            
            loaded = graph2.get_contact("test-uid")
            assert loaded is not None
    
    def test_json_schema_compliance(self):
        """Test that exported JSON matches the expected schema."""
        graph = ContactGraph()
        
        contact1 = Contact(fn="Thomas", uid="thomas-uid")
        contact2 = Contact(fn="Eric", uid="eric-uid")
        
        graph.add_contact(contact1)
        graph.add_contact(contact2)
        
        rel = Relationship(
            source=contact1,
            target=contact2,
            types=["KNOWS"],
            directional=True
        )
        graph.add_relationship(rel)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "schema.json")
            graph.save(json_file, format='json')
            
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Verify top-level structure
            assert set(data.keys()) == {"attributes", "options", "nodes", "edges"}
            
            # Verify attributes
            assert isinstance(data["attributes"], dict)
            assert "name" in data["attributes"]
            
            # Verify options
            assert data["options"]["allowSelfLoops"] in [True, False]
            assert data["options"]["multi"] in [True, False]
            assert data["options"]["type"] in ["directed", "undirected", "mixed"]
            
            # Verify nodes structure
            for node in data["nodes"]:
                assert "key" in node
                assert isinstance(node["key"], str)
                # attributes is optional but if present should be dict
                if "attributes" in node:
                    assert isinstance(node["attributes"], dict)
            
            # Verify edges structure
            for edge in data["edges"]:
                assert "key" in edge
                assert "source" in edge
                assert "target" in edge
                assert isinstance(edge["source"], str)
                assert isinstance(edge["target"], str)
                # attributes is optional but if present should be dict
                if "attributes" in edge:
                    assert isinstance(edge["attributes"], dict)
