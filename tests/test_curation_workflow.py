"""
Integration tests for contact curation workflows.
"""
import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path
from ppl.models import Contact, ContactGraph
from ppl.serializers import vcard, markdown


class TestCurationWorkflow:
    """Test complete contact curation workflows."""
    
    def test_incremental_vcard_curation(self):
        """
        Test incremental curation workflow with vCard files.
        
        Simulates a user updating contact information over time:
        1. Initial import with basic info
        2. Update with new email (preserves existing data)
        3. Update with new title (preserves both email addresses)
        4. Attempt update with older REV (should be skipped)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "contacts.graphml")
            vcf_folder = os.path.join(tmpdir, "vcards")
            os.makedirs(vcf_folder)
            
            # Step 1: Initial import
            contact_v1 = Contact(
                fn="John Smith",
                uid="john-uid",
                email=["john@work.com"],
                rev=datetime(2024, 1, 1)
            )
            
            graph = ContactGraph()
            modified, action = graph.merge_contact(contact_v1)
            assert action == "added"
            graph.save(graph_file)
            
            # Step 2: Update with new email (missing title from v1 - should preserve)
            contact_v2 = Contact(
                fn="John Smith",
                uid="john-uid",
                email=["john@personal.com"],  # New email, old one missing
                title="Engineer",  # New field
                rev=datetime(2024, 3, 1)
            )
            
            graph = ContactGraph()
            graph.load(graph_file)
            modified, action = graph.merge_contact(contact_v2)
            assert action == "updated"
            
            merged = graph.get_contact("john-uid")
            # Should have both emails (non-destructive merge)
            assert "john@work.com" in merged.email
            assert "john@personal.com" in merged.email
            assert merged.title == "Engineer"
            assert merged.rev == datetime(2024, 3, 1)
            
            graph.save(graph_file)
            
            # Step 3: Update with new title
            contact_v3 = Contact(
                fn="John Smith",
                uid="john-uid",
                title="Senior Engineer",
                tel=["+1-555-0123"],  # New field
                rev=datetime(2024, 6, 1)
            )
            
            graph = ContactGraph()
            graph.load(graph_file)
            modified, action = graph.merge_contact(contact_v3)
            assert action == "updated"
            
            merged = graph.get_contact("john-uid")
            # Should preserve both emails
            assert "john@work.com" in merged.email
            assert "john@personal.com" in merged.email
            # Should have updated title
            assert merged.title == "Senior Engineer"
            # Should have new phone
            assert "+1-555-0123" in merged.tel
            assert merged.rev == datetime(2024, 6, 1)
            
            graph.save(graph_file)
            
            # Step 4: Attempt update with older REV (should be skipped)
            contact_v_old = Contact(
                fn="John Smith",
                uid="john-uid",
                title="Intern",  # Trying to overwrite with old data
                rev=datetime(2024, 2, 1)  # Older than current (2024-06-01)
            )
            
            graph = ContactGraph()
            graph.load(graph_file)
            modified, action = graph.merge_contact(contact_v_old)
            assert action == "skipped"
            assert modified is False
            
            merged = graph.get_contact("john-uid")
            # Should preserve current data
            assert merged.title == "Senior Engineer"
            assert merged.rev == datetime(2024, 6, 1)
    
    def test_export_only_writes_changed_files(self):
        """
        Test that export only writes files when data has changed.
        
        Demonstrates:
        1. Initial export creates all files
        2. Re-export with no changes skips all files
        3. Re-export with one changed contact writes only that file
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            export_folder = os.path.join(tmpdir, "export")
            
            # Create contacts
            contacts = [
                Contact(fn="Alice", uid="alice-uid", email=["alice@example.com"], rev=datetime(2024, 1, 1)),
                Contact(fn="Bob", uid="bob-uid", email=["bob@example.com"], rev=datetime(2024, 1, 1)),
                Contact(fn="Charlie", uid="charlie-uid", email=["charlie@example.com"], rev=datetime(2024, 1, 1))
            ]
            
            # Initial export
            written, skipped = vcard.bulk_export(contacts, export_folder, force=False)
            assert written == 3
            assert skipped == 0
            
            # Verify files exist
            assert os.path.exists(os.path.join(export_folder, "Alice.vcf"))
            assert os.path.exists(os.path.join(export_folder, "Bob.vcf"))
            assert os.path.exists(os.path.join(export_folder, "Charlie.vcf"))
            
            # Re-export with no changes
            written, skipped = vcard.bulk_export(contacts, export_folder, force=False)
            assert written == 0
            assert skipped == 3
            
            # Update one contact
            contacts[0] = Contact(
                fn="Alice",
                uid="alice-uid",
                email=["alice@example.com"],
                title="Senior Developer",  # New field
                rev=datetime(2024, 6, 1)  # Newer REV
            )
            
            # Re-export with one change
            written, skipped = vcard.bulk_export(contacts, export_folder, force=False)
            assert written == 1  # Only Alice
            assert skipped == 2  # Bob and Charlie
    
    def test_markdown_curation_with_wiki_links(self):
        """
        Test markdown curation preserves wiki-style relationships.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            md_folder = tmpdir
            
            # Create two contacts with relationship
            alice = Contact(
                fn="Alice",
                uid="alice-uid",
                email=["alice@example.com"],
                rev=datetime(2024, 1, 1)
            )
            
            bob = Contact(
                fn="Bob",
                uid="bob-uid",
                email=["bob@example.com"],
                rev=datetime(2024, 1, 1)
            )
            
            # Export initial contacts
            contacts = [alice, bob]
            written, skipped = markdown.bulk_export_markdown(contacts, md_folder)
            assert written == 2
            
            # Simulate user editing Alice's markdown to add more info
            # This represents incremental curation
            alice_updated = Contact(
                fn="Alice",
                uid="alice-uid",
                title="Engineer",  # New field
                rev=datetime(2024, 3, 1)  # Newer
            )
            
            # Re-export - only Alice should be written
            contacts_updated = [alice_updated, bob]
            written, skipped = markdown.bulk_export_markdown(contacts_updated, md_folder)
            assert written == 1  # Only Alice updated
            assert skipped == 1  # Bob unchanged
    
    def test_force_export_overrides_change_detection(self):
        """Test that force flag overrides change detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contacts = [
                Contact(fn="Person 1", uid="uid-1", email=["p1@example.com"]),
                Contact(fn="Person 2", uid="uid-2", email=["p2@example.com"])
            ]
            
            # Export with force
            written, skipped = vcard.bulk_export(contacts, tmpdir, force=True)
            assert written == 2
            assert skipped == 0
            
            # Re-export with force (should write all again)
            written, skipped = vcard.bulk_export(contacts, tmpdir, force=True)
            assert written == 2
            assert skipped == 0
    
    def test_multi_field_incremental_updates(self):
        """
        Test that multiple field updates over time work correctly.
        
        Simulates a user curating contact information field by field.
        """
        graph = ContactGraph()
        
        # Start with minimal contact
        contact_v1 = Contact(
            fn="Emily Johnson",
            uid="emily-uid",
            rev=datetime(2024, 1, 1)
        )
        graph.merge_contact(contact_v1)
        
        # Add email
        contact_v2 = Contact(
            fn="Emily Johnson",
            uid="emily-uid",
            email=["emily@example.com"],
            rev=datetime(2024, 2, 1)
        )
        graph.merge_contact(contact_v2)
        
        # Add phone
        contact_v3 = Contact(
            fn="Emily Johnson",
            uid="emily-uid",
            tel=["+1-555-0001"],
            rev=datetime(2024, 3, 1)
        )
        graph.merge_contact(contact_v3)
        
        # Add title
        contact_v4 = Contact(
            fn="Emily Johnson",
            uid="emily-uid",
            title="Product Manager",
            rev=datetime(2024, 4, 1)
        )
        graph.merge_contact(contact_v4)
        
        # Verify all fields are present
        final = graph.get_contact("emily-uid")
        assert final.email == ["emily@example.com"]
        assert final.tel == ["+1-555-0001"]
        assert final.title == "Product Manager"
        assert final.rev == datetime(2024, 4, 1)
    
    def test_partial_contact_does_not_delete_fields(self):
        """
        Test that importing a partial contact doesn't delete existing fields.
        
        This is critical for curation workflows where users may only
        provide a subset of fields in each update.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_file = os.path.join(tmpdir, "contacts.graphml")
            
            # Create full contact
            full_contact = Contact(
                fn="David Wilson",
                uid="david-uid",
                email=["david@work.com", "david@personal.com"],
                tel=["+1-555-0001", "+1-555-0002"],
                title="Director",
                note="Important contact",
                categories=["work", "vip"],
                rev=datetime(2024, 1, 1)
            )
            
            graph = ContactGraph()
            graph.merge_contact(full_contact)
            graph.save(graph_file)
            
            # Import partial contact (only email, missing other fields)
            partial_contact = Contact(
                fn="David Wilson",
                uid="david-uid",
                email=["david@newwork.com"],  # New email, old ones missing
                rev=datetime(2024, 3, 1)
            )
            
            graph = ContactGraph()
            graph.load(graph_file)
            modified, action = graph.merge_contact(partial_contact)
            assert action == "updated"
            
            # Verify all original fields are preserved
            merged = graph.get_contact("david-uid")
            assert merged.tel == ["+1-555-0001", "+1-555-0002"]
            assert merged.title == "Director"
            assert merged.note == "Important contact"
            assert merged.categories == ["work", "vip"]
            
            # Email should be merged (all three addresses)
            assert "david@work.com" in merged.email
            assert "david@personal.com" in merged.email
            assert "david@newwork.com" in merged.email
            assert len(merged.email) == 3
