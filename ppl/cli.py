"""
Command-line interface for PPL.
"""
import click
import sys
from pathlib import Path

from .models import ContactGraph, import_pipeline, Contact
from .serializers import vcard, yaml_serializer, markdown
from .filters import UIDFilter, GenderFilter


# Register filters in the import pipeline
import_pipeline.register(UIDFilter())
import_pipeline.register(GenderFilter())


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
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def import_contacts(folder_path, graph_file, format, verbose):
    """Import contacts from a folder and save to graph.
    
    Uses intelligent merging to preserve existing data while importing new information.
    Missing fields in imported contacts do not delete existing graph data.
    
    FOLDER_PATH: Path to folder containing contact files
    GRAPH_FILE: Path to save the contact graph (GraphML format)
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
            graph.load(graph_file)
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
    graph.save(graph_file)
    
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
@click.option('--force', is_flag=True, help='Force overwrite all files (ignore change detection)')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def export_contacts(graph_file, output_folder, format, force, verbose):
    """Export contacts from graph to a folder.
    
    Only writes files when data has changed to minimize file system operations.
    Use --force to override and write all files.
    
    GRAPH_FILE: Path to the contact graph file
    OUTPUT_FOLDER: Path to folder where contacts will be exported
    """
    if verbose:
        click.echo(f"Loading graph from {graph_file}...")
    
    # Load graph
    graph = ContactGraph()
    try:
        graph.load(graph_file)
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
def list_contacts(graph_file):
    """List all contacts in the graph.
    
    GRAPH_FILE: Path to the contact graph file
    """
    # Load graph
    graph = ContactGraph()
    try:
        graph.load(graph_file)
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
def search(graph_file, query):
    """Search for contacts by name or email in the graph.
    
    GRAPH_FILE: Path to the contact graph file
    QUERY: Search query (case-insensitive)
    """
    # Load graph
    graph = ContactGraph()
    try:
        graph.load(graph_file)
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
@click.argument('source_folder', type=click.Path(exists=True))
@click.argument('source_format', type=click.Choice(['vcard', 'markdown']))
@click.argument('graph_file', type=click.Path())
@click.argument('target_folder', type=click.Path())
@click.argument('target_format', type=click.Choice(['vcard', 'markdown', 'yaml']))
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def convert(source_folder, source_format, graph_file, target_folder, target_format, verbose):
    """Convert contacts from one format to another via graph.
    
    SOURCE_FOLDER: Path to folder with source contacts
    SOURCE_FORMAT: Format of source files (vcard or markdown)
    GRAPH_FILE: Path to save/load the contact graph
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
            graph.load(graph_file)
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
    graph.save(graph_file)
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
