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
**Purpose:** Data model representing a person or organization  
**Responsibilities:**
- Store contact information (name, email, phone, address, etc.)
- Maintain UID for unique identification
- Track REV timestamp for version control
- Validate contact data

**Dependencies:** vobject for vCard schema  
**Interfaces:**
- Serialize to vCard 4.0
- Serialize to YAML
- Serialize to Markdown
- Parse from various formats
- Compare timestamps (REV field)

### Component 3: Relationship Model (/ppl/models/relationship.py)
**Purpose:** Model connections between contacts  
**Responsibilities:**
- Define relationship type/kind
- Support directional relationships (source->target)
- Support bidirectional relationships
- Store gender-neutral relationship data
- Optional gender rendering when contact data available

**Dependencies:** None (pure Python)  
**Interfaces:**
- Create directional relationship
- Create bidirectional relationship
- Get relationship type
- Render with optional gender context

### Component 4: vCard Importer/Exporter (/ppl/serializers/vcard.py)
**Purpose:** Handle vCard 4.0 format import/export  
**Responsibilities:**
- Parse .VCF files to Contact objects
- Generate .VCF files from Contact objects
- Compare REV fields for merge decisions
- Ensure vCard 4.0 compliance

**Dependencies:** vobject library  
**Interfaces:**
- import_vcard(file_path) -> Contact
- export_vcard(contact, file_path)
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

### Contact
```python
class Contact:
    uid: str  # Unique identifier (UUID)
    rev: datetime  # Revision timestamp
    fn: str  # Formatted name (required)
    n: StructuredName  # Structured name
    email: List[str]  # Email addresses
    tel: List[str]  # Phone numbers
    adr: List[Address]  # Addresses
    org: str  # Organization
    title: str  # Job title
    note: str  # Notes
    # ... other vCard 4.0 fields
```

### Relationship
```python
class Relationship:
    source: Contact  # Source contact (for directional)
    target: Contact  # Target contact
    kind: str  # Relationship type (parent, friend, colleague, etc.)
    directional: bool  # True if relationship has direction
    metadata: dict  # Additional relationship data
```

### Graph Structure
- Nodes: Contact objects
- Edges: Relationship objects
- Edge attributes: kind, directional, metadata

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
