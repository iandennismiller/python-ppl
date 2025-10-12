"""
Contact model representing a vCard 4.0 entity.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any


@dataclass
class Contact:
    """
    Data model representing a person or organization (vCard 4.0 entity).
    
    Stores all vCard 4.0 properties and maintains UID for unique identification
    and REV timestamp for version control and merge logic.
    """
    # Required Properties (vCard 4.0)
    fn: str  # Formatted name (FN) - REQUIRED
    version: str = "4.0"  # VERSION - REQUIRED
    
    # Identification Properties
    uid: Optional[str] = None  # Unique identifier (UID) - globally unique
    n: Optional[str] = None  # Structured name (N) - family;given;additional;prefixes;suffixes
    nickname: List[str] = field(default_factory=list)  # Nickname(s)
    photo: Optional[str] = None  # Photo/avatar URI
    bday: Optional[str] = None  # Birthday (ISO 8601 date)
    anniversary: Optional[str] = None  # Anniversary (ISO 8601 date)
    gender: Optional[str] = None  # Gender identity (separate from relationship rendering)
    
    # Communications Properties
    email: List[str] = field(default_factory=list)  # Email addresses
    tel: List[str] = field(default_factory=list)  # Phone numbers
    impp: List[str] = field(default_factory=list)  # Instant messaging addresses
    lang: List[str] = field(default_factory=list)  # Language preferences
    
    # Delivery Addressing Properties
    adr: List[str] = field(default_factory=list)  # Addresses (structured format)
    
    # Geographical Properties
    tz: Optional[str] = None  # Time zone
    geo: Optional[Tuple[float, float]] = None  # Geographic position (lat, long)
    
    # Organizational Properties
    title: Optional[str] = None  # Job title
    role: Optional[str] = None  # Role or occupation
    logo: Optional[str] = None  # Organization logo URI
    org: List[str] = field(default_factory=list)  # Organization (structured)
    member: List[str] = field(default_factory=list)  # Group membership (for KIND=group)
    related: List['Related'] = field(default_factory=list)  # RELATED - Social graph relationships
    
    # Explanatory Properties
    categories: List[str] = field(default_factory=list)  # Tags/categories
    note: Optional[str] = None  # Free-form notes
    prodid: Optional[str] = None  # Product ID that created vCard
    rev: Optional[datetime] = None  # Revision timestamp - CRITICAL for merge logic
    sound: Optional[str] = None  # Pronunciation URI
    clientpidmap: Dict[str, Any] = field(default_factory=dict)  # Client PID mapping
    url: List[str] = field(default_factory=list)  # URLs
    
    # Security Properties
    key: List[str] = field(default_factory=list)  # Public keys
    
    # Calendar Properties
    fburl: Optional[str] = None  # Free/busy URL
    caladruri: Optional[str] = None  # Calendar address
    caluri: Optional[str] = None  # Calendar URL
    
    # Extended Properties
    x_properties: Dict[str, Any] = field(default_factory=dict)  # Vendor-specific extensions
    
    def __post_init__(self):
        """Validate required fields."""
        if not self.fn:
            raise ValueError("FN (formatted name) is required")
    
    def compare_rev(self, other: 'Contact') -> int:
        """
        Compare revision timestamps for merge decisions.
        
        Args:
            other: Another Contact to compare with
            
        Returns:
            -1 if self is older, 0 if equal, 1 if self is newer
        """
        if self.rev is None and other.rev is None:
            return 0
        if self.rev is None:
            return -1
        if other.rev is None:
            return 1
        if self.rev < other.rev:
            return -1
        if self.rev > other.rev:
            return 1
        return 0
    
    def merge_from(self, other: 'Contact', prefer_newer: bool = True) -> 'Contact':
        """
        Merge another contact into this one without data loss.
        
        Rules:
        1. If this contact has a value and other doesn't, keep this value
        2. If other has a value and this doesn't, import other's value
        3. If both have values:
           a. If prefer_newer=True, use REV to decide (newer wins)
           b. If prefer_newer=False, keep this contact's value
        4. For list fields (email, tel, etc.), merge unique values
        
        Args:
            other: Contact to merge from
            prefer_newer: Use REV timestamps to resolve conflicts
            
        Returns:
            This contact with merged data
        """
        # Determine which contact is newer if prefer_newer is True
        other_is_newer = False
        if prefer_newer and self.compare_rev(other) < 0:
            other_is_newer = True
        
        # Define simple optional fields to merge
        simple_fields = [
            'n', 'photo', 'bday', 'anniversary', 'gender',
            'tz', 'title', 'role', 'logo', 'note', 'prodid',
            'sound', 'fburl', 'caladruri', 'caluri'
        ]
        
        # Merge simple fields
        for field_name in simple_fields:
            self_value = getattr(self, field_name)
            other_value = getattr(other, field_name)
            
            # If other has a value and self doesn't, import it
            if other_value is not None and self_value is None:
                setattr(self, field_name, other_value)
            # If both have values and other is newer (or prefer_newer is False and other has value)
            elif other_value is not None and self_value is not None:
                if other_is_newer:
                    setattr(self, field_name, other_value)
        
        # Merge geo (tuple field)
        if other.geo is not None and self.geo is None:
            self.geo = other.geo
        elif other.geo is not None and self.geo is not None and other_is_newer:
            self.geo = other.geo
        
        # Define list fields to merge
        list_fields = [
            'nickname', 'email', 'tel', 'impp', 'lang', 'adr',
            'org', 'member', 'categories', 'url', 'key'
        ]
        
        # Merge list fields by combining unique values
        for field_name in list_fields:
            self_list = getattr(self, field_name)
            other_list = getattr(other, field_name)
            
            # Merge lists, preserving unique values
            if other_list:
                for item in other_list:
                    if item not in self_list:
                        self_list.append(item)
        
        # Merge related (complex list field)
        if other.related:
            # Create a set of existing URIs for quick lookup
            existing_uris = {r.uri for r in self.related if hasattr(r, 'uri')}
            
            for other_rel in other.related:
                # Only add if URI doesn't already exist
                if hasattr(other_rel, 'uri') and other_rel.uri not in existing_uris:
                    self.related.append(other_rel)
                    existing_uris.add(other_rel.uri)
        
        # Merge x_properties (dict field)
        if other.x_properties:
            for key, value in other.x_properties.items():
                if key not in self.x_properties:
                    self.x_properties[key] = value
                elif other_is_newer:
                    self.x_properties[key] = value
        
        # Merge clientpidmap (dict field)
        if other.clientpidmap:
            for key, value in other.clientpidmap.items():
                if key not in self.clientpidmap:
                    self.clientpidmap[key] = value
                elif other_is_newer:
                    self.clientpidmap[key] = value
        
        # Always update REV to the latest timestamp
        if other.rev is not None:
            if self.rev is None or other.rev > self.rev:
                self.rev = other.rev
        
        return self


@dataclass
class Related:
    """
    Represents the vCard 4.0 RELATED property.
    Used to project the social graph onto vCard representations.
    """
    uri: str  # URI reference to related contact (typically urn:uuid:xxx)
    type: List[str] = field(default_factory=list)  # Relationship types
    text_value: Optional[str] = None  # Optional text description (alternative to URI)
    pref: Optional[int] = None  # Preference order (1-100)
    
    # Supported TYPE values (from RFC 6350):
    # Social: contact, acquaintance, friend, met
    # Professional: co-worker, colleague
    # Residential: co-resident, neighbor
    # Family: child, parent, sibling, spouse, kin
    # Romantic: muse, crush, date, sweetheart
    # Special: me, agent, emergency
