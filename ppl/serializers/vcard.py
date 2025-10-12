"""
vCard serializer for importing and exporting Contact objects.
"""
import os
import vobject
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from ..models import Contact, Related, Relationship, ContactGraph


def to_vcard(contact: Contact) -> str:
    """
    Serialize a Contact to vCard 4.0 format.
    
    Args:
        contact: Contact object to serialize
        
    Returns:
        String containing vCard 4.0 representation
    """
    vcard = vobject.vCard()
    
    # Required: VERSION
    vcard.add('version')
    vcard.version.value = '4.0'
    
    # Required: FN (Formatted Name)
    vcard.add('fn')
    vcard.fn.value = contact.fn
    
    # UID (highly recommended)
    if contact.uid:
        vcard.add('uid')
        vcard.uid.value = contact.uid
    
    # N (Structured Name)
    if contact.n:
        vcard.add('n')
        vcard.n.value = contact.n
    
    # REV (Revision timestamp)
    if contact.rev:
        vcard.add('rev')
        vcard.rev.value = contact.rev.isoformat()
    
    # Email addresses
    for email in contact.email:
        email_item = vcard.add('email')
        email_item.value = email
    
    # Phone numbers
    for tel in contact.tel:
        tel_item = vcard.add('tel')
        tel_item.value = tel
    
    # Addresses
    for adr in contact.adr:
        adr_item = vcard.add('adr')
        adr_item.value = adr
    
    # Organization
    for org in contact.org:
        org_item = vcard.add('org')
        org_item.value = org
    
    # Title
    if contact.title:
        vcard.add('title')
        vcard.title.value = contact.title
    
    # Role
    if contact.role:
        vcard.add('role')
        vcard.role.value = contact.role
    
    # Note
    if contact.note:
        vcard.add('note')
        vcard.note.value = contact.note
    
    # Categories
    for category in contact.categories:
        cat_item = vcard.add('categories')
        cat_item.value = category
    
    # URLs
    for url in contact.url:
        url_item = vcard.add('url')
        url_item.value = url
    
    # Nickname
    for nickname in contact.nickname:
        nick_item = vcard.add('nickname')
        nick_item.value = nickname
    
    # Birthday
    if contact.bday:
        vcard.add('bday')
        vcard.bday.value = contact.bday
    
    # Anniversary
    if contact.anniversary:
        vcard.add('anniversary')
        vcard.anniversary.value = contact.anniversary
    
    # Gender
    if contact.gender:
        vcard.add('gender')
        vcard.gender.value = contact.gender
    
    # Photo
    if contact.photo:
        vcard.add('photo')
        vcard.photo.value = contact.photo
    
    # Time zone
    if contact.tz:
        vcard.add('tz')
        vcard.tz.value = contact.tz
    
    # Geographic position
    if contact.geo:
        vcard.add('geo')
        vcard.geo.value = f"geo:{contact.geo[0]},{contact.geo[1]}"
    
    # Related contacts
    for related in contact.related:
        rel = vcard.add('related')
        rel.value = related.uri
        if related.type:
            rel.type_param = ','.join(related.type)
        if related.pref:
            rel.pref_param = str(related.pref)
    
    return vcard.serialize()


def from_vcard(vcard_str: str) -> Contact:
    """
    Parse a vCard 4.0 string into a Contact object.
    
    Args:
        vcard_str: String containing vCard data
        
    Returns:
        Contact object
    """
    vcard = vobject.readOne(vcard_str)
    
    # Extract FN (required)
    fn = vcard.fn.value if hasattr(vcard, 'fn') else ""
    
    # Create contact with basic fields
    contact = Contact(fn=fn)
    
    # UID
    if hasattr(vcard, 'uid'):
        contact.uid = vcard.uid.value
    
    # N (Structured Name)
    if hasattr(vcard, 'n'):
        # Handle both string and Name object
        n_value = vcard.n.value
        if isinstance(n_value, str):
            contact.n = n_value
        else:
            # It's a vobject Name object, serialize it
            contact.n = str(n_value)
    
    # REV
    if hasattr(vcard, 'rev'):
        rev_value = vcard.rev.value
        if isinstance(rev_value, str):
            try:
                contact.rev = datetime.fromisoformat(rev_value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        elif isinstance(rev_value, datetime):
            contact.rev = rev_value
    
    # Email addresses
    if hasattr(vcard, 'email_list'):
        contact.email = [email.value for email in vcard.email_list]
    elif hasattr(vcard, 'email'):
        contact.email = [vcard.email.value]
    
    # Phone numbers
    if hasattr(vcard, 'tel_list'):
        contact.tel = [tel.value for tel in vcard.tel_list]
    elif hasattr(vcard, 'tel'):
        contact.tel = [vcard.tel.value]
    
    # Addresses
    if hasattr(vcard, 'adr_list'):
        contact.adr = [str(adr.value) for adr in vcard.adr_list]
    elif hasattr(vcard, 'adr'):
        contact.adr = [str(vcard.adr.value)]
    
    # Organization
    if hasattr(vcard, 'org_list'):
        contact.org = [str(org.value) for org in vcard.org_list]
    elif hasattr(vcard, 'org'):
        contact.org = [str(vcard.org.value)]
    
    # Title
    if hasattr(vcard, 'title'):
        contact.title = vcard.title.value
    
    # Role
    if hasattr(vcard, 'role'):
        contact.role = vcard.role.value
    
    # Note
    if hasattr(vcard, 'note'):
        contact.note = vcard.note.value
    
    # Categories
    if hasattr(vcard, 'categories_list'):
        contact.categories = [cat.value for cat in vcard.categories_list]
    elif hasattr(vcard, 'categories'):
        contact.categories = [vcard.categories.value]
    
    # URLs
    if hasattr(vcard, 'url_list'):
        contact.url = [url.value for url in vcard.url_list]
    elif hasattr(vcard, 'url'):
        contact.url = [vcard.url.value]
    
    # Nickname
    if hasattr(vcard, 'nickname_list'):
        contact.nickname = [nick.value for nick in vcard.nickname_list]
    elif hasattr(vcard, 'nickname'):
        contact.nickname = [vcard.nickname.value]
    
    # Birthday
    if hasattr(vcard, 'bday'):
        contact.bday = str(vcard.bday.value)
    
    # Anniversary
    if hasattr(vcard, 'anniversary'):
        contact.anniversary = str(vcard.anniversary.value)
    
    # Gender
    if hasattr(vcard, 'gender'):
        contact.gender = vcard.gender.value
    
    # Photo
    if hasattr(vcard, 'photo'):
        contact.photo = vcard.photo.value
    
    # Time zone
    if hasattr(vcard, 'tz'):
        contact.tz = vcard.tz.value
    
    # Geographic position
    if hasattr(vcard, 'geo'):
        geo_value = vcard.geo.value
        if isinstance(geo_value, str) and geo_value.startswith('geo:'):
            parts = geo_value[4:].split(',')
            if len(parts) == 2:
                try:
                    contact.geo = (float(parts[0]), float(parts[1]))
                except ValueError:
                    pass
    
    # Related contacts
    if hasattr(vcard, 'related_list'):
        for rel in vcard.related_list:
            related = Related(uri=rel.value)
            if hasattr(rel, 'type_param'):
                type_value = rel.type_param
                if isinstance(type_value, str):
                    related.type = [t.strip() for t in type_value.split(',')]
                elif isinstance(type_value, list):
                    related.type = type_value
            if hasattr(rel, 'pref_param'):
                try:
                    related.pref = int(rel.pref_param)
                except (ValueError, TypeError):
                    pass
            contact.related.append(related)
    elif hasattr(vcard, 'related'):
        related = Related(uri=vcard.related.value)
        if hasattr(vcard.related, 'type_param'):
            type_value = vcard.related.type_param
            if isinstance(type_value, str):
                related.type = [t.strip() for t in type_value.split(',')]
            elif isinstance(type_value, list):
                related.type = type_value
        if hasattr(vcard.related, 'pref_param'):
            try:
                related.pref = int(vcard.related.pref_param)
            except (ValueError, TypeError):
                pass
        contact.related.append(related)
    
    return contact


def import_vcard(file_path: str) -> Contact:
    """
    Import a contact from a vCard file.
    
    Args:
        file_path: Path to the .vcf file
        
    Returns:
        Contact object
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        vcard_str = f.read()
    
    return from_vcard(vcard_str)


def export_vcard(contact: Contact, file_path: str) -> None:
    """
    Export a contact to a vCard file.
    
    Args:
        contact: Contact to export
        file_path: Path where the .vcf file will be written
    """
    vcard_str = to_vcard(contact)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(vcard_str)


def bulk_import(folder_path: str) -> List[Contact]:
    """
    Import all vCard files from a folder.
    
    Args:
        folder_path: Path to folder containing .vcf files
        
    Returns:
        List of Contact objects
    """
    contacts = []
    folder = Path(folder_path)
    
    if not folder.exists():
        return contacts
    
    for vcf_file in folder.glob('*.vcf'):
        try:
            contact = import_vcard(str(vcf_file))
            contacts.append(contact)
        except Exception as e:
            print(f"Warning: Failed to import {vcf_file}: {e}")
    
    return contacts


def bulk_export(contacts: List[Contact], folder_path: str) -> None:
    """
    Export multiple contacts to vCard files in a folder.
    
    Args:
        contacts: List of contacts to export
        folder_path: Path to folder where .vcf files will be written
    """
    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)
    
    for contact in contacts:
        # Use FN as filename, sanitized
        filename = contact.fn.replace('/', '_').replace('\\', '_') + '.vcf'
        file_path = folder / filename
        
        export_vcard(contact, str(file_path))


def extract_relationships(contact: Contact) -> List[Relationship]:
    """
    Extract relationships from a contact's RELATED properties.
    
    Args:
        contact: Contact with RELATED properties
        
    Returns:
        List of Relationship objects (targets may be None if not resolved)
    """
    relationships = []
    
    for related in contact.related:
        rel = Relationship.from_vcard_related(contact, related)
        relationships.append(rel)
    
    return relationships


def inject_relationships(contact: Contact, relationships: List[Relationship]) -> Contact:
    """
    Inject relationships into a contact's RELATED properties.
    
    Args:
        contact: Contact to inject relationships into
        relationships: List of relationships where this contact is the source
        
    Returns:
        Updated contact with RELATED properties
    """
    contact.related = []
    
    for rel in relationships:
        if rel.source == contact or (rel.source and rel.source.uid == contact.uid):
            related = rel.to_vcard_related()
            contact.related.append(related)
    
    return contact


def compare_rev(contact1: Contact, contact2: Contact) -> bool:
    """
    Compare REV fields for merge decisions.
    
    Args:
        contact1: First contact
        contact2: Second contact
        
    Returns:
        True if contact1 is newer or equal, False otherwise
    """
    return contact1.compare_rev(contact2) >= 0
