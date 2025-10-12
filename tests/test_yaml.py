"""
Unit tests for YAML serializer.
"""
import pytest
import yaml
from datetime import datetime

from ppl.models import Contact, Related
from ppl.serializers import yaml_serializer


class TestYAMLSerializer:
    """Test cases for YAML serialization."""
    
    def test_to_yaml_minimal(self):
        """Test serializing a minimal contact to YAML."""
        contact = Contact(fn="John Doe")
        yaml_str = yaml_serializer.to_yaml(contact)
        
        # Parse YAML to verify structure
        data = yaml.safe_load(yaml_str)
        
        assert data['FN'] == "John Doe"
        assert data['VERSION'] == "4.0"
    
    def test_to_yaml_with_uid(self):
        """Test serializing a contact with UID."""
        contact = Contact(fn="Jane Smith", uid="urn:uuid:12345")
        yaml_str = yaml_serializer.to_yaml(contact)
        
        data = yaml.safe_load(yaml_str)
        assert data['UID'] == "urn:uuid:12345"
    
    def test_to_yaml_with_email(self):
        """Test serializing a contact with emails."""
        contact = Contact(
            fn="John Doe",
            email=["john@example.com", "jdoe@work.com"]
        )
        yaml_str = yaml_serializer.to_yaml(contact)
        
        data = yaml.safe_load(yaml_str)
        assert "john@example.com" in data['EMAIL']
        assert "jdoe@work.com" in data['EMAIL']
    
    def test_to_yaml_with_related(self):
        """Test serializing a contact with RELATED properties."""
        contact = Contact(
            fn="Alice",
            uid="alice-uid",
            related=[
                Related(uri="urn:uuid:bob-uid", type=["friend", "colleague"]),
                Related(uri="urn:uuid:charlie-uid", type=["parent"])
            ]
        )
        yaml_str = yaml_serializer.to_yaml(contact)
        
        data = yaml.safe_load(yaml_str)
        assert 'RELATED' in data
        assert len(data['RELATED']) == 2
        
        # Check first relationship
        bob_rel = next(r for r in data['RELATED'] if r['uri'] == "urn:uuid:bob-uid")
        assert "friend" in bob_rel['type']
        assert "colleague" in bob_rel['type']
    
    def test_from_yaml_minimal(self):
        """Test parsing a minimal YAML."""
        yaml_str = """
FN: John Doe
VERSION: '4.0'
"""
        contact = yaml_serializer.from_yaml(yaml_str)
        
        assert contact.fn == "John Doe"
        assert contact.version == "4.0"
    
    def test_from_yaml_with_uid(self):
        """Test parsing YAML with UID."""
        yaml_str = """
FN: Jane Smith
UID: urn:uuid:12345
VERSION: '4.0'
"""
        contact = yaml_serializer.from_yaml(yaml_str)
        
        assert contact.fn == "Jane Smith"
        assert contact.uid == "urn:uuid:12345"
    
    def test_from_yaml_with_email(self):
        """Test parsing YAML with emails."""
        yaml_str = """
FN: John Doe
EMAIL:
  - john@example.com
  - jdoe@work.com
VERSION: '4.0'
"""
        contact = yaml_serializer.from_yaml(yaml_str)
        
        assert "john@example.com" in contact.email
        assert "jdoe@work.com" in contact.email
    
    def test_from_yaml_with_related(self):
        """Test parsing YAML with RELATED properties."""
        yaml_str = """
FN: Alice
UID: alice-uid
RELATED:
  - uri: urn:uuid:bob-uid
    type:
      - friend
  - uri: urn:uuid:charlie-uid
    type:
      - parent
VERSION: '4.0'
"""
        contact = yaml_serializer.from_yaml(yaml_str)
        
        assert len(contact.related) == 2
        
        bob_rel = next(r for r in contact.related if r.uri == "urn:uuid:bob-uid")
        assert "friend" in bob_rel.type
    
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
        yaml_str = yaml_serializer.to_yaml(original)
        
        # Parse
        parsed = yaml_serializer.from_yaml(yaml_str)
        
        # Compare
        assert parsed.fn == original.fn
        assert parsed.uid == original.uid
        assert parsed.email == original.email
        assert parsed.tel == original.tel
        assert parsed.title == original.title
    
    def test_to_flat_yaml(self):
        """Test serializing to flat YAML format."""
        contact = Contact(
            fn="John Doe",
            uid="urn:uuid:12345",
            email=["john@example.com", "jdoe@work.com"]
        )
        
        flat_yaml = yaml_serializer.to_flat_yaml(contact)
        
        data = yaml.safe_load(flat_yaml)
        
        # Flat YAML should use dot notation
        assert 'FN' in data
        assert 'UID' in data
        assert 'EMAIL.0' in data or 'EMAIL' in data
    
    def test_flat_yaml_roundtrip(self):
        """Test flat YAML roundtrip."""
        original = Contact(
            fn="Jane Smith",
            uid="jane-uid",
            email=["jane@example.com"]
        )
        
        # Serialize to flat YAML
        flat_yaml = yaml_serializer.to_flat_yaml(original)
        
        # Parse from flat YAML
        parsed = yaml_serializer.from_flat_yaml(flat_yaml)
        
        # Compare
        assert parsed.fn == original.fn
        assert parsed.uid == original.uid
        assert "jane@example.com" in parsed.email


class TestYAMLHelpers:
    """Test helper functions for YAML serialization."""
    
    def test_flatten_dict_simple(self):
        """Test flattening a simple dictionary."""
        d = {'a': {'b': 'c'}}
        flat = yaml_serializer._flatten_dict(d)
        
        assert 'a.b' in flat
        assert flat['a.b'] == 'c'
    
    def test_flatten_dict_with_list(self):
        """Test flattening a dictionary with list."""
        d = {'a': ['x', 'y', 'z']}
        flat = yaml_serializer._flatten_dict(d)
        
        assert 'a.0' in flat
        assert flat['a.0'] == 'x'
        assert flat['a.1'] == 'y'
        assert flat['a.2'] == 'z'
    
    def test_unflatten_dict_simple(self):
        """Test unflattening a simple dictionary."""
        flat = {'a.b': 'c'}
        d = yaml_serializer._unflatten_dict(flat)
        
        assert 'a' in d
        assert d['a']['b'] == 'c'
