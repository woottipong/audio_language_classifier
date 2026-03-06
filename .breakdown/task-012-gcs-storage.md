# Task: GCS/MinIO Storage Backend

## Task ID
task-012

## Epic
epic-07-cloud-storage

## Area
backend

## Status
todo

## Priority
high

## Depends On
- task-001 (config)
- task-002 (storage abstraction exists)

## Summary
Implement `storage/gcs.py` cloud storage backend ที่ใช้ `google-cloud-storage` SDK.
รองรับ list files จาก GCS bucket และ download เป็น temp file สำหรับ processing.
Optional: MinIO/S3 compatible backend.

## Scope
- Implement `GCSStorage(StorageBackend)` ใน `storage/gcs.py`
- `list_audio_files()` → list objects จาก bucket/prefix ที่มี audio extension
- `get_local_path()` → download object เป็น temp file, return Path
- เพิ่ม `storage_type: gcs` support ใน config validation
- Register ใน `storage/__init__.py`
- Cleanup temp files หลัง processing

## Out of Scope
- MinIO/S3 (ทำเป็น task แยก)
- Streaming จาก cloud โดยตรง
- Upload results กลับไป cloud

## Acceptance Criteria
- [ ] `GCSStorage` implement ครบทั้ง `list_audio_files()` และ `get_local_path()`
- [ ] Config รองรับ `--storage-type gcs --input gs://bucket/prefix`
- [ ] Temp files ถูก cleanup
- [ ] Error handling ใช้ `StorageError` exception
- [ ] Type hints ครบ 100%
- [ ] ทดสอบกับ GCS bucket จริง (manual)

## Files Likely Affected
- `storage/gcs.py` (new)
- `storage/__init__.py`
- `config.py`
- `main.py`
- `requirements.txt`

## Test Checklist
- [ ] List files จาก bucket ที่มี audio files
- [ ] List files จาก bucket ที่ว่าง → return empty list
- [ ] Download file → process → detect language สำเร็จ
- [ ] Bucket ไม่มีอยู่ → StorageError
- [ ] Credentials ไม่มี → ConfigurationError
- [ ] Temp file ถูก cleanup หลัง processing

## Outcome

## Completion Evidence

## Completed At
