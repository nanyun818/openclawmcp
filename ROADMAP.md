# Roadmap

## Phase 1: Experiment Control Plane

- [x] Create experiment configs.
- [x] Run mock training loops.
- [x] Read metrics and generate diagnosis reports.
- [x] Compare multiple runs.
- [x] Serve a token-protected dashboard.
- [x] Deploy behind Nginx and HTTPS.

## Phase 2: MCP Agent Interface

- [x] Expose a stable Python tool layer.
- [x] Add a local stdio tool server.
- [x] Add a JSON-RPC MCP-style stdio adapter.
- [ ] Add an official MCP SDK adapter when dependencies are allowed.
- [ ] Add tool-call tracing and audit logs.
- [ ] Add policy controls for high-risk tools.

## Phase 3: Real OpenCLAW Integration

- [x] Add a runner abstraction.
- [ ] Wire a real OpenCLAW training command.
- [ ] Parse real OpenCLAW metrics.
- [ ] Add checkpoint and artifact tracking.
- [ ] Add failure pattern detection for real logs.

## Phase 4: Research Automation

- [ ] Generate learning-rate and batch-size sweeps.
- [ ] Let an agent propose the next experiment.
- [ ] Generate tool-use fine-tuning traces.
- [ ] Benchmark agent tool-calling reliability.
- [ ] Add prompt-injection test cases for tool outputs.

