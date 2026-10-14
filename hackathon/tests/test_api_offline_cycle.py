"""Route contract checks; production startup/provider loops remain out of scope."""
from fastapi.testclient import TestClient
from hackathon import api_server


def test_route_runs_real_offline_cycle_and_matches_cli_receipt():
    client = TestClient(api_server.app)
    params = {'simulate': 'true', 'seed': 8257, 'as_of': '2026-10-13T00:00:00Z'}
    first = client.post('/api/v1/system/run-full-cycle', params=params)
    second = client.post('/api/v1/system/run-full-cycle', params=params)
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    body = first.json()
    assert body['scope'] == 'provider-free synthetic fixture; no market submission'
    assert body['cycle_result']['success'] is True
    assert body['offline_receipt'] == second.json()['offline_receipt']
    assert body['offline_receipt']['constraints_satisfied'] is True
    assert body['offline_receipt']['seed'] == 8257


def test_route_reports_failed_orchestration_as_http_failure(monkeypatch):
    monkeypatch.setattr(api_server.main, 'run_gridpilot_gt', lambda **kwargs: {'success': False, 'error': 'fixture failure'})
    response = TestClient(api_server.app).post('/api/v1/system/run-full-cycle')
    assert response.status_code == 500
    assert response.json()['detail'] == 'Full cycle failed: fixture failure'


def test_route_rejects_invalid_datetime_before_running_cycle(monkeypatch):
    def must_not_run(**kwargs):
        raise AssertionError('invalid input reached orchestration')
    monkeypatch.setattr(api_server.main, 'run_gridpilot_gt', must_not_run)
    response = TestClient(api_server.app).post('/api/v1/system/run-full-cycle', params={'as_of': 'invalid'})
    assert response.status_code == 422


def test_real_http_process_matches_root_cli_receipt(tmp_path):
    import json
    from pathlib import Path
    import socket
    import subprocess
    import sys
    import time
    import httpx

    root = Path(__file__).resolve().parents[2]
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'api_server:app', '--app-dir', 'hackathon',
         '--host', '127.0.0.1', '--port', str(port), '--lifespan', 'off'],
        cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}', trust_env=False, timeout=30) as client:
            deadline = time.monotonic() + 30
            while True:
                if process.poll() is not None:
                    raise AssertionError(process.stderr.read())
                try:
                    ready = client.get('/')
                    if ready.status_code == 200:
                        break
                except httpx.ConnectError:
                    pass
                if time.monotonic() >= deadline:
                    raise AssertionError('HTTP server failed to start')
                time.sleep(0.05)
            params = {'simulate': 'true', 'seed': 8257, 'as_of': '2026-10-13T00:00:00Z'}
            first = client.post('/api/v1/system/run-full-cycle', params=params)
            second = client.post('/api/v1/system/run-full-cycle', params=params)
            assert first.status_code == second.status_code == 200, first.text
            receipt = tmp_path / 'cli.json'
            cli = subprocess.run(
                [sys.executable, 'main.py', '--mode', 'gridpilot', '--simulate', '1',
                 '--seed', '8257', '--as-of', '2026-10-13T00:00:00Z', '--receipt', str(receipt)],
                cwd=root, capture_output=True, text=True, timeout=60,
            )
            assert cli.returncode == 0, cli.stderr
            assert first.json()['offline_receipt'] == second.json()['offline_receipt'] == json.loads(receipt.read_text())
            assert client.post('/api/v1/system/run-full-cycle', params={'as_of': 'bad'}).status_code == 422
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
