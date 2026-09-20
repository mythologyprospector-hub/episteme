"""Phase 21 proof of public captured-representation inspection."""
import json,sys,hashlib
from threading import Thread
from urllib.request import urlopen
from episteme import CaptureOutcome,CapturedRepresentation,Store,get_captured_representation,list_captured_representations
CID="99999999-9999-4999-8999-999999999999"; CAPTURED_AT="2026-09-20T00:00:00Z"
def _seed(path):
    content=b'{"message":"phase21"}'; digest=hashlib.sha256(content).hexdigest()
    capture=CapturedRepresentation(CID,"phase21-fixture","https://example.org/phase21",{"rows":1},CAPTURED_AT,200,"application/json","fixture-1",digest,f"sha256/{digest}","fixture","1",CaptureOutcome.COMPLETE,None,2)
    with Store(path,capture_root=path.parent/"captures") as store: store.put_captured_representation(capture,content=content)
    return capture
def test_public_capture_inspection_preserves_existing_representation(tmp_path):
    capture=_seed(tmp_path/"phase21.sqlite")
    with Store(tmp_path/"phase21.sqlite",read_only=True) as store:
        assert get_captured_representation(store,CID)==capture.to_dict()
        assert list_captured_representations(store)==[capture.to_dict()]
        assert list_captured_representations(store,source_id="phase21-fixture")==[capture.to_dict()]
def test_missing_capture_is_not_found(tmp_path):
    _seed(tmp_path/"phase21.sqlite")
    with Store(tmp_path/"phase21.sqlite",read_only=True) as store:
        try: get_captured_representation(store,"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        except ValueError as exc: assert str(exc).startswith("captured representation not found:")
        else: raise AssertionError("missing captured representation must be rejected")
def test_cli_capture_inspection_is_read_only(tmp_path,capsys):
    capture=_seed(tmp_path/"phase21.sqlite"); from episteme.__main__ import main; old=sys.argv
    try:
        sys.argv=["episteme","--store",str(tmp_path/"phase21.sqlite"),"capture",CID]; assert main()==0; assert json.loads(capsys.readouterr().out)==capture.to_dict()
        sys.argv=["episteme","--store",str(tmp_path/"phase21.sqlite"),"captures","--source-id","phase21-fixture"]; assert main()==0; assert json.loads(capsys.readouterr().out)==[capture.to_dict()]
    finally: sys.argv=old
def test_http_capture_inspection_is_read_only(tmp_path):
    capture=_seed(tmp_path/"phase21.sqlite"); from episteme.http_api import create_http_server
    server=create_http_server(tmp_path/"phase21.sqlite",port=0); thread=Thread(target=server.serve_forever,daemon=True); thread.start()
    try:
        host,port=server.server_address; base=f"http://{host}:{port}/api/v1"
        with urlopen(f"{base}/captures/{CID}") as response: assert json.loads(response.read())==capture.to_dict()
        with urlopen(f"{base}/captures?source_id=phase21-fixture") as response: assert json.loads(response.read())==[capture.to_dict()]
    finally: server.shutdown(); server.server_close(); thread.join(timeout=2)
