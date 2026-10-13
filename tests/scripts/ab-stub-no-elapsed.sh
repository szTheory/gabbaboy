#!/usr/bin/env bash
# Test double for measure_core in measure-release-baseline.sh --ab: prints a mode= line with the right
# workload and digest but no elapsed_ns, so the harness must name the missing field (IN-03).
echo "mode=stub workload=original-wram-tracer-1m-half-dots-v1 correctness_digest_fnv1a64=4c7a57ff3d50d228"
