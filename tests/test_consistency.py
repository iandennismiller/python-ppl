"""
Tests for ConsistencyService.
"""
import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from ppl.services import ConsistencyService, Inconsistency, ConsistencyReport
from ppl.models import Contact, ContactGraph
from ppl.serializers import vcard, markdown


class TestInconsistency:
    """Test Inconsistency dataclass."""
    
    def test_inconsistency_str(self):
        """Test string representation."""
        inc = Inconsistency(
            type="missing",
            source="vcf_folder",
            target="uid-123",
            details="Contact not found"
        )
        assert str(inc) == "[MISSING] Contact not found"


class TestConsistencyReport:
    """Test ConsistencyReport dataclass."""
    
    def test_report_is_consistent_when_empty(self):
        """Test report is consistent when no inconsistencies."""
        report = ConsistencyReport()
        assert report.is_consistent
        assert report.error_count == 0
        assert report.warning_count == 0
    
    def test_report_is_inconsistent_when_has_issues(self):
        """Test report is inconsistent when has issues."""
        report = ConsistencyReport()
        report.add_inconsistency(Inconsistency(
            type="missing",
            source="vcf_folder",
            details="Test"
        ))
        assert not report.is_consistent
        assert report.warning_count == 1
    
    def test_report_counts_errors_and_warnings(self):
        """Test report counts errors and warnings correctly."""
        report = ConsistencyReport()
        report.add_inconsistency(Inconsistency(
            type="missing",
            source="vcf_folder",
            details="Test",
            severity="error"
        ))
        report.add_inconsistency(Inconsistency(
            type="outdated",
            source="vcf_folder",
            details="Test2",
            severity="warning"
        ))
        
        assert report.error_count == 1
        assert report.warning_count == 1


class TestConsistencyService:
    """Test ConsistencyService."""
    
    def test_check_graph_vcf_consistency_missing_folder(self):
        """Test checking VCF folder that doesn't exist."""
        graph = ContactGraph()
        service = ConsistencyService(graph)
        
        inconsistencies = service.check_graph_vcf_consistency("/nonexistent/folder")
        
        assert len(inconsistencies) == 1
        assert inconsistencies[0].type == "missing"
        assert inconsistencies[0].severity == "error"
    
    def test_check_graph_vcf_consistency_contact_in_graph_not_vcf(self):
        """Test contact exists in graph but not in VCF folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create graph with contact
            contact = Contact(fn="Alice", email=["alice@example.com"], uid="alice-uid")
            graph = ContactGraph()
            graph.add_contact(contact)
            
            # Create empty VCF folder
            vcf_folder = os.path.join(tmpdir, "vcf")
            os.makedirs(vcf_folder)
            
            service = ConsistencyService(graph)
            inconsistencies = service.check_graph_vcf_consistency(vcf_folder)
            
            assert len(inconsistencies) == 1
            assert inconsistencies[0].type == "missing"
            assert inconsistencies[0].source == "vcf_folder"
            assert "alice-uid" in inconsistencies[0].target
    
    def test_check_graph_vcf_consistency_orphaned_vcf(self):
        """Test VCF file exists but contact not in graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty graph
            graph = ContactGraph()
            
            # Create VCF folder with contact
            vcf_folder = os.path.join(tmpdir, "vcf")
            os.makedirs(vcf_folder)
            
            contact = Contact(fn="Bob", email=["bob@example.com"], uid="bob-uid")
            vcf_file = os.path.join(vcf_folder, "Bob.vcf")
            with open(vcf_file, 'w') as f:
                f.write(vcard.to_vcard(contact))
            
            service = ConsistencyService(graph)
            inconsistencies = service.check_graph_vcf_consistency(vcf_folder)
            
            assert len(inconsistencies) == 1
            assert inconsistencies[0].type == "orphaned"
            assert inconsistencies[0].source == "vcf_folder"
    
    def test_check_graph_vcf_consistency_consistent(self):
        """Test when graph and VCF folder are consistent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create contact
            contact = Contact(fn="Alice", email=["alice@example.com"], uid="alice-uid")
            contact.rev = datetime.now()
            
            # Add to graph
            graph = ContactGraph()
            graph.add_contact(contact)
            
            # Export to VCF folder
            vcf_folder = os.path.join(tmpdir, "vcf")
            os.makedirs(vcf_folder)
            vcf_file = os.path.join(vcf_folder, "Alice.vcf")
            with open(vcf_file, 'w') as f:
                f.write(vcard.to_vcard(contact))
            
            service = ConsistencyService(graph)
            inconsistencies = service.check_graph_vcf_consistency(vcf_folder)
            
            # Should be consistent
            assert len(inconsistencies) == 0
    
    def test_check_graph_markdown_consistency_missing_folder(self):
        """Test checking Markdown folder that doesn't exist."""
        graph = ContactGraph()
        service = ConsistencyService(graph)
        
        inconsistencies = service.check_graph_markdown_consistency("/nonexistent/folder")
        
        assert len(inconsistencies) == 1
        assert inconsistencies[0].type == "missing"
        assert inconsistencies[0].severity == "error"
    
    def test_check_all_representations(self):
        """Test comprehensive consistency check."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create contact
            contact = Contact(fn="Alice", email=["alice@example.com"], uid="alice-uid")
            contact.rev = datetime.now()
            
            # Add to graph
            graph = ContactGraph()
            graph.add_contact(contact)
            
            # Create VCF folder
            vcf_folder = os.path.join(tmpdir, "vcf")
            os.makedirs(vcf_folder)
            
            # Create Markdown folder with contact
            md_folder = os.path.join(tmpdir, "md")
            os.makedirs(md_folder)
            md_file = os.path.join(md_folder, "Alice.md")
            with open(md_file, 'w') as f:
                f.write(markdown.to_markdown(contact))
            
            service = ConsistencyService(graph)
            report = service.check_all_representations(
                vcf_folder=vcf_folder,
                markdown_folder=md_folder
            )
            
            # VCF folder is empty but markdown has contact
            assert report.total_contacts_graph == 1
            assert report.total_files_vcf == 0
            assert report.total_files_markdown == 1
            assert not report.is_consistent  # Should find missing VCF
    
    def test_generate_report_text_format(self):
        """Test text format report generation."""
        graph = ContactGraph()
        contact = Contact(fn="Alice", email=["alice@example.com"], uid="alice-uid")
        graph.add_contact(contact)
        
        service = ConsistencyService(graph)
        report = ConsistencyReport()
        report.total_contacts_graph = 1
        
        report_text = service.generate_report(report, format="text")
        
        assert "Consistency Check Report" in report_text
        assert "CONSISTENT" in report_text
        assert "Total contacts in graph: 1" in report_text
    
    def test_generate_report_json_format(self):
        """Test JSON format report generation."""
        graph = ContactGraph()
        service = ConsistencyService(graph)
        
        report = ConsistencyReport()
        report.total_contacts_graph = 1
        report.add_inconsistency(Inconsistency(
            type="missing",
            source="vcf_folder",
            target="uid-123",
            details="Test inconsistency"
        ))
        
        report_text = service.generate_report(report, format="json")
        
        assert '"is_consistent": false' in report_text
        assert '"total_contacts_graph": 1' in report_text
        assert '"type": "missing"' in report_text
    
    def test_generate_report_yaml_format(self):
        """Test YAML format report generation."""
        graph = ContactGraph()
        service = ConsistencyService(graph)
        
        report = ConsistencyReport()
        report.total_contacts_graph = 1
        
        report_text = service.generate_report(report, format="yaml")
        
        assert "is_consistent: true" in report_text
        assert "total_contacts_graph: 1" in report_text
