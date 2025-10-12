"""
Gender Inference Filter - Infers gender from relationship terms.
"""
import logging
from typing import Dict, Set

from ..models import AbstractFilter, FilterContext, Contact


class GenderFilter(AbstractFilter):
    """
    Filter that infers gender from relationship terms.
    
    Maps terms like mother/father/sister/brother to M/F gender.
    Only infers when term clearly indicates gender.
    
    Priority: 50 (runs after UID assignment and basic validation)
    """
    
    # Terms that clearly indicate female gender
    FEMALE_TERMS: Set[str] = {
        'mother', 'mom', 'daughter', 'sister', 'wife', 'girlfriend',
        'grandmother', 'grandma', 'aunt', 'niece'
    }
    
    # Terms that clearly indicate male gender
    MALE_TERMS: Set[str] = {
        'father', 'dad', 'son', 'brother', 'husband', 'boyfriend',
        'grandfather', 'grandpa', 'uncle', 'nephew'
    }
    
    # Neutral terms that don't indicate gender
    NEUTRAL_TERMS: Set[str] = {
        'parent', 'child', 'sibling', 'spouse', 'partner',
        'friend', 'colleague', 'contact', 'acquaintance'
    }
    
    def __init__(self):
        """Initialize gender filter."""
        self.logger = logging.getLogger(f"filter.{self.name}")
    
    @property
    def priority(self) -> int:
        """Return filter priority (lower runs first)."""
        return 50
    
    @property
    def name(self) -> str:
        """Return filter name for logging."""
        return "Gender Inference"
    
    def execute(self, contact: Contact, context: FilterContext) -> Contact:
        """
        Infer gender from relationship terms if not already set.
        
        Args:
            contact: Contact to process
            context: Execution context
            
        Returns:
            Contact with potentially inferred gender
        """
        # Skip if gender already set
        if contact.gender:
            return contact
        
        # Check related properties for gendered terms
        inferred_gender = None
        
        for related in contact.related:
            for rel_type in related.type:
                rel_type_lower = rel_type.lower()
                
                if rel_type_lower in self.FEMALE_TERMS:
                    if inferred_gender and inferred_gender != 'F':
                        self.logger.warning(
                            f"Conflicting gender signals for {contact.fn}: "
                            f"was {inferred_gender}, now F"
                        )
                    inferred_gender = 'F'
                    self.logger.info(
                        f"Inferred gender F for {contact.fn} from term: {rel_type}"
                    )
                
                elif rel_type_lower in self.MALE_TERMS:
                    if inferred_gender and inferred_gender != 'M':
                        self.logger.warning(
                            f"Conflicting gender signals for {contact.fn}: "
                            f"was {inferred_gender}, now M"
                        )
                    inferred_gender = 'M'
                    self.logger.info(
                        f"Inferred gender M for {contact.fn} from term: {rel_type}"
                    )
        
        # Set inferred gender if we found one
        if inferred_gender:
            contact.gender = inferred_gender
        
        return contact
    
    def should_run(self, context: FilterContext) -> bool:
        """
        Determine if filter should run.
        
        Only run during import or curation, not export.
        
        Args:
            context: Execution context
            
        Returns:
            True if should run
        """
        return context.pipeline_name in ('import', 'curation')
    
    def on_error(self, contact: Contact, error: Exception) -> None:
        """Log errors during gender inference."""
        self.logger.error(f"Error inferring gender for {contact.fn}: {error}")
