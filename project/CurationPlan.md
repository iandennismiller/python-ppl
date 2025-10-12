# Contact Curation Implementation Plan

## Overview

This document outlines the implementation plan for extending the CLI to handle incremental contact curation use cases. Users will be able to curate information over time, with typically one or two fields changing at once, while preserving existing data and avoiding unnecessary file system writes.

## Problem Statement

Users need to:
1. Import contacts from various formats (vcard, yaml, markdown)
2. Compare incoming information to the reference graph
3. Determine if anything has changed
4. Determine if changes are newer than what's in the graph (using REV timestamps)
5. Update the graph with new information only if newer
6. Export to filesystem only when information has actually changed
7. **Never destroy information** - missing fields are not interpreted as deletion requests
8. Import new fields that didn't exist before

## Key Principles

### 1. Non-Destructive Merging
- **Missing fields do not mean deletion**: If an incoming contact lacks a field that exists in the graph, keep the graph's value
- **New fields are imported**: If an incoming contact has a field the graph lacks, add it to the graph
- **REV-based conflict resolution**: When both have a value for the same field, use REV timestamp to decide which to keep

### 2. Smart Export
- **Change detection**: Only write files when data has actually changed
- **REV comparison**: Check existing file's REV before overwriting
- **Minimize file events**: Avoid generating unnecessary file-changed events that other processes might watch

### 3. Incremental Updates
- Designed for workflows where users update 1-2 fields at a time
- Preserve all other data during updates
- Support iterative refinement over time

## Implementation Components

### Component 1: Contact Merge Logic

**Location**: `ppl/models/contact.py`

**New Method**: `Contact.merge_from(other: Contact, prefer_newer: bool = True) -> Contact`

**Purpose**: Intelligently merge two contact objects without data loss

**Algorithm**:
```python
def merge_from(self, other: Contact, prefer_newer: bool = True) -> Contact:
    """
    Merge another contact into this one without data loss.
    
    Rules:
    1. If this contact has a value and other doesn't, keep this value
    2. If other has a value and this doesn't, import other's value
    3. If both have values:
       a. If prefer_newer=True, use REV to decide (newer wins)
       b. If prefer_newer=False, keep this contact's value
    4. For list fields (email, tel, etc.), merge unique values
    
    Args:
        other: Contact to merge from
        prefer_newer: Use REV timestamps to resolve conflicts
        
    Returns:
        This contact with merged data
    """
```

**Fields to Handle**:
- Simple fields: fn, n, uid, title, role, note, etc.
- List fields: email, tel, adr, categories, url, etc.
- Complex fields: related, x_properties
- Timestamp: rev (always update to latest)

**Testing Requirements**:
- Test merging with missing fields on both sides
- Test REV-based conflict resolution
- Test list field merging (unique values only)
- Test that merge is non-destructive

### Component 2: Graph-Level Merge

**Location**: `ppl/models/graph.py`

**New Method**: `ContactGraph.merge_contact(contact: Contact) -> Tuple[bool, str]`

**Purpose**: Add or merge a contact into the graph with intelligence

**Algorithm**:
```python
def merge_contact(self, contact: Contact) -> Tuple[bool, str]:
    """
    Intelligently add or merge a contact into the graph.
    
    If contact doesn't exist in graph:
        - Add it as new contact
        - Return (True, "added")
    
    If contact exists in graph:
        - Compare REV timestamps
        - If incoming is newer or equal, merge data
        - Return (True, "updated") if changes made
        - Return (False, "skipped") if incoming is older
    
    Args:
        contact: Contact to add or merge
        
    Returns:
        Tuple of (was_modified, action) where action is "added", "updated", or "skipped"
    """
```

**Testing Requirements**:
- Test adding new contact
- Test merging with newer data
- Test skipping older data
- Test merging with equal REV

### Component 3: Change Detection for Export

**Location**: `ppl/serializers/vcard.py`, `ppl/serializers/markdown.py`, `ppl/serializers/yaml_serializer.py`

**New Functions**: 
- `should_export_vcard(contact: Contact, file_path: str) -> bool`
- `should_export_markdown(contact: Contact, file_path: str) -> bool`
- `should_export_yaml(contact: Contact, file_path: str) -> bool`

**Purpose**: Determine if a file should be written/overwritten

**Algorithm**:
```python
def should_export_vcard(contact: Contact, file_path: str) -> bool:
    """
    Determine if vCard file should be written.
    
    Returns True if:
    - File doesn't exist
    - File exists but contact has newer REV
    - File exists but content differs (REV is same)
    
    Returns False if:
    - File exists with same or newer REV and identical content
    
    Args:
        contact: Contact to potentially export
        file_path: Path where file would be written
        
    Returns:
        True if file should be written, False otherwise
    """
```

**Implementation Notes**:
- Load existing file if it exists
- Compare REV timestamps
- If REV is same, do deep comparison of content
- Use this in bulk_export functions to skip unchanged files

**Testing Requirements**:
- Test with non-existent file (should export)
- Test with older file (should export)
- Test with newer file (should not export)
- Test with same REV but different content (should export)
- Test with same REV and same content (should not export)

### Component 4: Updated bulk_export Functions

**Location**: `ppl/serializers/vcard.py`, `ppl/serializers/markdown.py`

**Modified Functions**:
- `bulk_export(contacts: List[Contact], folder_path: str, force: bool = False) -> Tuple[int, int]`
- `bulk_export_markdown(contacts: List[Contact], folder_path: str, force: bool = False) -> Tuple[int, int]`

**Purpose**: Only write files that have changed

**Changes**:
```python
def bulk_export(contacts: List[Contact], folder_path: str, force: bool = False) -> Tuple[int, int]:
    """
    Export contacts to vCard files, only writing changed files.
    
    Args:
        contacts: List of contacts to export
        folder_path: Folder to export to
        force: If True, write all files regardless of changes
        
    Returns:
        Tuple of (files_written, files_skipped)
    """
    written = 0
    skipped = 0
    
    for contact in contacts:
        file_path = ...  # Calculate file path
        
        if force or should_export_vcard(contact, file_path):
            export_vcard(contact, file_path)
            written += 1
        else:
            skipped += 1
    
    return (written, skipped)
```

**Testing Requirements**:
- Test that unchanged files are skipped
- Test that changed files are written
- Test force flag overrides skip logic
- Test return values are correct

### Component 5: CLI Updates

**Location**: `ppl/cli.py`

**Modified Commands**:

#### import_contacts command
```python
@cli.command()
@click.argument('folder_path', type=click.Path(exists=True))
@click.argument('graph_file', type=click.Path())
@click.option('--format', type=click.Choice(['vcard', 'yaml', 'markdown']), default='vcard')
@click.option('--verbose', is_flag=True)
def import_contacts(folder_path, graph_file, format, verbose):
    """Import contacts with intelligent merging."""
    
    # Load contacts from folder
    contacts = load_contacts_by_format(folder_path, format)
    
    # Load or create graph
    graph = load_or_create_graph(graph_file)
    
    # Merge contacts using new logic
    added = 0
    updated = 0
    skipped = 0
    
    for contact in contacts:
        # Ensure UID exists (apply filters)
        if not contact.uid:
            contact = import_pipeline.run(contact, context)
        
        # Use new merge_contact method
        modified, action = graph.merge_contact(contact)
        
        if action == "added":
            added += 1
        elif action == "updated":
            updated += 1
        else:  # skipped
            skipped += 1
    
    # Save graph
    graph.save(graph_file)
    
    # Report results
    if verbose:
        click.echo(f"Added: {added}, Updated: {updated}, Skipped: {skipped}")
```

#### export_contacts command
```python
@cli.command()
@click.argument('graph_file', type=click.Path(exists=True))
@click.argument('output_folder', type=click.Path())
@click.option('--format', type=click.Choice(['vcard', 'yaml', 'markdown']), default='vcard')
@click.option('--force', is_flag=True, help='Force overwrite all files')
@click.option('--verbose', is_flag=True)
def export_contacts(graph_file, output_folder, format, force, verbose):
    """Export contacts, only writing changed files."""
    
    # Load graph
    graph = ContactGraph()
    graph.load(graph_file)
    contacts = graph.get_all_contacts()
    
    # Export with change detection
    if format == 'vcard':
        written, skipped = vcard.bulk_export(contacts, output_folder, force)
    elif format == 'markdown':
        written, skipped = markdown.bulk_export_markdown(contacts, output_folder, force)
    elif format == 'yaml':
        written, skipped = yaml_serializer.bulk_export(contacts, output_folder, force)
    
    # Report results
    if verbose:
        click.echo(f"Written: {written}, Skipped: {skipped}")
```

**Testing Requirements**:
- Test import with new contacts
- Test import with updated contacts
- Test import with older contacts (should skip)
- Test export skips unchanged files
- Test export --force writes all files

### Component 6: Documentation

**Location**: `project/CurationWorkflow.md`

**Content**: User-facing documentation explaining:
- How to curate contacts over time
- How REV timestamps work
- How to avoid data loss
- Example workflows
- Troubleshooting

## Implementation Order

### Phase 1: Core Merge Logic
1. Implement `Contact.merge_from()` method
2. Add comprehensive unit tests
3. Document behavior with examples

### Phase 2: Graph Integration
1. Implement `ContactGraph.merge_contact()` method
2. Add unit tests
3. Update existing tests that might be affected

### Phase 3: Change Detection
1. Implement `should_export_*()` functions for each format
2. Add unit tests for each format
3. Test edge cases (missing files, corrupted files, etc.)

### Phase 4: Export Updates
1. Modify `bulk_export()` functions to use change detection
2. Update function signatures to return statistics
3. Add integration tests

### Phase 5: CLI Updates
1. Update `import_contacts` command
2. Update `export_contacts` command
3. Add `--force` flag to export command
4. Test CLI end-to-end

### Phase 6: Documentation
1. Create user-facing workflow documentation
2. Add inline code comments
3. Update README if needed

## Testing Strategy

### Unit Tests
- Test each new method in isolation
- Test edge cases and error conditions
- Test with various data combinations

### Integration Tests
- Test complete import → merge → export cycles
- Test with multiple formats (vcard, yaml, markdown)
- Test REV-based resolution across full workflow

### Regression Tests
- Ensure existing functionality still works
- Run full test suite after each phase

## Success Criteria

1. ✅ Users can import contacts without losing existing data
2. ✅ Missing fields in imports don't delete graph data
3. ✅ New fields in imports are added to graph
4. ✅ REV timestamps properly control merge decisions
5. ✅ Exports only write files when data has changed
6. ✅ All existing tests still pass
7. ✅ New functionality has comprehensive test coverage
8. ✅ Documentation explains curation workflow clearly

## Future Enhancements

- Conflict resolution UI for manual merge decisions
- Audit log of all merges and decisions made
- Batch operations for managing large contact sets
- Advanced merge strategies (e.g., field-level priorities)
- Integration with version control systems
