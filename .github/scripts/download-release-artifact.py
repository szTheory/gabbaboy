#!/usr/bin/env python3
"""Download one release artifact with hard byte and time bounds, using only the standard library.

curl >= 8.4.0 already enforces --max-filesize on responses without a Content-Length. This helper exists for the
guarantees curl does not give on every host: a total deadline and a stall deadline, a streamed-byte cap that does not
trust any header, a bounded number of redirects, credentials that never leave the original origin, and an output
file that is either complete or absent.

  download-release-artifact.py URL OUTPUT [--max-bytes N] [--total-timeout S] [--stall-timeout S]
                               [--max-redirects N] [--bearer-env NAME] [--allow-http-loopback]
  download-release-artifact.py --self-test

Authentication follows the original policy: none unless --bearer-env names an environment variable. Its value is
sent only to the origin of the first URL, is never printed, and is dropped on any redirect to another origin.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import http.server
import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse

CHUNK = 64 * 1024
REDIRECTS = (301, 302, 303, 307, 308)
LOOPBACK = ("127.0.0.1", "localhost", "::1")


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"REJECT download-{code}: {message}")
        self.code = code


def _origin(parts: urllib.parse.SplitResult) -> tuple[str, str, int]:
    default = 443 if parts.scheme == "https" else 80
    return parts.scheme, (parts.hostname or "").lower(), parts.port or default


def _check_url(url: str, allow_http_loopback: bool) -> urllib.parse.SplitResult:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise Reject("scheme", f"only https downloads are allowed, not {parts.scheme or 'a relative URL'}")
    if not parts.hostname or parts.username or parts.password:
        raise Reject("url", "the URL must name a host and carry no embedded credentials")
    if parts.scheme == "https":
        return parts
    if parts.scheme == "http" and allow_http_loopback and parts.hostname in LOOPBACK:
        return parts
    raise Reject("scheme", f"only https downloads are allowed, not {parts.scheme or 'a relative URL'}")


def _open(parts: urllib.parse.SplitResult, timeout: float) -> http.client.HTTPConnection:
    port = parts.port
    if parts.scheme == "https":
        return http.client.HTTPSConnection(parts.hostname, port, timeout=timeout)
    return http.client.HTTPConnection(parts.hostname, port, timeout=timeout)


def fetch(url: str, output: pathlib.Path, *, max_bytes: int, total_timeout: float, stall_timeout: float,
          max_redirects: int, bearer: str | None, allow_http_loopback: bool) -> tuple[int, str]:
    """Stream `url` into `output`; return (bytes, sha256). The output exists only after a complete, bounded transfer."""
    deadline = time.monotonic() + total_timeout

    def remaining() -> float:
        left = deadline - time.monotonic()
        if left <= 0:
            raise Reject("timeout", f"the {total_timeout:g}s total deadline passed")
        return left

    output.unlink(missing_ok=True)
    first = _check_url(url, allow_http_loopback)
    home = _origin(first)
    current = first
    temp_name = ""
    try:
        for _ in range(max_redirects + 1):
            connection = _open(current, min(stall_timeout, remaining()))
            try:
                target = urllib.parse.urlunsplit(("", "", current.path or "/", current.query, ""))
                headers = {"User-Agent": "gabbaboy-release-download", "Accept-Encoding": "identity"}
                if bearer is not None and _origin(current) == home:
                    headers["Authorization"] = f"Bearer {bearer}"
                connection.request("GET", target, headers=headers)
                response = connection.getresponse()
                if response.status in REDIRECTS:
                    location = response.getheader("Location")
                    if not location:
                        raise Reject("redirect", "a redirect carried no Location")
                    current = _check_url(urllib.parse.urljoin(urllib.parse.urlunsplit(current), location), allow_http_loopback)
                    continue
                if response.status != 200:
                    raise Reject("status", f"the server answered HTTP {response.status}")
                declared = response.getheader("Content-Length")
                length = None
                if declared is not None:
                    if not declared.isdigit():
                        raise Reject("length", "Content-Length is not a number")
                    length = int(declared)
                    if length > max_bytes:
                        raise Reject("size-limit", f"the server declares {length} bytes, above the {max_bytes} byte cap")
                handle, temp_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".part", dir=output.parent)
                digest = hashlib.sha256()
                received = 0
                with os.fdopen(handle, "wb") as sink:
                    while True:
                        if connection.sock is not None:
                            connection.sock.settimeout(min(stall_timeout, remaining()))
                        remaining()
                        try:
                            block = response.read1(CHUNK)
                        except http.client.IncompleteRead as error:
                            raise Reject("truncated", "the chunked response ended before its final chunk") from error
                        if not block:
                            break
                        received += len(block)
                        if received > max_bytes:
                            raise Reject("size-limit", f"the stream passed the {max_bytes} byte cap")
                        digest.update(block)
                        sink.write(block)
                if length is not None and received != length:
                    raise Reject("truncated", f"received {received} of the {length} declared bytes")
                os.replace(temp_name, output)
                temp_name = ""
                return received, digest.hexdigest()
            finally:
                connection.close()
        raise Reject("redirect", f"more than {max_redirects} redirects")
    except (socket.timeout, TimeoutError) as error:
        if time.monotonic() >= deadline:
            raise Reject("timeout", f"the {total_timeout:g}s total deadline passed") from error
        raise Reject("timeout", f"the server stalled past the {stall_timeout:g}s stall deadline") from error
    except (http.client.HTTPException, OSError) as error:
        raise Reject("network", f"{type(error).__name__}: {error}") from error
    finally:
        if temp_name:
            pathlib.Path(temp_name).unlink(missing_ok=True)


def run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url")
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--max-bytes", type=int, default=1 << 30)
    parser.add_argument("--total-timeout", type=float, default=600.0)
    parser.add_argument("--stall-timeout", type=float, default=30.0)
    parser.add_argument("--max-redirects", type=int, default=5)
    parser.add_argument("--bearer-env", default="", help="name of an environment variable holding a bearer token")
    parser.add_argument("--allow-http-loopback", action="store_true", help="permit http to loopback hosts (self-test only)")
    args = parser.parse_args(argv)
    if args.max_bytes < 1 or args.total_timeout <= 0 or args.stall_timeout <= 0 or not 0 <= args.max_redirects <= 10:
        parser.error("limits must be positive and at most 10 redirects")
    args.output.unlink(missing_ok=True)  # a failed download must never leave an earlier file to be mistaken for success
    bearer = None
    if args.bearer_env:
        bearer = os.environ.get(args.bearer_env)
        if not bearer:
            print(f"REJECT download-auth: environment variable {args.bearer_env} is empty or unset", file=sys.stderr)
            return 1
    try:
        count, sha = fetch(args.url, args.output, max_bytes=args.max_bytes, total_timeout=args.total_timeout,
                           stall_timeout=args.stall_timeout, max_redirects=args.max_redirects, bearer=bearer,
                           allow_http_loopback=args.allow_http_loopback)
    except Reject as error:
        print(error, file=sys.stderr)
        return 1
    print(f"PASS: downloaded {count} bytes sha256={sha}")
    return 0


# --------------------------------------------------------------------------- self-test
class Fixture:
    """Two loopback servers (different ports are different origins) with misbehaving routes and a record of requests."""

    def __init__(self) -> None:
        self.seen: list[tuple[str, str, str | None]] = []
        self.sent: dict[str, int] = {}
        fixture = self

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_: object) -> None:  # silence
                return

            def do_GET(self) -> None:  # noqa: N802
                fixture.seen.append((self.server.label, self.path, self.headers.get("Authorization")))
                route = getattr(self, "route_" + self.path.strip("/").replace("-", "_"), None)
                if route is None:
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                try:
                    route()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                self.close_connection = True

            def _chunk(self, data: bytes) -> None:
                self.wfile.write(b"%x\r\n" % len(data) + data + b"\r\n")
                self.wfile.flush()
                fixture.sent[self.path] = fixture.sent.get(self.path, 0) + len(data)

            def _chunked_headers(self) -> None:
                self.send_response(200)
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()

            def route_ok(self) -> None:
                body = b"qualified bytes\n" * 100
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def route_endless(self) -> None:  # no Content-Length, never ends
                self._chunked_headers()
                while True:
                    self._chunk(b"x" * CHUNK)

            def route_declared_huge(self) -> None:
                self.send_response(200)
                self.send_header("Content-Length", str(1 << 40))
                self.end_headers()
                fixture.sent[self.path] = 0
                time.sleep(2)

            def route_stall(self) -> None:
                self._chunked_headers()
                self._chunk(b"partial")
                time.sleep(20)

            def route_drip(self) -> None:  # each read succeeds in time, but the transfer never finishes
                self._chunked_headers()
                while True:
                    self._chunk(b"d")
                    time.sleep(0.2)

            def route_short(self) -> None:  # declares 1000 bytes, delivers 100, closes
                self.send_response(200)
                self.send_header("Content-Length", "1000")
                self.end_headers()
                self.wfile.write(b"s" * 100)
                self.wfile.flush()

            def route_short_chunked(self) -> None:  # closes without the terminating chunk
                self._chunked_headers()
                self._chunk(b"c" * 100)

            def route_loop(self) -> None:
                self.send_response(302)
                self.send_header("Location", "/loop")
                self.send_header("Content-Length", "0")
                self.end_headers()

            def route_same_origin(self) -> None:
                self.send_response(302)
                self.send_header("Location", "/ok")
                self.send_header("Content-Length", "0")
                self.end_headers()

            def route_cross_origin(self) -> None:
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{fixture.far_port}/ok")
                self.send_header("Content-Length", "0")
                self.end_headers()

            def route_to_ftp(self) -> None:
                self.send_response(302)
                self.send_header("Location", "ftp://127.0.0.1/ok")
                self.send_header("Content-Length", "0")
                self.end_headers()

        self.servers = []
        for label in ("near", "far"):
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            server.daemon_threads = True
            server.label = label  # type: ignore[attr-defined]
            threading.Thread(target=server.serve_forever, daemon=True).start()
            self.servers.append(server)
        self.near_port = self.servers[0].server_port
        self.far_port = self.servers[1].server_port

    def close(self) -> None:
        for server in self.servers:
            server.shutdown()
            server.server_close()


def _cli(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    environment = {key: value for key, value in os.environ.items() if key != "SELFTEST_TOKEN"}
    environment.update(env or {})
    return subprocess.run([sys.executable, "-I", str(pathlib.Path(__file__).resolve()), *args],
                          capture_output=True, text=True, check=False, timeout=60, env=environment)


def self_test() -> None:
    fixture = Fixture()
    rejected = 0
    try:
        with tempfile.TemporaryDirectory(prefix="gbb-download.") as directory:
            root = pathlib.Path(directory)
            base = f"http://127.0.0.1:{fixture.near_port}"
            out = root / "artifact.bin"
            common = ["--allow-http-loopback", "--total-timeout", "10", "--stall-timeout", "10"]

            expected = b"qualified bytes\n" * 100
            result = _cli([base + "/ok", str(out), *common])
            if (result.returncode != 0 or out.read_bytes() != expected
                    or f"sha256={hashlib.sha256(expected).hexdigest()}" not in result.stdout):
                raise SystemExit(f"download positive control failed: {result.returncode} {result.stderr!r}")
            result = _cli([base + "/same-origin", str(out), *common])
            if result.returncode != 0 or out.read_bytes() != expected:
                raise SystemExit("a same-origin redirect was not followed")
            out.unlink()

            def reject(label: str, code: str, args: list[str], *, within: float | None = None, env: dict[str, str] | None = None) -> None:
                nonlocal rejected
                out.write_bytes(b"stale bytes from an earlier download")
                started = time.monotonic()
                result = _cli(args, env)
                elapsed = time.monotonic() - started
                leftovers = sorted(p.name for p in root.iterdir())
                if (result.returncode != 1 or f"REJECT download-{code}:" not in result.stderr or "PASS" in result.stdout
                        or leftovers):
                    raise SystemExit(f"download negative {label!r} failed: want download-{code}, exit={result.returncode}, "
                                     f"stderr={result.stderr.strip()!r}, leftovers={leftovers}")
                if within is not None and elapsed > within:
                    raise SystemExit(f"download negative {label!r} took {elapsed:.1f}s, past the {within}s bound")
                rejected += 1
                print(f"rejected: {label}: {result.stderr.strip()}")

            cap = ["--max-bytes", str(1 << 20)]
            reject("unknown-length stream passes the byte cap", "size-limit", [base + "/endless", str(out), *common, *cap])
            # The server may run ahead of the client by the kernel socket buffers (a hosted Linux runner queued about 8 MB
            # on loopback), but it must stop once the client leaves: an endless stream that kept being read would
            # grow without bound, so the allowance is a generous fixed ceiling, not a statement about buffer size.
            time.sleep(0.3)
            settled = fixture.sent.get("/endless", 0)
            time.sleep(0.3)
            if fixture.sent.get("/endless", 0) != settled or settled > (1 << 20) + (63 << 20):
                raise SystemExit(f"the endless stream was read far past the cap: {fixture.sent['/endless']} bytes")
            reject("declared length above the cap", "size-limit", [base + "/declared-huge", str(out), *common, *cap], within=1.5)
            reject("stalled response", "timeout", [base + "/stall", str(out), "--allow-http-loopback", "--total-timeout", "10",
                                                   "--stall-timeout", "1"], within=5)
            reject("slow drip beyond the total deadline", "timeout", [base + "/drip", str(out), "--allow-http-loopback", "--total-timeout", "2",
                                                                      "--stall-timeout", "5"], within=6)
            reject("truncated fixed-length response", "truncated", [base + "/short", str(out), *common])
            reject("truncated chunked response", "truncated", [base + "/short-chunked", str(out), *common])
            reject("redirect loop", "redirect", [base + "/loop", str(out), *common, "--max-redirects", "3"])
            reject("redirect to a non-http scheme", "scheme", [base + "/to-ftp", str(out), *common])
            reject("missing artifact", "status", [base + "/absent", str(out), *common])
            reject("plain http to a non-loopback host", "scheme", ["http://example.invalid/a", str(out)])
            reject("plain http without the loopback flag", "scheme", [base + "/ok", str(out)])
            reject("file URL", "scheme", ["file:///etc/hosts", str(out)])
            reject("unset bearer variable", "auth", [base + "/ok", str(out), *common, "--bearer-env", "SELFTEST_TOKEN"])

            # Credentials: sent to the original origin, never to another origin, never printed.
            secret = "selftest-secret-value"
            fixture.seen.clear()
            result = _cli([base + "/cross-origin", str(out), *common, "--bearer-env", "SELFTEST_TOKEN"], {"SELFTEST_TOKEN": secret})
            if result.returncode != 0 or out.read_bytes() != expected:
                raise SystemExit(f"a cross-origin redirect download failed: {result.stderr!r}")
            if secret in result.stdout or secret in result.stderr:
                raise SystemExit("the bearer value was printed")
            auth = {(label, path): header for label, path, header in fixture.seen}
            if auth.get(("near", "/cross-origin")) != f"Bearer {secret}":
                raise SystemExit("the credential was not sent to the original origin")
            if auth.get(("far", "/ok")) is not None:
                raise SystemExit("the credential followed a redirect to another origin")
            out.unlink()
            if list(root.iterdir()):
                raise SystemExit(f"download self-test left files behind: {sorted(p.name for p in root.iterdir())}")
    finally:
        fixture.close()
    print(f"PASS: bounded download self-test negative_controls={rejected} positive_controls=3 credential_controls=2")


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
