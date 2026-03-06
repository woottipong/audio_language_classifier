# Task: Integration Tests — End-to-End

## Task ID
task-014

## Epic
epic-08-testing

## Area
backend

## Status
done

## Priority
high

## Depends On
- task-013 (pytest infrastructure)

## Summary
เขียน integration tests ที่ทดสอบ end-to-end flow: CLI → config → storage → detection → export
ใช้ audio files จริง (ขนาดเล็ก) และ faster-whisper model จริง (tiny)

## Scope
- Test: CLI argument parsing → AppConfig → process → export
- Test: LocalStorage list → detect language → CSV/JSON output
- Test: Caching flow (first run → cache miss → second run → cache hit)
- Test: Error cases (missing directory, invalid files)
- ใช้ tiny model เพื่อความเร็ว
- สร้าง fixture audio files (short, synthetic)

## Out of Scope
- Google STT integration test (ต้อง credentials + billing)
- GPU testing
- Performance benchmarks
- Docker testing

## Acceptance Criteria
- [x] `pytest tests/integration/ -v` passes
- [x] ทดสอบ full pipeline: input → detect → export
- [x] ทดสอบ caching flow
- [x] ทดสอบ error handling (graceful failure)
- [x] ไม่ต้องการ external services (offline-capable)

## Files Likely Affected
- `tests/integration/` (new directory)
- `tests/integration/test_pipeline.py` (new)
- `tests/integration/test_caching.py` (new)
- `tests/fixtures/` (test audio files)

## Test Checklist
- [x] Full pipeline produces valid CSV + JSON
- [x] Detection results include correct fields
- [x] Cache hit skips re-processing
- [x] Invalid input dir → proper error

## Outcome
7 integration tests in tests/integration/test_pipeline.py — all green (no real model download required;
classifier.detect_language is mocked; real LocalStorage + ResultCache + Exporter are exercised).
Completed: Epic 8 integration test phase.
## Completion Evidence

## Completed At
