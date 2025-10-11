# Architecture Design

## System Overview
PPL uses a graph-based architecture where contacts (vCard 4.0 entities) are nodes and relationships are edges in a NetworkX graph. The graph serves as the single source of truth, with the vCard 4.0 RELATED property used to project the social graph onto vCard representations. Multiple serialization formats (vCard, YAML, Markdown) act as different views of the same data. The system emphasizes idempotent operations and timestamp-based conflict resolution (via REV field) for reliable data synchronization.

## Design Principles

1. **Graph as Source of Truth**: The NetworkX graph is the authoritative data store during runtime
2. **vCard 4.0 Standards Compliance**: Full vCard 4.0 compliance including RELATED property for social graph projection
3. **RELATED Property for Relationships**: Use vCard 4.0 RELATED property with TYPE parameter to represent graph edges
4. **vCard Taxonomy Adherence**: Use standard vCard 4.0 relationship types (contact, friend, parent, colleague, etc.)
5. **Idempotent Operations**: All import/export operations can be safely repeated
6. **Timestamp-based Merging**: Use vCard 4.0 REV field to intelligently merge data
7. **UID-based Identification**: Use vCard 4.0 UID property for unique contact identification
8. **Separation of Concerns**: Clear boundaries between models, serializers, and filters
9. **Leverage Existing Libraries**: Minimize custom code by using well-tested libraries (vobject, networkx)
10. **Extensible Architecture**: Filter pipeline and serializer pattern support future expansion
11. **Gender Neutrality**: Relationships use vCard 4.0 taxonomy which is gender-neutral with optional gender rendering

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│                      (click framework)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Import     │  │   Export     │  │   Filter     │      │
│  │  Orchestrator│  │ Orchestrator │  │   Pipeline   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         NetworkX Graph (Source of Truth)             │   │
│  │  Nodes: Contact Objects  │  Edges: Relationships     │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Serialization Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    vCard     │  │     YAML     │  │   Markdown   │      │
│  │  Serializer  │  │  Serializer  │  │  Serializer  │      │
│  │  (vobject)   │  │  (pyyaml)    │  │  (marko-py)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   File System Layer                          │
│              (*.vcf, *.yaml, *.md files)                     │
└─────────────────────────────────────────────────────────────┘
```

## Sequence Diagrams

### Import VCF Folder Sequence
```
User -> CLI: import --folder /path/to/vcards
CLI -> ImportOrchestrator: bulk_import(folder_path)
ImportOrchestrator -> FileSystem: list *.vcf files
FileSystem -> ImportOrchestrator: [file1.vcf, file2.vcf, ...]

loop for each VCF file
    ImportOrchestrator -> VCardSerializer: parse(file)
    VCardSerializer -> Contact: new Contact(vcard_data)
    Contact -> ImportOrchestrator: contact_object
    
    ImportOrchestrator -> Graph: get_contact(uid)
    alt Contact exists
        Graph -> ImportOrchestrator: existing_contact
        ImportOrchestrator -> Contact: compare_rev(existing, new)
        alt new REV is newer
            ImportOrchestrator -> FilterPipeline: run(contact)
            FilterPipeline -> ImportOrchestrator: filtered_contact
            ImportOrchestrator -> Graph: update_contact(contact)
        else
            ImportOrchestrator: skip (existing is newer)
        end
    else Contact doesn't exist
        ImportOrchestrator -> FilterPipeline: run(contact)
        FilterPipeline -> ImportOrchestrator: filtered_contact
        ImportOrchestrator -> Graph: add_contact(contact)
    end
end

ImportOrchestrator -> CLI: import_complete
CLI -> User: "Imported N contacts"
```

### Export to VCF Folder Sequence
```
User -> CLI: export --folder /path/to/output
CLI -> ExportOrchestrator: bulk_export(folder_path)
ExportOrchestrator -> Graph: get_all_contacts()
Graph -> ExportOrchestrator: [contact1, contact2, ...]

loop for each Contact
    ExportOrchestrator -> Contact: get_uid()
    Contact -> ExportOrchestrator: uid
    ExportOrchestrator: vcf_path = folder_path / f"{uid}.vcf"
    
    alt VCF file exists
        ExportOrchestrator -> FileSystem: read(vcf_path)
        FileSystem -> VCardSerializer: parse(vcf_data)
        VCardSerializer -> ExportOrchestrator: existing_contact
        ExportOrchestrator -> Contact: compare_rev(graph_contact, existing_contact)
        alt graph REV is newer
            ExportOrchestrator -> VCardSerializer: serialize(contact)
            VCardSerializer -> ExportOrchestrator: vcf_data
            ExportOrchestrator -> FileSystem: write(vcf_path, vcf_data)
        else
            ExportOrchestrator: skip (file is up to date)
        end
    else File doesn't exist
        ExportOrchestrator -> VCardSerializer: serialize(contact)
        VCardSerializer -> ExportOrchestrator: vcf_data
        ExportOrchestrator -> FileSystem: write(vcf_path, vcf_data)
    end
end

ExportOrchestrator -> CLI: export_complete
CLI -> User: "Exported N contacts"
```

### Filter Pipeline Execution
```
ImportOrchestrator -> FilterPipeline: run(contact)
FilterPipeline: sort filters by priority

loop for each filter
    FilterPipeline -> Filter: execute(contact)
    Filter -> Contact: check/modify data
    Contact -> Filter: modified_contact
    Filter -> FilterPipeline: contact
end

FilterPipeline -> ImportOrchestrator: filtered_contact
```

## Design Patterns

### Repository Pattern
- NetworkX graph acts as repository for Contact objects
- Abstracts storage mechanism from business logic
- Supports queries and traversals

### Strategy Pattern
- Multiple serializers (vCard, YAML, Markdown) implement common interface
- Allows swapping serialization strategies
- Each serializer encapsulates format-specific logic

### Chain of Responsibility
- Filter pipeline implements chain pattern
- Each filter processes contact and passes to next
- Filters can be added/removed without affecting others

### Facade Pattern
- CLI provides simplified interface to complex subsystems
- Orchestrators hide complexity of import/export logic
- Users interact with simple commands, not internal components

## Scalability Considerations

### Current Design (Phase 1)
- In-memory graph suitable for personal use (1000-10,000 contacts)
- File-based persistence through VCF files
- No database required

### Future Scaling Options
- Graph persistence: Serialize NetworkX graph to disk for large datasets
- Database backend: Optional SQLite/PostgreSQL for very large networks
- Lazy loading: Load contact details on-demand rather than all at once
- Indexing: Build indexes on common query fields (name, email)

## Fault Tolerance

### Data Integrity
- vCard 4.0 REV field prevents overwriting newer data with older data
- vCard 4.0 UID ensures unique identification even across systems
- RELATED properties maintain bidirectional relationship consistency
- Idempotent operations allow safe retries

### Error Handling
- Invalid VCF files logged but don't stop batch import
- Missing RELATED targets handled gracefully
- Filter failures logged but don't crash pipeline
- Graceful degradation when optional vCard fields missing

### Recovery
- File-based storage allows easy backup/restore
- Graph can be rebuilt from VCF folder at any time (including RELATED properties)
- No data loss on crashes (files remain on disk)

## vCard 4.0 RELATED Property Mapping

### Graph to vCard Projection
The NetworkX graph is projected onto vCard representations using the RELATED property:

```
NetworkX Graph Edge:
  Contact A --[friend, colleague]--> Contact B

Maps to vCard RELATED in Contact A:
  RELATED;TYPE=friend,colleague:urn:uuid:<Contact B's UID>
```

### Relationship Type Taxonomy (RFC 6350)
All relationship types follow vCard 4.0 specification:

**Social Relationships:**
- `contact` - Someone in contact list
- `acquaintance` - Known but not close
- `friend` - Friend relationship
- `met` - Have met before

**Professional Relationships:**
- `co-worker` - Works for same organization
- `colleague` - Professional peer

**Residential Relationships:**
- `co-resident` - Lives in same residence
- `neighbor` - Lives nearby

**Family Relationships:**
- `child` - Child of this contact (directional)
- `parent` - Parent of this contact (directional)
- `sibling` - Sibling relationship
- `spouse` - Married or partnered
- `kin` - Other family relation

**Romantic Relationships:**
- `muse` - Artistic inspiration
- `crush` - Romantic interest
- `date` - Dating relationship
- `sweetheart` - Romantic partner

**Special Relationships:**
- `me` - Self-reference
- `agent` - Acts on behalf of contact
- `emergency` - Emergency contact

### Bidirectional Relationship Handling
- Most relationships are symmetric (friend, colleague, spouse)
- When Contact A has `RELATED;TYPE=friend` to Contact B, Contact B should have reciprocal RELATED to Contact A
- System maintains consistency during import/export
- Directional relationships (parent/child) are one-way

### Multiple Relationship Types
- vCard 4.0 allows comma-separated TYPE values: `RELATED;TYPE=friend,colleague:urn:uuid:xxx`
- Single relationship edge can have multiple types
- Each type is maintained separately in graph metadata

## Markdown Relationship Representation

### Format Specification
Relationships are serialized in Markdown using a structured format within the document object model (DOM):

**Structure:**
```markdown
## Related

- relationship_kind [[Contact Name]]
- relationship_kind URL
```

**Key Features:**
1. **Heading**: "Related" (case-insensitive)
2. **Unordered List**: Each item is a relationship tuple
3. **Tuple Format**: `(relationship_kind, object)` where subject is implied
4. **Objects**: Wiki-style links `[[Name]]`, URLs, or plain text

### Graph Triple to Markdown Tuple

**Full Graph Representation:**
```
(Subject Contact, relationship_kind, Object Contact)
```

**Markdown Representation:**
```markdown
## Related

- relationship_kind [[Object Contact]]
```

The subject is always the current contact, so it's implied and not repeated in the list.

### Examples

**Example 1: Family Relationships**
```markdown
# John Smith

## Related

- parent [[Mary Smith]]
- parent [[Robert Smith]]
- sibling [[Jane Smith]]
- spouse [[Emily Johnson]]
- child [[Tommy Smith]]
```

Interpretation:
- John Smith's parents are Mary Smith and Robert Smith
- John Smith's sibling is Jane Smith
- John Smith is married to Emily Johnson
- John Smith's child is Tommy Smith

**Example 2: Professional Relationships**
```markdown
# Alice Johnson

Email: alice@company.com

## Related

- colleague [[Bob Wilson]]
- colleague https://company.com/contacts/carol.vcf
- agent [[Legal Associates LLC]]
```

**Example 3: Mixed Relationships**
```markdown
# Sarah Lee

## Related

- friend [[Mike Chen]]
- colleague [[Mike Chen]]
- emergency [[Mom]]
```

### Directional Relationship Semantics

Directional relationships are interpreted from the current contact's perspective:

- `- parent [[Mary]]`: Current contact is the child of Mary
- `- child [[Tom]]`: Current contact is the parent of Tom
- `- spouse [[Alex]]`: Bidirectional - both are spouses

### Parsing Algorithm

1. **Locate "Related" Section**: Find heading with text matching "related" (case-insensitive)
2. **Extract List**: Get unordered list immediately following heading
3. **Parse List Items**: Each item format: `relationship_kind object_reference`
4. **Resolve References**:
   - Wiki links `[[Name]]` -> lookup "Name.md" in markdown folder
   - URLs -> resolve to UID or create external reference
   - Plain text -> fuzzy match against contact names
5. **Create Relationships**: Generate graph edges with current contact as subject

### Rendering Algorithm

1. **Generate Heading**: Create "## Related" section
2. **Collect Relationships**: Get all relationships where current contact is subject
3. **Format List Items**:
   - Prefer wiki-style links for internal contacts: `- friend [[Bob Johnson]]`
   - Use URLs for external references: `- contact https://...`
   - Fall back to plain text if needed
4. **Sort**: Order by relationship_kind for consistent output

## Markdown File Format with YAML Front Matter

### Complete File Structure

Markdown files combine YAML front matter with Markdown content:

```markdown
---
fn: John Smith
uid: urn:uuid:a1b2c3d4-e5f6-7890-abcd-ef1234567890
rev: 2024-10-11T12:00:00Z
email: john.smith@example.com
tel: +1-555-0123
adr_street: 123 Main St
adr_locality: Springfield
adr_region: IL
adr_postal: 62701
org: Acme Corp
title: Software Engineer
---

# John Smith

**Email:** john.smith@example.com  
**Phone:** +1-555-0123  
**Organization:** Acme Corp  
**Title:** Software Engineer

## Address

123 Main St  
Springfield, IL 62701

## Related

- parent [[Mary Smith]]
- sibling [[Jane Smith]]
- spouse [[Emily Johnson]]
- friend [[Bob Wilson]]
- colleague [[Alice Brown]]
```

### YAML Front Matter Specification

**Purpose**: Machine-readable serialization of complete Contact object

**Format**: Flat YAML (unnested namespace)
- All vCard properties flattened to single-level keys
- Complex properties like addresses use prefixed keys: `adr_street`, `adr_locality`, etc.
- Array values serialized as YAML lists
- Example: Multiple emails → `email: [primary@example.com, secondary@example.com]`

**Delimiters**: 
- Opening: `---` (three hyphens)
- Closing: `---` (three hyphens)

**Precedence**: Front matter data takes precedence over Markdown content during import

### File Naming and Folder Operations

#### Naming Convention
- **VCF Files**: Named by UID → `{uid}.vcf` (e.g., `urn-uuid-12345.vcf`)
- **Markdown Files**: Named by Full Name (FN) → `{fn}.md` (e.g., `John Smith.md`)

#### Flat Namespace
Within a markdown folder, file names create a flat namespace:
- `John Smith.md` → Contact with FN="John Smith"
- `Mary Smith.md` → Contact with FN="Mary Smith"
- `Bob Wilson.md` → Contact with FN="Bob Wilson"

#### Wiki-style Link Dereferencing
1. Encounter `[[John Smith]]` in Related section
2. Look up `John Smith.md` in current markdown folder
3. Load and parse that file to get Contact object
4. Create relationship edge to that Contact

#### Bulk Import from Markdown Folder
```
1. Scan folder for *.md files
2. For each file:
   a. Parse YAML front matter → extract Contact properties
   b. Parse Markdown content → extract additional details
   c. Parse Related section → extract relationship tuples
   d. Add Contact to graph (or update if REV is newer)
3. Second pass: Resolve all wiki-style links
4. Create relationship edges in graph
```

#### Bulk Export to Markdown Folder
```
1. For each Contact in graph:
   a. Generate filename: "{contact.fn}.md"
   b. Serialize Contact as Flat YAML → front matter
   c. Render Contact as Markdown → content
   d. Render Related section with wiki-style links
   e. Combine front matter + content
   f. Write to file (check REV for smart overwrite)
```

### Idempotent Operations

Like VCF import/export, Markdown operations are idempotent:
- **Import**: Use REV field (from front matter) to determine if update needed
- **Export**: Check existing file's REV before overwriting
- **Wiki Links**: Consistent resolution ensures same relationships each time
- **Front Matter**: Flat YAML ensures consistent serialization

### Integration with vCard RELATED

The Markdown format complements vCard RELATED:

**vCard Format:**
```
BEGIN:VCARD
VERSION:4.0
FN:John Smith
UID:urn:uuid:12345
RELATED;TYPE=parent:urn:uuid:67890
RELATED;TYPE=friend:urn:uuid:abcdef
END:VCARD
```

**Equivalent Markdown:**
```markdown
# John Smith

## Related

- parent [[Mary Smith]]
- friend [[Bob Johnson]]
```

Both representations map to the same graph structure, allowing seamless conversion between formats.

## Design Trade-offs

### vCard RELATED vs Custom Relationship Storage
**Decision**: Use vCard 4.0 RELATED property
**Rationale**: Standards-compliant, interoperable with other vCard systems, built-in taxonomy
**Trade-off**: Limited to vCard-defined types, but extensible via custom TYPE values

### NetworkX vs Custom Graph
**Decision**: Use NetworkX
**Rationale**: Well-tested, efficient, rich feature set
**Trade-off**: Dependency on external library, but reduces bug surface area

### File-based vs Database Storage
**Decision**: File-based (VCF files)
**Rationale**: Interoperability, simplicity, no server needed, vCard 4.0 RELATED preserves graph
**Trade-off**: Less efficient for very large datasets, but suitable for target use case

### Multiple Serialization Formats
**Decision**: Support vCard, YAML, and Markdown
**Rationale**: Different formats for different use cases (interop, programmatic, human)
**Trade-off**: More code to maintain, but provides flexibility

### Gender-neutral Relationships
**Decision**: Use vCard 4.0 relationship taxonomy (already gender-neutral)
**Rationale**: Standards-compliant, inclusive, accurate modeling
**Trade-off**: May require gender context for rendering (e.g., "parent" -> "mother"/"father")

### Filter Pipeline
**Decision**: Extensible filter architecture
**Rationale**: Future-proof for data curation needs
**Trade-off**: More complex than simple validation, but provides flexibility

### CLI-first Approach
**Decision**: Start with CLI using Click
**Rationale**: Simple to implement, sufficient for power users
**Trade-off**: Not beginner-friendly, but establishes API for future GUI
