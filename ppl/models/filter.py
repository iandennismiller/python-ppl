"""
Filter model for data curation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .contact import Contact
    from .graph import ContactGraph


@dataclass
class FilterContext:
    """Context passed to filters during execution."""
    pipeline_name: str
    folder_path: Optional[str] = None
    graph: Optional['ContactGraph'] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AbstractFilter(ABC):
    """Base class for all curation filters."""
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """
        Execution priority (lower = earlier).
        
        Returns:
            Integer priority value
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Filter name for logging.
        
        Returns:
            Filter name string
        """
        pass
    
    @abstractmethod
    def execute(self, contact: 'Contact', context: FilterContext) -> 'Contact':
        """
        Execute filter logic, return modified contact.
        
        Args:
            contact: Contact to process
            context: Execution context
            
        Returns:
            Modified contact
        """
        pass
    
    def should_run(self, context: FilterContext) -> bool:
        """
        Determine if filter should run in context (default: True).
        
        Args:
            context: Execution context
            
        Returns:
            True if filter should run, False otherwise
        """
        return True
    
    def on_error(self, contact: 'Contact', error: Exception) -> None:
        """
        Handle filter execution errors.
        
        Args:
            contact: Contact that caused the error
            error: Exception that was raised
        """
        pass
