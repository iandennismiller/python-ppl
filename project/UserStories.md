# User Stories

## Story 1: Import Contacts from vCard Files

As a user
I want to import contact information from a folder of .VCF files
So that I can populate my contact graph from existing vCard data

### Acceptance Criteria
- [ ] System iterates through all *.VCF files in specified folder
- [ ] Each vCard is parsed and added as a Contact to the graph
- [ ] If contact already exists (by UID), system checks REV field
- [ ] When imported REV is newer, contact data is updated in graph
- [ ] When imported REV is older or equal, existing data is preserved
- [ ] Invalid vCard files are logged but don't stop import process

### Priority
High

### Notes
This is the primary method for getting data into the system. Must handle vCard 4.0 specification correctly.

---

## Story 2: Export Contacts as vCard Files

As a user
I want to export my contact graph to a folder of .VCF files
So that I can use my contacts in other vCard-compatible systems

### Acceptance Criteria
- [ ] System exports each Contact as a vCard 4.0 compliant .VCF file
- [ ] Files are named using the UID field from the contact
- [ ] If destination file already exists, check REV field
- [ ] Only overwrite if graph has newer data than existing file
- [ ] All vCard 4.0 required fields are included
- [ ] Export operation is idempotent (can be run multiple times safely)

### Priority
High

### Notes
Export must maintain vCard 4.0 compliance for interoperability with other systems.

---

## Story 3: Model Contact Relationships

As a user
I want to define relationships between my contacts
So that I can track how people and organizations are connected

### Acceptance Criteria
- [ ] Can create directional relationships (e.g., parent->child)
- [ ] Can create bidirectional relationships (e.g., friendship, colleagues)
- [ ] Can specify relationship type/kind
- [ ] Can have multiple relationships between same two contacts
- [ ] Relationships are gender-neutral by default
- [ ] Can query graph for all relationships of a contact

### Priority
High

### Notes
Graph-based relationship model is a key differentiator. Must support complex relationship networks.

---

## Story 4: Automatic UID Assignment

As a developer
I want contacts without UIDs to automatically receive a UUID
So that all contacts have unique identifiers without manual intervention

### Acceptance Criteria
- [ ] Filter checks if Contact has UID field populated
- [ ] If UID is missing, generates new UUID
- [ ] UUID is assigned to contact's UID field
- [ ] Filter can be triggered as part of import pipeline
- [ ] Filter logs when UIDs are assigned

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
- [ ] Can export contact graph to YAML file
- [ ] Can import YAML file to populate graph
- [ ] YAML import/export is idempotent
- [ ] Supports both standard YAML and "flat YAML" with unnested keys
- [ ] Maintains data integrity equivalent to vCard import/export

### Priority
Medium

### Notes
Developer-friendly format for programmatic access and version control.

---

## Story 6: Markdown Contact Display

As a user
I want to view contacts in Markdown format
So that I can read contact information in a clean, human-friendly way

### Acceptance Criteria
- [ ] Can render Contact to Markdown representation
- [ ] Markdown is readable and well-formatted
- [ ] Includes all relevant contact information
- [ ] Can parse Markdown back into Contact (via DOM)

### Priority
Medium

### Notes
Markdown rendering for human consumption. DOM-based parsing is novel approach.

---

## Story 7: Command-Line Interface

As a user
I want to interact with the contact manager via command line
So that I can manage contacts efficiently without a GUI

### Acceptance Criteria
- [ ] CLI built with Click framework
- [ ] Support import command (folder of VCFs to graph)
- [ ] Support export command (graph to folder of VCFs)
- [ ] Support list/search commands
- [ ] Clear help documentation for all commands
- [ ] Proper error messages for invalid operations

### Priority
Medium

### Notes
Starting point for user interaction. May expand to GUI later.

---

## Story 8: Filter Pipeline Execution

As a developer
I want to run filters on contact data at various trigger points
So that I can validate and curate information in the graph

### Acceptance Criteria
- [ ] Filter pipeline can be triggered programmatically
- [ ] Filters execute in defined order
- [ ] Can trigger pipeline during import
- [ ] Can trigger pipeline on-demand
- [ ] Each filter logs its actions
- [ ] Failed filters don't crash pipeline

### Priority
Medium

### Notes
Extensible architecture for data quality. Foundation for future data curation features.

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
