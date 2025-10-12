"""
Unit tests for vCard serializer.
"""
import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path

from ppl.models import Contact, Related
from ppl.serializers import vcard


class TestVCardSerializer:
    """Test cases for vCard serialization."""
    
    def test_to_vcard_minimal(self):
        """Test serializing a minimal contact to vCard."""
        contact = Contact(fn="John Doe")
        vcard_str = vcard.to_vcard(contact)
        
        assert "BEGIN:VCARD" in vcard_str
        assert "VERSION:4.0" in vcard_str
        assert "FN:John Doe" in vcard_str
        assert "END:VCARD" in vcard_str
    
    def test_to_vcard_with_uid(self):
        """Test serializing a contact with UID."""
        contact = Contact(fn="Jane Smith", uid="urn:uuid:12345")
        vcard_str = vcard.to_vcard(contact)
        
        assert "UID:urn:uuid:12345" in vcard_str
    
    def test_to_vcard_with_email(self):
        """Test serializing a contact with email."""
        contact = Contact(
            fn="John Doe",
            email=["john@example.com", "jdoe@work.com"]
        )
        vcard_str = vcard.to_vcard(contact)
        
        assert "EMAIL:john@example.com" in vcard_str
        assert "EMAIL:jdoe@work.com" in vcard_str
    
    def test_to_vcard_with_related(self):
        """Test serializing a contact with RELATED properties."""
        contact = Contact(
            fn="Alice",
            uid="alice-uid",
            related=[
                Related(uri="urn:uuid:bob-uid", type=["friend", "colleague"]),
                Related(uri="urn:uuid:charlie-uid", type=["parent"])
            ]
        )
        vcard_str = vcard.to_vcard(contact)
        
        assert "RELATED" in vcard_str
        assert "urn:uuid:bob-uid" in vcard_str
        assert "urn:uuid:charlie-uid" in vcard_str
        assert "friend" in vcard_str or "colleague" in vcard_str
    
    def test_from_vcard_minimal(self):
        """Test parsing a minimal vCard."""
        vcard_str = """BEGIN:VCARD
VERSION:4.0
FN:John Doe
END:VCARD"""
        
        contact = vcard.from_vcard(vcard_str)
        
        assert contact.fn == "John Doe"
        assert contact.version == "4.0"
    
    def test_from_vcard_with_uid(self):
        """Test parsing a vCard with UID."""
        vcard_str = """BEGIN:VCARD
VERSION:4.0
UID:urn:uuid:12345
FN:Jane Smith
END:VCARD"""
        
        contact = vcard.from_vcard(vcard_str)
        
        assert contact.fn == "Jane Smith"
        assert contact.uid == "urn:uuid:12345"
    
    def test_from_vcard_with_email(self):
        """Test parsing a vCard with email addresses."""
        vcard_str = """BEGIN:VCARD
VERSION:4.0
FN:John Doe
EMAIL:john@example.com
EMAIL:jdoe@work.com
END:VCARD"""
        
        contact = vcard.from_vcard(vcard_str)
        
        assert "john@example.com" in contact.email
        assert "jdoe@work.com" in contact.email
    
    def test_from_vcard_with_related(self):
        """Test parsing a vCard with RELATED properties."""
        vcard_str = """BEGIN:VCARD
VERSION:4.0
FN:Alice
UID:alice-uid
RELATED;TYPE=friend:urn:uuid:bob-uid
RELATED;TYPE=parent:urn:uuid:charlie-uid
END:VCARD"""
        
        contact = vcard.from_vcard(vcard_str)
        
        assert len(contact.related) == 2
        assert any(r.uri == "urn:uuid:bob-uid" for r in contact.related)
        assert any(r.uri == "urn:uuid:charlie-uid" for r in contact.related)
        
        bob_related = next(r for r in contact.related if r.uri == "urn:uuid:bob-uid")
        assert "friend" in bob_related.type
    
    def test_roundtrip(self):
        """Test that serialization and parsing are inverse operations."""
        original = Contact(
            fn="John Doe",
            uid="urn:uuid:12345",
            email=["john@example.com"],
            tel=["+1-555-0100"],
            title="Software Engineer"
        )
        
        # Serialize
        vcard_str = vcard.to_vcard(original)
        
        # Parse
        parsed = vcard.from_vcard(vcard_str)
        
        # Compare
        assert parsed.fn == original.fn
        assert parsed.uid == original.uid
        assert parsed.email == original.email
        assert parsed.tel == original.tel
        assert parsed.title == original.title
    
    def test_import_export_file(self):
        """Test importing and exporting vCard files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.vcf")
            
            # Create and export
            contact = Contact(
                fn="Jane Smith",
                uid="jane-uid",
                email=["jane@example.com"]
            )
            vcard.export_vcard(contact, file_path)
            
            # Import
            imported = vcard.import_vcard(file_path)
            
            # Verify
            assert imported.fn == "Jane Smith"
            assert imported.uid == "jane-uid"
            assert "jane@example.com" in imported.email
    
    def test_bulk_import_export(self):
        """Test bulk import and export operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create contacts
            contacts = [
                Contact(fn="Alice", uid="alice-uid", email=["alice@example.com"]),
                Contact(fn="Bob", uid="bob-uid", email=["bob@example.com"]),
                Contact(fn="Charlie", uid="charlie-uid", email=["charlie@example.com"])
            ]
            
            # Bulk export
            vcard.bulk_export(contacts, tmpdir)
            
            # Verify files were created
            assert os.path.exists(os.path.join(tmpdir, "Alice.vcf"))
            assert os.path.exists(os.path.join(tmpdir, "Bob.vcf"))
            assert os.path.exists(os.path.join(tmpdir, "Charlie.vcf"))
            
            # Bulk import
            imported = vcard.bulk_import(tmpdir)
            
            # Verify
            assert len(imported) == 3
            assert any(c.fn == "Alice" for c in imported)
            assert any(c.fn == "Bob" for c in imported)
            assert any(c.fn == "Charlie" for c in imported)
    
    def test_extract_relationships(self):
        """Test extracting relationships from a contact."""
        contact = Contact(
            fn="Alice",
            uid="alice-uid",
            related=[
                Related(uri="urn:uuid:bob-uid", type=["friend"]),
                Related(uri="urn:uuid:charlie-uid", type=["colleague"])
            ]
        )
        
        relationships = vcard.extract_relationships(contact)
        
        assert len(relationships) == 2
        assert all(rel.source == contact for rel in relationships)
    
    def test_compare_rev(self):
        """Test REV comparison for merge decisions."""
        older = Contact(fn="Contact", rev=datetime(2024, 1, 1))
        newer = Contact(fn="Contact", rev=datetime(2024, 6, 1))
        
        assert vcard.compare_rev(newer, older) is True
        assert vcard.compare_rev(older, newer) is False
        assert vcard.compare_rev(newer, newer) is True
