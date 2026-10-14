import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
APPROVED = [
    "gbc_dma_cont",
    "gdma_addr_mask",
    "hdma_lcd_off",
    "hdma_mode0",
]


class SameSuiteFullAdmission(unittest.TestCase):
    def test_exact_four_cases_and_roms_are_admitted(self):
        fixture_dir = ROOT / "fixtures" / "samesuite"
        manifest = json.loads((fixture_dir / "manifest.json").read_text())
        aliases = [row.get("alias") for row in manifest.get("fixtures", [])]
        self.assertEqual(
            APPROVED,
            aliases,
            "D-16 admits exactly the four approved SameSuite DMA cases in order",
        )
        for row in manifest["fixtures"]:
            rom = fixture_dir / row["file"]
            self.assertEqual(row["size_bytes"], rom.stat().st_size, row["alias"])
            self.assertEqual("CGB-E", row["target_revision"], row["alias"])
            self.assertTrue(row["bootless_applicability"], row["alias"])


if __name__ == "__main__":
    unittest.main()
