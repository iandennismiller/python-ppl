"""
Unit tests for Contact model.
"""
import pytest
from datetime import datetime
from ppl.models import Contact, Related


class TestContact:
    """Test cases for Contact class."""
    
    def test_contact_creation_minimal(self):
        """Test creating a contact with minimal required fields."""
        contact = Contact(fn="John Doe")
        assert contact.fn == "John Doe"
        assert contact.version == "4.0"
        assert contact.uid is None
        assert contact.email == []
        assert contact.tel == []
    
    def test_contact_creation_full(self):
        """Test creating a contact with all common fields."""
        contact = Contact(
            fn="Jane Smith",
            uid="urn:uuid:12345",
            n="Smith;Jane;Mary;Dr.;PhD",
            email=["jane@example.com"],
            tel=["+1-555-0100"],
            org=["Acme Corp"],
            title="Software Engineer"
        )
        assert contact.fn == "Jane Smith"
        assert contact.uid == "urn:uuid:12345"
        assert contact.n == "Smith;Jane;Mary;Dr.;PhD"
        assert "jane@example.com" in contact.email
        assert "+1-555-0100" in contact.tel
        assert "Acme Corp" in contact.org
        assert contact.title == "Software Engineer"
    
    def test_contact_requires_fn(self):
        """Test that Contact requires FN field."""
        with pytest.raises(ValueError, match="FN .* is required"):
            Contact(fn="")
    
    def test_contact_compare_rev_both_none(self):
        """Test REV comparison when both are None."""
        c1 = Contact(fn="Contact 1")
        c2 = Contact(fn="Contact 2")
        assert c1.compare_rev(c2) == 0
    
    def test_contact_compare_rev_one_none(self):
        """Test REV comparison when one is None."""
        c1 = Contact(fn="Contact 1")
        c2 = Contact(fn="Contact 2", rev=datetime(2024, 1, 1))
        assert c1.compare_rev(c2) == -1
        assert c2.compare_rev(c1) == 1
    
    def test_contact_compare_rev_different(self):
        """Test REV comparison with different timestamps."""
        c1 = Contact(fn="Contact 1", rev=datetime(2024, 1, 1))
        c2 = Contact(fn="Contact 2", rev=datetime(2024, 6, 1))
        assert c1.compare_rev(c2) == -1
        assert c2.compare_rev(c1) == 1
    
    def test_contact_compare_rev_equal(self):
        """Test REV comparison with equal timestamps."""
        rev_time = datetime(2024, 1, 1)
        c1 = Contact(fn="Contact 1", rev=rev_time)
        c2 = Contact(fn="Contact 2", rev=rev_time)
        assert c1.compare_rev(c2) == 0


class TestRelated:
    """Test cases for Related class."""
    
    def test_related_creation_minimal(self):
        """Test creating a Related with minimal fields."""
        related = Related(uri="urn:uuid:12345")
        assert related.uri == "urn:uuid:12345"
        assert related.type == []
        assert related.text_value is None
        assert related.pref is None
    
    def test_related_creation_full(self):
        """Test creating a Related with all fields."""
        related = Related(
            uri="urn:uuid:12345",
            type=["friend", "colleague"],
            text_value="John Doe",
            pref=1
        )
        assert related.uri == "urn:uuid:12345"
        assert "friend" in related.type
        assert "colleague" in related.type
        assert related.text_value == "John Doe"
        assert related.pref == 1
