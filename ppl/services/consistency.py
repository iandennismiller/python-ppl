"""
Consistency checking service for PPL.

Detects inconsistencies across multiple data representations
(graph, VCF files, Markdown files, YAML front matter).
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

from ..models import Contact, ContactGraph
from ..serializers import vcard, markdown, yaml_serializer


@dataclass
class Inconsistency:
    """
    Represents a single inconsistency found during checking.
    """
    type: str  # Type of inconsistency: missing, outdated, conflict, orphaned, inconsistent
    source: str  # Source where issue was found (e.g., "graph", "vcf_folder", "markdown_folder")
    target: Optional[str] = None  # Target entity affected (e.g., contact UID or filename)
    details: str = ""  # Human-readable description of the issue
    severity: str = "warning"  # Severity: error, warning, info
    
    def __str__(self):
        """String representation of inconsistency."""
        return f"[{self.type.upper()}] {self.details}"


@dataclass
class ConsistencyReport:
    """
    Aggregated consistency check results.
    """
    inconsistencies: List[Inconsistency] = field(default_factory=list)
    total_contacts_graph: int = 0
    total_files_vcf: int = 0
    total_files_markdown: int = 0
    total_files_yaml: int = 0
    checked_at: datetime = field(default_factory=datetime.now)
    
    @property
    def is_consistent(self) -> bool:
        """Check if all representations are consistent."""
        return len(self.inconsistencies) == 0
    
    @property
    def error_count(self) -> int:
        """Count of errors."""
        return sum(1 for i in self.inconsistencies if i.severity == "error")
    
    @property
    def warning_count(self) -> int:
        """Count of warnings."""
        return sum(1 for i in self.inconsistencies if i.severity == "warning")
    
    def add_inconsistency(self, inconsistency: Inconsistency):
        """Add an inconsistency to the report."""
        self.inconsistencies.append(inconsistency)


class ConsistencyService:
    """
    Service for checking consistency across data representations.
    """
    
    def __init__(self, graph: ContactGraph):
        """
        Initialize consistency service.
        
        Args:
            graph: ContactGraph to check
        """
        self.graph = graph
    
    def check_graph_vcf_consistency(self, vcf_folder: str) -> List[Inconsistency]:
        """
        Compare graph with VCF folder for inconsistencies.
        
        Args:
            vcf_folder: Path to folder containing VCF files
            
        Returns:
            List of inconsistencies found
        """
        inconsistencies = []
        vcf_path = Path(vcf_folder)
        
        if not vcf_path.exists():
            inconsistencies.append(Inconsistency(
                type="missing",
                source="vcf_folder",
                details=f"VCF folder not found: {vcf_folder}",
                severity="error"
            ))
            return inconsistencies
        
        # Load VCF files
        try:
            vcf_contacts = vcard.bulk_import(vcf_folder)
        except Exception as e:
            inconsistencies.append(Inconsistency(
                type="error",
                source="vcf_folder",
                details=f"Failed to load VCF files: {e}",
                severity="error"
            ))
            return inconsistencies
        
        # Create UID mapping for VCF contacts
        vcf_by_uid = {c.uid: c for c in vcf_contacts if c.uid}
        graph_contacts = self.graph.get_all_contacts()
        graph_by_uid = {c.uid: c for c in graph_contacts if c.uid}
        
        # Check for contacts in graph but not in VCF folder
        for uid, contact in graph_by_uid.items():
            if uid not in vcf_by_uid:
                inconsistencies.append(Inconsistency(
                    type="missing",
                    source="vcf_folder",
                    target=uid,
                    details=f"Contact \"{contact.fn}\" ({uid}) exists in graph but not in VCF folder",
                    severity="warning"
                ))
        
        # Check for VCF files not in graph
        for uid, contact in vcf_by_uid.items():
            if uid not in graph_by_uid:
                inconsistencies.append(Inconsistency(
                    type="orphaned",
                    source="vcf_folder",
                    target=uid,
                    details=f"VCF file for \"{contact.fn}\" ({uid}) exists but contact not in graph",
                    severity="warning"
                ))
        
        # Check for REV timestamp mismatches
        for uid in set(graph_by_uid.keys()) & set(vcf_by_uid.keys()):
            graph_contact = graph_by_uid[uid]
            vcf_contact = vcf_by_uid[uid]
            
            # Compare REV timestamps
            if graph_contact.rev and vcf_contact.rev:
                if graph_contact.rev != vcf_contact.rev:
                    inconsistencies.append(Inconsistency(
                        type="outdated",
                        source="vcf_folder",
                        target=uid,
                        details=f"Contact \"{graph_contact.fn}\" has REV {vcf_contact.rev.strftime('%Y-%m-%d %H:%M:%S')} in VCF but {graph_contact.rev.strftime('%Y-%m-%d %H:%M:%S')} in graph",
                        severity="warning"
                    ))
        
        return inconsistencies
    
    def check_graph_markdown_consistency(self, markdown_folder: str) -> List[Inconsistency]:
        """
        Compare graph with Markdown folder for inconsistencies.
        
        Args:
            markdown_folder: Path to folder containing Markdown files
            
        Returns:
            List of inconsistencies found
        """
        inconsistencies = []
        md_path = Path(markdown_folder)
        
        if not md_path.exists():
            inconsistencies.append(Inconsistency(
                type="missing",
                source="markdown_folder",
                details=f"Markdown folder not found: {markdown_folder}",
                severity="error"
            ))
            return inconsistencies
        
        # Load Markdown files
        try:
            md_contacts = markdown.bulk_import_markdown(markdown_folder)
        except Exception as e:
            inconsistencies.append(Inconsistency(
                type="error",
                source="markdown_folder",
                details=f"Failed to load Markdown files: {e}",
                severity="error"
            ))
            return inconsistencies
        
        # Create UID mapping for Markdown contacts
        md_by_uid = {c.uid: c for c in md_contacts if c.uid}
        graph_contacts = self.graph.get_all_contacts()
        graph_by_uid = {c.uid: c for c in graph_contacts if c.uid}
        
        # Check for contacts in graph but not in Markdown folder
        for uid, contact in graph_by_uid.items():
            if uid not in md_by_uid:
                inconsistencies.append(Inconsistency(
                    type="missing",
                    source="markdown_folder",
                    target=uid,
                    details=f"Contact \"{contact.fn}\" ({uid}) exists in graph but not in Markdown folder",
                    severity="warning"
                ))
        
        # Check for Markdown files not in graph
        for uid, contact in md_by_uid.items():
            if uid not in graph_by_uid:
                inconsistencies.append(Inconsistency(
                    type="orphaned",
                    source="markdown_folder",
                    target=uid,
                    details=f"Markdown file for \"{contact.fn}\" ({uid}) exists but contact not in graph",
                    severity="warning"
                ))
        
        # Check for REV timestamp mismatches
        for uid in set(graph_by_uid.keys()) & set(md_by_uid.keys()):
            graph_contact = graph_by_uid[uid]
            md_contact = md_by_uid[uid]
            
            # Compare REV timestamps
            if graph_contact.rev and md_contact.rev:
                if graph_contact.rev != md_contact.rev:
                    inconsistencies.append(Inconsistency(
                        type="outdated",
                        source="markdown_folder",
                        target=uid,
                        details=f"Contact \"{graph_contact.fn}\" has REV {md_contact.rev.strftime('%Y-%m-%d %H:%M:%S')} in Markdown but {graph_contact.rev.strftime('%Y-%m-%d %H:%M:%S')} in graph",
                        severity="warning"
                    ))
        
        return inconsistencies
    
    def check_front_matter_content_consistency(self, markdown_folder: str) -> List[Inconsistency]:
        """
        Validate YAML front matter vs Markdown content consistency.
        
        Args:
            markdown_folder: Path to folder containing Markdown files
            
        Returns:
            List of inconsistencies found
        """
        inconsistencies = []
        md_path = Path(markdown_folder)
        
        if not md_path.exists():
            inconsistencies.append(Inconsistency(
                type="missing",
                source="markdown_folder",
                details=f"Markdown folder not found: {markdown_folder}",
                severity="error"
            ))
            return inconsistencies
        
        # Check each markdown file
        for md_file in md_path.glob("*.md"):
            try:
                with open(md_file, 'r') as f:
                    content = f.read()
                
                # Parse the contact
                contact = markdown.from_markdown(content)
                
                # Check if YAML front matter exists
                if '---' not in content:
                    inconsistencies.append(Inconsistency(
                        type="inconsistent",
                        source="markdown_file",
                        target=str(md_file.name),
                        details=f"File \"{md_file.name}\" has no YAML front matter",
                        severity="warning"
                    ))
                    continue
                
                # Parse front matter and content separately
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = parts[1].strip()
                    body = parts[2].strip()
                    
                    # Check for related section in body
                    if 'related' in body.lower():
                        # Extract YAML front matter related entries
                        import yaml
                        try:
                            fm_data = yaml.safe_load(front_matter)
                            fm_related = fm_data.get('RELATED', []) if fm_data else []
                            
                            # Parse related section from body
                            # This is a simplified check - full implementation would parse markdown structure
                            if '[[' in body and not fm_related:
                                inconsistencies.append(Inconsistency(
                                    type="inconsistent",
                                    source="markdown_file",
                                    target=str(md_file.name),
                                    details=f"File \"{md_file.name}\" has wiki-links in Related section but no RELATED in front matter",
                                    severity="info"
                                ))
                        except Exception as e:
                            # Ignore YAML parsing errors for now
                            pass
                            
            except Exception as e:
                inconsistencies.append(Inconsistency(
                    type="error",
                    source="markdown_file",
                    target=str(md_file.name),
                    details=f"Failed to parse \"{md_file.name}\": {e}",
                    severity="error"
                ))
        
        return inconsistencies
    
    def check_all_representations(
        self,
        vcf_folder: Optional[str] = None,
        markdown_folder: Optional[str] = None,
        yaml_folder: Optional[str] = None
    ) -> ConsistencyReport:
        """
        Comprehensive consistency check across all representations.
        
        Args:
            vcf_folder: Optional path to VCF folder
            markdown_folder: Optional path to Markdown folder
            yaml_folder: Optional path to YAML folder
            
        Returns:
            ConsistencyReport with all inconsistencies found
        """
        report = ConsistencyReport()
        report.total_contacts_graph = len(self.graph.get_all_contacts())
        
        # Check VCF folder
        if vcf_folder:
            vcf_inconsistencies = self.check_graph_vcf_consistency(vcf_folder)
            for inc in vcf_inconsistencies:
                report.add_inconsistency(inc)
            
            # Count VCF files
            vcf_path = Path(vcf_folder)
            if vcf_path.exists():
                report.total_files_vcf = len(list(vcf_path.glob("*.vcf")))
        
        # Check Markdown folder
        if markdown_folder:
            md_inconsistencies = self.check_graph_markdown_consistency(markdown_folder)
            for inc in md_inconsistencies:
                report.add_inconsistency(inc)
            
            # Check front matter consistency
            fm_inconsistencies = self.check_front_matter_content_consistency(markdown_folder)
            for inc in fm_inconsistencies:
                report.add_inconsistency(inc)
            
            # Count Markdown files
            md_path = Path(markdown_folder)
            if md_path.exists():
                report.total_files_markdown = len(list(md_path.glob("*.md")))
        
        # TODO: Check YAML folder when implemented
        if yaml_folder:
            yaml_path = Path(yaml_folder)
            if yaml_path.exists():
                report.total_files_yaml = len(list(yaml_path.glob("*.yaml"))) + len(list(yaml_path.glob("*.yml")))
        
        return report
    
    def generate_report(self, report: ConsistencyReport, format: str = "text") -> str:
        """
        Generate human-readable consistency report.
        
        Args:
            report: ConsistencyReport to format
            format: Output format (text, json, yaml)
            
        Returns:
            Formatted report string
        """
        if format == "json":
            import json
            return json.dumps({
                "is_consistent": report.is_consistent,
                "total_contacts_graph": report.total_contacts_graph,
                "total_files_vcf": report.total_files_vcf,
                "total_files_markdown": report.total_files_markdown,
                "total_files_yaml": report.total_files_yaml,
                "inconsistencies": [
                    {
                        "type": inc.type,
                        "source": inc.source,
                        "target": inc.target,
                        "details": inc.details,
                        "severity": inc.severity
                    }
                    for inc in report.inconsistencies
                ],
                "error_count": report.error_count,
                "warning_count": report.warning_count,
                "checked_at": report.checked_at.isoformat()
            }, indent=2)
        
        elif format == "yaml":
            import yaml
            return yaml.dump({
                "is_consistent": report.is_consistent,
                "total_contacts_graph": report.total_contacts_graph,
                "total_files_vcf": report.total_files_vcf,
                "total_files_markdown": report.total_files_markdown,
                "total_files_yaml": report.total_files_yaml,
                "inconsistencies": [
                    {
                        "type": inc.type,
                        "source": inc.source,
                        "target": inc.target,
                        "details": inc.details,
                        "severity": inc.severity
                    }
                    for inc in report.inconsistencies
                ],
                "error_count": report.error_count,
                "warning_count": report.warning_count,
                "checked_at": report.checked_at.isoformat()
            })
        
        else:  # text format
            lines = []
            lines.append("Consistency Check Report")
            lines.append("=" * 80)
            lines.append("")
            
            # Status
            status = "CONSISTENT" if report.is_consistent else "INCONSISTENT"
            if report.is_consistent:
                lines.append(f"Status: {status}")
            else:
                lines.append(f"Status: {status} ({len(report.inconsistencies)} issue(s) found)")
                lines.append(f"  Errors: {report.error_count}")
                lines.append(f"  Warnings: {report.warning_count}")
            
            lines.append("")
            
            # Summary
            lines.append("Summary:")
            lines.append(f"  Total contacts in graph: {report.total_contacts_graph}")
            if report.total_files_vcf > 0:
                lines.append(f"  Total VCF files: {report.total_files_vcf}")
            if report.total_files_markdown > 0:
                lines.append(f"  Total Markdown files: {report.total_files_markdown}")
            if report.total_files_yaml > 0:
                lines.append(f"  Total YAML files: {report.total_files_yaml}")
            
            # List inconsistencies
            if report.inconsistencies:
                lines.append("")
                lines.append("Issues:")
                for i, inc in enumerate(report.inconsistencies, 1):
                    lines.append(f"{i}. {inc}")
                
                # Recommendations
                lines.append("")
                lines.append("Recommendations:")
                
                # Check for missing contacts in folders
                missing_vcf = [inc for inc in report.inconsistencies 
                              if inc.type == "missing" and inc.source == "vcf_folder"]
                if missing_vcf:
                    lines.append("- Export graph to VCF folder to add missing contacts")
                
                missing_md = [inc for inc in report.inconsistencies 
                             if inc.type == "missing" and inc.source == "markdown_folder"]
                if missing_md:
                    lines.append("- Export graph to Markdown folder to add missing contacts")
                
                # Check for orphaned files
                orphaned_vcf = [inc for inc in report.inconsistencies 
                               if inc.type == "orphaned" and inc.source == "vcf_folder"]
                if orphaned_vcf:
                    lines.append("- Import VCF folder to add orphaned contacts to graph")
                
                orphaned_md = [inc for inc in report.inconsistencies 
                              if inc.type == "orphaned" and inc.source == "markdown_folder"]
                if orphaned_md:
                    lines.append("- Import Markdown folder to add orphaned contacts to graph")
                
                # Check for outdated files
                outdated = [inc for inc in report.inconsistencies if inc.type == "outdated"]
                if outdated:
                    lines.append("- Review REV timestamps to determine which version is correct")
                    lines.append("- Export graph with --force to update outdated files")
            
            lines.append("")
            lines.append(f"Checked at: {report.checked_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return "\n".join(lines)
