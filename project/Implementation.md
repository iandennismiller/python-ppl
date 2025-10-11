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
- [ ] Contact class with all vCard 4.0 properties (FN, N, UID, REV, EMAIL, TEL, ADR, RELATED, etc.)
- [ ] Related class for vCard 4.0 RELATED property representation
- [ ] Relationship class for internal graph edge representation
- [ ] Mapping between RELATED properties and graph edges
- [ ] Graph manager using NetworkX
- [ ] Basic unit tests for models
- [ ] vCard 4.0 UID and REV field handling

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
- [ ] /ppl/serializers/vcard.py module
- [ ] Parse VCF file to Contact object (all vCard 4.0 properties)
- [ ] Extract RELATED properties and create graph edges
- [ ] Generate VCF file from Contact object
- [ ] Inject RELATED properties from graph edges during export
- [ ] Support all 18 vCard 4.0 RELATED TYPE values
- [ ] Handle multiple TYPE values in single RELATED property
- [ ] REV comparison logic for conflict resolution
- [ ] bulk_import_vcards(folder) function with relationship reconstruction
- [ ] bulk_export_vcards(contacts, folder) function with RELATED projection
- [ ] Smart overwrite logic (only when graph REV is newer)
- [ ] Unit tests for vCard serializer
- [ ] Unit tests for RELATED property handling
- [ ] Integration tests for import/export cycle with relationships

**Dependencies:** Phase 1 complete

---

### Phase 3: Filter Pipeline
**Duration:** 1 week  
**Goals:**
- Create extensible filter framework
- Implement UID assignment filter
- Integrate with import process

**Deliverables:**
- [ ] /ppl/filters/ directory structure
- [ ] Filter pipeline framework
- [ ] Filter registration system (priority-based)
- [ ] UID assignment filter
- [ ] Pipeline trigger points (import, on-demand)
- [ ] Logging for filter actions
- [ ] Unit tests for pipeline
- [ ] Unit tests for UID filter

**Dependencies:** Phase 1 complete

---

### Phase 4: YAML Serialization
**Duration:** 1-2 weeks  
**Goals:**
- Support YAML import/export
- Support flat YAML format
- Ensure idempotent operations

**Deliverables:**
- [ ] /ppl/serializers/yaml_serializer.py module
- [ ] to_yaml(contact) function
- [ ] from_yaml(yaml_str) function
- [ ] to_flat_yaml(contact) function (unnested keys)
- [ ] from_flat_yaml(yaml_str) function
- [ ] YAML bulk import/export
- [ ] Unit tests for YAML serializer
- [ ] Integration tests for YAML idempotency

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
- [ ] /ppl/serializers/markdown.py module
- [ ] YAML front matter support with `---` delimiters
- [ ] vCard 4.0 property serialization in YAML front matter (FN, UID, EMAIL, TEL, etc.)
- [ ] parse_yaml_front_matter(markdown_str) function
- [ ] render_yaml_front_matter(contact) function
- [ ] to_markdown(contact) function with YAML front matter + content
- [ ] Render "Related" heading with unordered list of relationships
- [ ] Format relationships as `- relationship_kind [[Contact Name]]`
- [ ] Support wiki-style links `[[Name]]` for related contacts
- [ ] from_markdown(markdown_str) using marko DOM
- [ ] Parse YAML front matter (precedence over Markdown content)
- [ ] Parse "Related" section (case-insensitive heading detection)
- [ ] Extract relationship tuples `(relationship_kind, object)`
- [ ] Resolve wiki-style links to "Contact Name.md" in folder
- [ ] bulk_import_markdown(folder_path) function
- [ ] bulk_export_markdown(contacts, folder_path) function
- [ ] File naming by Full Name (FN): "{fn}.md"
- [ ] Flat namespace for wiki-link dereferencing
- [ ] Create graph edges from parsed relationships
- [ ] Markdown template design with front matter and "Related" section
- [ ] Unit tests for YAML front matter parsing/rendering
- [ ] Unit tests for Markdown serializer
- [ ] Unit tests for relationship parsing/rendering
- [ ] Unit tests for wiki-link resolution
- [ ] Unit tests for bulk folder operations
- [ ] Sample Markdown outputs for validation with relationships

**Dependencies:** Phase 1, Phase 4 (for Flat YAML) complete

---

### Phase 6: Command-Line Interface
**Duration:** 1-2 weeks  
**Goals:**
- Create user-friendly CLI
- Support common operations
- Provide help and documentation

**Deliverables:**
- [ ] /ppl/cli.py module using Click
- [ ] `ppl import vcf` command (folder of VCFs to graph)
- [ ] `ppl export vcf` command (graph to folder of VCFs)
- [ ] `ppl import markdown` command (folder of .md files to graph)
- [ ] `ppl export markdown` command (graph to folder of .md files)
- [ ] `ppl list` command (list all contacts)
- [ ] `ppl search` command (search contacts)
- [ ] `ppl show <uid>` command (display single contact)
- [ ] `ppl filter` command (run filter pipeline)
- [ ] Help documentation for all commands
- [ ] Error handling and user-friendly messages
- [ ] CLI integration tests

**Dependencies:** Phases 2, 3 complete

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
