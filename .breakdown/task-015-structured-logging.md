# Task: Structured Logging + Metrics Export

## Task ID
task-015

## Epic
epic-09-observability

## Area
backend

## Status
done

## Priority
low

## Depends On
- task-008 (performance metrics exists)

## Summary
ปรับ logging ให้เป็น structured format (JSON) สำหรับ production observability
เพิ่ม option export metrics เป็น JSON file สำหรับ monitoring/alerting

## Scope
- Export `PerformanceMetrics.get_summary()` เป็น `metrics.json` อัตโนมัติทุก run

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
เพิ่ม `export_metrics()` ใน `exporter.py` + เรียกใน `main.py` หลัง export CSV
ผลลัพธ์: `results/metrics.json` มี throughput, error rate, model load time ฯลฯ

## Completion Evidence
- `exporter.py`: เพิ่ม `export_metrics(metrics_data, output_dir)`
- `main.py`: เรียก `export_metrics(metrics.get_summary(), cfg.output_dir)` หลัง CSV

## Completed At
2026-03-07
