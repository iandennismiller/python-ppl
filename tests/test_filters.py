"""
Unit tests for filter pipeline.
"""
import pytest
from ppl.models import Contact, Related, FilterPipeline, FilterContext, AbstractFilter
from ppl.filters import UIDFilter, GenderFilter


class TestFilterPipeline:
    """Test cases for FilterPipeline class."""
    
    def test_pipeline_creation(self):
        """Test creating a filter pipeline."""
        pipeline = FilterPipeline("test")
        assert pipeline.name == "test"
        assert len(pipeline.filters) == 0
    
    def test_register_filter(self):
        """Test registering filters in a pipeline."""
        pipeline = FilterPipeline("test")
        uid_filter = UIDFilter()
        
        pipeline.register(uid_filter)
        
        assert len(pipeline.filters) == 1
        assert pipeline.filters[0] == uid_filter
    
    def test_filter_priority_ordering(self):
        """Test that filters are ordered by priority."""
        pipeline = FilterPipeline("test")
        
        # Register filters in reverse priority order
        gender_filter = GenderFilter()  # priority 50
        uid_filter = UIDFilter()  # priority 10
        
        pipeline.register(gender_filter)
        pipeline.register(uid_filter)
        
        # Should be sorted by priority (lower first)
        assert pipeline.filters[0].priority < pipeline.filters[1].priority
        assert pipeline.filters[0] == uid_filter
        assert pipeline.filters[1] == gender_filter
    
    def test_run_single_filter(self):
        """Test running a single filter."""
        pipeline = FilterPipeline("test")
        uid_filter = UIDFilter()
        pipeline.register(uid_filter)
        
        contact = Contact(fn="John Doe")
        context = FilterContext(pipeline_name="test")
        
        result = pipeline.run(contact, context)
        
        # UID should be assigned
        assert result.uid is not None
        assert result.uid.startswith("urn:uuid:")
    
    def test_run_multiple_filters(self):
        """Test running multiple filters in sequence."""
        pipeline = FilterPipeline("test")
        uid_filter = UIDFilter()
        gender_filter = GenderFilter()
        
        pipeline.register(gender_filter)
        pipeline.register(uid_filter)
        
        contact = Contact(
            fn="Jane Doe",
            related=[Related(uri="urn:uuid:123", type=["mother"])]
        )
        context = FilterContext(pipeline_name="import")
        
        result = pipeline.run(contact, context)
        
        # Both filters should have run
        assert result.uid is not None  # UID filter
        assert result.gender == 'F'  # Gender filter inferred from "mother"
    
    def test_run_batch(self):
        """Test running pipeline on multiple contacts."""
        pipeline = FilterPipeline("test")
        uid_filter = UIDFilter()
        pipeline.register(uid_filter)
        
        contacts = [
            Contact(fn="Alice"),
            Contact(fn="Bob"),
            Contact(fn="Charlie")
        ]
        context = FilterContext(pipeline_name="test")
        
        results = pipeline.run_batch(contacts, context)
        
        assert len(results) == 3
        # All should have UIDs assigned
        assert all(c.uid is not None for c in results)


class TestUIDFilter:
    """Test cases for UIDFilter."""
    
    def test_assigns_uid_when_missing(self):
        """Test that UID is assigned when missing."""
        filter = UIDFilter()
        contact = Contact(fn="John Doe")
        context = FilterContext(pipeline_name="test")
        
        result = filter.execute(contact, context)
        
        assert result.uid is not None
        assert result.uid.startswith("urn:uuid:")
    
    def test_preserves_existing_uid(self):
        """Test that existing UID is preserved."""
        filter = UIDFilter()
        existing_uid = "urn:uuid:12345"
        contact = Contact(fn="John Doe", uid=existing_uid)
        context = FilterContext(pipeline_name="test")
        
        result = filter.execute(contact, context)
        
        assert result.uid == existing_uid
    
    def test_filter_properties(self):
        """Test filter properties."""
        filter = UIDFilter()
        
        assert filter.priority == 10
        assert filter.name == "UID Assignment"
        assert filter.should_run(FilterContext(pipeline_name="test"))


class TestGenderFilter:
    """Test cases for GenderFilter."""
    
    def test_infers_female_from_mother(self):
        """Test inferring female gender from 'mother' term."""
        filter = GenderFilter()
        contact = Contact(
            fn="Jane Doe",
            related=[Related(uri="urn:uuid:123", type=["mother"])]
        )
        context = FilterContext(pipeline_name="import")
        
        result = filter.execute(contact, context)
        
        assert result.gender == 'F'
    
    def test_infers_male_from_father(self):
        """Test inferring male gender from 'father' term."""
        filter = GenderFilter()
        contact = Contact(
            fn="John Doe",
            related=[Related(uri="urn:uuid:123", type=["father"])]
        )
        context = FilterContext(pipeline_name="import")
        
        result = filter.execute(contact, context)
        
        assert result.gender == 'M'
    
    def test_preserves_existing_gender(self):
        """Test that existing gender is preserved."""
        filter = GenderFilter()
        contact = Contact(
            fn="Jane Doe",
            gender="F",
            related=[Related(uri="urn:uuid:123", type=["father"])]
        )
        context = FilterContext(pipeline_name="import")
        
        result = filter.execute(contact, context)
        
        # Should preserve original gender
        assert result.gender == 'F'
    
    def test_neutral_terms_dont_infer(self):
        """Test that neutral terms don't infer gender."""
        filter = GenderFilter()
        contact = Contact(
            fn="Alex Doe",
            related=[
                Related(uri="urn:uuid:123", type=["parent"]),
                Related(uri="urn:uuid:456", type=["friend"])
            ]
        )
        context = FilterContext(pipeline_name="import")
        
        result = filter.execute(contact, context)
        
        # Gender should not be inferred from neutral terms
        assert result.gender is None
    
    def test_should_run_import(self):
        """Test that filter runs during import."""
        filter = GenderFilter()
        context = FilterContext(pipeline_name="import")
        
        assert filter.should_run(context) is True
    
    def test_should_not_run_export(self):
        """Test that filter doesn't run during export."""
        filter = GenderFilter()
        context = FilterContext(pipeline_name="export")
        
        assert filter.should_run(context) is False
    
    def test_filter_properties(self):
        """Test filter properties."""
        filter = GenderFilter()
        
        assert filter.priority == 50
        assert filter.name == "Gender Inference"
