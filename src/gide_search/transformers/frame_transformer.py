from gide_search.transformers.base_transformer import Transformer


class FrameTransformer(Transformer):

    def _get_ro_crate_context(self) -> str | dict | list[dict | str]:
        return "https://www.gide-project.org/ro-crate/search/1.0/context"

    def _get_ro_crate_context_with_containers(self) -> list | str:
        return [
            "https://www.gide-project.org/ro-crate/search/1.0/context",
            {
                "hasCellLine": {"@id": "bao:BAO_0002004", "@container": "@set"},
                "measurementMethod": {
                    "@id": "dwciri:measurementMethod",
                    "@container": "@set",
                },
                "measurementTechnique": {
                    "@id": "http://schema.org/measurementTechnique",
                    "@container": "@set",
                },
                "seeAlso": {"@id": "rdf:seeAlso", "@container": "@set"},
                "about": {"@id": "http://schema.org/about", "@container": "@set"},
                "citation": {"@id": "http://schema.org/citation", "@container": "@set"},
                "author": {"@id": "http://schema.org/author", "@container": "@set"},
                "affiliation": {
                    "@id": "http://schema.org/affiliation",
                    "@container": "@set",
                },
                "funder": {"@id": "http://schema.org/funder", "@container": "@set"},
                "keywords": {"@id": "http://schema.org/keywords", "@container": "@set"},
                "size": {"@id": "http://schema.org/size", "@container": "@set"},
                "thumbnailUrl": {
                    "@id": "http://schema.org/thumbnailUrl",
                    "@container": "@set",
                },
                "taxonomicRange": {
                    "@id": "http://schema.org/taxonomicRange",
                    "@container": "@set",
                },
                "@type": {"@container": "@set"},
            },
        ]
