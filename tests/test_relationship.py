"""
Unit tests for Relationship model.
"""
import pytest
from ppl.models import Contact, Related, Relationship


class TestRelationship:
    """Test cases for Relationship class."""
    
    def test_relationship_creation(self):
        """Test creating a basic relationship."""
        source = Contact(fn="Alice", uid="alice-uid")
        target = Contact(fn="Bob", uid="bob-uid")
        
        rel = Relationship(
            source=source,
            target=target,
            types=["friend"],
            directional=False
        )
        
        assert rel.source == source
        assert rel.target == target
        assert "friend" in rel.types
        assert rel.directional is False
    
    def test_relationship_to_vcard_related(self):
        """Test converting relationship to vCard Related."""
        source = Contact(fn="Alice", uid="alice-uid")
        target = Contact(fn="Bob", uid="bob-uid")
        
        rel = Relationship(
            source=source,
            target=target,
            types=["friend", "colleague"],
            directional=False
        )
        
        related = rel.to_vcard_related()
        
        assert related.uri == "urn:uuid:bob-uid"
        assert "friend" in related.type
        assert "colleague" in related.type
    
    def test_relationship_from_vcard_related(self):
        """Test creating relationship from vCard Related."""
        source = Contact(fn="Alice", uid="alice-uid")
        target = Contact(fn="Bob", uid="bob-uid")
        
        related = Related(
            uri="urn:uuid:bob-uid",
            type=["parent"]
        )
        
        rel = Relationship.from_vcard_related(source, related, target)
        
        assert rel.source == source
        assert rel.target == target
        assert "parent" in rel.types
        assert rel.directional is True  # parent is a directional type
    
    def test_relationship_directional_detection(self):
        """Test that directional types are detected correctly."""
        source = Contact(fn="Alice", uid="alice-uid")
        target = Contact(fn="Bob", uid="bob-uid")
        
        # Directional type
        related_parent = Related(uri="urn:uuid:bob-uid", type=["parent"])
        rel_parent = Relationship.from_vcard_related(source, related_parent, target)
        assert rel_parent.directional is True
        
        # Non-directional type
        related_friend = Related(uri="urn:uuid:bob-uid", type=["friend"])
        rel_friend = Relationship.from_vcard_related(source, related_friend, target)
        assert rel_friend.directional is False
