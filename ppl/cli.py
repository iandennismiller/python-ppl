"""
Command-line interface for PPL.
"""
import click
import sys
from pathlib import Path

from .models import ContactGraph, import_pipeline, Contact, curation_pipeline
from .serializers import vcard, yaml_serializer, markdown
from .filters import UIDFilter, GenderFilter
from .services import ConsistencyService


# Register filters in the import pipeline
import_pipeline.register(UIDFilter())
import_pipeline.register(GenderFilter())

# Register filters in the curation pipeline
curation_pipeline.register(GenderFilter())


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """PPL - Python People Manager.
    
    A command-line tool for managing contacts and relationships.
    """
    pass


@cli.command()
@click.argument('folder_path', type=click.Path(exists=True))
@click.argument('graph_file', type=click.Path())
@click.option('--format', type=click.Choice(['vcard', 'yaml', 'markdown']), default='vcard',
              help='Format of files to import (default: vcard)')
@click.option('--graph-format', type=click.Choice(['graphml', 'json']), default=None,
              help='Format for graph file (default: auto-detect from extension)')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def import_contacts(folder_path, graph_file, format, graph_format, verbose):
    """Import contacts from a folder and save to graph.
    
    Uses intelligent merging to preserve existing data while importing new information.
    Missing fields in imported contacts do not delete existing graph data.
    
    FOLDER_PATH: Path to folder containing contact files
    GRAPH_FILE: Path to save the contact graph (.graphml or .json)
    """
    if verbose:
        click.echo(f"Importing {format} files from {folder_path}...")
    
    # Import contacts based on format
    if format == 'vcard':
        contacts = vcard.bulk_import(folder_path)
    elif format == 'yaml':
        # Not implemented in yaml_serializer yet, use vcard as fallback
        click.echo("YAML bulk import not yet implemented. Using vcard format.")
        contacts = vcard.bulk_import(folder_path)
    elif format == 'markdown':
        contacts = markdown.bulk_import_markdown(folder_path)
    else:
        click.echo(f"Unknown format: {format}", err=True)
        sys.exit(1)
    
    # Load existing graph if it exists
    graph = ContactGraph()
    if Path(graph_file).exists():
        if verbose:
            click.echo(f"Loading existing graph from {graph_file}...")
        try:
            graph.load(graph_file, format=graph_format)
        except Exception as e:
            click.echo(f"Warning: Could not load existing graph: {e}", err=True)
    
    # Merge contacts into graph using intelligent merging
    added = 0
    updated = 0
    skipped = 0
    
    for contact in contacts:
        if not contact.uid:
            # Apply filters if needed
            from .models import FilterContext
            context = FilterContext(pipeline_name="import")
            contact = import_pipeline.run(contact, context)
        
        # Use merge_contact for intelligent merging
        modified, action = graph.merge_contact(contact)
        
        if action == "added":
            added += 1
        elif action == "updated":
            updated += 1
        elif action == "skipped":
            skipped += 1
    
    # Save graph
    graph.save(graph_file, format=graph_format)
    
    if verbose:
        click.echo(f"Added: {added}, Updated: {updated}, Skipped: {skipped}")
        click.echo(f"Graph saved to {graph_file}")
        click.echo(f"Total contacts in graph: {len(graph.get_all_contacts())}")
    else:
        click.echo(f"Imported {len(contacts)} contacts to {graph_file} (added: {added}, updated: {updated}, skipped: {skipped})")


@cli.command()
@click.argument('graph_file', type=click.Path(exists=True))
@click.argument('output_folder', type=click.Path())
@click.option('--format', type=click.Choice(['vcard', 'yaml', 'markdown']), default='vcard',
              help='Format to export (default: vcard)')
@click.option('--graph-format', type=click.Choice(['graphml', 'json']), default=None,
              help='Format for graph file (default: auto-detect from extension)')
@click.option('--force', is_flag=True, help='Force overwrite all files (ignore change detection)')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def export_contacts(graph_file, output_folder, format, graph_format, force, verbose):
    """Export contacts from graph to a folder.
    
    Only writes files when data has changed to minimize file system operations.
    Use --force to override and write all files.
    
    GRAPH_FILE: Path to the contact graph file (.graphml or .json)
    OUTPUT_FOLDER: Path to folder where contacts will be exported
    """
    if verbose:
        click.echo(f"Loading graph from {graph_file}...")
    
    # Load graph
    graph = ContactGraph()
    try:
        graph.load(graph_file, format=graph_format)
    except FileNotFoundError:
        click.echo(f"Error: Graph file not found: {graph_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading graph: {e}", err=True)
        sys.exit(1)
    
    contacts = graph.get_all_contacts()
    
    if verbose:
        click.echo(f"Exporting {len(contacts)} contacts to {output_folder} in {format} format...")
        if force:
            click.echo("Force mode enabled - all files will be written")
    
    # Export contacts based on format
    written = 0
    skipped = 0
    
    if format == 'vcard':
        written, skipped = vcard.bulk_export(contacts, output_folder, force=force)
    elif format == 'yaml':
        # Create output folder
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        # TODO: Implement change detection for YAML when bulk_export is available
        for contact in contacts:
            filename = contact.fn.replace('/', '_').replace('\\', '_') + '.yaml'
            file_path = Path(output_folder) / filename
            with open(file_path, 'w') as f:
                f.write(yaml_serializer.to_yaml(contact))
            written += 1
    elif format == 'markdown':
        written, skipped = markdown.bulk_export_markdown(contacts, output_folder, force=force)
    else:
        click.echo(f"Unknown format: {format}", err=True)
        sys.exit(1)
    
    if verbose:
        click.echo(f"Written: {written}, Skipped: {skipped}")
        click.echo(f"Export complete")
    else:
        click.echo(f"Exported to {output_folder} (written: {written}, skipped: {skipped})")


@cli.command()
@click.argument('graph_file', type=click.Path(exists=True))
@click.option('--graph-format', type=click.Choice(['graphml', 'json']), default=None,
              help='Format for graph file (default: auto-detect from extension)')
def list_contacts(graph_file, graph_format):
    """List all contacts in the graph.
    
    GRAPH_FILE: Path to the contact graph file (.graphml or .json)
    """
    # Load graph
    graph = ContactGraph()
    try:
        graph.load(graph_file, format=graph_format)
    except FileNotFoundError:
        click.echo(f"Error: Graph file not found: {graph_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading graph: {e}", err=True)
        sys.exit(1)
    
    contacts = graph.get_all_contacts()
    
    if not contacts:
        click.echo("No contacts found")
        return
    
    click.echo(f"Found {len(contacts)} contacts:\n")
    
    for contact in sorted(contacts, key=lambda c: c.fn):
        click.echo(f"  {contact.fn}")
        if contact.uid:
            click.echo(f"    UID: {contact.uid}")
        if contact.email:
            click.echo(f"    Email: {', '.join(contact.email)}")
        if contact.tel:
            click.echo(f"    Phone: {', '.join(contact.tel)}")
        if contact.org:
            click.echo(f"    Org: {', '.join(contact.org)}")
        if contact.related:
            click.echo(f"    Relationships: {len(contact.related)}")
        click.echo()


@cli.command()
@click.argument('graph_file', type=click.Path(exists=True))
@click.argument('query')
@click.option('--graph-format', type=click.Choice(['graphml', 'json']), default=None,
              help='Format for graph file (default: auto-detect from extension)')
def search(graph_file, query, graph_format):
    """Search for contacts by name or email in the graph.
    
    GRAPH_FILE: Path to the contact graph file (.graphml or .json)
    QUERY: Search query (case-insensitive)
    """
    # Load graph
    graph = ContactGraph()
    try:
        graph.load(graph_file, format=graph_format)
    except FileNotFoundError:
        click.echo(f"Error: Graph file not found: {graph_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading graph: {e}", err=True)
        sys.exit(1)
    
    contacts = graph.get_all_contacts()
    query_lower = query.lower()
    matches = []
    
    for contact in contacts:
        # Search in name
        if query_lower in contact.fn.lower():
            matches.append(contact)
            continue
        
        # Search in email
        if any(query_lower in email.lower() for email in contact.email):
            matches.append(contact)
            continue
        
        # Search in organization
        if any(query_lower in org.lower() for org in contact.org):
            matches.append(contact)
            continue
    
    if not matches:
        click.echo(f"No contacts found matching '{query}'")
        return
    
    click.echo(f"Found {len(matches)} contact(s) matching '{query}':\n")
    
    for contact in matches:
        click.echo(f"  {contact.fn}")
        if contact.email:
            click.echo(f"    Email: {', '.join(contact.email)}")
        if contact.org:
            click.echo(f"    Org: {', '.join(contact.org)}")
        click.echo()


@cli.command()
@click.argument('graph_file', type=click.Path(exists=True))
@click.argument('uid')
@click.option('--format', type=click.Choice(['text', 'vcard', 'yaml', 'json', 'markdown']), default='text',
              help='Output format (default: text)')
@click.option('--graph-format', type=click.Choice(['graphml', 'json']), default=None,
              help='Format for graph file (default: auto-detect from extension)')
def show(graph_file, uid, format, graph_format):
    """Display detailed information about a single contact.
    
    GRAPH_FILE: Path to the contact graph file (.graphml or .json)
    UID: Unique identifier of the contact to display
    """
    # Load graph
    graph = ContactGraph()
    try:
        graph.load(graph_file, format=graph_format)
    except FileNotFoundError:
        click.echo(f"Error: Graph file not found: {graph_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading graph: {e}", err=True)
        sys.exit(1)
    
    # Get contact by UID
    contact = graph.get_contact(uid)
    
    if not contact:
        click.echo(f"Error: Contact with UID '{uid}' not found", err=True)
        sys.exit(1)
    
    # Display contact in requested format
    if format == 'text':
        # Display human-readable text format
        click.echo(f"{contact.fn} ({contact.uid})")
        click.echo("=" * (len(contact.fn) + len(contact.uid) + 3))
        
        if contact.email:
            click.echo(f"Email: {', '.join(contact.email)}")
        if contact.tel:
            click.echo(f"Phone: {', '.join(contact.tel)}")
        if contact.title:
            click.echo(f"Title: {contact.title}")
        if contact.org:
            click.echo(f"Organization: {', '.join(contact.org)}")
        if contact.adr:
            click.echo(f"Address: {', '.join(contact.adr)}")
        if contact.note:
            click.echo(f"Note: {contact.note}")
        if contact.gender:
            click.echo(f"Gender: {contact.gender}")
        if contact.bday:
            click.echo(f"Birthday: {contact.bday}")
        
        # Show relationships
        relationships = graph.get_relationships(uid)
        if relationships:
            click.echo(f"\nRelationships:")
            for rel in relationships:
                rel_types = ', '.join(rel.types) if rel.types else 'related'
                click.echo(f"- {rel_types} → {rel.target.fn} ({rel.target.uid})")
        
        # Show last updated
        if contact.rev:
            click.echo(f"\nLast Updated: {contact.rev.strftime('%Y-%m-%d %H:%M:%S')}")
    
    elif format == 'vcard':
        # Output as vCard
        click.echo(vcard.to_vcard(contact))
    
    elif format == 'yaml':
        # Output as YAML
        click.echo(yaml_serializer.to_yaml(contact))
    
    elif format == 'json':
        # Output as JSON
        import json
        contact_dict = {
            'fn': contact.fn,
            'uid': contact.uid,
            'email': contact.email,
            'tel': contact.tel,
            'title': contact.title,
            'org': contact.org,
            'adr': contact.adr,
            'note': contact.note,
            'gender': contact.gender,
            'bday': contact.bday,
            'rev': contact.rev.isoformat() if contact.rev else None,
        }
        # Add relationships
        relationships = graph.get_relationships(uid)
        if relationships:
            contact_dict['relationships'] = [
                {
                    'types': rel.types,
                    'target_fn': rel.target.fn,
                    'target_uid': rel.target.uid
                }
                for rel in relationships
            ]
        click.echo(json.dumps(contact_dict, indent=2))
    
    elif format == 'markdown':
        # Output as Markdown
        click.echo(markdown.to_markdown(contact))


@cli.command()
@click.argument('graph_file', type=click.Path(exists=True))
@click.argument('uid', required=False)
@click.option('--all', 'all_contacts', is_flag=True, help='Run filters on all contacts')
@click.option('--dry-run', is_flag=True, help='Preview changes without saving')
@click.option('--graph-format', type=click.Choice(['graphml', 'json']), default=None,
              help='Format for graph file (default: auto-detect from extension)')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def filter(graph_file, uid, all_contacts, dry_run, graph_format, verbose):
    """Run filter pipeline on contacts.
    
    Execute the curation pipeline on a specific contact or all contacts.
    Use --dry-run to preview changes without saving to the graph.
    
    GRAPH_FILE: Path to the contact graph file (.graphml or .json)
    UID: Unique identifier of the contact to filter (optional if --all is used)
    """
    # Validate arguments
    if not uid and not all_contacts:
        click.echo("Error: Must specify either UID or --all flag", err=True)
        sys.exit(1)
    
    if uid and all_contacts:
        click.echo("Error: Cannot specify both UID and --all flag", err=True)
        sys.exit(1)
    
    # Load graph
    graph = ContactGraph()
    try:
        graph.load(graph_file, format=graph_format)
    except FileNotFoundError:
        click.echo(f"Error: Graph file not found: {graph_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading graph: {e}", err=True)
        sys.exit(1)
    
    # Get contacts to filter
    if all_contacts:
        contacts = graph.get_all_contacts()
        if verbose:
            click.echo(f"Running filters on {len(contacts)} contacts...")
    else:
        contact = graph.get_contact(uid)
        if not contact:
            click.echo(f"Error: Contact with UID '{uid}' not found", err=True)
            sys.exit(1)
        contacts = [contact]
        if verbose:
            click.echo(f"Running filters on {contact.fn}...")
    
    # Run filters
    from .models import FilterContext
    import copy
    
    context = FilterContext(pipeline_name="curation")
    modified_count = 0
    changes = []
    
    for contact in contacts:
        # Create a copy to compare before/after
        contact_before = copy.deepcopy(contact)
        
        # Run curation pipeline
        contact_after = curation_pipeline.run(contact, context)
        
        # Check for changes
        contact_changed = False
        contact_changes = []
        
        # Compare fields for changes
        if contact_before.gender != contact_after.gender:
            contact_changed = True
            contact_changes.append(f"  GENDER: {contact_before.gender} → {contact_after.gender}")
        
        if contact_before.email != contact_after.email:
            contact_changed = True
            contact_changes.append(f"  EMAIL: {contact_before.email} → {contact_after.email}")
        
        if contact_before.tel != contact_after.tel:
            contact_changed = True
            contact_changes.append(f"  TEL: {contact_before.tel} → {contact_after.tel}")
        
        if contact_changed:
            modified_count += 1
            changes.append({
                'contact': contact_after,
                'changes': contact_changes
            })
            
            if verbose or not all_contacts:
                click.echo(f"\n{contact_after.fn} ({contact_after.uid}):")
                for change in contact_changes:
                    click.echo(change)
            
            # Update graph unless dry-run
            if not dry_run:
                graph.update_contact(contact_after)
    
    # Save graph unless dry-run
    if not dry_run and modified_count > 0:
        graph.save(graph_file, format=graph_format)
        if verbose:
            click.echo(f"\nGraph saved to {graph_file}")
    
    # Summary
    if dry_run:
        click.echo(f"\nDry run complete. {modified_count} contact(s) would be modified.")
    else:
        click.echo(f"\nFilters complete. {modified_count} contact(s) modified.")


@cli.command()
@click.argument('graph_file', type=click.Path(exists=True))
@click.option('--vcard-folder', type=click.Path(), help='Path to VCF folder to check')
@click.option('--markdown-folder', type=click.Path(), help='Path to Markdown folder to check')
@click.option('--yaml-folder', type=click.Path(), help='Path to YAML folder to check')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json', 'yaml']), default='text',
              help='Output format (default: text)')
@click.option('--graph-format', type=click.Choice(['graphml', 'json']), default=None,
              help='Format for graph file (default: auto-detect from extension)')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def check_consistency(graph_file, vcard_folder, markdown_folder, yaml_folder, output_format, graph_format, verbose):
    """Check consistency across data representations.
    
    Compare the graph with VCF, Markdown, and/or YAML folders to detect
    inconsistencies such as missing contacts, outdated files, or conflicts.
    
    GRAPH_FILE: Path to the contact graph file (.graphml or .json)
    """
    # Validate that at least one folder is specified
    if not any([vcard_folder, markdown_folder, yaml_folder]):
        click.echo("Error: Must specify at least one folder to check (--vcard-folder, --markdown-folder, or --yaml-folder)", err=True)
        sys.exit(1)
    
    # Load graph
    if verbose:
        click.echo(f"Loading graph from {graph_file}...")
    
    graph = ContactGraph()
    try:
        graph.load(graph_file, format=graph_format)
    except FileNotFoundError:
        click.echo(f"Error: Graph file not found: {graph_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading graph: {e}", err=True)
        sys.exit(1)
    
    # Create consistency service
    service = ConsistencyService(graph)
    
    # Run consistency checks
    if verbose:
        click.echo("Running consistency checks...")
        if vcard_folder:
            click.echo(f"  Checking VCF folder: {vcard_folder}")
        if markdown_folder:
            click.echo(f"  Checking Markdown folder: {markdown_folder}")
        if yaml_folder:
            click.echo(f"  Checking YAML folder: {yaml_folder}")
    
    report = service.check_all_representations(
        vcf_folder=vcard_folder,
        markdown_folder=markdown_folder,
        yaml_folder=yaml_folder
    )
    
    # Generate and display report
    report_text = service.generate_report(report, format=output_format)
    click.echo(report_text)
    
    # Exit with error code if inconsistencies found
    if not report.is_consistent:
        sys.exit(1)


@cli.command()
@click.argument('source_folder', type=click.Path(exists=True))
@click.argument('source_format', type=click.Choice(['vcard', 'markdown']))
@click.argument('graph_file', type=click.Path())
@click.argument('target_folder', type=click.Path())
@click.argument('target_format', type=click.Choice(['vcard', 'markdown', 'yaml']))
@click.option('--graph-format', type=click.Choice(['graphml', 'json']), default=None,
              help='Format for graph file (default: auto-detect from extension)')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def convert(source_folder, source_format, graph_file, target_folder, target_format, graph_format, verbose):
    """Convert contacts from one format to another via graph.
    
    SOURCE_FOLDER: Path to folder with source contacts
    SOURCE_FORMAT: Format of source files (vcard or markdown)
    GRAPH_FILE: Path to save/load the contact graph (.graphml or .json)
    TARGET_FOLDER: Path to folder for converted contacts
    TARGET_FORMAT: Format to convert to (vcard, markdown, or yaml)
    """
    if verbose:
        click.echo(f"Converting {source_format} to {target_format}...")
    
    # Import from source format
    if source_format == 'vcard':
        contacts = vcard.bulk_import(source_folder)
    elif source_format == 'markdown':
        contacts = markdown.bulk_import_markdown(source_folder)
    else:
        click.echo(f"Unknown source format: {source_format}", err=True)
        sys.exit(1)
    
    # Load or create graph
    graph = ContactGraph()
    if Path(graph_file).exists():
        if verbose:
            click.echo(f"Loading existing graph from {graph_file}...")
        try:
            graph.load(graph_file, format=graph_format)
        except Exception as e:
            click.echo(f"Warning: Could not load existing graph: {e}", err=True)
    
    # Add contacts to graph using intelligent merging
    added = 0
    updated = 0
    skipped = 0
    
    for contact in contacts:
        if not contact.uid:
            from .models import FilterContext
            context = FilterContext(pipeline_name="import")
            contact = import_pipeline.run(contact, context)
        
        # Use merge_contact for intelligent merging
        modified, action = graph.merge_contact(contact)
        if action == "added":
            added += 1
        elif action == "updated":
            updated += 1
        elif action == "skipped":
            skipped += 1
    
    # Save graph
    graph.save(graph_file, format=graph_format)
    if verbose:
        click.echo(f"Graph saved to {graph_file}")
        click.echo(f"Added: {added}, Updated: {updated}, Skipped: {skipped}")
    
    # Get all contacts for export
    all_contacts = graph.get_all_contacts()
    
    # Export to target format
    written = 0
    skipped_export = 0
    
    if target_format == 'vcard':
        written, skipped_export = vcard.bulk_export(all_contacts, target_folder)
    elif target_format == 'markdown':
        written, skipped_export = markdown.bulk_export_markdown(all_contacts, target_folder)
    elif target_format == 'yaml':
        Path(target_folder).mkdir(parents=True, exist_ok=True)
        for contact in all_contacts:
            filename = contact.fn.replace('/', '_').replace('\\', '_') + '.yaml'
            file_path = Path(target_folder) / filename
            with open(file_path, 'w') as f:
                f.write(yaml_serializer.to_yaml(contact))
            written += 1
    else:
        click.echo(f"Unknown target format: {target_format}", err=True)
        sys.exit(1)
    
    if verbose:
        click.echo(f"Converted {len(all_contacts)} contacts from {source_format} to {target_format}")
        click.echo(f"Export: Written: {written}, Skipped: {skipped_export}")
    else:
        click.echo(f"Converted {len(all_contacts)} contacts from {source_format} to {target_format}")


if __name__ == '__main__':
    cli()
