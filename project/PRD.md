# Product Requirements Document (PRD)

## Overview
PPL is a People Manager application - a modern take on the Rolodex or Contacts app. It manages contact information for people and organizations, models relationships between contacts, and provides multiple serialization formats including vCard 4.0, YAML, and Markdown. The system uses a graph-based data model to represent contacts and their relationships.

## Problem Statement
Contact management systems often treat contacts in isolation, failing to capture the rich web of relationships between people and organizations. Additionally, most systems lock data into proprietary formats, making it difficult to work with contact information programmatically or integrate with other tools. PPL solves this by:
- Modeling contacts as a graph with explicit, typed relationships
- Supporting standard formats (vCard 4.0) alongside developer-friendly formats (YAML, Markdown)
- Providing bidirectional import/export with intelligent merge strategies based on timestamps
- Separating gender from relationships to support modern, inclusive relationship modeling

## Goals and Objectives
- Create a graph-based contact management system that preserves relationship context
- Support multiple serialization formats with idempotent import/export
- Implement intelligent data merging using vCard REV field for conflict resolution
- Provide extensible filter pipeline for data curation and validation
- Build a command-line interface for common operations
- Leverage existing, well-tested libraries to minimize custom code and bugs

## Target Audience
- Developers who want programmatic access to contact data
- Users who need to manage complex relationship networks
- Power users who prefer command-line tools
- People working with vCard files across multiple systems
- Anyone needing flexible contact data import/export

## Features and Requirements

### Functional Requirements

#### Core Data Model
- **Contact**: Fundamental class representing a person or organization with contact details (vCard 4.0 entity)
- **Relationship**: Model connections between contacts with directional and bidirectional support
- **vCard RELATED Field**: Use the vCard 4.0 RELATED property to project the social graph onto contact representations
- **Relationship Types**: Support all vCard 4.0 defined relationship types:
  - Social: contact, acquaintance, friend, met
  - Professional: co-worker, colleague
  - Residential: co-resident, neighbor
  - Family: child, parent, sibling, spouse, kin
  - Romantic: muse, crush, date, sweetheart
  - Special: me, agent, emergency
- **Multiple Relationships**: Allow multiple RELATED properties per contact (cardinality: *)
- **Gender-neutral Relationships**: Separate gender information from relationship types (aligned with vCard 4.0)

#### Import/Export
- **vCard Import**: Parse vCard 4.0 files including RELATED properties and add/update contacts in graph
- **vCard Export**: Generate vCard 4.0 compliant .VCF files with RELATED properties from graph
- **Social Graph Projection**: Use RELATED field to represent the NetworkX graph in vCard format
- **YAML Import/Export**: Support standard YAML serialization
- **Flat YAML**: Support flattened YAML with unnested namespace using vCard 4.0 property names as keys
- **Markdown Import/Export**: Use Markdown DOM for contact representation with structured relationship format
- **Markdown Relationship Format**: Parse and render "Related" heading with unordered list of relationship tuples `(relationship_kind, object)` where subject is implied
- **Wiki-style Links**: Support `[[Contact Name]]` syntax in Markdown for related contacts
- **REV-based Merging**: Use vCard 4.0 REV field (timestamp) to determine data freshness and merge conflicts
- **UID Field**: Use vCard 4.0 UID field for unique contact identification
- **Idempotent Operations**: Import/export operations should be repeatable without data loss

#### Bulk Operations
- **VCF Folder Import**: Iterate *.VCF files in a folder and import all contacts
- **VCF Folder Export**: Bulk export graph as .VCF files to destination folder
- **VCF UID-based Naming**: Name VCF files according to UID field
- **Markdown Folder Import**: Iterate *.md files in a folder and import all contacts
- **Markdown Folder Export**: Bulk export graph as .md files to destination folder
- **Markdown FN-based Naming**: Name Markdown files according to Full Name (FN) field: "First Last.md"
- **Wiki-style Link Resolution**: Dereference [[Contact Name]] to "Contact Name.md" in flat namespace
- **Smart Overwrite**: Only overwrite existing files when graph has newer data
- **YAML Front Matter**: Include vCard 4.0 properties as YAML in Markdown files between `---` delimiters (e.g., FN, UID, EMAIL, TEL)

#### Data Curation
- **Filter Pipeline**: Extensible, composable architecture for data validation and curation
- **AbstractFilter Base Class**: Defines filter contract (priority, execute, should_run)
- **Multiple Pipelines**: import_pipeline, export_pipeline, curation_pipeline for different scenarios
- **UID Assignment Filter**: Check contacts for UID field and assign UUID if missing (priority=10)
- **Gender Inference Filter**: Infer GENDER property from gendered relationship terms in markdown (priority=50)
- **Gender Term Detection**: Detect mother/father/sister/brother/aunt/uncle → infer F/M gender
- **Wiki-link Dereferencing**: Update target contact's markdown file with inferred GENDER
- **Composable Architecture**: Filters can be combined, reused, and independently developed
- **Trigger Options**: Run filters at various lifecycle points (import, export, on-demand)

#### Data Consistency
- **Consistency Service**: Detect inconsistencies across multiple data representations
- **Multi-Representation Architecture**: Graph, VCF files, Markdown files, YAML front matter, Markdown content
- **Inconsistency Detection**: Identify missing, outdated, conflicting, and orphaned data
- **Consistency Checks**: 
  - Graph ↔ VCF consistency (REV timestamps, RELATED properties, file existence)
  - Graph ↔ Markdown consistency (FN-based files, front matter, Related section)
  - Front matter ↔ Content consistency (YAML vs human-readable content)
- **Consistency Reports**: Detailed reports showing all discrepancies with actionable messages
- **Consistency Command**: `ppl check-consistency` to validate system state
- **Future Enhancement**: Repair pipelines to automatically resolve inconsistencies with configurable strategies

#### User Interface
- **Command-line Interface**: Use Click for minimal CLI
- **Contact Rendering**: Display contacts in human-readable Markdown format
- **Consistency Checking**: Command to detect and report data inconsistencies

### Non-Functional Requirements

#### Performance
- Efficient graph operations for large contact networks
- Fast import/export for bulk operations

#### Reliability
- Idempotent import/export operations
- Data integrity through timestamp-based conflict resolution
- Use of established libraries (networkx, vobject, pyyaml, marko-py, click)

#### Maintainability
- Clean separation of concerns (models, filters, renderers)
- Minimal custom code by leveraging existing libraries
- Extensible filter pipeline architecture

#### Standards Compliance
- Full vCard 4.0 specification compliance
- Proper YAML serialization

## Success Metrics
- Successfully import/export vCard files without data loss
- Idempotent operations: repeated imports of same data produce identical results
- Support for complex relationship networks with multiple relationship types
- Filter pipeline successfully validates and curates contact data
- Clean, usable CLI for common contact management tasks

## Timeline and Milestones

### Phase 1: Core Infrastructure
- Data models (Contact, Relationship)
- Graph management with networkx
- Basic filter pipeline

### Phase 2: vCard Support
- vCard 4.0 import/export
- REV-based merge logic
- UID assignment filter

### Phase 3: Bulk Operations
- Folder import/export
- Smart file overwrite logic

### Phase 4: Additional Formats
- YAML import/export
- Flat YAML support
- Markdown rendering and import

### Phase 5: CLI
- Click-based command-line interface
- Common operations (import, export, list, search)

## Risks and Assumptions

### Risks
- vCard 4.0 specification complexity may require careful implementation
- Graph operations may become slow with very large contact networks
- Markdown DOM approach for import is novel and may need iteration

### Assumptions
- vCard 4.0 REV field is reliably present in imported files
- NetworkX provides sufficient performance for contact graph operations
- Existing libraries (vobject, marko-py) are mature and well-maintained

## Open Questions
- How should conflicts be resolved when REV fields are identical?
- Should the system support vCard versions prior to 4.0?
- What is the maximum expected size of contact networks?
- Should there be a GUI in addition to CLI?
