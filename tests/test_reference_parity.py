import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "skills"
    / "education-industry-observation"
    / "scripts"
    / "validate_reference_parity.py"
)
SPEC = importlib.util.spec_from_file_location("validate_reference_parity", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def valid_manifest():
    return {
        "mode": "reference_parity",
        "reference": {
            "file": "reference.pdf",
            "sha256": "a" * 64,
        },
        "expected": {
            "page_count": 8,
            "page_size_pts": [720, 540],
            "required_fonts": ["KaiTi", "SimSun"],
            "reference_items": [
                {
                    "reference_id": "R01",
                    "page": 2,
                    "short_title": "天立国际",
                    "content_markers": ["天立国际", "天籁科技"],
                    "event_date": "2026-06-09",
                    "date_scope": "reference_carryover",
                    "sources": [
                        {
                            "name": "公司公告",
                            "url": "https://example.com/a.pdf",
                            "published_at": "2026-06-10",
                            "access_checked_at": "2026-07-23",
                        }
                    ],
                }
            ],
        },
        "output_items": [{"reference_id": "R01", "page": 2}],
    }


class ReferenceParityTests(unittest.TestCase):
    def test_valid_manifest_passes(self):
        self.assertEqual(MODULE.validate_manifest(valid_manifest()), [])

    def test_missing_reference_item_fails(self):
        manifest = valid_manifest()
        manifest["output_items"] = []
        issues = MODULE.validate_manifest(manifest)
        self.assertTrue(any("output_items 必须是非空列表" in issue for issue in issues))
        self.assertTrue(any("成品缺少样稿事项" in issue for issue in issues))

    def test_page_mapping_must_match(self):
        manifest = valid_manifest()
        manifest["output_items"][0]["page"] = 3
        issues = MODULE.validate_manifest(manifest)
        self.assertTrue(any("与样稿页码不一致" in issue for issue in issues))

    def test_sources_are_required(self):
        manifest = valid_manifest()
        manifest["expected"]["reference_items"][0]["sources"] = []
        issues = MODULE.validate_manifest(manifest)
        self.assertTrue(any("sources 必须是非空列表" in issue for issue in issues))

    def test_date_scope_is_typed(self):
        manifest = valid_manifest()
        manifest["expected"]["reference_items"][0]["date_scope"] = "outside"
        issues = MODULE.validate_manifest(manifest)
        self.assertTrue(any("within_period 或 reference_carryover" in issue for issue in issues))

    def test_reference_hash_is_required(self):
        manifest = valid_manifest()
        manifest["reference"]["sha256"] = "not-a-hash"
        issues = MODULE.validate_manifest(manifest)
        self.assertTrue(any("64 位 SHA-256" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
