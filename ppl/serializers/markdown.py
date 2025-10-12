"""
Markdown serializer for Contact objects with YAML front matter.
"""
import re
import os
import yaml
import marko
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from ..models import Contact, Related, Relationship, ContactGraph
from .yaml_serializer import _contact_to_dict, _dict_to_contact


def to_markdown(contact: Contact) -> str:
    """
    Render Contact to Markdown with YAML front matter.
    
    Args:
        contact: Contact to render
        
    Returns:
        String containing Markdown with YAML front matter
    """
    # Render YAML front matter
    front_matter = render_yaml_front_matter(contact)
    
    # Render main content
    content = f"# {contact.fn}\n\n"
    
    # Add note if present
    if contact.note:
        content += f"{contact.note}\n\n"
    
    # Render relationships
    if contact.related:
        content += render_related_section(contact.related)
    
    return f"{front_matter}\n{content}"


def from_markdown(markdown_str: str, folder_path: Optional[str] = None) -> Contact:
    """
    Parse Markdown with YAML front matter into Contact.
    
    Args:
        markdown_str: Markdown string with front matter
        folder_path: Optional folder path for resolving wiki links
        
    Returns:
        Contact object
    """
    # Parse YAML front matter
    front_matter_dict = parse_yaml_front_matter(markdown_str)
    
    # Create contact from front matter
    contact = _dict_to_contact(front_matter_dict)
    
    # Parse markdown body
    body = _extract_markdown_body(markdown_str)
    
    # Parse related section
    relationships = parse_related_section(body, folder_path)
    
    # Add relationships to contact
    for rel in relationships:
        # Create Related object from relationship
        related = Related(
            uri=rel.get('uri', ''),
            type=rel.get('types', []),
            text_value=rel.get('text_value')
        )
        contact.related.append(related)
    
    return contact


def render_yaml_front_matter(contact: Contact) -> str:
    """
    Render YAML front matter for a contact.
    
    Args:
        contact: Contact to render
        
    Returns:
        YAML front matter string with delimiters
    """
    contact_dict = _contact_to_dict(contact)
    yaml_str = yaml.dump(contact_dict, default_flow_style=False, allow_unicode=True)
    return f"---\n{yaml_str}---"


def parse_yaml_front_matter(markdown_str: str) -> Dict[str, Any]:
    """
    Parse YAML front matter from Markdown string.
    
    Args:
        markdown_str: Markdown string with front matter
        
    Returns:
        Dictionary of front matter data
    """
    # Match YAML front matter between --- delimiters
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, markdown_str, re.DOTALL)
    
    if match:
        yaml_str = match.group(1)
        return yaml.safe_load(yaml_str)
    
    return {}


def _extract_markdown_body(markdown_str: str) -> str:
    """
    Extract markdown body (without front matter).
    
    Args:
        markdown_str: Full markdown string
        
    Returns:
        Body content without front matter
    """
    # Remove YAML front matter
    pattern = r'^---\s*\n.*?\n---\s*\n'
    body = re.sub(pattern, '', markdown_str, count=1, flags=re.DOTALL)
    return body.strip()


def render_related_section(related_list: List[Related]) -> str:
    """
    Render relationships as "Related" section.
    
    Args:
        related_list: List of Related objects
        
    Returns:
        Markdown string for Related section
    """
    if not related_list:
        return ""
    
    lines = ["## Related\n"]
    
    # Sort by relationship type for consistency
    sorted_related = sorted(related_list, key=lambda r: ','.join(r.type))
    
    for rel in sorted_related:
        # Format: - relationship_type target
        types_str = ','.join(rel.type) if rel.type else 'related'
        
        # Try to extract name from URI or use text_value
        target_name = rel.text_value
        if not target_name and rel.uri:
            # Extract UID from URI
            if rel.uri.startswith('urn:uuid:'):
                uid = rel.uri[9:]
                target_name = f"[[{uid}]]"
            else:
                target_name = rel.uri
        
        lines.append(f"- {types_str} {target_name}\n")
    
    return ''.join(lines)


def parse_related_section(markdown_str: str, folder_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse "Related" section from Markdown.
    
    Args:
        markdown_str: Markdown string (body only)
        folder_path: Optional folder path for resolving wiki links
        
    Returns:
        List of relationship dictionaries
    """
    relationships = []
    
    # Parse markdown
    doc = marko.parse(markdown_str)
    
    # Find "Related" heading
    in_related_section = False
    
    for child in doc.children:
        # Check if this is the Related heading
        if hasattr(child, 'children') and child.get_type() == 'Heading':
            heading_text = _extract_text(child).strip().lower()
            if heading_text == 'related':
                in_related_section = True
                continue
            elif in_related_section:
                # Reached a different heading, stop
                break
        
        # If we're in the Related section and this is a list
        if in_related_section and child.get_type() == 'List':
            for item in child.children:
                if item.get_type() == 'ListItem':
                    # Extract text from list item
                    item_text = _extract_text(item).strip()
                    
                    # Parse relationship: "type target" or "type [[target]]"
                    rel = _parse_relationship_item(item_text, folder_path)
                    if rel:
                        relationships.append(rel)
    
    return relationships


def _extract_text(node) -> str:
    """
    Recursively extract text from a marko node.
    
    Args:
        node: Marko AST node
        
    Returns:
        Extracted text
    """
    if isinstance(node, str):
        return node
    
    if hasattr(node, 'children'):
        if isinstance(node.children, str):
            return node.children
        elif isinstance(node.children, list):
            return ''.join(_extract_text(child) for child in node.children)
    
    return ''


def _parse_relationship_item(item_text: str, folder_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Parse a relationship list item.
    
    Format: "type target" or "type [[target]]"
    
    Args:
        item_text: Text of the list item
        folder_path: Optional folder path for resolving wiki links
        
    Returns:
        Dictionary with relationship data or None
    """
    # Pattern: relationship_type [[Name]] or relationship_type URI or relationship_type text
    parts = item_text.split(None, 1)
    
    if len(parts) < 2:
        return None
    
    rel_types = parts[0].split(',')
    target = parts[1].strip()
    
    rel = {
        'types': rel_types,
        'uri': '',
        'text_value': None
    }
    
    # Check for wiki-style link [[Name]]
    wiki_match = re.search(r'\[\[(.+?)\]\]', target)
    if wiki_match:
        name = wiki_match.group(1)
        
        # Try to resolve wiki link to UID
        if folder_path:
            resolved_contact = resolve_wiki_link(name, folder_path)
            if resolved_contact and resolved_contact.uid:
                rel['uri'] = f"urn:uuid:{resolved_contact.uid}"
                rel['text_value'] = name
            else:
                # Can't resolve, use name as text
                rel['text_value'] = name
        else:
            # No folder path, use name as text
            rel['text_value'] = name
    
    # Check for URI
    elif target.startswith('urn:uuid:') or target.startswith('http'):
        rel['uri'] = target
    
    # Otherwise, it's plain text
    else:
        rel['text_value'] = target
    
    return rel


def resolve_wiki_link(link_text: str, folder_path: str) -> Optional[Contact]:
    """
    Resolve wiki-style link to a Contact.
    
    Searches for a markdown file with matching FN in the folder.
    
    Args:
        link_text: Name to search for
        folder_path: Path to folder containing markdown files
        
    Returns:
        Contact if found, None otherwise
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        return None
    
    # Try direct filename match first
    expected_filename = f"{link_text}.md"
    file_path = folder / expected_filename
    
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            return from_markdown(md_content, folder_path)
        except Exception:
            pass
    
    # Search all markdown files for matching FN
    for md_file in folder.glob('*.md'):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Parse front matter to check FN
            front_matter = parse_yaml_front_matter(md_content)
            if front_matter.get('FN') == link_text:
                return from_markdown(md_content, folder_path)
        except Exception:
            continue
    
    return None


def bulk_import_markdown(folder_path: str) -> List[Contact]:
    """
    Import all markdown files from a folder.
    
    Args:
        folder_path: Path to folder containing .md files
        
    Returns:
        List of Contact objects
    """
    contacts = []
    folder = Path(folder_path)
    
    if not folder.exists():
        return contacts
    
    for md_file in folder.glob('*.md'):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            contact = from_markdown(md_content, folder_path)
            contacts.append(contact)
        except Exception as e:
            print(f"Warning: Failed to import {md_file}: {e}")
    
    return contacts


def should_export_markdown(contact: Contact, file_path: str, folder_path: Optional[str] = None) -> bool:
    """
    Determine if markdown file should be written.
    
    Returns True if:
    - File doesn't exist
    - File exists but contact has newer REV
    - File exists but content differs (REV is same)
    
    Returns False if:
    - File exists with same or newer REV and identical content
    
    Args:
        contact: Contact to potentially export
        file_path: Path where file would be written
        folder_path: Path to folder (for resolving wiki links)
        
    Returns:
        True if file should be written, False otherwise
    """
    # If file doesn't exist, always export
    if not os.path.exists(file_path):
        return True
    
    try:
        # Load existing contact from file
        with open(file_path, 'r', encoding='utf-8') as f:
            existing_md = f.read()
        
        existing_contact = from_markdown(existing_md, folder_path or os.path.dirname(file_path))
        
        # Compare REV timestamps
        rev_comparison = contact.compare_rev(existing_contact)
        
        # If contact is newer, export
        if rev_comparison > 0:
            return True
        
        # If existing is newer, don't export
        if rev_comparison < 0:
            return False
        
        # REV is equal or both None, compare content
        new_md = to_markdown(contact)
        
        # If content is different, export
        return new_md != existing_md
    
    except Exception:
        # If we can't read the existing file, export to be safe
        return True


def bulk_export_markdown(contacts: List[Contact], folder_path: str, force: bool = False) -> Tuple[int, int]:
    """
    Export multiple contacts to markdown files.
    Only writes files when data has changed unless force=True.
    
    Args:
        contacts: List of contacts to export
        folder_path: Path to folder where .md files will be written
        force: If True, write all files regardless of changes
        
    Returns:
        Tuple of (files_written, files_skipped)
    """
    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)
    
    written = 0
    skipped = 0
    
    for contact in contacts:
        # Use FN as filename, sanitized
        filename = contact.fn.replace('/', '_').replace('\\', '_') + '.md'
        file_path = folder / filename
        
        if force or should_export_markdown(contact, str(file_path), folder_path):
            md_content = to_markdown(contact)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            written += 1
        else:
            skipped += 1
    
    return (written, skipped)
