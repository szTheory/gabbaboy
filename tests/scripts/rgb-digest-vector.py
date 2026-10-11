#!/usr/bin/env python3
"""Independent stdlib vectors for the D-24 frame digest and the D-16 PCM digest.

Run as: python3 -I tests/scripts/rgb-digest-vector.py --check <helper-exe> --ppm <path>
        python3 -I tests/scripts/rgb-digest-vector.py --uniform <shade 0..3>

The digest definitions are re-derived here from the written rule, not from the C source, so a
shared misreading cannot hide in both (D-26 anti-circularity for the digest container):
  frame digest = SHA-256(b"GBB-RGB888-v1 160x144\n" + 160x144x3 row-major R,G,B bytes),
  shade map 0->255, 1->170, 2->85, 3->0 on all three channels;
  PCM digest   = SHA-256 over little-endian int16 L,R per frame.
"""
import hashlib
import os
import struct
import subprocess
import sys

WIDTH, HEIGHT = 160, 144
HEADER = b"GBB-RGB888-v1 160x144\n"
GRAY = (255, 170, 85, 0)
PCM_VECTOR = ((-1, 258), (32767, -32768), (0, 1))


def rgb_bytes(shades):
    return b"".join(bytes((GRAY[s],)) * 3 for s in shades)


def digest_of(shades):
    assert len(shades) == WIDTH * HEIGHT
    return hashlib.sha256(HEADER + rgb_bytes(shades)).hexdigest()


def synthetic_shades():
    return [(x + 2 * y) % 4 for y in range(HEIGHT) for x in range(WIDTH)]


def ppm_of(shades):
    return b"P6\n160 144\n255\n" + rgb_bytes(shades)


def pcm_digest():
    return hashlib.sha256(b"".join(struct.pack("<hh", l, r) for l, r in PCM_VECTOR)).hexdigest()


def fail(message):
    print("rgb-digest-vector: FAIL: " + message)
    sys.exit(1)


def check(exe, ppm_path):
    if os.path.exists(ppm_path):
        os.remove(ppm_path)
    shades = synthetic_shades()
    run = subprocess.run([exe, "acceptance_digest_vectors_helper", ppm_path],
                         capture_output=True, text=True, timeout=25)
    if run.returncode != 0:
        fail("helper exited %d: %s%s" % (run.returncode, run.stdout, run.stderr))
    fields = dict(line.split("=", 1) for line in run.stdout.splitlines() if "=" in line)
    expected = {"rgb_sha256": digest_of(shades), "pcm_sha256": pcm_digest(),
                "invalid_shade": "rejected"}
    for key, value in expected.items():
        if fields.get(key) != value:
            fail("%s: C helper printed %r, python computed %r" % (key, fields.get(key), value))
    with open(ppm_path, "rb") as handle:
        written = handle.read()
    if written != ppm_of(shades):
        fail("PPM bytes differ (C wrote %d bytes, python built %d)" % (len(written), len(ppm_of(shades))))
    print("rgb-digest-vector: OK rgb=%s pcm=%s ppm_bytes=%d" %
          (expected["rgb_sha256"], expected["pcm_sha256"], len(written)))


def main(argv):
    if len(argv) == 3 and argv[1] == "--uniform" and argv[2] in ("0", "1", "2", "3"):
        print(digest_of([int(argv[2])] * (WIDTH * HEIGHT)))
        return 0
    if len(argv) == 5 and argv[1] == "--check" and argv[3] == "--ppm":
        check(argv[2], argv[4])
        return 0
    sys.stderr.write("usage: rgb-digest-vector.py --check <exe> --ppm <path> | --uniform <0..3>\n")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
