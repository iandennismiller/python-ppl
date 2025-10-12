# Implementation Plan

## Phases

### Phase 1: Core Data Models and Graph Infrastructure
**Duration:** 1-2 weeks  
**Goals:**
- Establish foundational data structures aligned with vCard 4.0
- Set up project structure and dependencies
- Create basic graph operations

**Deliverables:**
- [x] Project structure with /ppl/models directory
- [x] pyproject.toml with dependencies (networkx, vobject, pyyaml, marko-py, click)
- [x] Contact class with all vCard 4.0 properties (FN, N, UID, REV, EMAIL, TEL, ADR, RELATED, etc.)
- [x] Related class for vCard 4.0 RELATED property representation
- [x] Relationship class for internal graph edge representation
- [x] Mapping between RELATED properties and graph edges
- [x] Graph manager using NetworkX
- [x] Basic unit tests for models
- [x] vCard 4.0 UID and REV field handling
- [x] Contact.merge_from() method for non-destructive merging
- [x] Contact.compare_rev() method for REV timestamp comparison

**Dependencies:** None

---

### Phase 2: vCard Import/Export with RELATED Properties
**Duration:** 2-3 weeks  
**Goals:**
- Implement vCard 4.0 parsing and generation
- Handle RELATED properties for social graph projection
- Implement REV-based merge logic
- Support single file and bulk operations

**Deliverables:**
- [x] /ppl/serializers/vcard.py module
- [x] Parse VCF file to Contact object (all vCard 4.0 properties)
- [x] Extract RELATED properties and create graph edges
- [x] Generate VCF file from Contact object
- [x] Inject RELATED properties from graph edges during export
- [x] Support all 18 vCard 4.0 RELATED TYPE values
- [x] Handle multiple TYPE values in single RELATED property
- [x] REV comparison logic for conflict resolution
- [x] bulk_import_vcards(folder) function with relationship reconstruction
- [x] bulk_export_vcards(contacts, folder) function with RELATED projection
- [x] Smart overwrite logic using should_export_vcard() - only when content/REV differs
- [x] bulk_export returns (written, skipped) statistics
- [x] Unit tests for vCard serializer
- [x] Unit tests for RELATED property handling
- [x] Integration tests for import/export cycle with relationships

**Dependencies:** Phase 1 complete

---

### Phase 3: Filter Pipeline and Models
**Duration:** 1-2 weeks  
**Goals:**
- Create extensible filter framework with abstract base class
- Implement composable pipeline architecture
- Build UID assignment filter
- Build gender inference filter
- Integrate with import process

**Deliverables:**
- [x] /ppl/filters/ directory structure
- [x] /ppl/models/filter.py - AbstractFilter base class
- [x] /ppl/models/pipeline.py - FilterPipeline and FilterContext classes
- [x] Filter pipeline framework with priority-based execution
- [x] Filter registration system
- [x] Multiple pipeline instances (import_pipeline, export_pipeline, curation_pipeline)
- [x] /ppl/filters/uid_filter.py - UID assignment filter (priority=10)
- [x] /ppl/filters/gender_filter.py - Gender inference filter (priority=50)
- [x] Gender term mapping (mother/father/sister/brother/etc → M/F)
- [x] Pipeline trigger points (import, on-demand)
- [x] Logging for filter actions and gender inferences
- [x] Unit tests for AbstractFilter and FilterPipeline
- [x] Unit tests for UID filter
- [x] Unit tests for gender filter
- [x] Integration tests for pipeline composition
- [ ] Wiki-link dereferencing for gender updates (partial)
- [ ] Markdown front matter update with GENDER property (partial)

**Dependencies:** Phase 1 complete

---

### Phase 4: YAML Serialization
**Duration:** 1-2 weeks  
**Goals:**
- Support YAML import/export
- Support flat YAML format
- Ensure idempotent operations

**Deliverables:**
- [x] /ppl/serializers/yaml_serializer.py module
- [x] to_yaml(contact) function
- [x] from_yaml(yaml_str) function
- [x] to_flat_yaml(contact) function (unnested keys)
- [x] from_flat_yaml(yaml_str) function
- [x] Unit tests for YAML serializer
- [x] Integration tests for YAML idempotency
- [ ] YAML bulk import/export (available through CLI)

**Dependencies:** Phase 1 complete

---

### Phase 5: Markdown Rendering and Parsing with Relationships
**Duration:** 2-3 weeks  
**Goals:**
- Render contacts as Markdown with YAML front matter and relationship sections
- Parse Markdown DOM to Contact objects
- Implement "Related" section with structured relationship format
- Support bulk folder operations
- Provide human-friendly display

**Deliverables:**
- [x] /ppl/serializers/markdown.py module
- [x] YAML front matter support with `---` delimiters
- [x] vCard 4.0 property serialization in YAML front matter (FN, UID, EMAIL, TEL, etc.)
- [x] Handle multiple values as YAML arrays (EMAIL, TEL, ADR, RELATED with same TYPE)
- [x] parse_yaml_front_matter(markdown_str) function
- [x] render_yaml_front_matter(contact) function
- [x] to_markdown(contact) function with YAML front matter + content
- [x] Render "Related" heading with unordered list of relationships
- [x] Format relationships as `- relationship_kind [[Contact Name]]`
- [x] Support wiki-style links `[[Name]]` for related contacts
- [x] from_markdown(markdown_str) using marko DOM
- [x] Parse YAML front matter (precedence over Markdown content)
- [x] Parse YAML arrays for multi-valued properties
- [x] Parse "Related" section (case-insensitive heading detection)
- [x] Extract relationship tuples `(relationship_kind, object)`
- [x] Resolve wiki-style links to "Contact Name.md" in folder
- [x] bulk_import_markdown(folder_path) function
- [x] bulk_export_markdown(contacts, folder_path) function with smart export
- [x] bulk_export returns (written, skipped) statistics
- [x] File naming by Full Name (FN): "{fn}.md"
- [x] Flat namespace for wiki-link dereferencing
- [x] Create graph edges from parsed relationships
- [x] Unit tests for YAML front matter parsing/rendering
- [x] Unit tests for array-valued properties
- [x] Unit tests for Markdown serializer
- [x] Unit tests for relationship parsing/rendering
- [x] Unit tests for wiki-link resolution
- [x] Unit tests for bulk folder operations
- [ ] Sort array values for deterministic output (optional enhancement)
- [ ] Markdown template design documentation (implicit in code)

**Dependencies:** Phase 1, Phase 4 (for Flat YAML) complete

---

### Phase 6: Command-Line Interface
**Duration:** 1-2 weeks  
**Goals:**
- Create user-friendly CLI
- Support common operations
- Provide help and documentation

**Deliverables:**
- [x] /ppl/cli.py module using Click
- [x] `ppl import-contacts` command (folder to graph, multiple formats)
- [x] `ppl export-contacts` command (graph to folder, multiple formats)
- [x] `ppl list-contacts` command (list all contacts)
- [x] `ppl search` command (search contacts by name, email, org)
- [x] `ppl convert` command (convert between formats via graph)
- [x] Help documentation for all commands
- [x] Error handling and user-friendly messages
- [x] CLI integration tests
- [x] --verbose flag for detailed output
- [x] --force flag for export to override smart detection
- [x] --graph-format option for JSON/GraphML selection
- [x] Import/export statistics (added, updated, skipped / written, skipped)
- [ ] `ppl show <uid>` command (display single contact)
- [ ] `ppl filter` command (run filter pipeline on-demand)
- [ ] `ppl check-consistency` command (run consistency checks)

**Dependencies:** Phases 2, 3 complete

---

### Phase 6A: Consistency Service
**Duration:** 1 week  
**Goals:**
- Detect inconsistencies across data representations
- Generate detailed consistency reports
- Lay foundation for future repair capabilities

**Deliverables:**
- [ ] /ppl/services/ directory structure
- [ ] /ppl/services/consistency.py module
- [ ] ConsistencyService class
- [ ] Inconsistency dataclass with type, source, target, details
- [ ] ConsistencyReport dataclass with aggregated results
- [ ] check_graph_vcf_consistency() - compare graph with VCF folder
- [ ] check_graph_markdown_consistency() - compare graph with Markdown folder
- [ ] check_front_matter_content_consistency() - validate YAML vs content
- [ ] check_all_representations() - comprehensive cross-check
- [ ] generate_report() - human-readable consistency report
- [ ] Inconsistency detection: missing, outdated, conflict, orphaned
- [ ] REV timestamp comparison logic
- [ ] RELATED property validation across representations
- [ ] CLI integration: `ppl check-consistency` command
- [ ] Unit tests for ConsistencyService
- [ ] Integration tests with sample inconsistent data
- [ ] Documentation for consistency checking workflow

**Dependencies:** Phases 2, 4, 5 complete

---

### Phase 7: Testing and Documentation
**Duration:** 1 week  
**Goals:**
- Comprehensive test coverage
- Documentation for users and developers
- Examples and tutorials

**Deliverables:**
- [ ] Test coverage > 80%
- [ ] Integration test suite
- [ ] Sample vCard files for testing
- [ ] README with installation and usage
- [ ] API documentation
- [ ] Tutorial: Basic workflow
- [ ] Tutorial: Working with relationships
- [ ] Tutorial: Extending filters

**Dependencies:** All previous phases

---

## Task Breakdown

### Immediate Tasks (Week 1)
1. Set up /ppl/models directory structure
2. Add dependencies to pyproject.toml
3. Implement Contact class
4. Implement Relationship class
5. Set up NetworkX graph manager
6. Write unit tests for models

### Near-term Tasks (Weeks 2-3)
1. Implement vCard parser using vobject
2. Implement vCard generator
3. Add REV comparison logic
4. Implement bulk import functionality
5. Implement bulk export functionality
6. Write integration tests for vCard cycle

### Medium-term Tasks (Weeks 4-6)
1. Create filter pipeline framework
2. Implement UID filter
3. Add YAML serializer
4. Add Markdown serializer
5. Write tests for all serializers

### Long-term Tasks (Weeks 7-8)
1. Build CLI with Click
2. Implement all CLI commands
3. Write comprehensive documentation
4. Create tutorials and examples
5. Final testing and bug fixes

## Resource Allocation

### Primary Developer
- Data models and graph infrastructure
- vCard import/export
- Filter pipeline
- CLI development

### Testing
- Unit test development alongside features
- Integration tests after each phase
- Manual testing of CLI

### Documentation
- Inline documentation during development
- User documentation after Phase 6
- API documentation throughout

## Risks and Mitigation

### Risk: vCard 4.0 Specification Complexity
**Impact:** High  
**Probability:** Medium  
**Mitigation:** 
- Use vobject library (handles most complexity)
- Start with required fields only
- Add optional fields incrementally
- Reference vCard 4.0 RFC throughout

### Risk: NetworkX Performance with Large Graphs
**Impact:** Medium  
**Probability:** Low  
**Mitigation:**
- Profile performance early
- Test with large datasets (10,000+ contacts)
- Optimize queries if needed
- Document performance characteristics

### Risk: Markdown DOM Parsing Novelty
**Impact:** Low  
**Probability:** Medium  
**Mitigation:**
- Design simple Markdown format
- Implement rendering before parsing
- Use marko-py DOM carefully
- Fall back to simpler parsing if needed

### Risk: Filter Pipeline Complexity
**Impact:** Low  
**Probability:** Low  
**Mitigation:**
- Start with simple priority-based execution
- Add one filter at a time
- Keep filters independent
- Document filter interface clearly

### Risk: Idempotent Operations Edge Cases
**Impact:** Medium  
**Probability:** Medium  
**Mitigation:**
- Extensive testing with repeated operations
- Clear REV timestamp handling
- Document edge cases (equal REV, missing REV)
- Logging for debugging

## Dependencies

### External Libraries
- **networkx** (v2.8+): Graph operations - stable, well-maintained
- **vobject** (v0.9+): vCard parsing - mature library
- **pyyaml** (v6.0+): YAML serialization - standard Python library
- **marko** (v2.0+): Markdown parsing - actively maintained
- **click** (v8.1+): CLI framework - industry standard

### Development Dependencies
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking

### Python Version
- Minimum: Python 3.8
- Target: Python 3.10+
- Rationale: Modern features, good library support

## Milestones

### Milestone 1: Core Foundation (End of Phase 1)
- Data models working
- Graph operations functional
- Can create contacts and relationships in memory

### Milestone 2: vCard Support (End of Phase 2)
- Can import VCF folder
- Can export to VCF folder
- REV-based merging works correctly

### Milestone 3: Data Pipeline (End of Phase 3)
- Filter pipeline operational
- UID assignment working
- Can curate imported data

### Milestone 4: Multiple Formats (End of Phases 4-5)
- YAML import/export working
- Markdown rendering implemented
- All formats idempotent

### Milestone 5: User Interface (End of Phase 6)
- CLI commands all working
- User can perform all operations via CLI
- Help and error messages clear

### Milestone 6: Production Ready (End of Phase 7)
- Tests passing with good coverage
- Documentation complete
- Ready for initial release

## Success Criteria

### Technical Success
- All unit tests passing
- Integration tests demonstrate idempotent operations
- Can import/export 1000+ contacts without errors
- REV-based merging prevents data loss
- Filter pipeline extensible

### User Success
- CLI is intuitive and well-documented
- Can successfully migrate contacts between systems
- Relationships preserved correctly
- Multiple format support useful

### Code Quality
- Test coverage > 80%
- Clean separation of concerns
- Minimal custom code (leverage libraries)
- Well-documented APIs

---

### Phase 7: Contact Curation Features
**Duration:** 2-3 weeks  
**Goals:**
- Implement non-destructive contact merging
- Add smart export with change detection
- Enhance CLI with detailed statistics
- Support incremental curation workflows

**Deliverables:**
- [x] Contact.merge_from() method for intelligent data merging
- [x] ContactGraph.merge_contact() with REV checking and statistics
- [x] should_export_vcard() for change detection
- [x] should_export_markdown() for change detection
- [x] Updated bulk_export functions returning (written, skipped) statistics
- [x] Enhanced import-contacts with merge logic and statistics
- [x] Enhanced export-contacts with smart export and --force flag
- [x] Updated convert command with merge logic
- [x] --verbose flag implementation across all commands
- [x] Comprehensive curation workflow documentation (CurationWorkflow.md)
- [x] 14 unit tests for Contact.merge_from()
- [x] 9 unit tests for ContactGraph.merge_contact()
- [x] 13 unit tests for export change detection
- [x] 6 integration tests for complete curation workflows

**Status:** ✅ Complete

**Dependencies:** Phases 1-6 complete

---

### Phase 8: JSON Graph Format Support
**Duration:** 1 week  
**Goals:**
- Add JSON export/import for graph data
- Enable integration with graph visualization tools
- Support graphology JSON schema
- Auto-detect format from file extension

**Deliverables:**
- [x] ContactGraph._save_json() method using graphology schema
- [x] ContactGraph._load_json() method
- [x] Updated save() method with format parameter and auto-detection
- [x] Updated load() method with format parameter and auto-detection
- [x] Format auto-detection from file extension (.json vs .graphml)
- [x] --graph-format option added to all CLI commands
- [x] JSON schema compliance (attributes, options, nodes, edges)
- [x] Human-readable JSON output with indentation
- [x] Preservation of all contact data in JSON format
- [x] Preservation of all relationship data in JSON format
- [x] 8 unit tests for JSON format operations
- [x] 5 integration tests for JSON workflows

**Status:** ✅ Complete

**Dependencies:** Phase 1 complete

---

## Current Status

### Implementation Summary
All 8 phases have been successfully completed:
1. ✅ Core Data Models and Graph Infrastructure
2. ✅ vCard Import/Export with RELATED Properties
3. ✅ Filter Pipeline and Models
4. ✅ YAML Serialization
5. ✅ Markdown Rendering and Parsing
6. ✅ CLI Interface
7. ✅ Contact Curation Features
8. ✅ JSON Graph Format Support

### Test Coverage
- **Total Tests:** 167 passing
  - 87 original tests
  - 14 contact merge tests
  - 9 graph merge tests
  - 13 export change detection tests
  - 6 curation workflow tests
  - 8 JSON format tests
  - 5 JSON integration tests
  - 25 additional unit/integration tests

### Features Implemented
1. ✅ Graph-based relationship modeling with NetworkX
2. ✅ Multi-format support (vCard 4.0, YAML, Markdown, JSON)
3. ✅ Non-destructive contact merging with REV timestamps
4. ✅ Smart export with change detection
5. ✅ Intelligent filter pipeline (UID, gender inference)
6. ✅ Comprehensive CLI with 5 commands
7. ✅ Wiki-style links in Markdown
8. ✅ Bulk operations for all formats
9. ✅ Import/export statistics and verbose output
10. ✅ JSON graph format for visualization tools

### Remaining Items
From original plan:
- [ ] Consistency service (Phase 6A) - not yet implemented
- [ ] `ppl show <uid>` command - not yet implemented
- [ ] `ppl filter` command for on-demand pipeline execution - not yet implemented
- [ ] `ppl check-consistency` command - not yet implemented
- [ ] Full gender filter wiki-link dereferencing - partially implemented
- [ ] Database backend for large datasets - future enhancement
- [ ] GUI interface - future enhancement

### Documentation Status
- [x] README.md with comprehensive examples
- [x] CurationPlan.md with implementation phases
- [x] CurationWorkflow.md user guide
- [x] UserStories.md updated with completed items
- [x] Implementation.md updated with all phases
- [x] Architecture.md documenting design decisions
- [x] Inline code documentation and docstrings

