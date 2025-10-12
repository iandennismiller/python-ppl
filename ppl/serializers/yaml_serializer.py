"""
YAML serializer for Contact objects.
"""
import yaml
from datetime import datetime
from typing import Dict, Any

from ..models import Contact, Related


def to_yaml(contact: Contact) -> str:
    """
    Serialize a Contact to YAML format.
    
    Args:
        contact: Contact object to serialize
        
    Returns:
        String containing YAML representation
    """
    data = _contact_to_dict(contact)
    return yaml.dump(data, default_flow_style=False, allow_unicode=True)


def from_yaml(yaml_str: str) -> Contact:
    """
    Parse a YAML string into a Contact object.
    
    Args:
        yaml_str: String containing YAML data
        
    Returns:
        Contact object
    """
    data = yaml.safe_load(yaml_str)
    return _dict_to_contact(data)


def to_flat_yaml(contact: Contact) -> str:
    """
    Serialize a Contact to flat YAML format (unnested keys).
    
    Flat YAML uses dot notation for nested properties.
    Example: contact.email.0 instead of nested structure.
    
    Args:
        contact: Contact object to serialize
        
    Returns:
        String containing flat YAML representation
    """
    flat_data = _flatten_dict(_contact_to_dict(contact))
    return yaml.dump(flat_data, default_flow_style=False, allow_unicode=True)


def from_flat_yaml(yaml_str: str) -> Contact:
    """
    Parse a flat YAML string into a Contact object.
    
    Args:
        yaml_str: String containing flat YAML data
        
    Returns:
        Contact object
    """
    flat_data = yaml.safe_load(yaml_str)
    data = _unflatten_dict(flat_data)
    return _dict_to_contact(data)


def _contact_to_dict(contact: Contact) -> Dict[str, Any]:
    """
    Convert Contact to dictionary for YAML serialization.
    
    Args:
        contact: Contact to convert
        
    Returns:
        Dictionary representation
    """
    data = {
        'FN': contact.fn,
        'VERSION': contact.version,
    }
    
    # Add optional fields if present
    if contact.uid:
        data['UID'] = contact.uid
    
    if contact.n:
        data['N'] = contact.n
    
    if contact.rev:
        data['REV'] = contact.rev.isoformat()
    
    if contact.email:
        data['EMAIL'] = contact.email
    
    if contact.tel:
        data['TEL'] = contact.tel
    
    if contact.adr:
        data['ADR'] = contact.adr
    
    if contact.org:
        data['ORG'] = contact.org
    
    if contact.title:
        data['TITLE'] = contact.title
    
    if contact.role:
        data['ROLE'] = contact.role
    
    if contact.note:
        data['NOTE'] = contact.note
    
    if contact.categories:
        data['CATEGORIES'] = contact.categories
    
    if contact.url:
        data['URL'] = contact.url
    
    if contact.nickname:
        data['NICKNAME'] = contact.nickname
    
    if contact.bday:
        data['BDAY'] = contact.bday
    
    if contact.anniversary:
        data['ANNIVERSARY'] = contact.anniversary
    
    if contact.gender:
        data['GENDER'] = contact.gender
    
    if contact.photo:
        data['PHOTO'] = contact.photo
    
    if contact.tz:
        data['TZ'] = contact.tz
    
    if contact.geo:
        data['GEO'] = f"{contact.geo[0]},{contact.geo[1]}"
    
    if contact.related:
        data['RELATED'] = []
        for rel in contact.related:
            rel_data = {'uri': rel.uri}
            if rel.type:
                rel_data['type'] = rel.type
            if rel.text_value:
                rel_data['text_value'] = rel.text_value
            if rel.pref:
                rel_data['pref'] = rel.pref
            data['RELATED'].append(rel_data)
    
    return data


def _dict_to_contact(data: Dict[str, Any]) -> Contact:
    """
    Convert dictionary to Contact object.
    
    Args:
        data: Dictionary representation
        
    Returns:
        Contact object
    """
    # Extract required fields
    fn = data.get('FN', '')
    
    # Create contact
    contact = Contact(fn=fn)
    
    # Set version if present
    if 'VERSION' in data:
        contact.version = data['VERSION']
    
    # Set optional fields
    if 'UID' in data:
        contact.uid = data['UID']
    
    if 'N' in data:
        contact.n = data['N']
    
    if 'REV' in data:
        rev_value = data['REV']
        if isinstance(rev_value, str):
            try:
                contact.rev = datetime.fromisoformat(rev_value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        elif isinstance(rev_value, datetime):
            contact.rev = rev_value
    
    if 'EMAIL' in data:
        contact.email = data['EMAIL'] if isinstance(data['EMAIL'], list) else [data['EMAIL']]
    
    if 'TEL' in data:
        contact.tel = data['TEL'] if isinstance(data['TEL'], list) else [data['TEL']]
    
    if 'ADR' in data:
        contact.adr = data['ADR'] if isinstance(data['ADR'], list) else [data['ADR']]
    
    if 'ORG' in data:
        contact.org = data['ORG'] if isinstance(data['ORG'], list) else [data['ORG']]
    
    if 'TITLE' in data:
        contact.title = data['TITLE']
    
    if 'ROLE' in data:
        contact.role = data['ROLE']
    
    if 'NOTE' in data:
        contact.note = data['NOTE']
    
    if 'CATEGORIES' in data:
        contact.categories = data['CATEGORIES'] if isinstance(data['CATEGORIES'], list) else [data['CATEGORIES']]
    
    if 'URL' in data:
        contact.url = data['URL'] if isinstance(data['URL'], list) else [data['URL']]
    
    if 'NICKNAME' in data:
        contact.nickname = data['NICKNAME'] if isinstance(data['NICKNAME'], list) else [data['NICKNAME']]
    
    if 'BDAY' in data:
        contact.bday = data['BDAY']
    
    if 'ANNIVERSARY' in data:
        contact.anniversary = data['ANNIVERSARY']
    
    if 'GENDER' in data:
        contact.gender = data['GENDER']
    
    if 'PHOTO' in data:
        contact.photo = data['PHOTO']
    
    if 'TZ' in data:
        contact.tz = data['TZ']
    
    if 'GEO' in data:
        geo_value = data['GEO']
        if isinstance(geo_value, str):
            parts = geo_value.split(',')
            if len(parts) == 2:
                try:
                    contact.geo = (float(parts[0]), float(parts[1]))
                except ValueError:
                    pass
    
    if 'RELATED' in data:
        for rel_data in data['RELATED']:
            if isinstance(rel_data, dict):
                related = Related(
                    uri=rel_data.get('uri', ''),
                    type=rel_data.get('type', []),
                    text_value=rel_data.get('text_value'),
                    pref=rel_data.get('pref')
                )
                contact.related.append(related)
    
    return contact


def _flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten a nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(_flatten_dict(item, f"{new_key}.{i}", sep=sep).items())
                else:
                    items.append((f"{new_key}.{i}", item))
        else:
            items.append((new_key, v))
    return dict(items)


def _unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """
    Unflatten a flattened dictionary.
    
    Args:
        d: Flattened dictionary
        sep: Separator used for nested keys
        
    Returns:
        Nested dictionary
    """
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        current = result
        for i, part in enumerate(parts[:-1]):
            # Check if this part is a list index
            if part.isdigit() or (i > 0 and parts[i-1].isdigit()):
                # Handle list creation
                if not isinstance(current, list):
                    parent_key = parts[i-1] if i > 0 else ''
                    if parent_key and parent_key not in result:
                        result[parent_key] = []
                    current = result.get(parent_key, [])
                continue
            
            if part not in current:
                # Look ahead to see if next part is a digit (indicating a list)
                if i + 1 < len(parts) and parts[i + 1].isdigit():
                    current[part] = []
                else:
                    current[part] = {}
            current = current[part]
        
        # Set the final value
        final_key = parts[-1]
        if final_key.isdigit():
            # This is a list item
            idx = int(final_key)
            parent_parts = parts[:-1]
            parent = result
            for p in parent_parts:
                if p in parent:
                    parent = parent[p]
            if isinstance(parent, list):
                # Extend list if needed
                while len(parent) <= idx:
                    parent.append(None)
                parent[idx] = value
        else:
            current[final_key] = value
    
    return result
