"""
Integration tests that simulate complete user workflows.

These tests demonstrate end-to-end functionality and inter-operation
of all PPL modules including models, serializers, filters, and graph management.
"""
import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from ppl.models import Contact, Related, Relationship, ContactGraph, FilterContext, import_pipeline
from ppl.serializers import vcard, yaml_serializer, markdown
from ppl.filters import UIDFilter, GenderFilter


class TestCompleteWorkflows:
    """Test complete user workflows from start to finish."""
    
    def test_workflow_create_contacts_and_export_vcard(self):
        """
        Workflow: Create contacts programmatically and export to vCard format.
        
        Simulates a user creating contacts in code and saving them as vCard files.
        """
        # Step 1: Create contacts
        alice = Contact(
            fn="Alice Johnson",
            email=["alice@example.com", "ajohnson@work.com"],
            tel=["+1-555-0100"],
            org=["Tech Corp"],
            title="Software Engineer"
        )
        
        bob = Contact(
            fn="Bob Smith",
            email=["bob@example.com"],
            tel=["+1-555-0200"],
            org=["Tech Corp"],
            title="Product Manager"
        )
        
        # Step 2: Apply filters to assign UIDs
        import_pipeline.filters.clear()
        import_pipeline.register(UIDFilter())
        
        context = FilterContext(pipeline_name="import")
        alice = import_pipeline.run(alice, context)
        bob = import_pipeline.run(bob, context)
        
        # Verify UIDs were assigned
        assert alice.uid is not None
        assert bob.uid is not None
        
        # Step 3: Add relationships
        alice.related.append(Related(uri=alice.uid, type=["colleague"]))
        bob.related.append(Related(uri=bob.uid, type=["colleague"]))
        
        # Step 4: Export to vCard
        with tempfile.TemporaryDirectory() as tmpdir:
            vcard.bulk_export([alice, bob], tmpdir)
            
            # Verify files exist
            assert os.path.exists(os.path.join(tmpdir, "Alice Johnson.vcf"))
            assert os.path.exists(os.path.join(tmpdir, "Bob Smith.vcf"))
            
            # Verify content
            with open(os.path.join(tmpdir, "Alice Johnson.vcf"), 'r') as f:
                content = f.read()
                assert "Alice Johnson" in content
                assert "alice@example.com" in content
                assert "RELATED" in content
    
    def test_workflow_import_vcard_build_graph_export_markdown(self):
        """
        Workflow: Import vCard files, build a graph, and export to Markdown.
        
        Simulates importing existing vCard files, creating a contact graph,
        and exporting to human-readable Markdown format.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create and export vCard files
            contacts = [
                Contact(fn="Alice", uid="alice-uid", email=["alice@example.com"]),
                Contact(fn="Bob", uid="bob-uid", email=["bob@example.com"]),
                Contact(fn="Charlie", uid="charlie-uid", email=["charlie@example.com"])
            ]
            
            # Add relationships
            contacts[0].related.append(Related(uri="urn:uuid:bob-uid", type=["friend"]))
            contacts[0].related.append(Related(uri="urn:uuid:charlie-uid", type=["colleague"]))
            
            vcard_dir = os.path.join(tmpdir, "vcards")
            vcard.bulk_export(contacts, vcard_dir)
            
            # Step 2: Import vCard files
            imported = vcard.bulk_import(vcard_dir)
            assert len(imported) == 3
            
            # Step 3: Build contact graph
            graph = ContactGraph()
            for contact in imported:
                graph.add_contact(contact)
            
            assert len(graph.get_all_contacts()) == 3
            
            # Step 4: Export to Markdown
            md_dir = os.path.join(tmpdir, "markdown")
            markdown.bulk_export_markdown(imported, md_dir)
            
            # Verify Markdown files
            assert os.path.exists(os.path.join(md_dir, "Alice.md"))
            
            # Check Markdown content
            with open(os.path.join(md_dir, "Alice.md"), 'r') as f:
                content = f.read()
                assert "---" in content  # YAML front matter
                assert "FN: Alice" in content
                assert "## Related" in content or len(imported[0].related) == 0
    
    def test_workflow_format_conversion_roundtrip(self):
        """
        Workflow: Convert between all formats and verify data integrity.
        
        Tests: vCard -> YAML -> Markdown -> vCard roundtrip.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Original contact
            original = Contact(
                fn="Jane Doe",
                uid="jane-uid",
                email=["jane@example.com"],
                tel=["+1-555-0300"],
                title="Designer",
                note="Lead designer"
            )
            
            # Step 1: Export to vCard
            vcard_dir = os.path.join(tmpdir, "step1_vcard")
            vcard.bulk_export([original], vcard_dir)
            
            # Step 2: Import from vCard
            from_vcard = vcard.bulk_import(vcard_dir)[0]
            assert from_vcard.fn == original.fn
            
            # Step 3: Export to YAML
            yaml_str = yaml_serializer.to_yaml(from_vcard)
            
            # Step 4: Import from YAML
            from_yaml = yaml_serializer.from_yaml(yaml_str)
            assert from_yaml.fn == original.fn
            assert from_yaml.uid == original.uid
            
            # Step 5: Export to Markdown
            md_str = markdown.to_markdown(from_yaml)
            
            # Step 6: Import from Markdown
            from_markdown = markdown.from_markdown(md_str)
            assert from_markdown.fn == original.fn
            assert from_markdown.uid == original.uid
            
            # Step 7: Back to vCard
            final_vcard = vcard.to_vcard(from_markdown)
            
            # Verify no data loss
            final_contact = vcard.from_vcard(final_vcard)
            assert final_contact.fn == original.fn
            assert final_contact.uid == original.uid
            assert final_contact.title == original.title
    
    def test_workflow_filter_pipeline_integration(self):
        """
        Workflow: Import contacts, apply filters, build graph with relationships.
        
        Tests the integration of import, filter pipeline, and graph operations.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create contacts without UIDs or gender
            contacts = [
                Contact(fn="Alice", email=["alice@example.com"]),
                Contact(fn="Bob", email=["bob@example.com"]),
                Contact(
                    fn="Carol",
                    email=["carol@example.com"],
                    related=[Related(uri="urn:uuid:placeholder", type=["mother"])]
                )
            ]
            
            # Step 2: Apply filter pipeline
            import_pipeline.filters.clear()
            import_pipeline.register(UIDFilter())
            import_pipeline.register(GenderFilter())
            
            context = FilterContext(pipeline_name="import")
            filtered = [import_pipeline.run(c, context) for c in contacts]
            
            # Verify UIDs assigned
            assert all(c.uid is not None for c in filtered)
            
            # Verify gender inference (Carol should be female based on "mother")
            carol = next(c for c in filtered if c.fn == "Carol")
            assert carol.gender == 'F'
            
            # Step 3: Build graph
            graph = ContactGraph()
            for contact in filtered:
                graph.add_contact(contact)
            
            # Step 4: Export and re-import to verify persistence
            vcard.bulk_export(filtered, tmpdir)
            reimported = vcard.bulk_import(tmpdir)
            
            # Verify all data preserved
            assert len(reimported) == 3
            carol_reimported = next(c for c in reimported if c.fn == "Carol")
            assert carol_reimported.gender == 'F'
            assert carol_reimported.uid == carol.uid
    
    def test_workflow_relationship_graph_operations(self):
        """
        Workflow: Create a complex relationship network and traverse it.
        
        Tests graph operations with multiple relationship types and directions.
        """
        # Step 1: Create a family/friend network
        alice = Contact(fn="Alice", uid="alice-uid")
        bob = Contact(fn="Bob", uid="bob-uid")
        charlie = Contact(fn="Charlie", uid="charlie-uid")
        diana = Contact(fn="Diana", uid="diana-uid")
        
        # Step 2: Build graph
        graph = ContactGraph()
        graph.add_contact(alice)
        graph.add_contact(bob)
        graph.add_contact(charlie)
        graph.add_contact(diana)
        
        # Step 3: Add various relationships
        # Alice and Bob are friends
        rel1 = Relationship(source=alice, target=bob, types=["friend"], directional=False)
        graph.add_relationship(rel1)
        
        # Charlie is Alice's parent
        rel2 = Relationship(source=alice, target=charlie, types=["parent"], directional=True)
        graph.add_relationship(rel2)
        
        # Diana is Alice's colleague
        rel3 = Relationship(source=alice, target=diana, types=["colleague"], directional=False)
        graph.add_relationship(rel3)
        
        # Step 4: Query relationships
        alice_rels = graph.get_relationships("alice-uid")
        assert len(alice_rels) == 3
        
        # Verify relationship types
        rel_types = [rel.types[0] for rel in alice_rels]
        assert "friend" in rel_types
        assert "parent" in rel_types
        assert "colleague" in rel_types
        
        # Step 5: Export with relationships as RELATED properties
        alice_updated = graph.get_contact("alice-uid")
        alice_updated = vcard.inject_relationships(alice_updated, alice_rels)
        
        assert len(alice_updated.related) == 3
    
    def test_workflow_markdown_wiki_links_resolution(self):
        """
        Workflow: Create Markdown files with wiki-style links and resolve them.
        
        Tests Markdown import/export with wiki-link resolution for relationships.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create contacts
            alice = Contact(fn="Alice Johnson", uid="alice-uid", email=["alice@example.com"])
            bob = Contact(fn="Bob Smith", uid="bob-uid", email=["bob@example.com"])
            
            # Step 2: Export to Markdown
            markdown.bulk_export_markdown([alice, bob], tmpdir)
            
            # Step 3: Manually add wiki-style relationships to one file
            alice_file = os.path.join(tmpdir, "Alice Johnson.md")
            with open(alice_file, 'r') as f:
                content = f.read()
            
            # Add Related section with wiki link
            if "## Related" not in content:
                content += "\n## Related\n\n- friend [[Bob Smith]]\n"
            
            with open(alice_file, 'w') as f:
                f.write(content)
            
            # Step 4: Re-import with wiki-link resolution
            alice_reimported = markdown.from_markdown(open(alice_file, 'r').read(), tmpdir)
            
            # Verify wiki link was parsed
            assert len(alice_reimported.related) >= 1
            friend_rel = next((r for r in alice_reimported.related if 'friend' in r.type), None)
            assert friend_rel is not None
    
    def test_workflow_merge_contacts_by_rev(self):
        """
        Workflow: Import contacts and merge based on REV timestamps.
        
        Tests REV-based merge logic for handling duplicate contacts.
        """
        # Step 1: Create two versions of the same contact
        older = Contact(
            fn="John Doe",
            uid="john-uid",
            email=["old@example.com"],
            rev=datetime(2024, 1, 1)
        )
        
        newer = Contact(
            fn="John Doe",
            uid="john-uid",
            email=["new@example.com"],
            rev=datetime(2024, 6, 1)
        )
        
        # Step 2: Compare REV fields
        assert vcard.compare_rev(newer, older) is True
        assert vcard.compare_rev(older, newer) is False
        
        # Step 3: Simulate merge - keep newer
        with tempfile.TemporaryDirectory() as tmpdir:
            # Export both
            vcard.export_vcard(older, os.path.join(tmpdir, "older.vcf"))
            vcard.export_vcard(newer, os.path.join(tmpdir, "newer.vcf"))
            
            # Import both
            imported = vcard.bulk_import(tmpdir)
            
            # Both should be imported (same UID but different filenames)
            assert len(imported) == 2
            
            # In a real merge scenario, we'd keep the newer one
            merged = newer if vcard.compare_rev(newer, older) else older
            assert merged.email == ["new@example.com"]
    
    def test_workflow_collaborative_contact_management(self):
        """
        Workflow: Multiple users managing shared contact database.
        
        Simulates a collaborative scenario where multiple people maintain
        the same contact database using different formats.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            vcard_dir = os.path.join(tmpdir, "vcards")
            yaml_dir = os.path.join(tmpdir, "yaml")
            md_dir = os.path.join(tmpdir, "markdown")
            
            # User 1: Creates initial contacts in vCard
            user1_contacts = [
                Contact(fn="Alice", uid="alice-uid", email=["alice@example.com"]),
                Contact(fn="Bob", uid="bob-uid", email=["bob@example.com"])
            ]
            vcard.bulk_export(user1_contacts, vcard_dir)
            
            # User 2: Imports vCards and exports to YAML for editing
            imported = vcard.bulk_import(vcard_dir)
            Path(yaml_dir).mkdir(exist_ok=True)
            for contact in imported:
                yaml_file = os.path.join(yaml_dir, f"{contact.fn}.yaml")
                with open(yaml_file, 'w') as f:
                    f.write(yaml_serializer.to_yaml(contact))
            
            # User 2: Modifies a contact in YAML
            with open(os.path.join(yaml_dir, "Alice.yaml"), 'r') as f:
                alice_yaml = f.read()
            
            alice_from_yaml = yaml_serializer.from_yaml(alice_yaml)
            alice_from_yaml.tel = ["+1-555-1111"]
            
            with open(os.path.join(yaml_dir, "Alice.yaml"), 'w') as f:
                f.write(yaml_serializer.to_yaml(alice_from_yaml))
            
            # User 3: Imports YAML and exports to Markdown for reading
            yaml_files = list(Path(yaml_dir).glob("*.yaml"))
            md_contacts = []
            for yaml_file in yaml_files:
                with open(yaml_file, 'r') as f:
                    contact = yaml_serializer.from_yaml(f.read())
                    md_contacts.append(contact)
            
            markdown.bulk_export_markdown(md_contacts, md_dir)
            
            # Verify all formats are in sync
            md_imported = markdown.bulk_import_markdown(md_dir)
            alice_final = next(c for c in md_imported if c.fn == "Alice")
            assert "+1-555-1111" in alice_final.tel
            assert alice_final.uid == "alice-uid"
    
    def test_workflow_contact_network_analysis(self):
        """
        Workflow: Build a contact network and analyze connections.
        
        Tests creating a complex relationship network and querying it.
        """
        # Step 1: Create a network of contacts
        contacts = {
            'alice': Contact(fn="Alice", uid="alice-uid"),
            'bob': Contact(fn="Bob", uid="bob-uid"),
            'charlie': Contact(fn="Charlie", uid="charlie-uid"),
            'diana': Contact(fn="Diana", uid="diana-uid"),
            'eve': Contact(fn="Eve", uid="eve-uid")
        }
        
        # Step 2: Build graph
        graph = ContactGraph()
        for contact in contacts.values():
            graph.add_contact(contact)
        
        # Step 3: Add relationships to create a network
        # Alice knows Bob, Charlie, Diana
        graph.add_relationship(Relationship(
            source=contacts['alice'],
            target=contacts['bob'],
            types=["friend"]
        ))
        graph.add_relationship(Relationship(
            source=contacts['alice'],
            target=contacts['charlie'],
            types=["colleague"]
        ))
        graph.add_relationship(Relationship(
            source=contacts['alice'],
            target=contacts['diana'],
            types=["friend"]
        ))
        
        # Bob knows Charlie and Eve
        graph.add_relationship(Relationship(
            source=contacts['bob'],
            target=contacts['charlie'],
            types=["colleague"]
        ))
        graph.add_relationship(Relationship(
            source=contacts['bob'],
            target=contacts['eve'],
            types=["friend"]
        ))
        
        # Step 4: Analyze network
        alice_connections = graph.get_relationships("alice-uid")
        assert len(alice_connections) == 3
        
        bob_connections = graph.get_relationships("bob-uid")
        assert len(bob_connections) == 2
        
        # Step 5: Export network with relationships
        all_contacts = graph.get_all_contacts()
        
        # Inject relationships into contacts for export
        for contact in all_contacts:
            rels = graph.get_relationships(contact.uid)
            vcard.inject_relationships(contact, rels)
        
        # Export and verify
        with tempfile.TemporaryDirectory() as tmpdir:
            vcard.bulk_export(all_contacts, tmpdir)
            
            # Re-import and verify relationships preserved
            reimported = vcard.bulk_import(tmpdir)
            alice_reimported = next(c for c in reimported if c.fn == "Alice")
            assert len(alice_reimported.related) == 3
    
    def test_workflow_gender_inference_from_relationships(self):
        """
        Workflow: Import contacts with family relationships and infer gender.
        
        Tests gender inference filter working with relationship data.
        """
        # Step 1: Create contacts with gendered relationship terms
        contacts = [
            Contact(
                fn="Mary",
                email=["mary@example.com"],
                related=[
                    Related(uri="urn:uuid:child1", type=["mother"]),
                    Related(uri="urn:uuid:child2", type=["mother"])
                ]
            ),
            Contact(
                fn="John",
                email=["john@example.com"],
                related=[
                    Related(uri="urn:uuid:child1", type=["father"])
                ]
            ),
            Contact(
                fn="Sam",
                email=["sam@example.com"],
                related=[
                    Related(uri="urn:uuid:friend1", type=["friend"])
                ]
            )
        ]
        
        # Step 2: Apply filter pipeline
        import_pipeline.filters.clear()
        import_pipeline.register(UIDFilter())
        import_pipeline.register(GenderFilter())
        
        context = FilterContext(pipeline_name="import")
        filtered = [import_pipeline.run(c, context) for c in contacts]
        
        # Step 3: Verify gender inference
        mary = next(c for c in filtered if c.fn == "Mary")
        assert mary.gender == 'F'  # Inferred from "mother"
        
        john = next(c for c in filtered if c.fn == "John")
        assert john.gender == 'M'  # Inferred from "father"
        
        sam = next(c for c in filtered if c.fn == "Sam")
        assert sam.gender is None  # "friend" is gender-neutral
        
        # Step 4: Export and verify gender is preserved
        with tempfile.TemporaryDirectory() as tmpdir:
            vcard.bulk_export(filtered, tmpdir)
            reimported = vcard.bulk_import(tmpdir)
            
            mary_reimported = next(c for c in reimported if c.fn == "Mary")
            assert mary_reimported.gender == 'F'
    
    def test_workflow_bulk_operations_with_filters(self):
        """
        Workflow: Bulk import folder, apply filters, and export.
        
        Tests the complete pipeline from import to export with filtering.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "input")
            output_dir = os.path.join(tmpdir, "output")
            
            # Step 1: Create input files without UIDs
            contacts = [
                Contact(fn=f"Person {i}", email=[f"person{i}@example.com"])
                for i in range(10)
            ]
            
            # Export without UIDs
            Path(input_dir).mkdir(exist_ok=True)
            for contact in contacts:
                filename = f"{contact.fn}.vcf"
                vcard.export_vcard(contact, os.path.join(input_dir, filename))
            
            # Step 2: Bulk import
            imported = vcard.bulk_import(input_dir)
            assert len(imported) == 10
            
            # Step 3: Apply filters
            import_pipeline.filters.clear()
            import_pipeline.register(UIDFilter())
            
            context = FilterContext(pipeline_name="import")
            filtered = import_pipeline.run_batch(imported, context)
            
            # Verify all have UIDs now
            assert all(c.uid is not None for c in filtered)
            
            # Step 4: Bulk export
            vcard.bulk_export(filtered, output_dir)
            
            # Step 5: Verify output
            output_files = list(Path(output_dir).glob("*.vcf"))
            assert len(output_files) == 10
            
            # Re-import and verify UIDs persist
            final_import = vcard.bulk_import(output_dir)
            assert all(c.uid is not None for c in final_import)


class TestCrossFormatIntegration:
    """Test integration between different serialization formats."""
    
    def test_vcard_to_yaml_to_markdown_pipeline(self):
        """Test data integrity through vCard -> YAML -> Markdown pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create contact in vCard
            original = Contact(
                fn="Integration Test",
                uid="test-uid",
                email=["test@example.com"],
                tel=["+1-555-9999"],
                related=[Related(uri="urn:uuid:related-uid", type=["friend"])]
            )
            
            # vCard
            vcard_file = os.path.join(tmpdir, "test.vcf")
            vcard.export_vcard(original, vcard_file)
            from_vcard = vcard.import_vcard(vcard_file)
            
            # YAML
            yaml_str = yaml_serializer.to_yaml(from_vcard)
            from_yaml = yaml_serializer.from_yaml(yaml_str)
            
            # Markdown
            md_file = os.path.join(tmpdir, "test.md")
            with open(md_file, 'w') as f:
                f.write(markdown.to_markdown(from_yaml))
            
            with open(md_file, 'r') as f:
                from_md = markdown.from_markdown(f.read())
            
            # Verify data consistency
            assert from_md.fn == original.fn
            assert from_md.uid == original.uid
            assert from_md.email == original.email
    
    def test_flat_yaml_integration(self):
        """Test flat YAML format in complete workflow."""
        original = Contact(
            fn="Flat Test",
            uid="flat-uid",
            email=["flat@example.com", "flat2@example.com"],
            categories=["work", "friend"]
        )
        
        # Convert to flat YAML
        flat_yaml = yaml_serializer.to_flat_yaml(original)
        
        # Verify flat structure
        assert "EMAIL.0" in flat_yaml or "EMAIL:" in flat_yaml
        
        # Convert back
        from_flat = yaml_serializer.from_flat_yaml(flat_yaml)
        
        # Verify data
        assert from_flat.fn == original.fn
        assert from_flat.uid == original.uid
        assert len(from_flat.email) >= 1


class TestErrorHandlingIntegration:
    """Test error handling across module boundaries."""
    
    def test_invalid_contact_in_pipeline(self):
        """Test filter pipeline handles invalid contacts gracefully."""
        # Contact missing required field
        with pytest.raises(ValueError, match="FN"):
            Contact(fn="")
    
    def test_graph_operations_with_missing_contact(self):
        """Test graph operations with invalid references."""
        graph = ContactGraph()
        alice = Contact(fn="Alice", uid="alice-uid")
        bob = Contact(fn="Bob", uid="bob-uid")
        
        graph.add_contact(alice)
        # Don't add bob
        
        # Try to create relationship with missing target
        rel = Relationship(source=alice, target=bob, types=["friend"])
        
        with pytest.raises(ValueError, match="not in graph"):
            graph.add_relationship(rel)
    
    def test_file_not_found_handling(self):
        """Test graceful handling of missing files."""
        # Try to import from non-existent folder
        contacts = vcard.bulk_import("/nonexistent/folder")
        assert contacts == []
        
        # Try to resolve wiki link in non-existent folder
        resolved = markdown.resolve_wiki_link("Test", "/nonexistent/folder")
        assert resolved is None


class TestPerformanceIntegration:
    """Test performance with larger datasets."""
    
    def test_large_contact_list_operations(self):
        """Test operations with 100+ contacts."""
        # Step 1: Create many contacts
        contacts = [
            Contact(
                fn=f"Contact {i:03d}",
                uid=f"uid-{i:03d}",
                email=[f"contact{i}@example.com"]
            )
            for i in range(100)
        ]
        
        # Step 2: Build graph
        graph = ContactGraph()
        for contact in contacts:
            graph.add_contact(contact)
        
        assert len(graph.get_all_contacts()) == 100
        
        # Step 3: Add relationships (each contact knows the next one)
        for i in range(99):
            rel = Relationship(
                source=contacts[i],
                target=contacts[i + 1],
                types=["acquaintance"]
            )
            graph.add_relationship(rel)
        
        assert len(graph.get_all_relationships()) == 99
        
        # Step 4: Export and import
        with tempfile.TemporaryDirectory() as tmpdir:
            # Export all formats
            vcard.bulk_export(contacts, os.path.join(tmpdir, "vcard"))
            markdown.bulk_export_markdown(contacts, os.path.join(tmpdir, "markdown"))
            
            # Import back
            vcard_imported = vcard.bulk_import(os.path.join(tmpdir, "vcard"))
            md_imported = markdown.bulk_import_markdown(os.path.join(tmpdir, "markdown"))
            
            assert len(vcard_imported) == 100
            assert len(md_imported) == 100
