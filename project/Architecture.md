# Architecture Design

## System Overview
PPL uses a graph-based architecture where contacts are nodes and relationships are edges in a NetworkX graph. The graph serves as the single source of truth, with multiple serialization formats (vCard, YAML, Markdown) acting as different views of the same data. The system emphasizes idempotent operations and timestamp-based conflict resolution for reliable data synchronization.

## Design Principles

1. **Graph as Source of Truth**: The NetworkX graph is the authoritative data store during runtime
2. **Standards Compliance**: Full vCard 4.0 compliance for interoperability
3. **Idempotent Operations**: All import/export operations can be safely repeated
4. **Timestamp-based Merging**: Use REV field to intelligently merge data
5. **Separation of Concerns**: Clear boundaries between models, serializers, and filters
6. **Leverage Existing Libraries**: Minimize custom code by using well-tested libraries
7. **Extensible Architecture**: Filter pipeline and serializer pattern support future expansion
8. **Gender Neutrality**: Relationships are gender-neutral with optional gender rendering

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
- REV field prevents overwriting newer data with older data
- UID ensures unique identification even across systems
- Idempotent operations allow safe retries

### Error Handling
- Invalid VCF files logged but don't stop batch import
- Filter failures logged but don't crash pipeline
- Graceful degradation when optional fields missing

### Recovery
- File-based storage allows easy backup/restore
- Graph can be rebuilt from VCF folder at any time
- No data loss on crashes (files remain on disk)

## Design Trade-offs

### NetworkX vs Custom Graph
**Decision**: Use NetworkX
**Rationale**: Well-tested, efficient, rich feature set
**Trade-off**: Dependency on external library, but reduces bug surface area

### File-based vs Database Storage
**Decision**: File-based (VCF files)
**Rationale**: Interoperability, simplicity, no server needed
**Trade-off**: Less efficient for very large datasets, but suitable for target use case

### Multiple Serialization Formats
**Decision**: Support vCard, YAML, and Markdown
**Rationale**: Different formats for different use cases (interop, programmatic, human)
**Trade-off**: More code to maintain, but provides flexibility

### Gender-neutral Relationships
**Decision**: Separate gender from relationship type
**Rationale**: More inclusive, more accurate modeling
**Trade-off**: May require more complex rendering logic

### Filter Pipeline
**Decision**: Extensible filter architecture
**Rationale**: Future-proof for data curation needs
**Trade-off**: More complex than simple validation, but provides flexibility

### CLI-first Approach
**Decision**: Start with CLI using Click
**Rationale**: Simple to implement, sufficient for power users
**Trade-off**: Not beginner-friendly, but establishes API for future GUI
