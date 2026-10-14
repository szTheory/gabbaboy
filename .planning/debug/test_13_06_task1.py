import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class SameSuiteAdmission(unittest.TestCase):
    def test_gbc_dma_cont_is_pinned_and_committed(self):
        manifest_path = ROOT / "fixtures" / "samesuite" / "manifest.json"
        manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
        aliases = {row.get("alias") for row in manifest.get("fixtures", [])}
        self.assertIn(
            "gbc_dma_cont",
            aliases,
            "approved gbc_dma_cont SameSuite source and ROM must be admitted",
        )


if __name__ == "__main__":
    unittest.main()
