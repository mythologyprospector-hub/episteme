"""Phase 23 proof of public captured-content inspection."""

import hashlib
import sys
from threading import Thread
from urllib.request import urlopen

from episteme import (
    CaptureOutcome,
    CapturedRepresentation,
    Store,
    get_captured_content,
)
from episteme.http_api import create_http_server


CID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
CAPTURED_AT = "2026-09-20T00:00:00Z"


def _seed(path):
    content = b'{"message":"phase23","value":7}'
    digest = hashlib.sha256(content).hexdigest()
    capture = CapturedRepresentation(
        CID,
        "phase23-fixture",
        "https://example.org/phase23",
        {"rows": 1},
        CAPTURED_AT,
        200,
        "application/json",
        "fixture-1",
        digest,
        f"sha256/{digest}",
        "fixture",
        "1",
        CaptureOutcome.COMPLETE,
        None,
        2,
    )
    root = path.parent / "captures"
    with Store(path, capture_root=root) as store:
        store.put_captured_representation(capture, content=content)
    return capture, content, root


def test_public_python_returns_exact_captured_bytes(tmp_path):
    capture, content, root = _seed(tmp_path / "phase23.sqlite")
    with Store(tmp_path / "phase23.sqlite", read_only=True, capture_root=root) as store:
        assert get_captured_content(store, CID) == (content, capture.media_type)


def test_public_cli_writes_exact_captured_bytes(tmp_path):
    _capture, content, root = _seed(tmp_path / "phase23.sqlite")
    from episteme.__main__ import main

    output = tmp_path / "captured.bin"
    old = sys.argv
    try:
        sys.argv = [
            "episteme",
            "--store",
            str(tmp_path / "phase23.sqlite"),
            "--capture-root",
            str(root),
            "capture-content",
            CID,
            "--output",
            str(output),
        ]
        assert main() == 0
    finally:
        sys.argv = old

    assert output.read_bytes() == content


def test_public_http_returns_exact_captured_bytes_and_media_type(tmp_path):
    capture, content, root = _seed(tmp_path / "phase23.sqlite")
    server = create_http_server(
        tmp_path / "phase23.sqlite",
        port=0,
        capture_root=root,
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urlopen(f"http://{host}:{port}/api/v1/captures/{CID}/content") as response:
            assert response.read() == content
            assert response.headers["Content-Type"].startswith(capture.media_type)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_public_content_rejects_capture_without_content(tmp_path):
    capture = CapturedRepresentation(
        CID,
        "phase23-fixture",
        "https://example.org/phase23",
        {},
        CAPTURED_AT,
        None,
        None,
        None,
        None,
        None,
        "fixture",
        "1",
        CaptureOutcome.FAILED,
        "fixture failure",
        2,
    )
    with Store(tmp_path / "phase23.sqlite", capture_root=tmp_path / "captures") as store:
        store.put_captured_representation(capture)
    with Store(
        tmp_path / "phase23.sqlite",
        read_only=True,
        capture_root=tmp_path / "captures",
    ) as store:
        try:
            get_captured_content(store, CID)
        except ValueError as exc:
            assert "has no content" in str(exc)
        else:
            raise AssertionError("failed capture must not expose content")
