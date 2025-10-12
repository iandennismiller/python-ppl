"""
Pipeline model for orchestrating filters.
"""
import logging
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .contact import Contact
    from .filter import AbstractFilter, FilterContext


class FilterPipeline:
    """Composable pipeline of filters."""
    
    def __init__(self, name: str):
        """
        Initialize a filter pipeline.
        
        Args:
            name: Name of the pipeline
        """
        self.name = name
        self.filters: List['AbstractFilter'] = []
        self.logger = logging.getLogger(f"pipeline.{name}")
    
    def register(self, filter: 'AbstractFilter') -> None:
        """
        Register filter and maintain priority order.
        
        Args:
            filter: Filter to register
        """
        self.filters.append(filter)
        # Sort by priority (lower priority runs first)
        self.filters.sort(key=lambda f: f.priority)
        self.logger.debug(f"Registered filter: {filter.name} (priority: {filter.priority})")
    
    def run(self, contact: 'Contact', context: 'FilterContext') -> 'Contact':
        """
        Execute all applicable filters in order.
        
        Args:
            contact: Contact to process
            context: Execution context
            
        Returns:
            Processed contact
        """
        for filter in self.filters:
            if filter.should_run(context):
                try:
                    self.logger.debug(f"Running filter: {filter.name}")
                    contact = filter.execute(contact, context)
                except Exception as e:
                    filter.on_error(contact, e)
                    self.logger.error(f"{filter.name} failed: {e}")
        return contact
    
    def run_batch(self, contacts: List['Contact'], context: 'FilterContext') -> List['Contact']:
        """
        Execute pipeline on multiple contacts.
        
        Args:
            contacts: List of contacts to process
            context: Execution context
            
        Returns:
            List of processed contacts
        """
        return [self.run(contact, context) for contact in contacts]


# Standard pipeline instances
import_pipeline = FilterPipeline("import")
export_pipeline = FilterPipeline("export")
curation_pipeline = FilterPipeline("curation")
