"""
Relationship model for connections between contacts.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .contact import Contact, Related


@dataclass
class Relationship:
    """
    Internal representation of relationship as graph edge.
    Maps to vCard RELATED property during serialization.
    """
    source: 'Contact'  # Source contact
    target: 'Contact'  # Target contact
    types: List[str] = field(default_factory=list)  # Relationship types from vCard RELATED TYPE taxonomy
    directional: bool = True  # True if relationship implies direction (child->parent)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional relationship data
    
    def to_vcard_related(self) -> 'Related':
        """
        Convert to vCard RELATED property.
        
        Returns:
            Related object representing this relationship
        """
        from .contact import Related
        
        # Use target's UID as the URI reference
        uri = f"urn:uuid:{self.target.uid}" if self.target.uid else ""
        return Related(
            uri=uri,
            type=self.types.copy(),
            text_value=self.target.fn if not self.target.uid else None
        )
    
    @staticmethod
    def from_vcard_related(source: 'Contact', related: 'Related', target: 'Contact' = None) -> 'Relationship':
        """
        Create from vCard RELATED property.
        
        Args:
            source: Source contact (the contact that has the RELATED property)
            related: Related property from vCard
            target: Optional target contact (if already resolved)
            
        Returns:
            Relationship object
        """
        # Determine if relationship is directional based on types
        directional_types = {'child', 'parent', 'sibling', 'spouse', 'muse', 'crush', 'date', 'sweetheart'}
        is_directional = any(t in directional_types for t in related.type)
        
        return Relationship(
            source=source,
            target=target,  # May be None if not yet resolved
            types=related.type.copy(),
            directional=is_directional
        )
