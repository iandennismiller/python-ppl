# Next Steps - Future Enhancements

## Overview

This document outlines the remaining features and enhancements identified during the planning document review. All core functionality has been implemented (8 phases complete, 167 tests passing), but several valuable features remain for future development.

## Priority: High

### 1. Consistency Service (Phase 6A)

**Status:** Not Implemented  
**Estimated Effort:** 2-3 weeks  
**User Story:** Story 10

#### Description
Implement a comprehensive consistency checking service that detects inconsistencies across multiple data representations (graph, VCF files, Markdown files, YAML front matter).

#### Components Needed

1. **ConsistencyService Class**
   - `check_graph_vcf_consistency()` - Compare graph with VCF folder
   - `check_graph_markdown_consistency()` - Compare graph with Markdown folder
   - `check_front_matter_content_consistency()` - Validate YAML vs content
   - `check_all_representations()` - Comprehensive cross-check
   - `generate_report()` - Human-readable consistency report

2. **Inconsistency Detection Types**
   - **Missing**: Contact exists in graph but not in files (or vice versa)
   - **Outdated**: REV timestamp mismatches between representations
   - **Conflict**: Same property with different values across representations
   - **Orphaned**: Files without corresponding graph nodes

3. **CLI Command**
   - `ppl check-consistency` command with options:
     - `--graph-file` - Path to graph file
     - `--vcard-folder` - Path to vCard folder (optional)
     - `--markdown-folder` - Path to Markdown folder (optional)
     - `--yaml-folder` - Path to YAML folder (optional)
     - `--format` - Output format (text, json, yaml)
     - `--verbose` - Detailed output

#### Example Output
```
Consistency Check Report
========================

Status: INCONSISTENT (5 issues found)

Issues:
1. [MISSING] Contact "John Smith" (uid-123) exists in graph but not in VCF folder
2. [OUTDATED] Contact "Alice" has REV 2024-01-15 in VCF but 2024-01-14 in graph
3. [CONFLICT] Email mismatch for "Bob": graph has bob@work.com, markdown has bob@personal.com
4. [ORPHANED] File "Unknown.vcf" exists but no matching contact in graph
5. [INCONSISTENT] Related section in markdown has "friend [[Carol]]" but no RELATED;TYPE=friend in front matter

Recommendations:
- Re-import VCF folder to add missing contacts
- Export graph to VCF folder with --force to update outdated files
- Review conflict for "Bob" - graph has newer REV
```

#### Testing Requirements
- Test missing contact detection
- Test REV timestamp comparison
- Test conflict detection for various fields
- Test orphaned file detection
- Test front matter vs content consistency
- Integration test with mixed inconsistencies
- Test report generation in multiple formats

#### Dependencies
- Phases 1-6 complete ✅
- Access to graph and file folders

---

### 2. Enhanced CLI Commands

**Status:** Partially Implemented  
**Estimated Effort:** 1 week

#### 2.1 `ppl show <uid>` Command

**Purpose:** Display detailed information about a single contact

**Features:**
- Display all contact fields in readable format
- Show relationships with types
- Option to show raw vCard/YAML/JSON representation
- Highlight recent changes (if REV is recent)

**Example:**
```bash
ppl show contacts.graphml alice-uid

# Output:
Alice Johnson (alice-uid)
========================
Email: alice@example.com, alice@work.com
Phone: +1-555-0001
Title: Senior Engineer
Organization: Tech Corp

Relationships:
- friend → Bob Smith (bob-uid)
- colleague → Charlie Davis (charlie-uid)
- parent → Diana Johnson (diana-uid)

Last Updated: 2024-10-12 15:30:00
```

**Acceptance Criteria:**
- [ ] Display contact with all fields formatted
- [ ] Show relationships with target contact names
- [ ] Support --format option (text, vcard, yaml, json, markdown)
- [ ] Support --graph-format option for graph file
- [ ] Error handling for non-existent UID
- [ ] Unit tests and integration tests

---

#### 2.2 `ppl filter <uid>` Command

**Purpose:** Run filter pipeline on-demand for specific contacts

**Features:**
- Execute curation pipeline on single contact
- Execute curation pipeline on all contacts
- Show before/after comparison
- Dry-run mode to preview changes

**Example:**
```bash
# Run filters on single contact
ppl filter contacts.graphml alice-uid

# Run filters on all contacts
ppl filter contacts.graphml --all

# Dry run to preview changes
ppl filter contacts.graphml --all --dry-run
```

**Acceptance Criteria:**
- [ ] Execute curation_pipeline on specified contact(s)
- [ ] Support --all flag for batch processing
- [ ] Support --dry-run flag to preview without saving
- [ ] Display changes made by each filter
- [ ] Update graph with filtered results (unless dry-run)
- [ ] Unit tests and integration tests

---

## Priority: Medium

### 3. Full Gender Filter Wiki-Link Dereferencing

**Status:** Partially Implemented  
**Estimated Effort:** 1 week  
**User Story:** Story 8A (partial completion)

#### Description
Complete the gender filter implementation to fully dereference wiki-style links and update target contact markdown files with inferred GENDER property.

#### Current State
- ✅ Gender term detection (mother, father, sister, etc.)
- ✅ Gender inference from terms (M/F)
- ✅ Logging of inferences
- ❌ Wiki-link dereferencing to find target contact
- ❌ Updating target contact's markdown front matter

#### Work Required

1. **Wiki-Link Resolution in Filter**
   - Parse relationship markdown to extract [[Contact Name]] links
   - Resolve links to find target contact in graph or folder
   - Get target contact's UID

2. **Target Contact Update**
   - Load target contact from graph
   - Check if GENDER property already set
   - If not set, add inferred GENDER
   - Update contact in graph
   - Mark for export (ensure markdown file gets updated)

3. **Integration with Export**
   - When exporting markdown, include GENDER in front matter
   - Ensure updated contacts are written to disk

#### Testing Requirements
- Test wiki-link resolution for gender inference
- Test target contact GENDER updates
- Test markdown front matter includes GENDER
- Test gender inference doesn't override existing GENDER
- Integration test showing complete flow

#### Example Workflow
```markdown
# Alice.md
---
FN: Alice Johnson
UID: alice-uid
---
## Related
- mother [[Carol Johnson]]

# After filter runs:
# Carol Johnson.md updated with GENDER: F in front matter
```

---

### 4. Additional CLI Enhancements

**Status:** Not Implemented  
**Estimated Effort:** 1-2 weeks

#### 4.1 Graph Statistics Command

**Purpose:** Display statistics about the contact graph

```bash
ppl stats contacts.graphml

# Output:
Graph Statistics
================
Total Contacts: 150
Total Relationships: 287

Relationship Types:
- friend: 89
- colleague: 67
- parent: 45
- child: 45
- spouse: 23
- sibling: 18

Contact Fields:
- With Email: 145 (96.7%)
- With Phone: 132 (88.0%)
- With Address: 89 (59.3%)
- With Organization: 112 (74.7%)

REV Timestamps:
- Oldest: 2023-01-15
- Newest: 2024-10-12
- Average Age: 6 months
```

**Acceptance Criteria:**
- [ ] Count contacts and relationships
- [ ] Breakdown by relationship type
- [ ] Field population statistics
- [ ] REV timestamp analysis
- [ ] Support --graph-format option

---

#### 4.2 Relationship Visualization Command

**Purpose:** Export graph visualization data

```bash
# Export to DOT format for Graphviz
ppl visualize contacts.graphml --format dot --output graph.dot

# Generate PNG image
ppl visualize contacts.graphml --format png --output graph.png

# Export to D3.js JSON
ppl visualize contacts.graphml --format d3 --output graph.json
```

**Acceptance Criteria:**
- [ ] Export to DOT format
- [ ] Export to D3.js format
- [ ] Support filtering (e.g., only certain relationship types)
- [ ] Color coding by relationship type
- [ ] Node size by connection count

---

### 5. Performance Optimizations

**Status:** Not Implemented  
**Estimated Effort:** 1-2 weeks

#### Description
Optimize performance for large contact databases (>10,000 contacts).

#### Enhancements Needed

1. **Lazy Loading**
   - Don't load all contacts into memory at once
   - Load contacts on-demand when queried
   - Cache frequently accessed contacts

2. **Indexed Search**
   - Build indexes for common search fields (FN, email, UID)
   - Use indexes for faster search operations
   - Rebuild indexes when graph changes

3. **Batch Operations**
   - Process imports in batches
   - Parallelize independent operations
   - Progress indicators for long operations

4. **Memory Optimization**
   - Stream large files instead of loading entirely
   - Release memory after processing each contact
   - Configurable batch sizes

#### Testing Requirements
- Benchmark tests with 1,000, 10,000, 100,000 contacts
- Memory usage profiling
- Performance regression tests
- Stress tests for concurrent operations

---

## Priority: Low

### 6. Database Backend

**Status:** Not Implemented  
**Estimated Effort:** 3-4 weeks

#### Description
Add optional database backend for large-scale deployments using SQLite or PostgreSQL.

#### Features
- Store contacts and relationships in relational database
- Keep NetworkX graph as in-memory cache
- Sync between database and graph
- Support for concurrent access
- Migration utilities from file-based storage

#### Benefits
- Better performance for large datasets
- Multi-user access
- Transaction support
- Query optimization
- Backup and recovery

---

### 7. GUI Interface

**Status:** Not Implemented  
**Estimated Effort:** 4-6 weeks

#### Description
Web-based GUI for contact management and visualization.

#### Features
- Browse and search contacts
- Visualize relationship network
- Edit contact information
- Import/export operations
- Consistency checking UI
- Real-time updates

#### Technology Stack
- Backend: FastAPI or Flask
- Frontend: React or Vue.js
- Graph Visualization: Cytoscape.js or Sigma.js
- Forms: React Hook Form or similar

---

### 8. Advanced Filters

**Status:** Not Implemented  
**Estimated Effort:** Ongoing (1 week per filter)

#### Potential Filters

1. **EmailValidationFilter** (Priority 20)
   - Validate email format
   - Check for common typos
   - Flag suspicious emails

2. **PhoneNormalizationFilter** (Priority 30)
   - Normalize phone numbers to E.164 format
   - Add country codes
   - Remove formatting inconsistencies

3. **DuplicateDetectionFilter** (Priority 40)
   - Find potential duplicate contacts
   - Compare by name similarity, email, phone
   - Suggest merges

4. **DataEnrichmentFilter** (Priority 60)
   - Look up additional info from external sources
   - Add missing fields
   - Update outdated information

5. **RelationshipInferenceFilter** (Priority 70)
   - Infer relationships from shared attributes
   - Same organization → colleague
   - Same address → co-resident
   - Email domain patterns

---

### 9. Plugin System

**Status:** Not Implemented  
**Estimated Effort:** 2-3 weeks

#### Description
Allow third-party filter and serializer plugins.

#### Features
- Plugin discovery mechanism
- Plugin registration API
- Plugin configuration
- Plugin documentation standard
- Sample plugins as examples

---

### 10. Automated Conflict Resolution

**Status:** Not Implemented  
**Estimated Effort:** 2 weeks

#### Description
Extend consistency service with automated repair capabilities.

#### Features
- Resolution strategies:
  - "trust_graph" - Graph is source of truth
  - "trust_files" - Files are source of truth
  - "newest_rev" - Newest REV wins
  - "manual" - Ask user for each conflict
- Configurable strategies per inconsistency type
- Dry-run mode to preview repairs
- Backup before repair
- Detailed repair logs

---

## Recommended Implementation Order

Based on user value and technical dependencies:

1. **Next Sprint (High Priority)**
   - Consistency Service (Phase 6A)
   - `ppl show` command
   - `ppl check-consistency` command

2. **Following Sprint (Medium Priority)**
   - Full gender filter wiki-link dereferencing
   - `ppl filter` command
   - Graph statistics command
   - Performance benchmarking

3. **Future Sprints (Lower Priority)**
   - Performance optimizations (as needed)
   - Additional filters (as needed)
   - Plugin system
   - Automated conflict resolution
   - Database backend
   - GUI interface
   - Visualization export

## Success Criteria

Each feature should meet these criteria before being considered complete:

### Technical Requirements
- [ ] Comprehensive unit tests
- [ ] Integration tests demonstrating user workflows
- [ ] Test coverage >80% for new code
- [ ] All existing tests still passing
- [ ] No performance regressions
- [ ] Proper error handling

### Documentation Requirements
- [ ] User story with acceptance criteria
- [ ] Updated CLI help documentation
- [ ] Usage examples in README or guides
- [ ] API documentation in code
- [ ] Integration test demonstrating feature

### User Experience Requirements
- [ ] Intuitive command syntax
- [ ] Clear error messages
- [ ] Progress indicators for long operations
- [ ] Verbose mode for debugging
- [ ] Dry-run mode where appropriate

## Notes

### Why These Features Matter

**Consistency Service** - Critical for maintaining data integrity across multiple representations. Users need confidence that graph, VCF, markdown, and YAML are all in sync.

**`ppl show` Command** - Quick way to inspect individual contacts without processing entire graph. Essential for debugging and verification.

**`ppl filter` Command** - Allows users to run curation filters on-demand, giving them control over when data enrichment happens.

**Performance Optimizations** - Current implementation works well for small-to-medium datasets (<1,000 contacts) but needs optimization for enterprise scale.

**Advanced Filters** - Community has requested email validation, phone normalization, and duplicate detection. These add significant value for data quality.

**Database Backend** - For organizations with >10,000 contacts or multi-user scenarios, file-based storage becomes limiting.

**GUI** - While CLI is powerful, many users prefer graphical interfaces for browsing and editing contacts.

### Technical Debt

Current implementation has minimal technical debt:
- ✅ Well-tested with 167 passing tests
- ✅ Clean architecture with separation of concerns
- ✅ Type hints throughout
- ✅ Comprehensive documentation
- ⚠️ Some performance optimizations needed for large datasets
- ⚠️ Gender filter partially complete (wiki-link dereferencing incomplete)

### Breaking Changes

None of the planned features should require breaking changes:
- All are additive (new commands, new features)
- Existing APIs remain stable
- File formats remain compatible
- Graph format supports both GraphML and JSON

### Community Feedback Needed

Before implementing major features, gather feedback on:
1. **Consistency Service** - What resolution strategies are most important?
2. **Database Backend** - SQLite sufficient or need PostgreSQL/MySQL?
3. **GUI** - Web-based or desktop? Must-have features?
4. **Filters** - Which filters provide most value?
5. **Performance** - What dataset sizes are users working with?

## Conclusion

The PPL system has a solid foundation with 8 completed phases. The roadmap above provides clear next steps organized by priority. The consistency service and enhanced CLI commands (`show`, `filter`, `check-consistency`) should be prioritized as they provide immediate user value and complete the core feature set.

With these additions, PPL will be a comprehensive, production-ready contact management system suitable for both individual users and organizations.
