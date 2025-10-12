"""
Tests for export change detection functionality.
"""
import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path
from ppl.models import Contact
from ppl.serializers import vcard, markdown


class TestVCardChangeDetection:
    """Test vCard export change detection."""
    
    def test_should_export_when_file_missing(self):
        """Test that should_export returns True when file doesn't exist."""
        contact = Contact(fn="Alice", uid="alice-uid")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "nonexistent.vcf")
            
            assert vcard.should_export_vcard(contact, file_path) is True
    
    def test_should_export_when_newer(self):
        """Test that should_export returns True when contact is newer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "contact.vcf")
            
            # Create and export old contact
            old_contact = Contact(
                fn="Bob",
                uid="bob-uid",
                title="Junior Dev",
                rev=datetime(2024, 1, 1)
            )
            vcard.export_vcard(old_contact, file_path)
            
            # Check if newer contact should be exported
            new_contact = Contact(
                fn="Bob",
                uid="bob-uid",
                title="Senior Dev",
                rev=datetime(2024, 6, 1)
            )
            
            assert vcard.should_export_vcard(new_contact, file_path) is True
    
    def test_should_not_export_when_older(self):
        """Test that should_export returns False when contact is older."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "contact.vcf")
            
            # Create and export newer contact
            new_contact = Contact(
                fn="Charlie",
                uid="charlie-uid",
                title="Senior Dev",
                rev=datetime(2024, 6, 1)
            )
            vcard.export_vcard(new_contact, file_path)
            
            # Check if older contact should be exported
            old_contact = Contact(
                fn="Charlie",
                uid="charlie-uid",
                title="Junior Dev",
                rev=datetime(2024, 1, 1)
            )
            
            assert vcard.should_export_vcard(old_contact, file_path) is False
    
    def test_should_export_when_content_differs_same_rev(self):
        """Test that should_export returns True when content differs with same REV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "contact.vcf")
            
            # Create and export contact
            contact1 = Contact(
                fn="Diana",
                uid="diana-uid",
                title="Engineer",
                rev=datetime(2024, 3, 1)
            )
            vcard.export_vcard(contact1, file_path)
            
            # Check contact with same REV but different content
            contact2 = Contact(
                fn="Diana",
                uid="diana-uid",
                title="Engineer",
                email=["diana@example.com"],  # Added email
                rev=datetime(2024, 3, 1)  # Same REV
            )
            
            assert vcard.should_export_vcard(contact2, file_path) is True
    
    def test_should_not_export_when_identical(self):
        """Test that should_export returns False when content is identical."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "contact.vcf")
            
            # Create and export contact
            contact = Contact(
                fn="Eve",
                uid="eve-uid",
                title="Manager",
                email=["eve@example.com"],
                rev=datetime(2024, 3, 1)
            )
            vcard.export_vcard(contact, file_path)
            
            # Check identical contact
            assert vcard.should_export_vcard(contact, file_path) is False
    
    def test_bulk_export_skips_unchanged(self):
        """Test that bulk_export skips unchanged files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial contacts
            contacts = [
                Contact(fn="Person 1", uid="uid-1", email=["p1@example.com"], rev=datetime(2024, 1, 1)),
                Contact(fn="Person 2", uid="uid-2", email=["p2@example.com"], rev=datetime(2024, 1, 1))
            ]
            
            # Export all
            written, skipped = vcard.bulk_export(contacts, tmpdir, force=True)
            assert written == 2
            assert skipped == 0
            
            # Export again without changes
            written, skipped = vcard.bulk_export(contacts, tmpdir, force=False)
            assert written == 0
            assert skipped == 2
    
    def test_bulk_export_writes_changed(self):
        """Test that bulk_export writes changed files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Export initial contacts
            contacts = [
                Contact(fn="Alice", uid="alice-uid", title="Dev", rev=datetime(2024, 1, 1)),
                Contact(fn="Bob", uid="bob-uid", title="PM", rev=datetime(2024, 1, 1))
            ]
            vcard.bulk_export(contacts, tmpdir, force=True)
            
            # Update one contact
            updated_contacts = [
                Contact(fn="Alice", uid="alice-uid", title="Senior Dev", rev=datetime(2024, 6, 1)),  # Updated
                Contact(fn="Bob", uid="bob-uid", title="PM", rev=datetime(2024, 1, 1))  # Unchanged
            ]
            
            written, skipped = vcard.bulk_export(updated_contacts, tmpdir, force=False)
            assert written == 1  # Only Alice updated
            assert skipped == 1  # Bob skipped
    
    def test_bulk_export_force_writes_all(self):
        """Test that bulk_export with force=True writes all files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contacts = [
                Contact(fn="Charlie", uid="charlie-uid", email=["charlie@example.com"]),
                Contact(fn="Diana", uid="diana-uid", email=["diana@example.com"])
            ]
            
            # First export
            vcard.bulk_export(contacts, tmpdir, force=True)
            
            # Second export with force
            written, skipped = vcard.bulk_export(contacts, tmpdir, force=True)
            assert written == 2
            assert skipped == 0


class TestMarkdownChangeDetection:
    """Test markdown export change detection."""
    
    def test_should_export_when_file_missing(self):
        """Test that should_export returns True when file doesn't exist."""
        contact = Contact(fn="Alice", uid="alice-uid")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "nonexistent.md")
            
            assert markdown.should_export_markdown(contact, file_path, tmpdir) is True
    
    def test_should_export_when_newer(self):
        """Test that should_export returns True when contact is newer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "Bob.md")
            
            # Create and export old contact
            old_contact = Contact(
                fn="Bob",
                uid="bob-uid",
                title="Junior Dev",
                rev=datetime(2024, 1, 1)
            )
            md_content = markdown.to_markdown(old_contact)
            with open(file_path, 'w') as f:
                f.write(md_content)
            
            # Check if newer contact should be exported
            new_contact = Contact(
                fn="Bob",
                uid="bob-uid",
                title="Senior Dev",
                rev=datetime(2024, 6, 1)
            )
            
            assert markdown.should_export_markdown(new_contact, file_path, tmpdir) is True
    
    def test_should_not_export_when_older(self):
        """Test that should_export returns False when contact is older."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "Charlie.md")
            
            # Create and export newer contact
            new_contact = Contact(
                fn="Charlie",
                uid="charlie-uid",
                title="Senior Dev",
                rev=datetime(2024, 6, 1)
            )
            md_content = markdown.to_markdown(new_contact)
            with open(file_path, 'w') as f:
                f.write(md_content)
            
            # Check if older contact should be exported
            old_contact = Contact(
                fn="Charlie",
                uid="charlie-uid",
                title="Junior Dev",
                rev=datetime(2024, 1, 1)
            )
            
            assert markdown.should_export_markdown(old_contact, file_path, tmpdir) is False
    
    def test_bulk_export_skips_unchanged(self):
        """Test that bulk_export skips unchanged files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contacts = [
                Contact(fn="Person 1", uid="uid-1", email=["p1@example.com"]),
                Contact(fn="Person 2", uid="uid-2", email=["p2@example.com"])
            ]
            
            # Export all
            written, skipped = markdown.bulk_export_markdown(contacts, tmpdir, force=True)
            assert written == 2
            assert skipped == 0
            
            # Export again without changes
            written, skipped = markdown.bulk_export_markdown(contacts, tmpdir, force=False)
            assert written == 0
            assert skipped == 2
    
    def test_bulk_export_writes_changed(self):
        """Test that bulk_export writes changed files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Export initial contacts
            contacts = [
                Contact(fn="Alice", uid="alice-uid", title="Dev", rev=datetime(2024, 1, 1)),
                Contact(fn="Bob", uid="bob-uid", title="PM", rev=datetime(2024, 1, 1))
            ]
            markdown.bulk_export_markdown(contacts, tmpdir, force=True)
            
            # Update one contact
            updated_contacts = [
                Contact(fn="Alice", uid="alice-uid", title="Senior Dev", rev=datetime(2024, 6, 1)),
                Contact(fn="Bob", uid="bob-uid", title="PM", rev=datetime(2024, 1, 1))
            ]
            
            written, skipped = markdown.bulk_export_markdown(updated_contacts, tmpdir, force=False)
            assert written == 1
            assert skipped == 1
