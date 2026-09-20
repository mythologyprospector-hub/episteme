"""Phase 18 proof of public discovery-finding inspection."""

import json
import sys
from threading import Thread
from urllib.request import urlopen

from episteme import (
    DiscoveryFinding,
    DiscoveryFindingKind,
    Provenance,
    Record,
    RecordKind,
    Store,
    get_discovery_finding,
    list_discovery_findings,
)

CREATED = "2026-09-20T00:00:00Z"
PROV = (Provenance(source_id="phase18-fixture", captured_at=CREATED, source_location="https://example.org/phase18", source_version="1"),)
RID = "77777777-7777-4777-8777-777777777777"
OID = "88888888-8888-4888-8888-888888888888"


def _seed(path):
    with Store(path) as store:
        observation = Record(OID, RecordKind.OBSERVATION, {"value": "fixture"}, PROV, CREATED)
        finding = DiscoveryFinding(
            RID,
            DiscoveryFindingKind.TENSION,
            "Fixture tension",
            "A generated discovery finding for public inspection.",
            (OID,),
            "fixture",
            "1",
            "The fixture establishes a bounded generated finding.",
            (),
            CREATED,
        )
        store.put_record(observation)
        store.put_discovery_finding(finding)
    return finding


def test_public_discovery_finding_inspection_preserves_existing_representation(tmp_path):
    finding = _seed(tmp_path / "phase18.sqlite")
    with Store(tmp_path / "phase18.sqlite", read_only=True) as store:
        assert get_discovery_finding(store, RID) == finding.to_dict()
        assert list_discovery_findings(store) == [finding.to_dict()]
        assert list_discovery_findings(store, kind=DiscoveryFindingKind.TENSION.value) == [finding.to_dict()]


def test_missing_discovery_finding_is_not_found(tmp_path):
    _seed(tmp_path / "phase18.sqlite")
    with Store(tmp_path / "phase18.sqlite", read_only=True) as store:
        try:
            get_discovery_finding(store, "99999999-9999-4999-8999-999999999999")
        except ValueError as exc:
            assert str(exc).startswith("discovery finding not found:")
        else:
            raise AssertionError("missing discovery finding must be rejected")


def test_cli_discovery_finding_inspection_is_read_only(tmp_path, capsys):
    finding = _seed(tmp_path / "phase18.sqlite")
    from episteme.__main__ import main

    original = sys.argv
    try:
        sys.argv = ["episteme", "--store", str(tmp_path / "phase18.sqlite"), "discovery", RID]
        assert main() == 0
        assert json.loads(capsys.readouterr().out) == finding.to_dict()

        sys.argv = ["episteme", "--store", str(tmp_path / "phase18.sqlite"), "discoveries", "--kind", "tension"]
        assert main() == 0
        assert json.loads(capsys.readouterr().out) == [finding.to_dict()]
    finally:
        sys.argv = original


def test_http_discovery_finding_inspection_is_read_only(tmp_path):
    finding = _seed(tmp_path / "phase18.sqlite")
    server = __import__("episteme.http_api", fromlist=["create_http_server"]).create_http_server(
        tmp_path / "phase18.sqlite", port=0
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        base = f"http://{host}:{port}/api/v1"
        with urlopen(f"{base}/discoveries/{RID}") as response:
            assert json.loads(response.read()) == finding.to_dict()
        with urlopen(f"{base}/discoveries?kind=tension") as response:
            assert json.loads(response.read()) == [finding.to_dict()]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
