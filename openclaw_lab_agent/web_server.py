from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .diagnostics import summarize_failure
from .experiments import compare_runs, create_experiment, get_status, list_experiments, read_metrics, run_training


HOST = "127.0.0.1"
PORT = 8765
API_TOKEN_ENV = "OPENCLAW_LAB_TOKEN"
HOST_ENV = "OPENCLAW_LAB_HOST"
PORT_ENV = "OPENCLAW_LAB_PORT"


class LabAgentHandler(BaseHTTPRequestHandler):
    server_version = "OpenCLAWLabAgent/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API.
        parsed = urlparse(self.path)
        path = parsed.path.strip("/")

        if parsed.path == "/":
            self._send_html(index_html())
            return

        if parsed.path == "/health":
            self._send_json({"ok": True})
            return

        if parsed.path.startswith("/api/") and not self._authorized():
            self._send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return

        if parsed.path == "/api/experiments":
            self._send_json({"experiments": list_experiments()})
            return

        parts = path.split("/")
        if len(parts) == 3 and parts[:2] == ["api", "experiments"]:
            self._send_json(get_status(parts[2]))
            return

        if len(parts) == 4 and parts[:2] == ["api", "experiments"] and parts[3] == "metrics":
            query = parse_qs(parsed.query)
            tail = int(query.get("tail", ["20"])[0])
            rows = read_metrics(parts[2])
            self._send_json({"run_id": parts[2], "count": len(rows), "metrics": rows[-tail:]})
            return

        self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API.
        parsed = urlparse(self.path)
        path = parsed.path.strip("/")
        parts = path.split("/")

        if parsed.path.startswith("/api/") and not self._authorized():
            self._send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return

        payload = self._read_payload()

        try:
            if parsed.path == "/api/experiments":
                name = payload.get("name")
                if not name:
                    self._send_json({"error": "name is required"}, HTTPStatus.BAD_REQUEST)
                    return
                result = create_experiment(
                    name=name,
                    config_path=payload.get("config_path"),
                    overrides=payload.get("overrides"),
                )
                self._send_json(result, HTTPStatus.CREATED)
                return

            if parsed.path == "/api/compare":
                run_ids = payload.get("run_ids", [])
                if not isinstance(run_ids, list) or len(run_ids) < 2:
                    self._send_json({"error": "run_ids must contain at least two runs"}, HTTPStatus.BAD_REQUEST)
                    return
                self._send_json(compare_runs(run_ids))
                return

            if len(parts) == 4 and parts[:2] == ["api", "experiments"] and parts[3] == "run":
                result = run_training(parts[2], payload.get("max_steps"))
                self._send_json(result)
                return

            if len(parts) == 4 and parts[:2] == ["api", "experiments"] and parts[3] == "diagnose":
                self._send_json(summarize_failure(parts[2]))
                return

            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:  # noqa: BLE001 - API should return structured errors.
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_payload(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8-sig")
        return json.loads(raw) if raw.strip() else {}

    def _authorized(self) -> bool:
        token = os.environ.get(API_TOKEN_ENV)
        if not token:
            return True
        header = self.headers.get("Authorization", "")
        return header == f"Bearer {token}"

    def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(host: str = HOST, port: int = PORT) -> None:
    httpd = ThreadingHTTPServer((host, port), LabAgentHandler)
    print(f"OpenCLAW Lab Agent listening on http://{host}:{port}")
    httpd.serve_forever()


def index_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OpenCLAW Lab Agent</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17202a;
      --muted: #5b6673;
      --line: #d7dde4;
      --surface: #ffffff;
      --band: #f3f7f8;
      --accent: #107c6a;
      --danger: #b42318;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background: var(--band);
    }
    header {
      padding: 28px max(20px, calc((100vw - 1080px) / 2));
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }
    h1 { margin: 0 0 8px; font-size: 28px; }
    p { margin: 0; color: var(--muted); line-height: 1.6; }
    main {
      max-width: 1080px;
      margin: 0 auto;
      padding: 24px 20px 48px;
      display: grid;
      gap: 20px;
    }
    section {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    h2 { margin: 0 0 14px; font-size: 20px; }
    .toolbar { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .field-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(150px, 1fr));
      gap: 12px;
      margin-top: 12px;
    }
    label {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 14px;
    }
    input {
      min-width: 220px;
      height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 10px;
      font: inherit;
      color: var(--ink);
    }
    label input { min-width: 0; width: 100%; }
    button {
      height: 38px;
      border: 1px solid #0d6f5f;
      background: var(--accent);
      color: white;
      border-radius: 6px;
      padding: 0 14px;
      font: inherit;
      cursor: pointer;
    }
    button.secondary {
      background: #ffffff;
      color: var(--accent);
    }
    button.small {
      height: 32px;
      padding: 0 10px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      table-layout: fixed;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
      word-break: break-word;
    }
    th { color: var(--muted); font-weight: 600; }
    pre {
      margin: 0;
      min-height: 160px;
      max-height: 360px;
      overflow: auto;
      background: #101820;
      color: #e9f2f1;
      border-radius: 8px;
      padding: 14px;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .status { color: var(--muted); margin-top: 10px; }
    .error { color: var(--danger); }
    @media (max-width: 720px) {
      h1 { font-size: 24px; }
      input { width: 100%; min-width: 0; }
      button { width: 100%; }
      .field-grid { grid-template-columns: 1fr; }
      th:nth-child(4), td:nth-child(4) { display: none; }
    }
  </style>
</head>
<body>
  <header>
    <h1>OpenCLAW Lab Agent</h1>
    <p>管理实验配置，运行轻量训练闭环，读取指标，生成诊断报告。</p>
  </header>
  <main>
    <section>
      <h2>新建实验</h2>
      <div class="toolbar">
        <input id="name" placeholder="实验名，例如 lr-sweep-001">
        <button onclick="createExperiment()">创建</button>
        <button class="secondary" onclick="loadExperiments()">刷新列表</button>
      </div>
      <div class="field-grid">
        <label>Learning Rate
          <input id="learningRate" value="0.0002" inputmode="decimal">
        </label>
        <label>Batch Size
          <input id="batchSize" value="8" inputmode="numeric">
        </label>
        <label>Max Steps
          <input id="maxSteps" value="80" inputmode="numeric">
        </label>
        <label>Seed
          <input id="seed" value="42" inputmode="numeric">
        </label>
        <label>Model
          <input id="modelName" value="openclaw-mini">
        </label>
        <label>Dataset
          <input id="datasetName" value="toy-instruction-mixture">
        </label>
        <label>Train Tokens
          <input id="trainTokens" value="25000000" inputmode="numeric">
        </label>
        <label>GPU Memory GB
          <input id="gpuMemory" value="24" inputmode="decimal">
        </label>
      </div>
      <p id="status" class="status"></p>
    </section>
    <section>
      <h2>实验列表</h2>
      <div class="toolbar">
        <button class="secondary" onclick="compareSelected()">比较选中实验</button>
        <button class="secondary" onclick="selectAllRuns()">全选</button>
        <button class="secondary" onclick="clearSelectedRuns()">清空选择</button>
      </div>
      <table>
        <thead>
          <tr><th>选择</th><th>Run ID</th><th>状态</th><th>步数</th><th>最佳 Eval Loss</th><th>操作</th></tr>
        </thead>
        <tbody id="experiments"></tbody>
      </table>
    </section>
    <section>
      <h2>输出</h2>
      <pre id="output">等待操作。</pre>
    </section>
  </main>
  <script>
    const output = document.getElementById('output');
    const statusLine = document.getElementById('status');

    async function api(path, options = {}) {
      const token = localStorage.getItem('openclaw_lab_token') || '';
      const headers = {'Content-Type': 'application/json'};
      if (token) headers.Authorization = `Bearer ${token}`;
      const response = await fetch(path, {
        headers,
        ...options
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || response.statusText);
      return data;
    }

    function show(data) {
      output.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
    }

    function setStatus(text, isError = false) {
      statusLine.textContent = text;
      statusLine.className = isError ? 'status error' : 'status';
    }

    function askTokenOnUnauthorized(error) {
      if (!String(error.message).includes('unauthorized')) return false;
      const token = prompt('请输入访问 token');
      if (!token) return false;
      localStorage.setItem('openclaw_lab_token', token);
      return true;
    }

    async function loadExperiments() {
      try {
        const data = await api('/api/experiments');
        const rows = data.experiments.map(run => `
          <tr>
            <td><input type="checkbox" class="run-select" value="${run.run_id}"></td>
            <td>${run.run_id}</td>
            <td>${run.status}</td>
            <td>${run.steps}</td>
            <td>${run.best_eval_loss ?? '-'}</td>
            <td>
              <button class="small" onclick="runTraining('${run.run_id}')">运行</button>
              <button class="secondary small" onclick="diagnose('${run.run_id}')">诊断</button>
              <button class="secondary small" onclick="metrics('${run.run_id}')">指标</button>
            </td>
          </tr>
        `).join('');
        document.getElementById('experiments').innerHTML = rows || '<tr><td colspan="6">还没有实验。</td></tr>';
        show(data);
        setStatus('列表已刷新。');
      } catch (error) {
        if (askTokenOnUnauthorized(error)) return loadExperiments();
        setStatus(error.message, true);
      }
    }

    async function createExperiment() {
      const name = document.getElementById('name').value.trim();
      if (!name) {
        setStatus('请输入实验名。', true);
        return;
      }
      try {
        const overrides = collectOverrides();
        const data = await api('/api/experiments', {
          method: 'POST',
          body: JSON.stringify({name, overrides})
        });
        show(data);
        setStatus('实验已创建。');
        await loadExperiments();
      } catch (error) {
        if (askTokenOnUnauthorized(error)) return createExperiment();
        setStatus(error.message, true);
      }
    }

    function collectOverrides() {
      const learningRate = Number(document.getElementById('learningRate').value);
      const batchSize = Number.parseInt(document.getElementById('batchSize').value, 10);
      const maxSteps = Number.parseInt(document.getElementById('maxSteps').value, 10);
      const seed = Number.parseInt(document.getElementById('seed').value, 10);
      const trainTokens = Number.parseInt(document.getElementById('trainTokens').value, 10);
      const gpuMemory = Number(document.getElementById('gpuMemory').value);
      const modelName = document.getElementById('modelName').value.trim();
      const datasetName = document.getElementById('datasetName').value.trim();

      if (!Number.isFinite(learningRate) || learningRate <= 0) throw new Error('Learning rate 必须是正数。');
      if (!Number.isInteger(batchSize) || batchSize <= 0) throw new Error('Batch size 必须是正整数。');
      if (!Number.isInteger(maxSteps) || maxSteps <= 0) throw new Error('Max steps 必须是正整数。');
      if (!Number.isInteger(seed)) throw new Error('Seed 必须是整数。');
      if (!Number.isInteger(trainTokens) || trainTokens <= 0) throw new Error('Train tokens 必须是正整数。');
      if (!Number.isFinite(gpuMemory) || gpuMemory <= 0) throw new Error('GPU memory 必须是正数。');
      if (!modelName) throw new Error('Model 不能为空。');
      if (!datasetName) throw new Error('Dataset 不能为空。');

      return {
        model: {name: modelName},
        data: {dataset: datasetName, train_tokens: trainTokens},
        training: {
          learning_rate: learningRate,
          batch_size: batchSize,
          max_steps: maxSteps,
          seed: seed
        },
        hardware: {gpu_memory_gb: gpuMemory}
      };
    }

    async function runTraining(runId) {
      try {
        setStatus(`正在运行 ${runId}...`);
        const data = await api(`/api/experiments/${runId}/run`, {
          method: 'POST',
          body: JSON.stringify({})
        });
        show(data);
        setStatus(`${runId} 已完成。`);
        await loadExperiments();
      } catch (error) {
        if (askTokenOnUnauthorized(error)) return runTraining(runId);
        setStatus(error.message, true);
      }
    }

    function selectedRunIds() {
      return Array.from(document.querySelectorAll('.run-select:checked')).map(input => input.value);
    }

    function selectAllRuns() {
      document.querySelectorAll('.run-select').forEach(input => input.checked = true);
    }

    function clearSelectedRuns() {
      document.querySelectorAll('.run-select').forEach(input => input.checked = false);
    }

    async function compareSelected() {
      const runIds = selectedRunIds();
      if (runIds.length < 2) {
        setStatus('至少选择两个实验再比较。', true);
        return;
      }
      try {
        const data = await api('/api/compare', {
          method: 'POST',
          body: JSON.stringify({run_ids: runIds})
        });
        show(data);
        setStatus(`比较完成，winner: ${data.winner ?? '暂无'}`);
      } catch (error) {
        if (askTokenOnUnauthorized(error)) return compareSelected();
        setStatus(error.message, true);
      }
    }

    async function diagnose(runId) {
      try {
        const data = await api(`/api/experiments/${runId}/diagnose`, {method: 'POST', body: '{}'});
        show(data);
        setStatus(`${runId} 诊断完成。`);
      } catch (error) {
        if (askTokenOnUnauthorized(error)) return diagnose(runId);
        setStatus(error.message, true);
      }
    }

    async function metrics(runId) {
      try {
        const data = await api(`/api/experiments/${runId}/metrics?tail=10`);
        show(data);
        setStatus(`${runId} 指标已读取。`);
      } catch (error) {
        if (askTokenOnUnauthorized(error)) return metrics(runId);
        setStatus(error.message, true);
      }
    }

    loadExperiments();
  </script>
</body>
</html>
"""


def main() -> None:
    host = os.environ.get(HOST_ENV, HOST)
    port = int(os.environ.get(PORT_ENV, str(PORT)))
    run(host, port)


if __name__ == "__main__":
    main()
