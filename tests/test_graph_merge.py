"""
Tests for ContactGraph merge functionality.
"""
import pytest
from datetime import datetime
from ppl.models import Contact, ContactGraph


class TestGraphMerge:
    """Test ContactGraph.merge_contact() method."""
    
    def test_merge_new_contact(self):
        """Test merging a new contact adds it to the graph."""
        graph = ContactGraph()
        contact = Contact(
            fn="Alice",
            uid="alice-uid",
            email=["alice@example.com"]
        )
        
        modified, action = graph.merge_contact(contact)
        
        assert modified is True
        assert action == "added"
        assert graph.get_contact("alice-uid") is not None
        assert graph.get_contact("alice-uid").email == ["alice@example.com"]
    
    def test_merge_existing_contact_with_newer_data(self):
        """Test merging newer data into an existing contact."""
        graph = ContactGraph()
        
        # Add initial contact
        old_contact = Contact(
            fn="Bob",
            uid="bob-uid",
            title="Junior Developer",
            rev=datetime(2024, 1, 1)
        )
        graph.add_contact(old_contact)
        
        # Merge newer contact
        new_contact = Contact(
            fn="Bob",
            uid="bob-uid",
            title="Senior Developer",
            email=["bob@example.com"],
            rev=datetime(2024, 6, 1)
        )
        
        modified, action = graph.merge_contact(new_contact)
        
        assert modified is True
        assert action == "updated"
        
        # Check merged data
        merged = graph.get_contact("bob-uid")
        assert merged.title == "Senior Developer"
        assert merged.email == ["bob@example.com"]
        assert merged.rev == datetime(2024, 6, 1)
    
    def test_merge_existing_contact_with_older_data(self):
        """Test that older data is skipped when merging."""
        graph = ContactGraph()
        
        # Add newer contact
        new_contact = Contact(
            fn="Charlie",
            uid="charlie-uid",
            title="Senior Engineer",
            rev=datetime(2024, 6, 1)
        )
        graph.add_contact(new_contact)
        
        # Try to merge older contact
        old_contact = Contact(
            fn="Charlie",
            uid="charlie-uid",
            title="Junior Engineer",
            rev=datetime(2024, 1, 1)
        )
        
        modified, action = graph.merge_contact(old_contact)
        
        assert modified is False
        assert action == "skipped"
        
        # Check that data wasn't changed
        existing = graph.get_contact("charlie-uid")
        assert existing.title == "Senior Engineer"
        assert existing.rev == datetime(2024, 6, 1)
    
    def test_merge_preserves_existing_fields(self):
        """Test that merge preserves existing fields when incoming contact lacks them."""
        graph = ContactGraph()
        
        # Add contact with multiple fields
        full_contact = Contact(
            fn="Diana",
            uid="diana-uid",
            email=["diana@example.com"],
            tel=["+1-555-0001"],
            title="Manager",
            note="Important person"
        )
        graph.add_contact(full_contact)
        
        # Merge partial contact
        partial_contact = Contact(
            fn="Diana",
            uid="diana-uid",
            email=["diana@newdomain.com"]  # Only has email
        )
        
        modified, action = graph.merge_contact(partial_contact)
        
        assert modified is True
        assert action == "updated"
        
        # Check that all original fields are preserved
        merged = graph.get_contact("diana-uid")
        assert merged.tel == ["+1-555-0001"]
        assert merged.title == "Manager"
        assert merged.note == "Important person"
        # Email should be merged
        assert "diana@example.com" in merged.email
        assert "diana@newdomain.com" in merged.email
    
    def test_merge_without_uid_raises(self):
        """Test that merging a contact without UID raises an error."""
        graph = ContactGraph()
        contact = Contact(fn="Eve")
        
        with pytest.raises(ValueError, match="Contact must have a UID"):
            graph.merge_contact(contact)
    
    def test_merge_with_equal_rev(self):
        """Test merging when REV timestamps are equal."""
        graph = ContactGraph()
        
        # Add contact
        contact1 = Contact(
            fn="Frank",
            uid="frank-uid",
            title="Developer",
            rev=datetime(2024, 3, 1)
        )
        graph.add_contact(contact1)
        
        # Merge with equal REV
        contact2 = Contact(
            fn="Frank",
            uid="frank-uid",
            email=["frank@example.com"],
            rev=datetime(2024, 3, 1)
        )
        
        modified, action = graph.merge_contact(contact2)
        
        # Should update (equal REV means merge)
        assert modified is True
        assert action == "updated"
        
        merged = graph.get_contact("frank-uid")
        assert merged.title == "Developer"
        assert merged.email == ["frank@example.com"]
    
    def test_merge_with_no_rev_timestamps(self):
        """Test merging when neither contact has REV."""
        graph = ContactGraph()
        
        # Add contact without REV
        contact1 = Contact(
            fn="Grace",
            uid="grace-uid",
            title="Analyst"
        )
        graph.add_contact(contact1)
        
        # Merge another without REV
        contact2 = Contact(
            fn="Grace",
            uid="grace-uid",
            email=["grace@example.com"]
        )
        
        modified, action = graph.merge_contact(contact2)
        
        # Should update (both have no REV, so equal)
        assert modified is True
        assert action == "updated"
        
        merged = graph.get_contact("grace-uid")
        assert merged.title == "Analyst"
        assert merged.email == ["grace@example.com"]
    
    def test_merge_batch_operations(self):
        """Test merging multiple contacts in sequence."""
        graph = ContactGraph()
        
        contacts = [
            Contact(fn="Person 1", uid="uid-1", email=["p1@example.com"]),
            Contact(fn="Person 2", uid="uid-2", email=["p2@example.com"]),
            Contact(fn="Person 3", uid="uid-3", email=["p3@example.com"])
        ]
        
        added = 0
        updated = 0
        skipped = 0
        
        for contact in contacts:
            modified, action = graph.merge_contact(contact)
            if action == "added":
                added += 1
            elif action == "updated":
                updated += 1
            elif action == "skipped":
                skipped += 1
        
        assert added == 3
        assert updated == 0
        assert skipped == 0
        assert len(graph.get_all_contacts()) == 3
    
    def test_merge_updates_statistics(self):
        """Test that merge operations return correct statistics."""
        graph = ContactGraph()
        
        # Add initial contacts
        contact1 = Contact(fn="Henry", uid="henry-uid", rev=datetime(2024, 1, 1))
        contact2 = Contact(fn="Iris", uid="iris-uid", rev=datetime(2024, 2, 1))
        
        graph.add_contact(contact1)
        graph.add_contact(contact2)
        
        # Prepare batch with: 1 new, 1 update, 1 skip
        batch = [
            Contact(fn="Jack", uid="jack-uid"),  # New
            Contact(fn="Henry", uid="henry-uid", title="Updated", rev=datetime(2024, 6, 1)),  # Update
            Contact(fn="Iris", uid="iris-uid", title="Old", rev=datetime(2024, 1, 1))  # Skip (older)
        ]
        
        added = 0
        updated = 0
        skipped = 0
        
        for contact in batch:
            modified, action = graph.merge_contact(contact)
            if action == "added":
                added += 1
            elif action == "updated":
                updated += 1
            elif action == "skipped":
                skipped += 1
        
        assert added == 1
        assert updated == 1
        assert skipped == 1
