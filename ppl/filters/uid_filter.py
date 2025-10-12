"""
UID Assignment Filter - Ensures all contacts have unique identifiers.
"""
import uuid
import logging

from ..models import AbstractFilter, FilterContext, Contact


class UIDFilter(AbstractFilter):
    """
    Filter that assigns UUIDs to contacts that don't have one.
    
    Priority: 10 (runs early in the pipeline)
    """
    
    def __init__(self):
        """Initialize UID filter."""
        self.logger = logging.getLogger(f"filter.{self.name}")
    
    @property
    def priority(self) -> int:
        """Return filter priority (lower runs first)."""
        return 10
    
    @property
    def name(self) -> str:
        """Return filter name for logging."""
        return "UID Assignment"
    
    def execute(self, contact: Contact, context: FilterContext) -> Contact:
        """
        Assign UID if contact doesn't have one.
        
        Args:
            contact: Contact to process
            context: Execution context
            
        Returns:
            Contact with UID assigned
        """
        if not contact.uid:
            new_uid = f"urn:uuid:{uuid.uuid4()}"
            contact.uid = new_uid
            self.logger.info(f"Assigned UID to {contact.fn}: {new_uid}")
        
        return contact
    
    def on_error(self, contact: Contact, error: Exception) -> None:
        """Log errors during UID assignment."""
        self.logger.error(f"Error assigning UID to {contact.fn}: {error}")
