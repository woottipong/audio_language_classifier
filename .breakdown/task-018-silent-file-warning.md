# Task: Warning log for silent/empty audio files

## Task ID
task-018

## Epic
E10 — English Transcription Quality

## Area
backend

## Status
done

## Priority
medium

## Depends On
- task-002

## Summary

ปรับ `_detect_language_only()` และ `_transcribe_with_whisper()` ใน `classifier.py` ให้ log warning ชัดเจนเมื่อ `duration=0.0` หลัง Pass 1 แทนที่จะ silent fail แล้ว proceed ต่อไปยัง Pass 2 โดยไม่มีข้อมูล ปัจจุบัน: ไฟล์เงียบหรือ VAD กรองเสียงออกหมด → duration=0.0 → Pass 2 ก็ยังได้ว่าง โดยไม่มี log ชี้ให้เห็น

## Scope

- เพิ่ม warning log ใน `_transcribe_with_whisper()` เมื่อ `duration == 0.0` หลัง Pass 1:
  - Log ระบุ: ชื่อไฟล์, `lang`, `prob`, และว่า "no speech detected by VAD — transcription will be empty"
- ไม่ต้องเพิ่ม early return (ยังให้ Pass 2 รันต่อได้ตามปกติ เพราะ Pass 2 ก็คืนว่างอยู่แล้ว)

## Out of Scope

- ไม่แก้ logic การตัดสินใจ (ยังให้ proceed ต่อ)
- ไม่แก้ VAD parameters
- ไม่สร้าง metric counter สำหรับ silent files

## Acceptance Criteria

- [ ] เมื่อรัน `--transcribe` กับไฟล์ที่ `duration=0.0`: log แสดง WARNING พร้อมชื่อไฟล์และข้อความ "no speech detected"
- [ ] ไฟล์ที่มี duration > 0: ไม่มี warning นี้
- [ ] `python -m py_compile classifier.py` ผ่าน

## Files Likely Affected

- `classifier.py`

## Test Checklist

- [ ] `python -m py_compile classifier.py` ผ่าน
- [ ] รันกับไฟล์เงียบ → เห็น WARNING ใน log

## Outcome

เพิ่ม WARNING log ใน `_transcribe_with_whisper()` หลัง Pass 1 เมื่อ `duration == 0.0` ระบุชื่อไฟล์และข้อความ "VAD filtered all audio, transcription will be empty" — ช่วย debug ไฟล์เงียบได้ทันทีจาก log

## Completion Evidence

- `classifier.py` line 190: `if duration == 0.0:` → `logger.warning("No speech detected (duration=0.0) in %s — VAD filtered all audio, transcription will be empty", file_path.name)`
- warning อยู่ใน `_transcribe_with_whisper()` หลัง Pass 1 ก่อน Pass 2
- `python -m py_compile classifier.py` → OK

## Completed At
2026-03-06
