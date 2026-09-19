[object Object]


def test_cli_serve_does_not_require_a_subcommand(monkeypatch):
    called = {}

    def fake_serve(store_path, host, port):
        called.update(store_path=store_path, host=host, port=port)

    monkeypatch.setattr("episteme.__main__.serve", fake_serve)
    monkeypatch.setattr("sys.argv", ["episteme", "--serve", "--store", "fixture.sqlite", "--host", "127.0.0.2", "--port", "8123"])

    assert main() == 0
    assert called == {"store_path": "fixture.sqlite", "host": "127.0.0.2", "port": 8123}
