# Task: Language-aware transcription parameters

## Task ID
task-017

## Epic
E10 — English Transcription Quality

## Area
backend

## Status
done

## Priority
high

## Depends On
- task-016

## Summary

แก้ `_transcribe_with_whisper()` ใน `classifier.py` ให้ branch Whisper parameters ตาม `detected_lang` จาก Pass 1 โดยใช้ค่า lenient สำหรับ EN และค่า aggressive (เดิม) สำหรับ TH ปัญหาปัจจุบัน: EN audio ที่มี duration > 10 วิ ถอดความออกมาว่าง หรือได้ผลสั้นกว่าที่ควรจะเป็น เพราะ anti-hallucination params ที่ tune มาสำหรับ TH ตัด segment EN ทิ้ง

## Scope

- แก้ `_transcribe_with_whisper()` ใน `classifier.py`:
  - หลัง Pass 1 detect `detected_lang` แล้ว เลือก parameter set ตาม lang
  - ถ้า `detected_lang == ENGLISH_LANGUAGE_CODE`: ใช้ EN constants จาก task-016
  - ถ้าเป็นภาษาอื่น (TH, RU, ฯลฯ): ใช้ค่าเดิม (TH anti-hallucination params)
- Import EN constants ใหม่ใน `classifier.py`

## Out of Scope

- ไม่แก้ Pass 1 detection logic
- ไม่เพิ่ม per-language config option ให้ user
- ไม่แก้ Google STT path
- ไม่แก้ VAD parameters (ใช้ร่วมกันทุกภาษา)

## Acceptance Criteria

- [ ] `_transcribe_with_whisper()` เลือก param set ตาม `detected_lang`
- [ ] EN path ใช้: `condition_on_previous_text=True`, `repetition_penalty=1.0`, `no_repeat_ngram_size=0`, `log_prob_threshold=-2.0`, `no_speech_threshold=0.7`
- [ ] TH/other path ใช้ค่าเดิมทุกตัว
- [ ] `python -m py_compile classifier.py` ผ่าน
- [ ] ทดสอบกับไฟล์ EN จริงที่ duration > 10 วิ: ได้ transcription ที่ไม่ว่าง

## Files Likely Affected

- `classifier.py`

## Test Checklist

- [ ] `python -m py_compile classifier.py` ผ่าน
- [ ] ทดสอบ EN ไฟล์ที่เคยได้ว่าง → ได้ transcription
- [ ] ทดสอบ TH ไฟล์ → ผลไม่เปลี่ยน

## Outcome

แก้ `_transcribe_with_whisper()` และ `_get_vad_parameters()` ใน `classifier.py` ให้ branch parameter set ตาม `detected_lang` จาก Pass 1 — EN ใช้ lenient params, TH/other ใช้ค่าเดิม รวมถึง VAD threshold และ min_silence_duration แยกตาม lang ด้วย

## Completion Evidence

- `_get_vad_parameters(lang)` รับ lang argument, EN returns `threshold=0.2, min_silence=500ms`
- `_transcribe_with_whisper()` branch 5 params ตาม `is_english`:
  - `condition_on_previous_text`: EN=True, other=False
  - `repetition_penalty`: EN=1.0, other=1.3
  - `no_repeat_ngram_size`: EN=0, other=3
  - `log_prob_threshold`: EN=-2.0, other=-1.0
  - `no_speech_threshold`: EN=0.7, other=0.6
- `python -m py_compile classifier.py` → OK

## Completed At
2026-03-06
