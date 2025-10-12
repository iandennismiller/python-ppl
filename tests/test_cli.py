"""
Tests for CLI commands.
"""
import pytest
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner

from ppl.cli import cli
from ppl.models import Contact, ContactGraph, FilterContext, import_pipeline
from ppl.filters import UIDFilter


class TestShowCommand:
    """Test the 'ppl show' command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
    def test_show_text_format(self):
        """Test show command with default text format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            # Create and save a test contact
            contact = Contact(
                fn="John Doe",
                email=["john@example.com"],
                tel=["+1-555-1234"],
                title="Engineer"
            )
            
            # Assign UID
            import_pipeline.filters.clear()
            import_pipeline.register(UIDFilter())
            context = FilterContext(pipeline_name="import")
            contact = import_pipeline.run(contact, context)
            
            # Save to graph
            graph = ContactGraph()
            graph.add_contact(contact)
            graph.save(graph_file)
            
            # Run show command
            result = self.runner.invoke(cli, ['show', graph_file, contact.uid])
            
            assert result.exit_code == 0
            assert "John Doe" in result.output
            assert contact.uid in result.output
            assert "john@example.com" in result.output
            assert "+1-555-1234" in result.output
            assert "Engineer" in result.output
    
    def test_show_json_format(self):
        """Test show command with JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            # Create and save a test contact
            contact = Contact(
                fn="Jane Smith",
                email=["jane@example.com"],
                uid="test-uid-123"
            )
            
            graph = ContactGraph()
            graph.add_contact(contact)
            graph.save(graph_file)
            
            # Run show command with JSON format
            result = self.runner.invoke(cli, ['show', graph_file, 'test-uid-123', '--format', 'json'])
            
            assert result.exit_code == 0
            assert '"fn": "Jane Smith"' in result.output
            assert '"uid": "test-uid-123"' in result.output
            assert '"email"' in result.output
    
    def test_show_yaml_format(self):
        """Test show command with YAML format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            # Create and save a test contact
            contact = Contact(
                fn="Bob Jones",
                email=["bob@example.com"],
                uid="test-uid-456"
            )
            
            graph = ContactGraph()
            graph.add_contact(contact)
            graph.save(graph_file)
            
            # Run show command with YAML format
            result = self.runner.invoke(cli, ['show', graph_file, 'test-uid-456', '--format', 'yaml'])
            
            assert result.exit_code == 0
            assert "FN: Bob Jones" in result.output
            assert "UID: test-uid-456" in result.output
    
    def test_show_vcard_format(self):
        """Test show command with vCard format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            # Create and save a test contact
            contact = Contact(
                fn="Alice Brown",
                email=["alice@example.com"],
                uid="test-uid-789"
            )
            
            graph = ContactGraph()
            graph.add_contact(contact)
            graph.save(graph_file)
            
            # Run show command with vCard format
            result = self.runner.invoke(cli, ['show', graph_file, 'test-uid-789', '--format', 'vcard'])
            
            assert result.exit_code == 0
            assert "BEGIN:VCARD" in result.output
            assert "FN:Alice Brown" in result.output
            assert "UID:test-uid-789" in result.output
            assert "END:VCARD" in result.output
    
    def test_show_markdown_format(self):
        """Test show command with Markdown format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            # Create and save a test contact
            contact = Contact(
                fn="Charlie Green",
                email=["charlie@example.com"],
                uid="test-uid-999"
            )
            
            graph = ContactGraph()
            graph.add_contact(contact)
            graph.save(graph_file)
            
            # Run show command with Markdown format
            result = self.runner.invoke(cli, ['show', graph_file, 'test-uid-999', '--format', 'markdown'])
            
            assert result.exit_code == 0
            assert "FN: Charlie Green" in result.output
            assert "UID: test-uid-999" in result.output
    
    def test_show_nonexistent_uid(self):
        """Test show command with non-existent UID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            # Create empty graph
            graph = ContactGraph()
            graph.save(graph_file)
            
            # Run show command with non-existent UID
            result = self.runner.invoke(cli, ['show', graph_file, 'nonexistent-uid'])
            
            assert result.exit_code == 1
            assert "not found" in result.output
    
    def test_show_with_relationships(self):
        """Test show command displays relationships."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            # Create contacts with relationships
            alice = Contact(
                fn="Alice",
                email=["alice@example.com"],
                uid="alice-uid"
            )
            
            bob = Contact(
                fn="Bob",
                email=["bob@example.com"],
                uid="bob-uid"
            )
            
            # Build graph
            graph = ContactGraph()
            graph.add_contact(alice)
            graph.add_contact(bob)
            
            # Add relationship
            from ppl.models import Relationship
            rel = Relationship(
                source=bob,
                target=alice,
                types=['friend']
            )
            graph.add_relationship(rel)
            
            graph.save(graph_file)
            
            # Run show command for Bob
            result = self.runner.invoke(cli, ['show', graph_file, 'bob-uid'])
            
            assert result.exit_code == 0
            assert "Bob" in result.output
            assert "Relationships:" in result.output
            assert "friend" in result.output
            assert "Alice" in result.output


class TestFilterCommand:
    """Test the 'ppl filter' command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
    def test_filter_single_contact_dry_run(self):
        """Test filter command on single contact with dry-run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            # Create a contact without gender
            contact = Contact(
                fn="Alice",
                email=["alice@example.com"],
                uid="alice-uid"
            )
            
            graph = ContactGraph()
            graph.add_contact(contact)
            graph.save(graph_file)
            
            # Run filter command with dry-run
            result = self.runner.invoke(cli, ['filter', graph_file, 'alice-uid', '--dry-run'])
            
            assert result.exit_code == 0
            assert "Dry run complete" in result.output
    
    def test_filter_all_contacts_dry_run(self):
        """Test filter command on all contacts with dry-run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            # Create contacts
            alice = Contact(fn="Alice", email=["alice@example.com"], uid="alice-uid")
            bob = Contact(fn="Bob", email=["bob@example.com"], uid="bob-uid")
            
            graph = ContactGraph()
            graph.add_contact(alice)
            graph.add_contact(bob)
            graph.save(graph_file)
            
            # Run filter command on all contacts with dry-run
            result = self.runner.invoke(cli, ['filter', graph_file, '--all', '--dry-run'])
            
            assert result.exit_code == 0
            assert "Dry run complete" in result.output
    
    def test_filter_missing_uid_and_all_flag(self):
        """Test filter command with neither UID nor --all flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            graph = ContactGraph()
            graph.save(graph_file)
            
            # Run filter command without UID or --all flag
            result = self.runner.invoke(cli, ['filter', graph_file])
            
            assert result.exit_code == 1
            assert "Must specify either UID or --all flag" in result.output
    
    def test_filter_both_uid_and_all_flag(self):
        """Test filter command with both UID and --all flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            contact = Contact(fn="Alice", email=["alice@example.com"], uid="alice-uid")
            graph = ContactGraph()
            graph.add_contact(contact)
            graph.save(graph_file)
            
            # Run filter command with both UID and --all flag
            result = self.runner.invoke(cli, ['filter', graph_file, 'alice-uid', '--all'])
            
            assert result.exit_code == 1
            assert "Cannot specify both UID and --all flag" in result.output
    
    def test_filter_nonexistent_uid(self):
        """Test filter command with non-existent UID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            graph = ContactGraph()
            graph.save(graph_file)
            
            # Run filter command with non-existent UID
            result = self.runner.invoke(cli, ['filter', graph_file, 'nonexistent-uid'])
            
            assert result.exit_code == 1
            assert "not found" in result.output
    
    def test_filter_saves_changes(self):
        """Test filter command saves changes when not in dry-run mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "test.graphml")
            
            # Create a contact
            contact = Contact(
                fn="Alice",
                email=["alice@example.com"],
                uid="alice-uid"
            )
            
            graph = ContactGraph()
            graph.add_contact(contact)
            graph.save(graph_file)
            
            # Run filter command (not dry-run)
            result = self.runner.invoke(cli, ['filter', graph_file, 'alice-uid'])
            
            assert result.exit_code == 0
            
            # Verify graph can still be loaded
            graph_after = ContactGraph()
            graph_after.load(graph_file)
            assert graph_after.get_contact("alice-uid") is not None

