"""
Unit tests for Markdown serializer.
"""
import pytest
import tempfile
import os
from pathlib import Path

from ppl.models import Contact, Related
from ppl.serializers import markdown


class TestMarkdownSerializer:
    """Test cases for Markdown serialization."""
    
    def test_to_markdown_minimal(self):
        """Test rendering a minimal contact to Markdown."""
        contact = Contact(fn="John Doe")
        md_str = markdown.to_markdown(contact)
        
        assert "---" in md_str
        assert "FN: John Doe" in md_str
        assert "# John Doe" in md_str
    
    def test_to_markdown_with_note(self):
        """Test rendering a contact with a note."""
        contact = Contact(fn="Jane Smith", note="Software engineer")
        md_str = markdown.to_markdown(contact)
        
        assert "Software engineer" in md_str
    
    def test_to_markdown_with_related(self):
        """Test rendering a contact with relationships."""
        contact = Contact(
            fn="Alice",
            uid="alice-uid",
            related=[
                Related(uri="urn:uuid:bob-uid", type=["friend"], text_value="Bob"),
                Related(uri="urn:uuid:charlie-uid", type=["colleague"], text_value="Charlie")
            ]
        )
        md_str = markdown.to_markdown(contact)
        
        assert "## Related" in md_str
        assert "friend" in md_str
        assert "colleague" in md_str
    
    def test_render_yaml_front_matter(self):
        """Test rendering YAML front matter."""
        contact = Contact(fn="John Doe", uid="john-uid")
        front_matter = markdown.render_yaml_front_matter(contact)
        
        assert front_matter.startswith("---\n")
        assert front_matter.endswith("---")
        assert "FN: John Doe" in front_matter
        assert "UID: john-uid" in front_matter
    
    def test_parse_yaml_front_matter(self):
        """Test parsing YAML front matter."""
        md_str = """---
FN: Jane Smith
UID: jane-uid
EMAIL:
  - jane@example.com
---

# Jane Smith
"""
        front_matter = markdown.parse_yaml_front_matter(md_str)
        
        assert front_matter['FN'] == "Jane Smith"
        assert front_matter['UID'] == "jane-uid"
        assert "jane@example.com" in front_matter['EMAIL']
    
    def test_parse_yaml_front_matter_empty(self):
        """Test parsing markdown without front matter."""
        md_str = "# John Doe\n\nSome content"
        front_matter = markdown.parse_yaml_front_matter(md_str)
        
        assert front_matter == {}
    
    def test_render_related_section(self):
        """Test rendering related section."""
        related_list = [
            Related(uri="urn:uuid:bob-uid", type=["friend"], text_value="Bob"),
            Related(uri="urn:uuid:alice-uid", type=["colleague"], text_value="Alice")
        ]
        
        section = markdown.render_related_section(related_list)
        
        assert "## Related" in section
        assert "friend Bob" in section
        assert "colleague Alice" in section
    
    def test_parse_related_section(self):
        """Test parsing related section."""
        md_body = """# John Doe

## Related

- friend [[Bob]]
- colleague [[Alice]]
"""
        relationships = markdown.parse_related_section(md_body)
        
        assert len(relationships) == 2
        assert any(r['types'] == ['friend'] for r in relationships)
        assert any(r['types'] == ['colleague'] for r in relationships)
    
    def test_parse_related_section_with_uri(self):
        """Test parsing related section with URIs."""
        md_body = """# John Doe

## Related

- friend urn:uuid:bob-uid
- colleague urn:uuid:alice-uid
"""
        relationships = markdown.parse_related_section(md_body)
        
        assert len(relationships) == 2
        assert any(r['uri'] == 'urn:uuid:bob-uid' for r in relationships)
    
    def test_from_markdown_minimal(self):
        """Test parsing minimal Markdown."""
        md_str = """---
FN: John Doe
UID: john-uid
VERSION: '4.0'
---

# John Doe
"""
        contact = markdown.from_markdown(md_str)
        
        assert contact.fn == "John Doe"
        assert contact.uid == "john-uid"
    
    def test_from_markdown_with_related(self):
        """Test parsing Markdown with related section."""
        md_str = """---
FN: Alice
UID: alice-uid
VERSION: '4.0'
---

# Alice

## Related

- friend Bob
- colleague Charlie
"""
        contact = markdown.from_markdown(md_str)
        
        assert len(contact.related) == 2
        assert any('friend' in r.type for r in contact.related)
    
    def test_roundtrip(self):
        """Test that rendering and parsing are inverse operations."""
        original = Contact(
            fn="John Doe",
            uid="john-uid",
            email=["john@example.com"],
            related=[
                Related(uri="urn:uuid:bob-uid", type=["friend"], text_value="Bob")
            ]
        )
        
        # Render
        md_str = markdown.to_markdown(original)
        
        # Parse
        parsed = markdown.from_markdown(md_str)
        
        # Compare
        assert parsed.fn == original.fn
        assert parsed.uid == original.uid
        assert parsed.email == original.email
        assert len(parsed.related) >= 1
    
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
            markdown.bulk_export_markdown(contacts, tmpdir)
            
            # Verify files were created
            assert os.path.exists(os.path.join(tmpdir, "Alice.md"))
            assert os.path.exists(os.path.join(tmpdir, "Bob.md"))
            assert os.path.exists(os.path.join(tmpdir, "Charlie.md"))
            
            # Bulk import
            imported = markdown.bulk_import_markdown(tmpdir)
            
            # Verify
            assert len(imported) == 3
            assert any(c.fn == "Alice" for c in imported)
            assert any(c.fn == "Bob" for c in imported)
            assert any(c.fn == "Charlie" for c in imported)
    
    def test_resolve_wiki_link(self):
        """Test resolving wiki-style links."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a markdown file
            contact = Contact(fn="Bob Smith", uid="bob-uid")
            md_str = markdown.to_markdown(contact)
            
            file_path = os.path.join(tmpdir, "Bob Smith.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_str)
            
            # Resolve wiki link
            resolved = markdown.resolve_wiki_link("Bob Smith", tmpdir)
            
            assert resolved is not None
            assert resolved.fn == "Bob Smith"
            assert resolved.uid == "bob-uid"
    
    def test_resolve_wiki_link_not_found(self):
        """Test resolving non-existent wiki link."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolved = markdown.resolve_wiki_link("Nonexistent", tmpdir)
            assert resolved is None


class TestMarkdownHelpers:
    """Test helper functions for Markdown serialization."""
    
    def test_extract_markdown_body(self):
        """Test extracting body from markdown with front matter."""
        md_str = """---
FN: John Doe
---

# John Doe

Some content
"""
        body = markdown._extract_markdown_body(md_str)
        
        assert "---" not in body
        assert "# John Doe" in body
        assert "Some content" in body
    
    def test_parse_relationship_item_wiki_link(self):
        """Test parsing relationship item with wiki link."""
        item = "friend [[Bob Smith]]"
        rel = markdown._parse_relationship_item(item)
        
        assert rel is not None
        assert rel['types'] == ['friend']
        assert rel['text_value'] == "Bob Smith"
    
    def test_parse_relationship_item_uri(self):
        """Test parsing relationship item with URI."""
        item = "colleague urn:uuid:bob-uid"
        rel = markdown._parse_relationship_item(item)
        
        assert rel is not None
        assert rel['types'] == ['colleague']
        assert rel['uri'] == "urn:uuid:bob-uid"
    
    def test_parse_relationship_item_text(self):
        """Test parsing relationship item with plain text."""
        item = "friend Bob"
        rel = markdown._parse_relationship_item(item)
        
        assert rel is not None
        assert rel['types'] == ['friend']
        assert rel['text_value'] == "Bob"
