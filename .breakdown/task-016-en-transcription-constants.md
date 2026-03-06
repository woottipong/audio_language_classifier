# Task: EN-specific transcription constants

## Task ID
task-016

## Epic
E10 — English Transcription Quality

## Area
backend

## Status
done

## Priority
high

## Depends On
- task-002
- task-003

## Summary

เพิ่ม EN-specific Whisper transcription constants ใน `constants.py` แยกออกจาก TH anti-hallucination params ที่มีอยู่ เพื่อให้ task-017 นำไปใช้ branch params ตาม detected language

## Scope

- เพิ่ม constants ใหม่ 5 ตัวสำหรับ EN transcription:
  - `WHISPER_EN_CONDITION_ON_PREVIOUS_TEXT = True`
  - `WHISPER_EN_REPETITION_PENALTY = 1.0`
  - `WHISPER_EN_NO_REPEAT_NGRAM_SIZE = 0`
  - `WHISPER_EN_LOG_PROB_THRESHOLD = -2.0`
  - `WHISPER_EN_NO_SPEECH_THRESHOLD = 0.7`
- เพิ่ม comment อธิบายว่าทำไมค่า EN ถึงต่างจาก TH

## Out of Scope

- ไม่แก้ classifier.py (นั่นคืองานของ task-017)
- ไม่แก้ TH constants เดิม
- ไม่เพิ่ม config option ให้ user override ค่าเหล่านี้

## Acceptance Criteria

- [ ] `constants.py` มี constants ใหม่ 5 ตัวครบ
- [ ] constants อยู่ในกลุ่มเดียวกัน มี comment block อธิบาย
- [ ] ค่าสะท้อนเหตุผล: EN ปิด penalty/ngram, threshold หลวมกว่า TH
- [ ] `python -m py_compile constants.py` ผ่าน

## Files Likely Affected

- `constants.py`

## Test Checklist

- [ ] `python -m py_compile constants.py` ผ่านโดยไม่มี error

## Outcome

เพิ่ม 7 constants ใหม่ใน `constants.py` แยก EN-specific transcription params ออกจาก TH anti-hallucination params พร้อม comment block อธิบายเหตุผลแต่ละค่า

## Completion Evidence

- `WHISPER_EN_CONDITION_ON_PREVIOUS_TEXT = True`
- `WHISPER_EN_REPETITION_PENALTY = 1.0`
- `WHISPER_EN_NO_REPEAT_NGRAM_SIZE = 0`
- `WHISPER_EN_LOG_PROB_THRESHOLD = -2.0`
- `WHISPER_EN_NO_SPEECH_THRESHOLD = 0.7`
- `WHISPER_EN_VAD_THRESHOLD = 0.2`
- `WHISPER_EN_VAD_MIN_SILENCE_DURATION_MS = 500`
- `python -m py_compile constants.py` → OK

## Completed At
2026-03-06
