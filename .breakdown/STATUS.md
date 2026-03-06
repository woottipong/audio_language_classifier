# Project Status

## Current Phase

Phase 2 — Enhancement & Hardening

> Phase 1 (MVP) เสร็จแล้ว: language detection, transcription, Google STT, caching, export, Docker

## Overall Progress

- [x] Epic 1: Core Language Detection (done)
- [x] Epic 2: Transcription Pipeline (done)
- [x] Epic 3: Google STT Integration (done)
- [x] Epic 4: Caching & Performance (done)
- [x] Epic 5: Export & CLI (done)
- [x] Epic 6: Docker & Deployment (done)
- [x] Epic 8: Testing & Quality
- [ ] Epic 9: Observability & Monitoring
- [x] Epic 10: English Transcription Quality (done)

**Overall: ~90% complete** (MVP done + full test suite + EN quality improvements)

## Current Priorities

1. **low** — Structured logging + metrics export (task-015)

## Blockers

- ไม่มี blocker ตอนนี้

## Epic Summary

| Epic | Name | Status | Tasks |
|------|------|--------|-------|
| E1 | Core Language Detection | done | task-001, task-002 |
| E2 | Transcription Pipeline | done | task-003, task-004 |
| E3 | Google STT Integration | done | task-005, task-006 |
| E4 | Caching & Performance | done | task-007, task-008 |
| E5 | Export & CLI | done | task-009, task-010 |
| E6 | Docker & Deployment | done | task-011 |
| E8 | Testing & Quality | done | task-013, task-014 |
| E9 | Observability & Monitoring | todo | task-015 |
| E10 | English Transcription Quality | done | task-016, task-017, task-018 |

## Task Index

| ID | Title | Epic | Status | Priority |
|----|-------|------|--------|----------|
| task-001 | Config dataclass + validation | E1 | done | high |
| task-002 | Language detection with faster-whisper | E1 | done | high |
| task-003 | Transcription mode (Whisper) | E2 | done | high |
| task-004 | Adaptive beam sizes + VAD | E2 | done | medium |
| task-005 | Google STT v2 sync API | E3 | done | high |
| task-006 | Google STT batch API + routing | E3 | done | high |
| task-007 | Result caching (SHA256 + TTL) | E4 | done | medium |
| task-008 | Performance metrics tracking | E4 | done | medium |
| task-009 | CSV + JSON exporter | E5 | done | high |
| task-010 | CLI argument parsing + batch orchestration | E5 | done | high |
| task-011 | Dockerfile (GPU + CPU variants) | E6 | done | medium |
| task-013 | Unit tests — core modules | E8 | done | high |
| task-014 | Integration tests — end-to-end | E8 | done | high |
| task-015 | Structured logging + metrics export | E9 | todo | low |
| task-016 | EN-specific transcription constants | E10 | done | high |
| task-017 | Language-aware transcription parameters | E10 | done | high |
| task-018 | Warning log for silent/empty audio files | E10 | done | medium |

## Definition of Done

- [ ] Code passes `python -m py_compile` สำหรับทุกไฟล์
- [ ] Type hints ครบ 100%
- [ ] ใช้ custom exceptions จาก `exceptions.py` (ห้าม bare `except: pass`)
- [ ] Config ผ่าน `AppConfig.validate()`
- [ ] Constants อยู่ใน `constants.py` (ไม่มี magic numbers)
- [ ] ทดสอบ manual กับ audio files จริง
- [ ] อัปเดต task file + STATUS.md

## Working Rules

- ทำทีละ 1 task
- ห้ามขยาย scope เกิน task file
- สมมติอะไรให้ระบุชัดใน task
- ใช้ `docs/architecture.md` เป็น source of truth ด้านระบบ
- ใช้ `.breakdown/STATUS.md` เป็น source of truth ด้านสถานะ
- อัปเดตทั้ง task file + STATUS.md ทุกครั้งที่สถานะเปลี่ยน
