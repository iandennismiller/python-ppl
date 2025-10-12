# Contact Curation Workflow Guide

## Overview

The contact curation feature allows you to manage and refine contact information over time without losing existing data. This guide explains how to use the curation workflow effectively.

## Key Concepts

### 1. Non-Destructive Merging

When you import contact information, the system intelligently merges new data with existing data:

- **Missing fields are not deletions**: If you import a contact with only an email address, it won't delete the phone number that was already in the graph
- **New fields are added**: If you import new information (like a title or organization), it will be added to the existing contact
- **List fields are merged**: Email addresses, phone numbers, and other list fields accumulate unique values

### 2. REV Timestamps

The REV field (revision timestamp) controls which data takes precedence when both the graph and incoming contact have values for the same field:

- Newer REV wins conflicts
- If REV timestamps are equal, data is merged
- If no REV exists, data is merged

### 3. Smart Export

Export operations only write files when data has actually changed:

- Reduces unnecessary file system writes
- Minimizes file-change events that other tools might monitor
- Can be overridden with the `--force` flag

## Common Workflows

### Workflow 1: Incremental Contact Curation

**Scenario**: You're building a contact database and adding information as you discover it.

```bash
# Day 1: Import initial contacts with basic info
ppl import-contacts contacts-basic/ contacts.graphml --format vcard

# Day 2: Add email addresses for some contacts
# Create new vCard files with just FN, UID, and EMAIL
ppl import-contacts contacts-emails/ contacts.graphml --format vcard

# Day 3: Add phone numbers
ppl import-contacts contacts-phones/ contacts.graphml --format vcard

# Export final result
ppl export-contacts contacts.graphml output/ --format vcard
```

**What happens**:
- Each import merges data into the graph
- Missing fields in new imports don't delete existing data
- Final export contains all accumulated information

### Workflow 2: Collaborative Editing

**Scenario**: Multiple people maintain the same contact database.

```bash
# Person A exports to markdown for editing
ppl export-contacts contacts.graphml alice-workspace/ --format markdown

# Person A edits markdown files, adding notes and categories

# Person A imports changes back
ppl import-contacts alice-workspace/ contacts.graphml --format markdown

# Person B exports to vCard for mobile sync
ppl export-contacts contacts.graphml bob-workspace/ --format vcard

# Person B updates phone numbers in vCard files

# Person B imports changes back
ppl import-contacts bob-workspace/ contacts.graphml --format vcard

# Both sets of changes are merged in the graph
ppl export-contacts contacts.graphml final-output/ --format vcard
```

**What happens**:
- Each person's changes are merged into the graph
- REV timestamps prevent conflicts
- No data is lost from either person's work

### Workflow 3: Periodic Sync with External Systems

**Scenario**: You sync contacts with external systems that provide partial updates.

```bash
# Initial export to sync folder
ppl export-contacts contacts.graphml sync-folder/ --format vcard

# External system updates some files (only changes REV for modified contacts)

# Re-import (only newer contacts are updated)
ppl import-contacts sync-folder/ contacts.graphml --format vcard --verbose
# Output: Added: 0, Updated: 5, Skipped: 45

# Re-export (only changed contacts are written)
ppl export-contacts contacts.graphml sync-folder/ --format vcard --verbose
# Output: Written: 3, Skipped: 47
```

**What happens**:
- Import skips contacts where external file is older
- Export skips files that haven't changed
- Minimal file system operations

### Workflow 4: Format Conversion with Preservation

**Scenario**: Convert between formats while preserving all data.

```bash
# Convert from vCard to Markdown, preserving all fields
ppl convert vcards/ vcard contacts.graphml markdown/ markdown --verbose

# Edit markdown files, adding notes

# Convert back to vCard
ppl convert markdown/ markdown contacts.graphml vcards-updated/ vcard --verbose
```

**What happens**:
- All vCard fields are preserved in markdown front matter
- Edits to markdown are merged on conversion
- Round-trip conversion preserves data

## Understanding Import Statistics

When you import contacts, the output shows what happened:

```
Imported 50 contacts to contacts.graphml (added: 10, updated: 35, skipped: 5)
```

- **Added**: New contacts not previously in the graph
- **Updated**: Existing contacts that had newer or additional information
- **Skipped**: Contacts where incoming data was older than graph data

### Verbose Output

Use `--verbose` to see detailed information:

```bash
ppl import-contacts contacts/ graph.graphml --format vcard --verbose
```

Output:
```
Importing vcard files from contacts/...
Loading existing graph from graph.graphml...
Added: 5, Updated: 12, Skipped: 3
Graph saved to graph.graphml
Total contacts in graph: 20
```

## Understanding Export Statistics

When you export contacts, the output shows what was written:

```
Exported to output/ (written: 15, skipped: 35)
```

- **Written**: Files that were created or updated because data changed
- **Skipped**: Files that already existed with identical data

### Force Export

Use `--force` to write all files regardless of changes:

```bash
ppl export-contacts graph.graphml output/ --format vcard --force
```

This is useful when:
- You want to ensure all files are present
- You've manually deleted some output files
- You're troubleshooting export issues

## Best Practices

### 1. Always Use REV Timestamps

When creating or editing contacts manually, always include a REV field:

```yaml
---
FN: John Smith
UID: john-uid
REV: 2024-10-12T15:30:00Z
EMAIL:
  - john@example.com
---
```

This ensures proper conflict resolution when merging.

### 2. Use UID for Identity

Always ensure contacts have a UID. The import pipeline will generate one if missing, but it's better to manage UIDs explicitly for contacts you track across systems.

### 3. Incremental Updates Are Safe

Don't worry about providing incomplete data:

```bash
# This is safe - won't delete existing phone numbers
echo "BEGIN:VCARD
VERSION:4.0
FN:Alice Johnson
UID:alice-uid
EMAIL:alice@newdomain.com
REV:2024-10-12T16:00:00Z
END:VCARD" > alice.vcf

ppl import-contacts . graph.graphml --format vcard
```

### 4. Check What Changed

Use verbose mode to see what the system did:

```bash
ppl import-contacts updates/ graph.graphml --verbose
ppl export-contacts graph.graphml output/ --verbose
```

### 5. Leverage Format Strengths

- **vCard**: Best for mobile sync, email clients
- **Markdown**: Best for human editing, notes, wiki-style relationships
- **YAML**: Best for scripting, data processing

## Troubleshooting

### Problem: Import Says "Skipped" But I Want to Update

**Cause**: Incoming contact has older REV than graph

**Solution**: Update the REV timestamp in your source file to be newer:

```yaml
REV: 2024-10-12T18:00:00Z  # Make this newer than existing
```

### Problem: Export Says "Skipped" But File Doesn't Exist

**Cause**: The file path might be wrong or permission issues

**Solution**: Use `--force` to write all files:

```bash
ppl export-contacts graph.graphml output/ --force
```

### Problem: Data Got Deleted

**Cause**: This shouldn't happen with the curation system, but check:

1. Was REV on incoming contact newer?
2. Did you manually edit the graph file?

**Solution**: The graph file is the source of truth. If data is in the graph, it will be exported:

```bash
# Check what's in the graph
ppl list-contacts graph.graphml

# Force export to recreate all files
ppl export-contacts graph.graphml output/ --force
```

### Problem: Too Many Files Being Written

**Cause**: REV timestamps might be changing unnecessarily

**Solution**: 
- Ensure REV only changes when content actually changes
- Don't auto-generate REV on every export
- Use the same REV for identical content

## Advanced Usage

### Batch Operations with Scripts

```bash
#!/bin/bash
# Process multiple import folders

for folder in imports/*; do
  echo "Processing $folder..."
  ppl import-contacts "$folder" contacts.graphml --format vcard --verbose
done

# Export final result
ppl export-contacts contacts.graphml final/ --format markdown --verbose
```

### Filtering During Import

The import pipeline applies filters automatically:

- **UID Filter**: Generates UIDs for contacts missing them
- **Gender Filter**: Infers gender from relationship terms (if applicable)

These run automatically and don't require configuration.

### Monitoring Changes

Track what changes over time:

```bash
# Before
ppl list-contacts contacts.graphml > before.txt

# Import updates
ppl import-contacts updates/ contacts.graphml

# After
ppl list-contacts contacts.graphml > after.txt

# See what changed
diff before.txt after.txt
```

## Example: Complete Curation Session

```bash
# 1. Start with initial vCard import
ppl import-contacts vcards-initial/ contacts.graphml --format vcard --verbose
# Output: Added: 50, Updated: 0, Skipped: 0

# 2. Export to markdown for editing
ppl export-contacts contacts.graphml markdown-workspace/ --format markdown
# Output: Written: 50, Skipped: 0

# 3. Edit markdown files (add notes, fix names, etc.)
# ... manual editing ...

# 4. Import changes back
ppl import-contacts markdown-workspace/ contacts.graphml --format markdown --verbose
# Output: Added: 0, Updated: 23, Skipped: 27

# 5. Export to vCard for mobile
ppl export-contacts contacts.graphml vcards-updated/ --format vcard --verbose
# Output: Written: 23, Skipped: 27

# 6. Verify changes
ppl list-contacts contacts.graphml
```

## Summary

The contact curation workflow is designed for:
- **Incremental refinement**: Add information as you discover it
- **Collaborative editing**: Multiple people can work on the same data
- **Non-destructive updates**: Missing fields don't mean deletion
- **Efficient operations**: Only writes files when necessary
- **Format flexibility**: Work in the format that suits your task

Key commands:
- `ppl import-contacts`: Merge new data into graph
- `ppl export-contacts`: Write graph to files (with change detection)
- `ppl convert`: Transform between formats
- `ppl list-contacts`: View what's in the graph

Use `--verbose` to understand what's happening and `--force` to override smart behaviors when needed.
