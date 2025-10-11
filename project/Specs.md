# Technical Specifications

## Architecture Overview
PPL is a Python application with a graph-based architecture for managing contacts and relationships. The system uses NetworkX for graph operations, with contacts as nodes and relationships as edges. Multiple serialization formats are supported through dedicated renderer/parser modules. A filter pipeline provides extensible data validation and curation.

## System Components

### Component 1: Contact Graph (networkx)
**Purpose:** Core data structure representing contacts and their relationships  
**Responsibilities:**
- Store Contact nodes with associated data
- Store Relationship edges between contacts
- Support graph queries and traversals
- Provide efficient access to contact network

**Dependencies:** networkx library  
**Interfaces:** 
- Add/update/remove contacts
- Add/update/remove relationships
- Query relationships for a contact
- Export graph structure

### Component 2: Contact Model (/ppl/models/contact.py)
**Purpose:** Data model representing a person or organization (vCard 4.0 entity)  
**Responsibilities:**
- Store all vCard 4.0 properties (FN, N, UID, REV, EMAIL, TEL, ADR, RELATED, etc.)
- Maintain UID for unique identification (vCard 4.0 UID property)
- Track REV timestamp for version control and merge logic (vCard 4.0 REV property)
- Manage RELATED properties to represent social graph connections
- Validate contact data against vCard 4.0 specification
- Support vCard 4.0 property taxonomy and cardinality rules

**Dependencies:** vobject for vCard 4.0 schema  
**Interfaces:**
- Serialize to vCard 4.0 (including RELATED properties)
- Serialize to YAML
- Serialize to Markdown
- Parse from various formats
- Compare timestamps (REV field) for merge decisions
- Get/set RELATED properties (social graph edges)

### Component 3: Relationship Model (/ppl/models/relationship.py)
**Purpose:** Model connections between contacts (maps to vCard 4.0 RELATED property)  
**Responsibilities:**
- Define relationship types using vCard 4.0 RELATED TYPE taxonomy
- Support directional relationships (source->target, e.g., child->parent)
- Support bidirectional relationships (e.g., friend, colleague)
- Store gender-neutral relationship data (aligned with vCard 4.0)
- Convert to/from vCard 4.0 RELATED property format
- Optional gender rendering when contact data available

**Dependencies:** None (pure Python)  
**Interfaces:**
- Create directional relationship
- Create bidirectional relationship
- Get relationship type
- Render with optional gender context

### Component 4: vCard Importer/Exporter (/ppl/serializers/vcard.py)
**Purpose:** Handle vCard 4.0 format import/export with RELATED properties  
**Responsibilities:**
- Parse .VCF files to Contact objects (including all vCard 4.0 properties)
- Extract RELATED properties to build graph relationships
- Generate .VCF files from Contact objects with RELATED properties
- Project NetworkX graph edges as vCard RELATED properties
- Compare REV fields for merge decisions (vCard 4.0 synchronization)
- Ensure full vCard 4.0 specification compliance
- Handle vCard 4.0 property taxonomy and parameters

**Dependencies:** vobject library  
**Interfaces:**
- import_vcard(file_path) -> Contact (with RELATED properties)
- export_vcard(contact, file_path) (includes RELATED from graph edges)
- extract_relationships(contact) -> List[Relationship]
- inject_relationships(contact, relationships) -> Contact
- compare_rev(contact1, contact2) -> bool
- bulk_import(folder_path) -> List[Contact]
- bulk_export(contacts, folder_path)

### Component 5: YAML Serializer (/ppl/serializers/yaml_serializer.py)
**Purpose:** Handle YAML and Flat YAML serialization  
**Responsibilities:**
- Serialize Contact to YAML
- Deserialize YAML to Contact
- Support flat YAML format (unnested keys)
- Maintain idempotent operations

**Dependencies:** pyyaml library  
**Interfaces:**
- to_yaml(contact) -> str
- from_yaml(yaml_str) -> Contact
- to_flat_yaml(contact) -> str
- from_flat_yaml(yaml_str) -> Contact

### Component 6: Markdown Renderer/Parser (/ppl/serializers/markdown.py)
**Purpose:** Handle Markdown format for contacts  
**Responsibilities:**
- Render Contact to human-readable Markdown
- Parse Markdown DOM to Contact objects
- Provide clean display format

**Dependencies:** marko-py library  
**Interfaces:**
- to_markdown(contact) -> str
- from_markdown(markdown_str) -> Contact

### Component 7: Filter Pipeline (/ppl/filters/)
**Purpose:** Extensible data validation and curation  
**Responsibilities:**
- Execute filters in defined order
- Provide hooks for various trigger points
- Log filter actions
- Handle filter failures gracefully

**Dependencies:** None (framework)  
**Interfaces:**
- register_filter(filter_func, priority)
- run_pipeline(contact) -> Contact
- trigger_on_import()
- trigger_on_demand()

### Component 8: UID Assignment Filter (/ppl/filters/uid_filter.py)
**Purpose:** Ensure all contacts have unique identifiers  
**Responsibilities:**
- Check for UID field presence
- Generate UUID when UID missing
- Log UID assignments

**Dependencies:** uuid (Python standard library)  
**Interfaces:**
- execute(contact) -> Contact

### Component 9: CLI Interface (/ppl/cli.py)
**Purpose:** Command-line interface for user interaction  
**Responsibilities:**
- Provide commands for import/export
- Provide commands for search/list
- Display help and error messages
- Orchestrate component interactions

**Dependencies:** click library  
**Interfaces:**
- import_command(folder_path)
- export_command(folder_path)
- list_command()
- search_command(query)

## Data Models

### Contact (vCard 4.0 Entity)
```python
class Contact:
    # Required Properties (vCard 4.0)
    fn: str  # Formatted name (FN) - REQUIRED
    version: str = "4.0"  # VERSION - REQUIRED
    
    # Identification Properties
    uid: str  # Unique identifier (UID) - globally unique
    n: StructuredName  # Structured name (N) - family, given, additional, prefixes, suffixes
    nickname: List[str]  # Nickname(s)
    photo: URI  # Photo/avatar
    bday: date  # Birthday
    anniversary: date  # Anniversary
    gender: str  # Gender identity (separate from relationship rendering)
    
    # Communications Properties
    email: List[Email]  # Email addresses with TYPE parameter
    tel: List[Phone]  # Phone numbers with TYPE parameter
    impp: List[str]  # Instant messaging addresses
    lang: List[str]  # Language preferences
    
    # Delivery Addressing Properties
    adr: List[Address]  # Addresses (structured: PO box, ext, street, locality, region, postal, country)
    
    # Geographical Properties
    tz: str  # Time zone
    geo: Tuple[float, float]  # Geographic position (lat, long)
    
    # Organizational Properties
    title: str  # Job title
    role: str  # Role or occupation
    logo: URI  # Organization logo
    org: List[str]  # Organization (structured: org name, units)
    member: List[str]  # Group membership (for KIND=group)
    related: List[Related]  # RELATED - Social graph relationships (cardinality: *)
    
    # Explanatory Properties
    categories: List[str]  # Tags/categories
    note: str  # Free-form notes
    prodid: str  # Product ID that created vCard
    rev: datetime  # Revision timestamp - CRITICAL for merge logic
    sound: URI  # Pronunciation
    clientpidmap: dict  # Client PID mapping for synchronization
    url: List[str]  # URLs
    
    # Security Properties
    key: List[str]  # Public keys
    
    # Calendar Properties
    fburl: str  # Free/busy URL
    caladruri: str  # Calendar address
    caluri: str  # Calendar URL
    
    # Extended Properties
    x_properties: dict  # Vendor-specific extensions
```

### Related (vCard 4.0 RELATED Property)
```python
class Related:
    """
    Represents the vCard 4.0 RELATED property.
    Used to project the social graph onto vCard representations.
    """
    uri: str  # URI reference to related contact (typically urn:uuid:xxx)
    type: List[str]  # Relationship types (comma-separated in vCard)
    # Supported TYPE values (from RFC 6350):
    # Social: contact, acquaintance, friend, met
    # Professional: co-worker, colleague
    # Residential: co-resident, neighbor
    # Family: child, parent, sibling, spouse, kin
    # Romantic: muse, crush, date, sweetheart
    # Special: me, agent, emergency
    text_value: str  # Optional text description (alternative to URI)
    pref: int  # Preference order (1-100)
```

### Relationship (Internal Graph Edge)
```python
class Relationship:
    """
    Internal representation of relationship as graph edge.
    Maps to vCard RELATED property during serialization.
    """
    source: Contact  # Source contact
    target: Contact  # Target contact
    types: List[str]  # Relationship types (from vCard RELATED TYPE taxonomy)
    directional: bool  # True if relationship implies direction (child->parent)
    metadata: dict  # Additional relationship data
    
    def to_vcard_related(self) -> Related:
        """Convert to vCard RELATED property"""
        
    @staticmethod
    def from_vcard_related(source: Contact, related: Related) -> 'Relationship':
        """Create from vCard RELATED property"""
```

### Graph Structure
- **Nodes**: Contact objects (vCard entities)
- **Edges**: Relationship objects (derived from vCard RELATED properties)
- **Edge attributes**: types (list of vCard RELATED TYPE values), directional, metadata
- **Serialization**: Graph edges stored as RELATED properties in each Contact's vCard

## API Specifications

### Internal Python API

#### Contact Graph API
```python
graph.add_contact(contact: Contact) -> None
graph.update_contact(contact: Contact) -> None
graph.get_contact(uid: str) -> Contact
graph.remove_contact(uid: str) -> None
graph.add_relationship(rel: Relationship) -> None
graph.get_relationships(uid: str) -> List[Relationship]
```

#### Importer/Exporter API
```python
# vCard
import_vcard(path: str) -> Contact
export_vcard(contact: Contact, path: str) -> None
bulk_import_vcards(folder: str) -> List[Contact]
bulk_export_vcards(contacts: List[Contact], folder: str) -> None

# YAML
to_yaml(contact: Contact) -> str
from_yaml(yaml_str: str) -> Contact
to_flat_yaml(contact: Contact) -> str

# Markdown
to_markdown(contact: Contact) -> str
from_markdown(md_str: str) -> Contact
```

#### Filter API
```python
@filter(priority=10)
def uid_filter(contact: Contact) -> Contact:
    if not contact.uid:
        contact.uid = str(uuid.uuid4())
    return contact

pipeline.register(uid_filter)
pipeline.run(contact) -> Contact
```

## Technology Stack

### Backend
- **Python 3.8+**: Primary programming language
- **networkx**: Graph data structure for contacts and relationships
- **vobject**: vCard 4.0 parsing and generation
- **pyyaml**: YAML serialization
- **marko-py**: Markdown document object model
- **click**: Command-line interface framework

### Storage
- **File system**: VCF files as primary storage
- **In-memory graph**: NetworkX graph during runtime

### Infrastructure
- **pip/pyproject.toml**: Dependency management
- **setuptools**: Build system

## Security Considerations
- Input validation for all imported data
- Path traversal protection for file operations
- Safe UUID generation for UIDs
- No network operations (local file system only)

## Performance Requirements
- Import 1000+ vCard files in reasonable time (<1 minute)
- Graph queries should be fast even with large networks (10000+ contacts)
- Idempotent operations with minimal overhead

## Testing Strategy

### Unit Tests
- Contact model serialization/deserialization
- Relationship model validation
- Filter pipeline execution
- Each serializer format

### Integration Tests
- Full import/export cycle (vCard, YAML, Markdown)
- REV-based merge logic
- Bulk operations on folders
- Filter pipeline integration

### Test Data
- Sample vCard files
- Edge cases (missing fields, invalid data)
- Large contact networks

## Deployment Process
- Package as Python wheel
- Install via pip
- CLI available after installation
- No server component needed

## Monitoring and Logging
- Filter actions logged
- Import/export operations logged
- Errors and warnings captured
- Optional verbose mode for debugging

## Open Technical Questions
- Should we support vCard versions before 4.0 (2.1, 3.0)?
- What graph serialization format for persistence beyond VCF files?
- Performance optimization strategy for very large graphs?
- Should filters be plugin-based for external extensions?
