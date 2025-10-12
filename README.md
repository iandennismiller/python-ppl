# PPL - Python People Manager

A modern contact management system that models relationships as a graph and supports multiple serialization formats including vCard 4.0, YAML, and Markdown.

## Overview

PPL (Python People Manager) is a command-line tool and Python library for managing contacts and their relationships. Unlike traditional contact managers that treat contacts in isolation, PPL models contacts as a graph with explicit, typed relationships.

### Key Features

- **Graph-based relationship modeling** using NetworkX
- **Multiple serialization formats**: vCard 4.0, YAML, and Markdown
- **vCard 4.0 compliant** with full support for RELATED properties
- **Intelligent merge logic** based on REV timestamps
- **Extensible filter pipeline** for data validation and curation
- **Wiki-style links** in Markdown format for easy relationship management
- **Command-line interface** for common operations

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

### Using the CLI

```bash
# List contacts in a folder
python -m ppl.cli list-contacts examples/contacts

# Search for contacts
python -m ppl.cli search examples/contacts "alice"

# Convert between formats
python -m ppl.cli convert examples/contacts vcard output markdown

# Import contacts with filters (UID assignment, gender inference)
python -m ppl.cli import-contacts examples/contacts --verbose

# Export to a different format
python -m ppl.cli export-contacts examples/contacts output --format markdown
```

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

4. **CLI** (`ppl/cli.py`)
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

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=ppl --cov-report=term-missing

# Run specific test file
pytest tests/test_contact.py -v
```

### Test Coverage

Current test coverage: **64%** (core modules >80%)

- 87 passing tests
- Full coverage of models, serializers, and filters
- Integration tests for import/export cycles

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
