"""
Tests for Contact merge functionality.
"""
import pytest
from datetime import datetime
from ppl.models import Contact, Related


class TestContactMerge:
    """Test Contact.merge_from() method."""
    
    def test_merge_empty_into_full(self):
        """Test merging an empty contact into a full one preserves all data."""
        full = Contact(
            fn="John Doe",
            uid="john-uid",
            email=["john@example.com"],
            tel=["+1-555-0123"],
            title="Engineer",
            note="Original note"
        )
        
        empty = Contact(fn="John Doe", uid="john-uid")
        
        full.merge_from(empty)
        
        # All original data should be preserved
        assert full.email == ["john@example.com"]
        assert full.tel == ["+1-555-0123"]
        assert full.title == "Engineer"
        assert full.note == "Original note"
    
    def test_merge_full_into_empty(self):
        """Test merging a full contact into an empty one imports all data."""
        empty = Contact(fn="John Doe", uid="john-uid")
        
        full = Contact(
            fn="John Doe",
            uid="john-uid",
            email=["john@example.com"],
            tel=["+1-555-0123"],
            title="Engineer",
            note="New note"
        )
        
        empty.merge_from(full)
        
        # All new data should be imported
        assert empty.email == ["john@example.com"]
        assert empty.tel == ["+1-555-0123"]
        assert empty.title == "Engineer"
        assert empty.note == "New note"
    
    def test_merge_missing_fields_not_deleted(self):
        """Test that missing fields in incoming contact don't delete existing data."""
        existing = Contact(
            fn="Jane Smith",
            uid="jane-uid",
            email=["jane@example.com"],
            tel=["+1-555-9999"],
            title="Manager",
            note="Important note"
        )
        
        # Incoming contact only has email, missing tel, title, note
        incoming = Contact(
            fn="Jane Smith",
            uid="jane-uid",
            email=["jane@newdomain.com"]
        )
        
        existing.merge_from(incoming, prefer_newer=False)
        
        # Original fields should be preserved
        assert existing.tel == ["+1-555-9999"]
        assert existing.title == "Manager"
        assert existing.note == "Important note"
        
        # Email should be merged
        assert "jane@example.com" in existing.email
        assert "jane@newdomain.com" in existing.email
    
    def test_merge_with_newer_rev(self):
        """Test that newer REV timestamp wins conflicts."""
        older = Contact(
            fn="Alice",
            uid="alice-uid",
            title="Junior Developer",
            note="Old note",
            rev=datetime(2024, 1, 1)
        )
        
        newer = Contact(
            fn="Alice",
            uid="alice-uid",
            title="Senior Developer",
            note="New note",
            rev=datetime(2024, 6, 1)
        )
        
        older.merge_from(newer, prefer_newer=True)
        
        # Newer values should win
        assert older.title == "Senior Developer"
        assert older.note == "New note"
        assert older.rev == datetime(2024, 6, 1)
    
    def test_merge_with_older_rev(self):
        """Test that older REV timestamp doesn't overwrite when prefer_newer=True."""
        newer = Contact(
            fn="Bob",
            uid="bob-uid",
            title="Senior Engineer",
            note="Current note",
            rev=datetime(2024, 6, 1)
        )
        
        older = Contact(
            fn="Bob",
            uid="bob-uid",
            title="Junior Engineer",
            note="Old note",
            rev=datetime(2024, 1, 1)
        )
        
        newer.merge_from(older, prefer_newer=True)
        
        # Newer values should be preserved
        assert newer.title == "Senior Engineer"
        assert newer.note == "Current note"
        assert newer.rev == datetime(2024, 6, 1)
    
    def test_merge_list_fields_unique(self):
        """Test that list fields merge with unique values only."""
        contact1 = Contact(
            fn="Charlie",
            uid="charlie-uid",
            email=["charlie@example.com", "charlie@work.com"],
            tel=["+1-555-0001"]
        )
        
        contact2 = Contact(
            fn="Charlie",
            uid="charlie-uid",
            email=["charlie@work.com", "charlie@personal.com"],
            tel=["+1-555-0002"]
        )
        
        contact1.merge_from(contact2)
        
        # Should have unique emails
        assert len(contact1.email) == 3
        assert "charlie@example.com" in contact1.email
        assert "charlie@work.com" in contact1.email
        assert "charlie@personal.com" in contact1.email
        
        # Should have both phone numbers
        assert len(contact1.tel) == 2
        assert "+1-555-0001" in contact1.tel
        assert "+1-555-0002" in contact1.tel
    
    def test_merge_categories(self):
        """Test that categories merge correctly."""
        contact1 = Contact(
            fn="Dave",
            uid="dave-uid",
            categories=["work", "friend"]
        )
        
        contact2 = Contact(
            fn="Dave",
            uid="dave-uid",
            categories=["friend", "family"]
        )
        
        contact1.merge_from(contact2)
        
        # Should have unique categories
        assert len(contact1.categories) == 3
        assert "work" in contact1.categories
        assert "friend" in contact1.categories
        assert "family" in contact1.categories
    
    def test_merge_related_unique_uris(self):
        """Test that RELATED properties merge by unique URI."""
        contact1 = Contact(
            fn="Eve",
            uid="eve-uid",
            related=[
                Related(uri="urn:uuid:person1", type=["friend"]),
                Related(uri="urn:uuid:person2", type=["colleague"])
            ]
        )
        
        contact2 = Contact(
            fn="Eve",
            uid="eve-uid",
            related=[
                Related(uri="urn:uuid:person2", type=["friend"]),  # Duplicate URI
                Related(uri="urn:uuid:person3", type=["sibling"])  # New URI
            ]
        )
        
        contact1.merge_from(contact2)
        
        # Should have 3 unique URIs (not 4)
        assert len(contact1.related) == 3
        uris = [r.uri for r in contact1.related]
        assert "urn:uuid:person1" in uris
        assert "urn:uuid:person2" in uris
        assert "urn:uuid:person3" in uris
    
    def test_merge_x_properties(self):
        """Test that x_properties merge correctly."""
        contact1 = Contact(
            fn="Frank",
            uid="frank-uid",
            x_properties={"X-CUSTOM-1": "value1", "X-CUSTOM-2": "old-value"}
        )
        
        contact2 = Contact(
            fn="Frank",
            uid="frank-uid",
            x_properties={"X-CUSTOM-2": "new-value", "X-CUSTOM-3": "value3"},
            rev=datetime(2024, 6, 1)
        )
        
        contact1.merge_from(contact2, prefer_newer=True)
        
        # Should merge all x_properties
        assert contact1.x_properties["X-CUSTOM-1"] == "value1"
        assert contact1.x_properties["X-CUSTOM-2"] == "new-value"  # Newer wins
        assert contact1.x_properties["X-CUSTOM-3"] == "value3"
    
    def test_merge_without_prefer_newer(self):
        """Test merging with prefer_newer=False keeps current values."""
        current = Contact(
            fn="Grace",
            uid="grace-uid",
            title="Director",
            note="Current note",
            rev=datetime(2024, 1, 1)
        )
        
        incoming = Contact(
            fn="Grace",
            uid="grace-uid",
            title="VP",
            note="New note",
            rev=datetime(2024, 6, 1)
        )
        
        current.merge_from(incoming, prefer_newer=False)
        
        # Current values should be preserved despite newer REV
        assert current.title == "Director"
        assert current.note == "Current note"
        # But REV should still update to latest
        assert current.rev == datetime(2024, 6, 1)
    
    def test_merge_rev_always_updates_to_latest(self):
        """Test that REV always updates to the latest timestamp."""
        contact1 = Contact(
            fn="Henry",
            uid="henry-uid",
            rev=datetime(2024, 1, 1)
        )
        
        contact2 = Contact(
            fn="Henry",
            uid="henry-uid",
            rev=datetime(2024, 6, 1)
        )
        
        contact1.merge_from(contact2)
        assert contact1.rev == datetime(2024, 6, 1)
        
        # Try the other way
        contact3 = Contact(
            fn="Henry",
            uid="henry-uid",
            rev=datetime(2024, 3, 1)
        )
        
        contact1.merge_from(contact3)
        # Should keep the latest (2024-06-01, not 2024-03-01)
        assert contact1.rev == datetime(2024, 6, 1)
    
    def test_merge_with_no_rev_timestamps(self):
        """Test merging when neither contact has REV."""
        contact1 = Contact(
            fn="Iris",
            uid="iris-uid",
            title="Analyst"
        )
        
        contact2 = Contact(
            fn="Iris",
            uid="iris-uid",
            note="Some note"
        )
        
        contact1.merge_from(contact2)
        
        # Both fields should be present
        assert contact1.title == "Analyst"
        assert contact1.note == "Some note"
        assert contact1.rev is None
    
    def test_merge_geo_field(self):
        """Test merging geographic coordinates."""
        contact1 = Contact(
            fn="Jack",
            uid="jack-uid",
            geo=(40.7128, -74.0060)  # New York
        )
        
        contact2 = Contact(
            fn="Jack",
            uid="jack-uid",
            geo=(34.0522, -118.2437),  # Los Angeles
            rev=datetime(2024, 6, 1)
        )
        
        contact1.merge_from(contact2, prefer_newer=True)
        
        # Newer geo should win
        assert contact1.geo == (34.0522, -118.2437)
    
    def test_merge_imports_new_field(self):
        """Test that new fields are imported from other contact."""
        minimal = Contact(
            fn="Karen",
            uid="karen-uid"
        )
        
        detailed = Contact(
            fn="Karen",
            uid="karen-uid",
            title="CEO",
            email=["karen@company.com"],
            tel=["+1-555-1234"],
            bday="1990-05-15",
            gender="F"
        )
        
        minimal.merge_from(detailed)
        
        # All new fields should be imported
        assert minimal.title == "CEO"
        assert minimal.email == ["karen@company.com"]
        assert minimal.tel == ["+1-555-1234"]
        assert minimal.bday == "1990-05-15"
        assert minimal.gender == "F"
