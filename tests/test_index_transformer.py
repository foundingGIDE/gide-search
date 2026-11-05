import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from gide_search.cli import app
from gide_search.search.schema_search_object import BioSample, DefinedTerm

runner = CliRunner()


def _create_rocrate_with_test_entities(test_name, test_entities: dict[str, list]):

    graph_objects = []
    [graph_objects.extend(entities) for entities in test_entities.values()]

    id_references = {}
    for field, entities in test_entities.items():
        id_references[field] = [
            {"@id": ro_crate_entity["@id"]} for ro_crate_entity in entities
        ]

    ro_crate = {
        "@context": "https://www.gide-project.org/ro-crate/search/1.0/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {
                    "@id": "https://www.gide-project.org/ro-crate/search/1.0/profile"
                },
                "about": {"@id": "https://example.org/dataset"},
            },
            {
                "@id": "https://example.org/dataset",
                "@type": "Dataset",
                "identifier": test_name,
                "name": f"Test: {test_name}",
                "description": f"Edge case test for {test_name}",
                "datePublished": "2024-01-01",
                "license": "https://creativecommons.org/licenses/by/4.0/",
                "publisher": {
                    "@id": "https://example.org",
                },
                "author": [{"@id": "#author"}],
                "about": id_references.get("about", [])
                + [{"@id": "obo:NCBITaxon_00000001"}],
                "measurementMethod": id_references.get("measurementMethod", [])
                + [{"@id": "obo:FBbi_00000001"}],
            },
            {
                "@id": "#author",
                "@type": "Person",
                "name": "Test Author",
            },
            {
                "@id": "https://example.org",
                "@type": "Organization",
                "name": "Example Publisher",
            },
            {
                "@type": ["DefinedTerm"],
                "@id": "obo:FBbi_00000001",
                "name": "Placeholder measurement method",
            },
            {
                "@type": ["Taxon"],
                "@id": "obo:NCBITaxon_00000001",
                "scientificName": "Test species",
            },
        ],
    }

    ro_crate["@graph"] += graph_objects

    return ro_crate


def test_index_transform_default(tmpdir, monkeypatch):
    """Test transformation of the default test fixture."""

    def mock_fetch_label_by_iri(self, term_iri: str) -> str | None:
        if term_iri == "http://purl.obolibrary.org/obo/FBbi_00000251":
            return "confocal microscopy"
        if term_iri == "http://purl.obolibrary.org/obo/NCBITaxon_10090":
            return "Mus musculus"
        return None

    def mock_ontology_term_finder_init(self):
        self.ebi_client = None
        self.avaliable_ontology_ids = ["fbbi", "ncbitaxon"]

    monkeypatch.setattr(
        "gide_search.utils.ontology_term_finder.OntologyTermFinder.__init__",
        mock_ontology_term_finder_init,
    )
    monkeypatch.setattr(
        "gide_search.utils.ontology_term_finder.OntologyTermFinder.fetch_label_by_iri",
        mock_fetch_label_by_iri,
    )

    result = runner.invoke(
        app,
        [
            "data",
            "transform-to-index",
            str(Path(__file__).parent / "data/gide_search_ro_crate"),
            "-o",
            str(tmpdir),
        ],
    )

    assert result.exit_code == 0

    with open(tmpdir / "index.json") as f:
        output_index = json.loads(f.read())

    expected_index_path = (
        Path(__file__).parent / "data/index_document/example_ro_crate_index.json"
    )
    with open(expected_index_path) as f:
        expected_index = json.loads(f.read())

    assert output_index == expected_index


def test_invalid_cell_line_defined_terms_are_dropped():
    biosample = BioSample.model_validate(
        {
            "@id": "https://example.org/sample",
            "@type": ["BioSample"],
            "name": "Test sample",
            "description": "Test sample description",
            "hasCellLine": [
                {"@id": "https://example.org/missing_type", "name": "Missing type"},
                {
                    "@id": "https://example.org/invalid-cell-line",
                    "@type": "DefinedTerm",
                },
                {
                    "@id": "https://example.org/valid-cell-line",
                    "@type": ["DefinedTerm"],
                    "name": "Valid cell line",
                },
                "Unspecified cell line",
            ],
        }
    )

    cell_lines = biosample.hasCellLine
    assert isinstance(cell_lines, list)
    assert len(cell_lines) == 3
    assert isinstance(cell_lines[0], DefinedTerm)
    assert cell_lines[0].name == "Missing type"
    assert isinstance(cell_lines[1], DefinedTerm)
    assert cell_lines[1].name == "Valid cell line"
    assert cell_lines[2] == "Unspecified cell line"


@pytest.mark.parametrize(
    "taxon_id,expected_id,scientific_name",
    [
        (
            "obo:NCBITaxon_06239",
            "http://purl.obolibrary.org/obo/NCBITaxon_6239",
            "Caenorhabditis elegans",
        ),
        (
            "obo:NCBITaxon_00006239",
            "http://purl.obolibrary.org/obo/NCBITaxon_6239",
            "Caenorhabditis elegans",
        ),
        (
            "http://purl.obolibrary.org/obo/NCBITaxon_10090",
            "http://purl.obolibrary.org/obo/NCBITaxon_10090",
            "Mus musculus",
        ),
        (
            "http://purl.obolibrary.org/obo/NCBITaxon_09606",
            "http://purl.obolibrary.org/obo/NCBITaxon_9606",
            "Homo sapiens",
        ),
        (
            "http://purl.obolibrary.org/obo/NCBITaxon_00006239",
            "http://purl.obolibrary.org/obo/NCBITaxon_6239",
            "Caenorhabditis elegans",
        ),
        (
            "https://www.ncbi.nlm.nih.gov/datasets/taxonomy/10090/",
            "http://purl.obolibrary.org/obo/NCBITaxon_10090",
            "Mus musculus",
        ),
        (
            "https://www.ncbi.nlm.nih.gov/datasets/taxonomy/00010090/",
            "http://purl.obolibrary.org/obo/NCBITaxon_10090",
            "Mus musculus",
        ),
    ],
)
def test_ncbitaxon_normalization(tmpdir, taxon_id, expected_id, scientific_name):
    """Validate that NCBITaxon IDs are normalized for compact and full URI inputs."""
    edge_cases = {
        "about": [
            {"@type": ["Taxon"], "@id": taxon_id, "scientificName": scientific_name}
        ],
    }

    ro_crate_content = _create_rocrate_with_test_entities(
        "ncbitaxon-normalization", edge_cases
    )

    source_dir = tmpdir / "source"
    source_dir.mkdir()

    with open(source_dir / "test-ro-crate-metadata.json", "w") as f:
        json.dump(ro_crate_content, f)

    output_dir = tmpdir / "output"
    output_dir.mkdir()

    result = runner.invoke(
        app,
        [
            "data",
            "transform-to-index",
            str(source_dir),
            "-o",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0

    with open(output_dir / "index.json") as f:
        index_document = json.load(f)

    assert len(index_document) == 1
    about_items = index_document[0].get("about", [])
    assert about_items
    assert about_items[0]["id"] == expected_id


@pytest.mark.parametrize(
    "fbbi_id,expected_id,description",
    [
        (
            "obo:FBbi_00000246",
            "http://purl.obolibrary.org/obo/FBbi_00000246",
            "obo-prefix expansion",
        ),
        (
            "obo:fbbi_00000246",
            "http://purl.obolibrary.org/obo/FBbi_00000246",
            "lowercase prefix normalization",
        ),
        (
            "obo:FBbi_455",
            "http://purl.obolibrary.org/obo/FBbi_00000455",
            "short ID padding to 8 digits",
        ),
        (
            "http://purl.obolibrary.org/obo/FBbi_455",
            "http://purl.obolibrary.org/obo/FBbi_00000455",
            "full URI short ID padding to 8 digits",
        ),
        (
            "obo:FBbi_000000455",
            "http://purl.obolibrary.org/obo/FBbi_00000455",
            "too many leading zeros",
        ),
    ],
)
def test_fbbi_id_normalization(tmpdir, monkeypatch, fbbi_id, expected_id, description):
    edge_cases = {
        "measurementMethod": [
            {
                "@type": ["DefinedTerm"],
                "@id": fbbi_id,
                "name": f"Test imaging method ({description})",
            }
        ],
    }

    ro_crate = _create_rocrate_with_test_entities("fbbi-normalization", edge_cases)

    source_dir = tmpdir / "source"
    source_dir.mkdir()

    with open(source_dir / "test-ro-crate-metadata.json", "w") as f:
        json.dump(ro_crate, f)

    output_dir = tmpdir / "output"
    output_dir.mkdir()

    result = runner.invoke(
        app,
        [
            "data",
            "transform-to-index",
            str(source_dir),
            "-o",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0

    with open(output_dir / "index.json") as f:
        index_document = json.load(f)

    assert len(index_document) == 1
    measurement_methods = index_document[0].get("measurementMethod", [])
    assert measurement_methods
    assert measurement_methods[0]["id"] == expected_id


def test_index_transform(tmpdir, monkeypatch):
    """Test transformation of the default test fixture."""

    result = runner.invoke(
        app,
        [
            "data",
            "transform-to-index",
            str(Path(__file__).parent.parent / "output/ro-crate/"),
            "-o",
            str(tmpdir),
        ],
    )

    assert result.exit_code == 0
