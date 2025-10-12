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
@click.option('--format', type=click.Choice(['vcard', 'yaml', 'markdown']), default='vcard',
              help='Format of files to import (default: vcard)')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def import_contacts(folder_path, format, verbose):
    """Import contacts from a folder.
    
    FOLDER_PATH: Path to folder containing contact files
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
    
    if verbose:
        click.echo(f"Imported {len(contacts)} contacts:")
        for contact in contacts:
            click.echo(f"  - {contact.fn} ({contact.uid})")
    else:
        click.echo(f"Imported {len(contacts)} contacts")


@cli.command()
@click.argument('contacts_source', type=click.Path(exists=True))
@click.argument('output_folder', type=click.Path())
@click.option('--format', type=click.Choice(['vcard', 'yaml', 'markdown']), default='vcard',
              help='Format to export (default: vcard)')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def export_contacts(contacts_source, output_folder, format, verbose):
    """Export contacts to a folder.
    
    CONTACTS_SOURCE: Path to folder with existing contacts
    OUTPUT_FOLDER: Path to folder where contacts will be exported
    """
    if verbose:
        click.echo(f"Exporting contacts to {output_folder} in {format} format...")
    
    # First import the contacts
    source_contacts = vcard.bulk_import(contacts_source)
    
    # Export contacts based on format
    if format == 'vcard':
        vcard.bulk_export(source_contacts, output_folder)
    elif format == 'yaml':
        # Create output folder
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        for contact in source_contacts:
            filename = contact.fn.replace('/', '_').replace('\\', '_') + '.yaml'
            file_path = Path(output_folder) / filename
            with open(file_path, 'w') as f:
                f.write(yaml_serializer.to_yaml(contact))
    elif format == 'markdown':
        markdown.bulk_export_markdown(source_contacts, output_folder)
    else:
        click.echo(f"Unknown format: {format}", err=True)
        sys.exit(1)
    
    if verbose:
        click.echo(f"Exported {len(source_contacts)} contacts")
    else:
        click.echo(f"Exported {len(source_contacts)} contacts to {output_folder}")


@cli.command()
@click.argument('folder_path', type=click.Path(exists=True))
@click.option('--format', type=click.Choice(['vcard', 'yaml', 'markdown']), default='vcard',
              help='Format of files to list (default: vcard)')
def list_contacts(folder_path, format):
    """List all contacts in a folder.
    
    FOLDER_PATH: Path to folder containing contact files
    """
    # Import contacts based on format
    if format == 'vcard':
        contacts = vcard.bulk_import(folder_path)
    elif format == 'markdown':
        contacts = markdown.bulk_import_markdown(folder_path)
    else:
        click.echo(f"Format {format} not supported for listing yet", err=True)
        sys.exit(1)
    
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
@click.argument('folder_path', type=click.Path(exists=True))
@click.argument('query')
@click.option('--format', type=click.Choice(['vcard', 'yaml', 'markdown']), default='vcard',
              help='Format of files to search (default: vcard)')
def search(folder_path, query, format):
    """Search for contacts by name or email.
    
    FOLDER_PATH: Path to folder containing contact files
    QUERY: Search query (case-insensitive)
    """
    # Import contacts based on format
    if format == 'vcard':
        contacts = vcard.bulk_import(folder_path)
    elif format == 'markdown':
        contacts = markdown.bulk_import_markdown(folder_path)
    else:
        click.echo(f"Format {format} not supported for search yet", err=True)
        sys.exit(1)
    
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
@click.argument('target_folder', type=click.Path())
@click.argument('target_format', type=click.Choice(['vcard', 'markdown', 'yaml']))
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def convert(source_folder, source_format, target_folder, target_format, verbose):
    """Convert contacts from one format to another.
    
    SOURCE_FOLDER: Path to folder with source contacts
    SOURCE_FORMAT: Format of source files (vcard or markdown)
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
    
    # Export to target format
    if target_format == 'vcard':
        vcard.bulk_export(contacts, target_folder)
    elif target_format == 'markdown':
        markdown.bulk_export_markdown(contacts, target_folder)
    elif target_format == 'yaml':
        Path(target_folder).mkdir(parents=True, exist_ok=True)
        for contact in contacts:
            filename = contact.fn.replace('/', '_').replace('\\', '_') + '.yaml'
            file_path = Path(target_folder) / filename
            with open(file_path, 'w') as f:
                f.write(yaml_serializer.to_yaml(contact))
    else:
        click.echo(f"Unknown target format: {target_format}", err=True)
        sys.exit(1)
    
    click.echo(f"Converted {len(contacts)} contacts from {source_format} to {target_format}")


if __name__ == '__main__':
    cli()
