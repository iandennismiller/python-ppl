"""
Integration tests for JSON graph format with CLI.
"""
import pytest
import tempfile
import os
import json
from pathlib import Path
from ppl.models import Contact, ContactGraph
from ppl.serializers import vcard


class TestJSONGraphCLIIntegration:
    """Test JSON graph format with CLI workflows."""
    
    def test_cli_workflow_with_json_graph(self):
        """
        Test complete CLI workflow using JSON graph format.
        
        Demonstrates:
        1. Import contacts to JSON graph
        2. List contacts from JSON graph
        3. Export contacts from JSON graph
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            vcf_folder = os.path.join(tmpdir, "vcards")
            json_graph = os.path.join(tmpdir, "contacts.json")
            export_folder = os.path.join(tmpdir, "export")
            
            os.makedirs(vcf_folder)
            
            # Create test vCard files
            contact1 = Contact(
                fn="Alice Johnson",
                uid="alice-uid",
                email=["alice@example.com"],
                title="Engineer"
            )
            
            contact2 = Contact(
                fn="Bob Smith",
                uid="bob-uid",
                email=["bob@example.com"],
                title="Manager"
            )
            
            vcard.export_vcard(contact1, os.path.join(vcf_folder, "alice.vcf"))
            vcard.export_vcard(contact2, os.path.join(vcf_folder, "bob.vcf"))
            
            # Import to JSON graph using auto-detection
            graph = ContactGraph()
            contacts = vcard.bulk_import(vcf_folder)
            
            for contact in contacts:
                graph.add_contact(contact)
            
            graph.save(json_graph)  # Should auto-detect JSON from extension
            
            # Verify JSON file was created
            assert os.path.exists(json_graph)
            with open(json_graph, 'r') as f:
                data = json.load(f)
            assert "nodes" in data
            assert len(data["nodes"]) == 2
            
            # Load from JSON and export
            graph2 = ContactGraph()
            graph2.load(json_graph)  # Should auto-detect JSON from extension
            
            assert len(graph2.get_all_contacts()) == 2
            
            # Export to vCard
            all_contacts = graph2.get_all_contacts()
            vcard.bulk_export(all_contacts, export_folder, force=True)
            
            # Verify exported files
            assert os.path.exists(os.path.join(export_folder, "Alice Johnson.vcf"))
            assert os.path.exists(os.path.join(export_folder, "Bob Smith.vcf"))
    
    def test_explicit_json_format_specification(self):
        """Test explicitly specifying JSON format via CLI option."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "graph.db")  # Non-standard extension
            
            graph = ContactGraph()
            contact = Contact(fn="Test User", uid="test-uid")
            graph.add_contact(contact)
            
            # Save with explicit JSON format
            graph.save(graph_file, format='json')
            
            # Verify it's JSON
            with open(graph_file, 'r') as f:
                data = json.load(f)
            assert "nodes" in data
            
            # Load with explicit JSON format
            graph2 = ContactGraph()
            graph2.load(graph_file, format='json')
            
            loaded = graph2.get_contact("test-uid")
            assert loaded is not None
            assert loaded.fn == "Test User"
    
    def test_json_vs_graphml_format_compatibility(self):
        """
        Test that same data can be saved in both JSON and GraphML formats.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "contacts.json")
            graphml_file = os.path.join(tmpdir, "contacts.graphml")
            
            # Create graph with data
            graph = ContactGraph()
            contact1 = Contact(
                fn="Person 1",
                uid="uid-1",
                email=["p1@example.com"],
                title="Title 1"
            )
            contact2 = Contact(
                fn="Person 2",
                uid="uid-2",
                email=["p2@example.com"],
                title="Title 2"
            )
            
            graph.add_contact(contact1)
            graph.add_contact(contact2)
            
            # Save in both formats
            graph.save(json_file, format='json')
            graph.save(graphml_file, format='graphml')
            
            # Load from JSON
            graph_from_json = ContactGraph()
            graph_from_json.load(json_file, format='json')
            
            # Load from GraphML
            graph_from_graphml = ContactGraph()
            graph_from_graphml.load(graphml_file, format='graphml')
            
            # Verify both have same data
            json_contacts = {c.uid: c for c in graph_from_json.get_all_contacts()}
            graphml_contacts = {c.uid: c for c in graph_from_graphml.get_all_contacts()}
            
            assert set(json_contacts.keys()) == set(graphml_contacts.keys())
            
            for uid in json_contacts:
                assert json_contacts[uid].fn == graphml_contacts[uid].fn
                assert json_contacts[uid].email == graphml_contacts[uid].email
                assert json_contacts[uid].title == graphml_contacts[uid].title
    
    def test_json_graph_with_relationships(self):
        """Test JSON format preserves graph relationships correctly."""
        from ppl.models import Relationship
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "network.json")
            
            graph = ContactGraph()
            
            # Create contacts
            alice = Contact(fn="Alice", uid="alice-uid")
            bob = Contact(fn="Bob", uid="bob-uid")
            charlie = Contact(fn="Charlie", uid="charlie-uid")
            
            graph.add_contact(alice)
            graph.add_contact(bob)
            graph.add_contact(charlie)
            
            # Create relationships
            rel1 = Relationship(
                source=alice,
                target=bob,
                types=["friend"],
                directional=True
            )
            
            rel2 = Relationship(
                source=alice,
                target=charlie,
                types=["colleague"],
                directional=True
            )
            
            graph.add_relationship(rel1)
            graph.add_relationship(rel2)
            
            # Save to JSON
            graph.save(json_file, format='json')
            
            # Verify JSON structure
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            assert len(data["nodes"]) == 3
            assert len(data["edges"]) == 2
            
            # Verify edge structure
            edges = data["edges"]
            alice_edges = [e for e in edges if e["source"] == "alice-uid"]
            assert len(alice_edges) == 2
            
            targets = {e["target"] for e in alice_edges}
            assert "bob-uid" in targets
            assert "charlie-uid" in targets
            
            # Load and verify
            graph2 = ContactGraph()
            graph2.load(json_file, format='json')
            
            alice_rels = graph2.get_relationships("alice-uid")
            assert len(alice_rels) == 2
            
            target_uids = {rel.target.uid for rel in alice_rels}
            assert "bob-uid" in target_uids
            assert "charlie-uid" in target_uids
    
    def test_json_format_human_readable(self):
        """Test that JSON output is formatted for human readability."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "readable.json")
            
            graph = ContactGraph()
            contact = Contact(fn="Test", uid="test-uid", email=["test@example.com"])
            graph.add_contact(contact)
            
            graph.save(json_file, format='json')
            
            # Read raw content
            with open(json_file, 'r') as f:
                content = f.read()
            
            # Verify it's formatted (contains newlines and indentation)
            assert '\n' in content
            assert '  ' in content or '\t' in content
            
            # Verify it's valid JSON
            data = json.loads(content)
            assert "nodes" in data
