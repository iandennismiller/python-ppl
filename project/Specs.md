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
**Purpose:** Handle Markdown format for contacts with relationship representation and YAML front matter  
**Responsibilities:**
- Render Contact to human-readable Markdown with YAML front matter
- Parse Markdown DOM to Contact objects
- Serialize Contact using vCard 4.0 property names in YAML front matter (between `---` delimiters)
- Use proper vCard 4.0 property names: FN, UID, EMAIL, TEL, ADR, ORG, TITLE, etc.
- Render relationships as "Related" section with unordered list
- Parse "Related" heading (case-insensitive) with relationship tuples
- Support wiki-style links [[Name]] for related contacts
- Handle relationship tuples: (relationship_kind, object) where subject is implied
- Support bulk import/export from folder of .md files
- Name files by Full Name (FN): "First Last.md"
- Dereference wiki-style links using flat namespace in markdown folder
- Provide clean display format

**Dependencies:** marko-py library, pyyaml library  
**Interfaces:**
- to_markdown(contact) -> str (includes YAML front matter and "Related" section)
- from_markdown(markdown_str) -> Contact (parses front matter and "Related" section)
- parse_related_section(markdown_dom) -> List[Relationship]
- render_related_section(relationships) -> str
- parse_yaml_front_matter(markdown_str) -> dict
- render_yaml_front_matter(contact) -> str
- bulk_import_markdown(folder_path) -> List[Contact]
- bulk_export_markdown(contacts, folder_path) -> None
- resolve_wiki_link(link_text, folder_path) -> Contact

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
bulk_import_markdown(folder: str) -> List[Contact]
bulk_export_markdown(contacts: List[Contact], folder: str) -> None

# Markdown Relationship Format
parse_related_section(markdown_dom: MarkoNode) -> List[Relationship]
render_related_section(contact: Contact, relationships: List[Relationship]) -> str
parse_yaml_front_matter(markdown_str: str) -> dict
render_yaml_front_matter(contact: Contact) -> str
resolve_wiki_link(link_text: str, folder_path: str) -> Contact
```

### Markdown File Format Specification

#### Complete File Structure
Markdown files contain both YAML front matter and Markdown content:

```markdown
---
# YAML Front Matter (vCard 4.0 properties in YAML format)
FN: First Last
UID: urn:uuid:12345678-1234-1234-1234-123456789abc
EMAIL: first.last@example.com
TEL: +1-555-0100
RELATED;TYPE=parent: urn:uuid:abcd1234-5678-90ab-cdef-0123456789ab
RELATED;TYPE=friend: urn:uuid:bcde2345-6789-01bc-def0-123456789abc
---

# First Last

Email: first.last@example.com
Phone: +1-555-0100

## Related

- parent [[Mary Last]]
- friend [[Bob Johnson]]
```

#### YAML Front Matter
- **Delimiters**: Front matter enclosed between `---` markers
- **Format**: vCard 4.0 properties as YAML keys (FN, UID, EMAIL, TEL, ADR, RELATED, etc.)
- **Content**: All vCard 4.0 properties from Contact object
- **Property Names**: Must match vCard 4.0 specification exactly (uppercase preferred)
- **Complex Properties**: Serialized as vCard-compliant strings (e.g., ADR: `;;street;locality;region;postal;country`)
- **RELATED Properties**: Include TYPE parameter (e.g., `RELATED;TYPE=parent: urn:uuid:...`)
- **Multiple RELATED**: Each relationship listed as separate RELATED property
- **Purpose**: Machine-readable representation for easy parsing

#### Markdown Content
- **Heading**: Contact's Full Name (FN)
- **Body**: Human-readable contact information
- **Related Section**: Relationship list (see Markdown Relationship Format Specification)

#### File Naming Convention
- **Pattern**: `{Full Name}.md`
- **Example**: Contact with FN="First Last" → File: `First Last.md`
- **Namespace**: Flat namespace within markdown folder
- **UID vs FN**: VCF files use UID for naming, Markdown files use FN

#### Folder Operations

**Bulk Import from Markdown Folder:**
```python
contacts = bulk_import_markdown("/path/to/markdown/folder")
# Iterates *.md files
# Parses YAML front matter to extract Contact properties
# Parses markdown content including Related section
# Resolves wiki-style links within folder namespace
```

**Bulk Export to Markdown Folder:**
```python
bulk_export_markdown(contacts, "/path/to/output/folder")
# Creates one .md file per contact
# Names files: "{contact.fn}.md"
# Serializes Contact as Flat YAML in front matter
# Renders markdown content with Related section
```

#### Wiki-style Link Resolution
- **Format**: `[[Contact Name]]`
- **Dereferencing**: Looks up `Contact Name.md` in the same folder
- **Namespace**: Flat namespace based on FN field
- **Example**: `[[First Last]]` → resolves to `First Last.md` → Contact with FN="First Last"

### Markdown Relationship Format Specification

#### Structure
Relationships are represented in Markdown using a specific DOM structure:
- **Heading**: "Related" (case-insensitive: "related", "RELATED", "Related", etc.)
- **Content**: Unordered list beneath the heading
- **List Items**: Each item is a relationship tuple

#### Relationship Tuple Format
```
- relationship_kind object
```

Where:
- `relationship_kind`: One of the vCard 4.0 RELATED TYPE values (parent, friend, colleague, etc.)
- `object`: The related contact, which can be:
  - Wiki-style link: `[[Firstname Lastname]]`
  - URL: `http://example.com/contact`
  - Plain text: `John Doe`

#### Implied Subject
The subject of all relationships in a "Related" section is the current contact. Therefore:
- Graph triple: `(subject, relationship_kind, object)`
- Markdown tuple: `(relationship_kind, object)` - subject is implied

#### Examples

**Markdown Representation:**
```markdown
# John Smith

Email: john@example.com

## Related

- parent [[Mary Smith]]
- sibling [[Jane Smith]]
- friend [[Bob Johnson]]
- colleague https://example.com/contacts/alice.vcf
```

**Interpretation:**
- John Smith is the child of Mary Smith (directional: child->parent)
- John Smith is the sibling of Jane Smith
- John Smith is a friend of Bob Johnson
- John Smith is a colleague of Alice (referenced by URL)

#### Directional Relationships
For directional relationships, the relationship type indicates the direction:
- `- parent [[Mary]]` means "current contact's parent is Mary" (current contact is child)
- `- child [[Tom]]` means "current contact's child is Tom" (current contact is parent)

#### Multiple Relationship Types
Multiple relationships to the same contact can be listed separately:
```markdown
## Related

- friend [[Bob]]
- colleague [[Bob]]
```

#### Parsing Rules
1. Find heading with text "Related" (case-insensitive)
2. Extract unordered list immediately following heading
3. Parse each list item as `relationship_kind object`
4. Resolve object references:
   - Wiki links `[[Name]]` -> lookup by name in graph
   - URLs -> resolve to UID or external reference
   - Plain text -> attempt fuzzy match in graph
5. Create Relationship with current contact as subject

#### Rendering Rules
1. Create "## Related" heading (level 2)
2. For each relationship where current contact is subject:
   - Format as `- relationship_kind [[object_name]]`
   - Prefer wiki-style links for internal contacts
   - Use URLs for external references
3. Sort by relationship_kind for consistency
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
