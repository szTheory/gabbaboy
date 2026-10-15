#!/usr/bin/env python3
"""Private test-side CGB corpus receipt adapter."""

import json
import sys


def main(argv):
    if argv == ["--self-test"]:
        # RED-phase baseline: the contract test must reject an incomplete result.
        print(json.dumps({
            "schema": "gabbaboy-cgb-corpus-receipt-v1",
            "version": 1,
            "status": "incomplete",
            "failure_codes": ["receipt-not-implemented"],
            "counts": {
                "attempted_cases": 0,
                "completed_cases": 0,
                "observed_pass_cases": 0,
                "assertions": 0,
            },
            "cases": [],
        }, sort_keys=True))
        return 1
    print("usage: verify-cgb-corpus-report.py --self-test", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
