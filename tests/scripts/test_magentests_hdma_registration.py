"""TDD guard for the exact CTest names promised by Magen HDMA admission."""

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
REQUIRED = ("magentests_hblank_vram_dma", "cgb_hdma_magen_controls")


class MagenHdmaRegistrationTests(unittest.TestCase):
    def test_hdma_cases_are_registered_once_in_exact_inventory(self):
        names = (ROOT / "tests" / "expected-tests.txt").read_text().splitlines()
        counts = {name: names.count(name) for name in REQUIRED}
        self.assertEqual(counts, {name: 1 for name in REQUIRED})


if __name__ == "__main__":
    unittest.main()
