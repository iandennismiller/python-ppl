# User Stories

## Story 1: Import Contacts from vCard Files

As a user
I want to import contact information from a folder of .VCF files
So that I can populate my contact graph from existing vCard data

### Acceptance Criteria
- [x] System iterates through all *.VCF files in specified folder
- [x] Each vCard is parsed and added as a Contact to the graph
- [x] RELATED properties are extracted and converted to graph edges
- [x] If contact already exists (by vCard UID), system checks REV field using merge logic
- [x] When imported REV is newer, contact data is updated in graph
- [x] When imported REV is older, existing data is preserved (skipped)
- [x] Invalid vCard files are logged but don't stop import process

### Priority
High

### Notes
This is the primary method for getting data into the system. Must handle vCard 4.0 specification correctly, including all RELATED properties for relationship reconstruction.

---

## Story 2: Export Contacts as vCard Files

As a user
I want to export my contact graph to a folder of .VCF files
So that I can use my contacts in other vCard-compatible systems

### Acceptance Criteria
- [x] System exports each Contact as a vCard 4.0 compliant .VCF file
- [x] Graph edges are projected as RELATED properties in each contact's vCard
- [x] Files are named using the FN field (sanitized) from the contact
- [x] If destination file already exists, check REV field and content
- [x] Only overwrite if graph has newer data or different content (smart export)
- [x] All vCard 4.0 required fields are included (FN, VERSION)
- [x] Export operation is idempotent (can be run multiple times safely)
- [x] Returns statistics (written, skipped) for monitoring

### Priority
High

### Notes
Export must maintain vCard 4.0 compliance for interoperability with other systems.

---

## Story 3: Model Contact Relationships Using vCard RELATED

As a user
I want to define relationships between my contacts using the vCard 4.0 RELATED property
So that I can track how people and organizations are connected in a standards-compliant way

### Acceptance Criteria
- [x] Can create directional relationships using vCard RELATED types (parent->child)
- [x] Can create bidirectional relationships (friend, colleague, spouse)
- [x] Can specify relationship types from vCard 4.0 taxonomy (18 standard types)
- [x] Can have multiple RELATED properties per contact (cardinality: *)
- [x] Can specify multiple TYPE values in single RELATED (comma-separated)
- [x] Relationships stored as RELATED properties in vCard export
- [x] Relationships reconstructed as graph edges from RELATED on import
- [x] Can query graph for all relationships of a contact

### Priority
High

### Notes
vCard 4.0 RELATED property is the key to projecting the social graph onto contact representations. Must support all vCard relationship types: contact, acquaintance, friend, met, co-worker, colleague, co-resident, neighbor, child, parent, sibling, spouse, kin, muse, crush, date, sweetheart, me, agent, emergency.

---

## Story 4: Automatic UID Assignment

As a developer
I want contacts without UIDs to automatically receive a UUID
So that all contacts have unique identifiers per vCard 4.0 specification

### Acceptance Criteria
- [x] Filter checks if Contact has vCard UID field populated
- [x] If UID is missing, generates new UUID per vCard 4.0 format
- [x] UUID is assigned to contact's UID property
- [x] Filter can be triggered as part of import pipeline
- [x] Filter logs when UIDs are assigned

### Priority
High

### Notes
This is the first filter in the pipeline. Sets pattern for other filters.

---

## Story 5: Import/Export YAML Format

As a developer
I want to import and export contacts in YAML format
So that I can work with contact data programmatically

### Acceptance Criteria
- [x] Can export contact graph to YAML file
- [x] Can import YAML file to populate graph
- [x] YAML import/export is idempotent
- [x] Supports both standard YAML and "flat YAML" with unnested keys
- [x] Maintains data integrity equivalent to vCard import/export

### Priority
Medium

### Notes
Developer-friendly format for programmatic access and version control.

---

## Story 6: Markdown Contact Display with Relationships

As a user
I want to view contacts in Markdown format with relationships
So that I can read contact information in a clean, human-friendly way

### Acceptance Criteria
- [x] Can render Contact to Markdown representation
- [x] Markdown is readable and well-formatted
- [x] Includes all relevant contact information
- [x] Renders "Related" section with unordered list of relationships
- [x] Relationship format: `- relationship_kind [[Contact Name]]`
- [x] Supports wiki-style links `[[Name]]` for related contacts
- [x] Can parse Markdown back into Contact (via DOM)
- [x] Can parse "Related" section (case-insensitive) to extract relationships
- [x] Relationship tuples are `(relationship_kind, object)` with implied subject

### Priority
Medium

### Notes
Markdown rendering for human consumption. DOM-based parsing is novel approach. The "Related" section provides a clean, readable way to display relationship networks. Example:

```markdown
# John Smith

## Related

- parent [[Mary Smith]]
- friend [[Bob Johnson]]
- colleague [[Alice Williams]]
```

---

## Story 6A: Import/Export Markdown Folder

As a user
I want to import and export contacts from a folder of .md files
So that I can work with contacts in a human-friendly, version-controllable format

### Acceptance Criteria
- [x] System iterates through all *.md files in specified folder
- [x] Each Markdown file is parsed: YAML front matter + content + Related section
- [x] Files named by Full Name (FN): "First Last.md"
- [x] YAML front matter contains Flat YAML serialization of Contact
- [x] Front matter delimited by `---` markers
- [x] Wiki-style links `[[Contact Name]]` dereferenced to "Contact Name.md" in folder
- [x] Flat namespace used for wiki-link resolution
- [x] Related section parsed to extract relationship tuples
- [x] If contact exists (by UID from front matter), check REV field and merge
- [x] Export creates one .md file per contact, named by FN
- [x] Export includes YAML front matter with Flat YAML Contact data
- [x] Export renders Related section with wiki-style links to other contacts
- [x] Operations are idempotent (same as VCF import/export)
- [x] Smart export only writes files when data changes

### Priority
Medium

### Notes
Markdown format provides human-readable, git-friendly contact storage. YAML front matter ensures machine-readable data is preserved. Example file:

```markdown
---
FN: John Smith
UID: urn:uuid:12345
EMAIL:
  - john@example.com
  - john.smith@work.com
TEL:
  - +1-555-1234
RELATED;TYPE=parent:
  - urn:uuid:67890
RELATED;TYPE=friend:
  - urn:uuid:abcde
  - urn:uuid:fghij
---

# John Smith

Email: john@example.com, john.smith@work.com
Phone: +1-555-1234

## Related

- parent [[Mary Smith]]
- friend [[Bob Johnson]]
- friend [[Alice Wilson]]
```

---

## Story 7: Command-Line Interface

As a user
I want to interact with the contact manager via command line
So that I can manage contacts efficiently without a GUI

### Acceptance Criteria
- [x] CLI built with Click framework
- [x] Support import command (folder to graph with multiple formats)
- [x] Support export command (graph to folder with multiple formats)
- [x] Support list command (list all contacts)
- [x] Support search command (search by name, email, org)
- [x] Support convert command (convert between formats)
- [x] Clear help documentation for all commands
- [x] Proper error messages for invalid operations
- [x] --verbose flag for detailed output
- [x] --force flag for export to override smart detection
- [x] --graph-format option for JSON/GraphML selection

### Priority
Medium

### Notes
Starting point for user interaction. May expand to GUI later.

---

## Story 8: Filter Pipeline Execution

As a developer
I want to run composable filters on contact data at various trigger points
So that I can validate and curate information in the graph

### Acceptance Criteria
- [x] AbstractFilter base class defines filter contract
- [x] FilterPipeline orchestrates filter execution by priority
- [x] Multiple pipeline instances (import, export, curation)
- [x] Filter pipeline can be triggered programmatically
- [x] Filters execute in priority order (lower priority runs first)
- [x] FilterContext carries pipeline-specific data
- [x] Can trigger pipeline during import
- [x] Each filter logs its actions
- [x] Failed filters don't crash pipeline (error handling)
- [x] Filters are composable and reusable across pipelines

### Priority
High

### Notes
Extensible architecture for data quality. Foundation for future data curation features. Chain of Responsibility pattern enables independent filter development.

---

## Story 8A: Gender Inference from Relationships

As a user
I want gender information to be inferred from gendered relationship terms
So that contact records are automatically enriched with gender data

### Acceptance Criteria
- [x] Gender filter examines markdown Related section
- [x] Detects gendered relationship terms (mother, father, sister, brother, uncle, aunt, etc.)
- [x] Infers GENDER property from terms (mother/sister/aunt → F, father/brother/uncle → M)
- [x] Gender-neutral terms (parent, sibling, spouse) don't trigger inference
- [x] All inferences logged for review
- [x] Filter runs in curation pipeline (priority=50)
- [ ] Dereferences wiki-style links to find target contact (not fully implemented)
- [ ] Updates target contact's markdown front matter with GENDER property (not fully implemented)

### Priority
Medium

### Notes
Example: If contact has `- mother [[Jane Doe]]` in Related section, system infers Jane Doe's GENDER=F and updates her markdown file front matter.

---

## Story 9: Gender-Neutral Relationship Rendering

As a user
I want relationships to be defined without gender assumptions
So that the system is inclusive and accurate

### Acceptance Criteria
- [ ] Relationship types don't encode gender (e.g., "parent" not "mother/father")
- [ ] Gender information stored separately from relationship
- [ ] Can optionally render relationships with gender if contact data includes it
- [ ] Default rendering is gender-neutral

### Priority
Low

### Notes
Important for inclusivity. Separate gender from relationship structure.

---

## Story 10: Consistency Checking Across Representations

As a user
I want to detect inconsistencies between graph, VCF files, and Markdown files
So that I can identify and resolve data discrepancies

### Acceptance Criteria
- [ ] Can run consistency check command: `ppl check-consistency`
- [ ] Detects missing contacts (in graph but not in files, or vice versa)
- [ ] Detects outdated representations (REV timestamp mismatches)
- [ ] Detects conflicts (same property with different values)
- [ ] Detects orphaned files (files without corresponding graph nodes)
- [ ] Validates YAML front matter consistency with Markdown content
- [ ] Validates RELATED properties match across all representations
- [ ] Generates detailed consistency report with all inconsistencies
- [ ] Report shows: type, source, target, contact UID, field, and values
- [ ] Report indicates whether system is in consistent state
- [ ] Each inconsistency includes actionable message

### Priority
High

### Notes
Foundation for data quality and future automated repair. Critical for maintaining multi-representation architecture integrity.

**Example Inconsistencies:**
- Contact exists in graph but VCF file missing
- VCF REV=2024-01-15 but graph REV=2024-01-14
- Email in YAML front matter differs from graph
- Related section has "friend [[Bob]]" but no RELATED;TYPE=friend in front matter
- Markdown file "John Smith.md" exists but no contact with FN="John Smith" in graph

**Future Enhancement:**
- Configure repair pipelines to automatically resolve inconsistencies
- Support resolution strategies: "trust graph", "trust files", "newest REV"
- Selective repair by inconsistency type


---

## Story 11: Non-Destructive Contact Merging

As a user
I want to update contact information incrementally without losing existing data
So that I can curate contacts over time by adding one or two fields at a time

### Acceptance Criteria
- [x] Contact.merge_from() method intelligently merges two contacts
- [x] Missing fields in incoming contact don't delete existing graph data
- [x] New fields in incoming contact are added to existing graph data
- [x] When both contacts have a value for same field, REV timestamp determines winner
- [x] List fields (email, tel, etc.) merge unique values
- [x] Complex fields (related, x_properties) merge without data loss
- [x] REV timestamp always updated to latest
- [x] prefer_newer parameter controls conflict resolution behavior

### Priority
High

### Notes
Critical for incremental curation workflows. Users often receive partial contact information from various sources and need to accumulate this data over time without manual intervention to preserve existing fields.

**Example Workflow:**
1. Import contact with basic info (name, email)
2. Later import same contact with phone number (email missing in new import)
3. System merges data: contact now has name, email, AND phone number
4. Email is not deleted because it was missing in the second import

---

## Story 12: Graph-Level Intelligent Merging

As a developer
I want the graph to handle contact merging automatically with statistics
So that import operations report what changes were made

### Acceptance Criteria
- [x] ContactGraph.merge_contact() method for smart graph operations
- [x] Returns tuple (was_modified, action) where action is "added", "updated", or "skipped"
- [x] Compares REV timestamps before merging
- [x] If contact doesn't exist, adds it (action="added")
- [x] If contact exists and incoming is newer, merges data (action="updated")
- [x] If contact exists and incoming is older, skips it (action="skipped")
- [x] Preserves all existing data during merge operations

### Priority
High

### Notes
Enables batch imports with detailed reporting. Users can see exactly what happened: how many contacts were added, updated, or skipped due to being older.

---

## Story 13: Smart Export with Change Detection

As a user
I want export operations to only write files when data has actually changed
So that I minimize file system operations and avoid unnecessary file-change events

### Acceptance Criteria
- [x] should_export_vcard() function detects if file needs writing
- [x] should_export_markdown() function detects if file needs writing
- [x] Returns True if file doesn't exist
- [x] Returns True if contact has newer REV than existing file
- [x] Returns True if content differs despite same REV
- [x] Returns False if file exists with same content
- [x] bulk_export() functions return (written, skipped) statistics
- [x] --force flag overrides smart detection to write all files

### Priority
High

### Notes
Important for workflows where exports are run frequently (e.g., git-based workflows, automated syncs). Minimizing file writes reduces git commits, file watcher events, and sync operations.

**Example:**
- Export 100 contacts to folder
- Re-export same 100 contacts
- Result: 0 written, 100 skipped (no unnecessary file operations)

---

## Story 14: CLI Statistics and Verbose Output

As a user
I want detailed statistics about import/export operations
So that I understand what changes were made to my contact graph

### Acceptance Criteria
- [x] import-contacts shows "Added: X, Updated: Y, Skipped: Z"
- [x] export-contacts shows "Written: X, Skipped: Y"
- [x] convert command shows import and export statistics
- [x] --verbose flag provides additional details
- [x] Statistics displayed in both verbose and normal modes
- [x] Clear, actionable output messages

### Priority
Medium

### Notes
Transparency is critical for user confidence in the system. Users need to know if their data is being correctly processed.

---

## Story 15: JSON Graph Format Support

As a developer
I want to export and import contact graphs in JSON format
So that I can integrate with graph visualization tools and JavaScript libraries

### Acceptance Criteria
- [x] Save contact graph in JSON format using graphology schema
- [x] JSON structure includes attributes, options, nodes, and edges
- [x] options.type set to "directed" for directed graphs
- [x] options.allowSelfLoops and options.multi configurable
- [x] Nodes contain key (UID) and attributes (contact data)
- [x] Edges contain key, source, target, and attributes (relationship data)
- [x] Load contact graph from JSON format
- [x] Auto-detect format from file extension (.json vs .graphml)
- [x] --graph-format option to explicitly specify format
- [x] All contact data and relationships preserved in JSON roundtrip
- [x] Human-readable JSON with indentation

### Priority
Medium

### Notes
JSON format enables integration with graph visualization libraries like Cytoscape.js, Sigma.js, and other tools that use the graphology JSON schema. This format is more portable than GraphML for web-based applications.

**Example JSON Structure:**
```json
{
  "attributes": {"name": "Contact Graph"},
  "options": {"allowSelfLoops": true, "multi": false, "type": "directed"},
  "nodes": [{"key": "uid-1", "attributes": {"fn": "Alice", ...}}],
  "edges": [{"key": "uid-1->uid-2", "source": "uid-1", "target": "uid-2", "attributes": {...}}]
}
```

---

## Story 16: Curation Workflow Documentation

As a user
I want comprehensive documentation on how to use the curation features
So that I can effectively manage my contacts over time

### Acceptance Criteria
- [x] Created CurationWorkflow.md guide with examples
- [x] Documents non-destructive merging principles
- [x] Explains REV timestamp behavior
- [x] Shows example workflows (incremental import, collaborative editing, etc.)
- [x] Includes troubleshooting section
- [x] Documents import/export statistics
- [x] Explains --force and --verbose flags
- [x] README updated with curation feature overview

### Priority
Medium

### Notes
Documentation is critical for user adoption of new features. Users need clear examples showing how to use curation features effectively.
