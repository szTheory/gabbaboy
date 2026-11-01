from pathlib import Path
import json
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tests/scripts/verify-phase3-player.sh"
PREFIX = ROOT / "build/phase3-player/package-stage/installed-prefix"


class PlayerPackagePolicyCliTests(unittest.TestCase):
    def test_valid_player_prefix_passes_production_policy_cli(self):
        result = subprocess.run(
            ["bash", str(SCRIPT), "--check-package-policy", str(PREFIX)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        (ROOT / "build/phase3-player/20-03-task1-observation.json").write_text(
            json.dumps(
                {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
                indent=2,
            )
            + "\n"
        )
        self.assertEqual(
            result.returncode,
            0,
            "production policy command should accept the valid player prefix",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
