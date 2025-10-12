# PPL - Python People Manager

A modern contact management system that models relationships as a graph and supports multiple serialization formats including vCard 4.0, YAML, and Markdown.

## Overview

PPL (Python People Manager) is a command-line tool and Python library for managing contacts and their relationships. Unlike traditional contact managers that treat contacts in isolation, PPL models contacts as a graph with explicit, typed relationships.

### Key Features

- **Graph-based relationship modeling** using NetworkX
- **Multiple serialization formats**: vCard 4.0, YAML, and Markdown
- **vCard 4.0 compliant** with full support for RELATED properties
- **Intelligent merge logic** based on REV timestamps for non-destructive curation
- **Smart export** that only writes changed files to minimize file system operations
- **Extensible filter pipeline** for data validation and curation
- **Wiki-style links** in Markdown format for easy relationship management
- **Command-line interface** for common operations
- **Incremental updates** that preserve existing data when importing partial contacts

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Development Tasks

PPL includes a Makefile for common development tasks:

```bash
# Show all available commands
make help

# Install production dependencies
make install

# Install development dependencies (includes test tools)
make install-dev

# Run all tests
make test

# Run tests with verbose output
make test-verbose

# Run tests with coverage report
make coverage

# Run all quality checks (tests + coverage)
make check

# Clean build artifacts and cache files
make clean

# Build distribution packages
make build
```

## Quick Start

### Contact Curation Workflow

PPL is designed for incremental contact curation - adding and refining information over time without losing data:

```bash
# Import initial contacts
ppl import-contacts contacts/ graph.graphml --format vcard --verbose
# Output: Added: 50, Updated: 0, Skipped: 0

# Later, import additional info (missing fields won't delete existing data)
ppl import-contacts updates/ graph.graphml --format vcard --verbose
# Output: Added: 5, Updated: 23, Skipped: 2

# Export only writes files that changed
ppl export-contacts graph.graphml output/ --format markdown --verbose
# Output: Written: 28, Skipped: 22

# Force export all files if needed
ppl export-contacts graph.graphml output/ --format vcard --force
```

**Key principles:**
- Missing fields in imports don't delete existing graph data
- REV timestamps control which data wins conflicts
- Exports only write files when data has changed
- Use `--verbose` to see what's happening

See [Curation Workflow Guide](project/CurationWorkflow.md) for detailed examples and best practices.

### Using the CLI

All CLI commands now use a graph file to persist contact data:

```bash
# Import contacts from a folder into the graph
python -m ppl.cli import-contacts examples/contacts contacts.graphml --verbose

# List all contacts in the graph
python -m ppl.cli list-contacts contacts.graphml

# Search for contacts in the graph
python -m ppl.cli search contacts.graphml "alice"

# Show detailed information about a specific contact
python -m ppl.cli show contacts.graphml <uid>
python -m ppl.cli show contacts.graphml <uid> --format json

# Run filters on contacts
python -m ppl.cli filter contacts.graphml <uid>  # Filter single contact
python -m ppl.cli filter contacts.graphml --all --dry-run  # Preview changes

# Check consistency between graph and folders
python -m ppl.cli check-consistency contacts.graphml --vcard-folder contacts/
python -m ppl.cli check-consistency contacts.graphml --markdown-folder md/ --format json

# Export contacts from the graph to a folder
python -m ppl.cli export-contacts contacts.graphml output --format markdown

# Convert between formats via graph
python -m ppl.cli convert examples/contacts vcard contacts.graphml output markdown
```

**Graph File**: The graph file (`.graphml` format) is the persistent storage for your contact network. It stores both contacts and their relationships using NetworkX's GraphML format.

### New Commands (Phase 6A)

PPL now includes advanced commands for contact management:

#### `ppl show` - Display Contact Details

Display detailed information about a single contact:

```bash
# Show contact in human-readable text format
ppl show contacts.graphml urn:uuid:alice-uid

# Show as JSON for programmatic access
ppl show contacts.graphml urn:uuid:alice-uid --format json

# Export to different formats
ppl show contacts.graphml urn:uuid:alice-uid --format vcard
ppl show contacts.graphml urn:uuid:alice-uid --format yaml
ppl show contacts.graphml urn:uuid:alice-uid --format markdown
```

#### `ppl filter` - On-Demand Curation

Execute filter pipeline on specific contacts:

```bash
# Run filters on single contact
ppl filter contacts.graphml urn:uuid:alice-uid

# Run filters on all contacts
ppl filter contacts.graphml --all

# Preview changes without saving (dry-run mode)
ppl filter contacts.graphml --all --dry-run

# Verbose output to see filter details
ppl filter contacts.graphml urn:uuid:alice-uid --verbose
```

**Available Filters:**
- `UIDFilter`: Assigns UUIDs to contacts without UIDs
- `GenderFilter`: Infers gender from relationship terms (mother/father/etc.)

#### `ppl check-consistency` - Consistency Checking

Detect inconsistencies across multiple data representations:

```bash
# Check graph against VCF folder
ppl check-consistency contacts.graphml --vcard-folder contacts/

# Check multiple formats
ppl check-consistency contacts.graphml \
  --vcard-folder contacts/ \
  --markdown-folder md/ \
  --verbose

# Output as JSON or YAML
ppl check-consistency contacts.graphml \
  --vcard-folder contacts/ \
  --format json

# Get recommendations for fixing issues
ppl check-consistency contacts.graphml \
  --markdown-folder md/ \
  --verbose
```

**What it checks:**
- Missing contacts (in graph but not in files)
- Orphaned files (in folder but not in graph)
- Outdated REV timestamps between representations
- YAML front matter vs content consistency

### Using the Python API

```python
from ppl.models import Contact, Related, ContactGraph
from ppl.serializers import vcard, yaml_serializer, markdown

# Create a contact
contact = Contact(
    fn="Alice Johnson",
    email=["alice@example.com"],
    tel=["+1-555-0100"],
    org=["Tech Corp"],
    title="Software Engineer"
)

# Add relationships
contact.related.append(
    Related(uri="urn:uuid:bob-uid", type=["friend", "colleague"])
)

# Serialize to vCard
vcard_str = vcard.to_vcard(contact)

# Serialize to YAML
yaml_str = yaml_serializer.to_yaml(contact)

# Serialize to Markdown
md_str = markdown.to_markdown(contact)

# Work with graphs
graph = ContactGraph()
graph.add_contact(contact)

# Save graph to disk
graph.save("contacts.graphml")

# Load graph from disk later
graph2 = ContactGraph()
graph2.load("contacts.graphml")
```

### Graph Persistence

PPL uses NetworkX's GraphML format to persist contact graphs:

```python
from ppl.models import ContactGraph

# Create and populate graph
graph = ContactGraph()
# ... add contacts and relationships ...

# Save to disk
graph.save("my_contacts.graphml")

# Load from disk later
graph = ContactGraph()
graph.load("my_contacts.graphml")

# Graph automatically preserves:
# - All contact data (names, emails, phones, etc.)
# - Relationships between contacts
# - Metadata and custom attributes
```

## Architecture

PPL uses a layered architecture:

1. **Data Models** (`ppl/models/`)
   - `Contact`: Represents a person or organization (vCard 4.0 entity)
   - `Related`: vCard 4.0 RELATED property
   - `Relationship`: Internal graph edge representation
   - `ContactGraph`: NetworkX-based graph manager

2. **Serializers** (`ppl/serializers/`)
   - `vcard`: vCard 4.0 import/export
   - `yaml_serializer`: YAML serialization with flat format support
   - `markdown`: Markdown rendering with YAML front matter and wiki-style links

3. **Filters** (`ppl/filters/`)
   - `UIDFilter`: Assigns UUIDs to contacts without UIDs
   - `GenderFilter`: Infers gender from relationship terms (mother/father/etc.)

4. **Services** (`ppl/services/`)
   - `ConsistencyService`: Detects inconsistencies across data representations

5. **CLI** (`ppl/cli.py`)
   - Command-line interface built with Click

## File Formats

### vCard 4.0

Standard vCard format with full support for RELATED properties:

```
BEGIN:VCARD
VERSION:4.0
UID:urn:uuid:550e8400-e29b-41d4-a716-446655440001
FN:Alice Johnson
EMAIL:alice@example.com
RELATED;TYPE="friend,colleague":urn:uuid:bob-uid
END:VCARD
```

### YAML

Clean YAML representation:

```yaml
FN: Alice Johnson
UID: urn:uuid:550e8400-e29b-41d4-a716-446655440001
EMAIL:
  - alice@example.com
RELATED:
  - uri: urn:uuid:bob-uid
    type:
      - friend
      - colleague
```

### Markdown

Human-readable format with YAML front matter:

```markdown
---
FN: Alice Johnson
UID: urn:uuid:550e8400-e29b-41d4-a716-446655440001
EMAIL:
  - alice@example.com
---

# Alice Johnson

Team lead for the backend team

## Related

- friend,colleague [[Bob Smith]]
- parent [[Charlie Davis]]
```

## Filter Pipeline

PPL includes an extensible filter pipeline for data validation and curation:

```python
from ppl.models import FilterPipeline, FilterContext
from ppl.filters import UIDFilter, GenderFilter

# Create a pipeline
pipeline = FilterPipeline("import")

# Register filters (automatically sorted by priority)
pipeline.register(UIDFilter())      # Priority 10
pipeline.register(GenderFilter())   # Priority 50

# Run pipeline
context = FilterContext(pipeline_name="import")
processed_contact = pipeline.run(contact, context)
```

## Relationship Types

PPL supports all vCard 4.0 RELATED TYPE values:

- **Social**: contact, acquaintance, friend, met
- **Professional**: co-worker, colleague
- **Residential**: co-resident, neighbor
- **Family**: child, parent, sibling, spouse, kin
- **Romantic**: muse, crush, date, sweetheart
- **Special**: me, agent, emergency

## Development

### Running Tests

Using the Makefile (recommended):

```bash
# Run all tests
make test

# Run tests with verbose output
make test-verbose

# Run with coverage report
make coverage

# Run all quality checks
make check
```

Or using pytest directly:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=ppl --cov-report=term-missing

# Run specific test file
pytest tests/test_contact.py -v

# Run only integration tests
pytest tests/test_integration.py -v
```

### Integration Tests

The test suite includes comprehensive integration tests (`tests/test_integration.py`) that simulate real user workflows:

- **Complete Workflows**: End-to-end scenarios from creating contacts to exporting
- **Format Conversions**: vCard → YAML → Markdown roundtrips
- **Filter Pipeline**: Integration of filters with import/export operations
- **Graph Operations**: Building and querying contact relationship networks
- **Collaborative Management**: Multi-user scenarios with different formats
- **Error Handling**: Graceful handling of invalid data and missing files
- **Performance**: Testing with 100+ contacts

Run integration tests separately:
```bash
pytest tests/test_integration.py -v
```

### Other Development Tasks

```bash
# Install dependencies
make install-dev

# Clean build artifacts
make clean

# Build distribution packages
make build

# Show all available commands
make help
```

### Test Coverage

Current test coverage: **68%** (core modules >80%)

- 154 passing tests
  - 87 unit tests for individual modules
  - 17 integration tests simulating user workflows
  - 8 graph persistence tests
  - 14 contact merge tests
  - 9 graph merge tests
  - 13 export change detection tests
  - 6 curation workflow tests
- Full coverage of models, serializers, and filters
- Integration tests cover:
  - Complete workflows from import to export
  - Cross-format conversions (vCard ↔ YAML ↔ Markdown)
  - Filter pipeline integration
  - Graph operations with relationships
  - Graph persistence and loading
  - Collaborative contact management scenarios
  - Incremental contact curation workflows
  - Non-destructive merging and REV-based conflict resolution
  - Smart export with change detection
  - Error handling and edge cases
  - Performance with large datasets (100+ contacts)

### Project Structure

```
ppl/
├── __init__.py
├── cli.py                  # Command-line interface
├── models/                 # Data models
│   ├── contact.py         # Contact and Related classes
│   ├── relationship.py    # Relationship class
│   ├── graph.py          # ContactGraph manager
│   ├── filter.py         # AbstractFilter base class
│   └── pipeline.py       # FilterPipeline
├── serializers/           # Serialization modules
│   ├── vcard.py          # vCard 4.0 serializer
│   ├── yaml_serializer.py # YAML serializer
│   └── markdown.py       # Markdown serializer
├── filters/              # Filter implementations
│   ├── uid_filter.py    # UID assignment
│   └── gender_filter.py # Gender inference
└── services/            # Service modules (future)
```

## Examples

Sample vCard files are provided in `examples/contacts/`:

- Alice Johnson - Software Engineer with relationships
- Bob Smith - Sales Manager
- Charlie Davis - Professor (Alice's advisor)

These demonstrate:
- Multiple email addresses and phone numbers
- Organization and title information
- Bidirectional relationships (friend/colleague)
- Directional relationships (parent/child)

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass (`pytest tests/`)
2. Code coverage remains >80% for core modules
3. New features include tests
4. Code follows existing style

## License

[License information to be added]

## Credits

Built with:
- [NetworkX](https://networkx.org/) - Graph operations
- [vobject](https://eventable.github.io/vobject/) - vCard parsing
- [PyYAML](https://pyyaml.org/) - YAML serialization
- [marko](https://marko-py.readthedocs.io/) - Markdown parsing
- [Click](https://click.palletsprojects.com/) - CLI framework
