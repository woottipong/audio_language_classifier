# Task: Structured Logging + Metrics Export

## Task ID
task-015

## Epic
epic-09-observability

## Area
backend

## Status
todo

## Priority
low

## Depends On
- task-008 (performance metrics exists)

## Summary
ปรับ logging ให้เป็น structured format (JSON) สำหรับ production observability
เพิ่ม option export metrics เป็น JSON file สำหรับ monitoring/alerting

## Scope
- JSON structured logging format (optional, via config flag)
- Export `PerformanceMetrics.get_summary()` เป็น `metrics.json`
- Log correlation: request_id per batch run
- Google STT success/failure rate ใน metrics

## Out of Scope
- Prometheus/Grafana integration
- Distributed tracing
- Real-time monitoring dashboard
- Alert configuration

## Acceptance Criteria
- [ ] `--log-format json` produces structured JSON logs
- [ ] `metrics.json` exported alongside results
- [ ] Metrics include: throughput, error rate, cache hit rate, Google STT stats
- [ ] Backward compatible (default = human-readable logs)

## Files Likely Affected
- `main.py` (logging setup)
- `config.py` (new flag)
- `performance.py` (metrics export)
- `exporter.py` (metrics file)

## Test Checklist
- [ ] JSON log format parseable
- [ ] metrics.json parseable
- [ ] Default behavior unchanged
- [ ] Performance metrics accurate

## Outcome

## Completion Evidence

## Completed At
