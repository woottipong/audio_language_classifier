# Task: Unit Tests — Core Modules

## Task ID
task-013

## Epic
epic-08-testing

## Area
backend

## Status
done

## Priority
high

## Depends On
- ไม่มี (ทดสอบ code ที่มีอยู่แล้ว)

## Summary
เขียน unit tests สำหรับ core modules: `config.py`, `classifier.py`, `cache.py`, `exporter.py`, `utils.py`, `exceptions.py`, `storage/local.py`
ใช้ `pytest` + mocking สำหรับ external dependencies (faster-whisper, Google STT, filesystem)

## Scope
- Setup pytest infrastructure (`tests/`, `conftest.py`, `pytest.ini`)
- Tests for `config.py`: validation logic, defaults, edge cases
- Tests for `classifier.py`: DetectionResult, detect_language flow (mocked model)
- Tests for `cache.py`: get/set/clear, TTL expiry, SHA256 matching
- Tests for `exporter.py`: CSV/JSON output format
- Tests for `utils.py`: file size check, duration check, validation
- Tests for `exceptions.py`: hierarchy correctness
- Tests for `storage/local.py`: file listing, extension filtering
- เพิ่ม `pytest` ใน `requirements.txt`

## Out of Scope
- Integration tests (ใช้ model จริง) → task-014
- Google STT tests (ต้อง credentials จริง) → task-014
- Performance/load tests

## Acceptance Criteria
- [x] `pytest` รันผ่าน 100% (0 failures)
- [x] ครอบคลุมทุก module ที่ระบุ
- [x] Mock ทุก external dependency (faster-whisper, filesystem I/O)
- [x] Edge cases: empty input, invalid config, corrupt files
- [x] Type hints ครบใน test files

## Files Likely Affected
- `tests/` (new directory)
- `tests/conftest.py` (new)
- `tests/test_config.py` (new)
- `tests/test_classifier.py` (new)
- `tests/test_cache.py` (new)
- `tests/test_exporter.py` (new)
- `tests/test_utils.py` (new)
- `tests/test_storage.py` (new)
- `requirements.txt` (add pytest)

## Test Checklist
- [x] `pytest tests/ -v` passes

## Outcome
119 unit tests across 8 modules — all green (0.81s).
Completed: Epic 8 unit test phase.
- [ ] Config validation rejects invalid inputs
- [ ] DetectionResult.to_dict() returns correct structure
- [ ] Cache respects TTL
- [ ] Exporter creates valid CSV/JSON
- [ ] LocalStorage filters by extension correctly

## Outcome

## Completion Evidence

## Completed At
