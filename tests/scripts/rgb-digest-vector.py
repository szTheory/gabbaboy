#!/usr/bin/env python3
"""Independent stdlib vectors for the D-24 frame digest and the D-16 PCM digest.

Run as: python3 -I tests/scripts/rgb-digest-vector.py --check <helper-exe> --ppm <path>
        python3 -I tests/scripts/rgb-digest-vector.py --uniform <shade 0..3>
        python3 -I tests/scripts/rgb-digest-vector.py --rgb555
        python3 -I tests/scripts/rgb-digest-vector.py --rgb555 --check <helper-exe> --ppm <path>

The digest definitions are re-derived here from the written rule, not from the C source, so a
shared misreading cannot hide in both (D-26 anti-circularity for the digest container):
  frame digest = SHA-256(b"GBB-RGB888-v1 160x144\n" + 160x144x3 row-major R,G,B bytes),
  shade map 0->255, 1->170, 2->85, 3->0 on all three channels;
  PCM digest   = SHA-256 over little-endian int16 L,R per frame.
The CGB digest (Phase 11, D-15, D-43) is a distinct format with its own label:
  frame555 digest = SHA-256(b"GBB-RGB555LE-v1 160x144\n" + 160x144 row-major 15-bit values, each as
  a low byte then a high byte); a value above 0x7FFF is invalid. The PPM expands each 5-bit channel
  c (red bits 0-4, green 5-9, blue 10-14) to (c << 3) | (c >> 2).
"""
import hashlib
import os
import struct
import subprocess
import sys

WIDTH, HEIGHT = 160, 144
HEADER = b"GBB-RGB888-v1 160x144\n"
GRAY = (255, 170, 85, 0)
HEADER555 = b"GBB-RGB555LE-v1 160x144\n"
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


def synthetic_555():
    return [(x * 37 + y * 101) & 0x7FFF for y in range(HEIGHT) for x in range(WIDTH)]


def digest555_of(values):
    assert len(values) == WIDTH * HEIGHT and all(0 <= v <= 0x7FFF for v in values)
    return hashlib.sha256(HEADER555 + b"".join(struct.pack("<H", v) for v in values)).hexdigest()


def expand5(c):
    return (c << 3) | (c >> 2)


def ppm555_of(values):
    body = b"".join(bytes((expand5(v & 31), expand5((v >> 5) & 31), expand5((v >> 10) & 31))) for v in values)
    return b"P6\n160 144\n255\n" + body


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


def check555(exe, ppm_path):
    if os.path.exists(ppm_path):
        os.remove(ppm_path)
    values = synthetic_555()
    run = subprocess.run([exe, "acceptance_digest_rgb555_helper", ppm_path],
                         capture_output=True, text=True, timeout=25)
    if run.returncode != 0:
        fail("rgb555 helper exited %d: %s%s" % (run.returncode, run.stdout, run.stderr))
    fields = dict(line.split("=", 1) for line in run.stdout.splitlines() if "=" in line)
    expected = {"rgb555_sha256": digest555_of(values),
                "padded_pitch_sha256": digest555_of(values),
                "invalid_value": "rejected",
                "expand5": bytes(expand5(c) for c in range(32)).hex(),
                "ppm": "written"}
    for key, value in expected.items():
        if fields.get(key) != value:
            fail("%s: C helper printed %r, python computed %r" % (key, fields.get(key), value))
    with open(ppm_path, "rb") as handle:
        written = handle.read()
    if written != ppm555_of(values):
        fail("RGB555 PPM bytes differ (C wrote %d bytes, python built %d)" % (len(written), len(ppm555_of(values))))
    print("rgb-digest-vector: OK rgb555=%s ppm_bytes=%d" % (expected["rgb555_sha256"], len(written)))


def main(argv):
    if len(argv) == 2 and argv[1] == "--rgb555":
        print(digest555_of(synthetic_555()))
        return 0
    if len(argv) == 6 and argv[1] == "--rgb555" and argv[2] == "--check" and argv[4] == "--ppm":
        check555(argv[3], argv[5])
        return 0
    if len(argv) == 3 and argv[1] == "--uniform" and argv[2] in ("0", "1", "2", "3"):
        print(digest_of([int(argv[2])] * (WIDTH * HEIGHT)))
        return 0
    if len(argv) == 5 and argv[1] == "--check" and argv[3] == "--ppm":
        check(argv[2], argv[4])
        return 0
    sys.stderr.write("usage: rgb-digest-vector.py --check <exe> --ppm <path> | --uniform <0..3> | --rgb555 [--check <exe> --ppm <path>]\n")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
