# AI Workflow

> โครงสร้างหลักใช้แบบนี้:
- `docs/ARCHITECTURE.md`
- `.breakdown/STATUS.md`
- `.breakdown/task-*.md`

---

## โครงสร้างไฟล์

```text
project/
├── docs/
│   └── ARCHITECTURE.md
└── .breakdown/
    ├── STATUS.md
    ├── task-template.md
    ├── task-001-<slug>.md
    └── task-002-<slug>.md
```

---

## หน้าที่ของแต่ละไฟล์

### `docs/ARCHITECTURE.md`
ใช้เก็บภาพรวมระบบ
- โปรเจกต์นี้คืออะไร
- MVP ทำอะไร
- ไม่ทำอะไร
- stack
- flow / component หลัก
- assumptions

### `.breakdown/STATUS.md`
ใช้เก็บภาพรวมงาน
- phase ปัจจุบัน
- progress
- priorities
- blockers
- task index
- working rules
- definition of done

### `.breakdown/task-*.md`
ใช้เก็บรายละเอียดงานแต่ละ task
- task นี้คืออะไร
- scope
- out of scope
- acceptance criteria
- dependencies
- outcome ตอนทำเสร็จ

---

## วิธีทำงาน

### 1) วางระบบ
เริ่มจากเขียน `docs/ARCHITECTURE.md`

**Prompt**
```text
ช่วยเขียน `docs/ARCHITECTURE.md` จาก requirements นี้: [รายละเอียด]
ให้สรุปเฉพาะภาพรวมระบบ, MVP scope, non-goals, stack, components, flow, assumptions
```

---

### 2) วางภาพรวมงาน
สร้าง `.breakdown/STATUS.md`

**Prompt**
```text
ช่วยเขียน `.breakdown/STATUS.md` จาก `docs/ARCHITECTURE.md`

ให้มี:
- Current Phase
- Overall Progress
- Current Priorities
- Blockers
- Epic Summary
- Task Index
- Definition of Done
- Working Rules
```

---

### 3) แตกงาน
สร้างไฟล์ใน `.breakdown/`

หลักการ:
- 1 task = 1 deliverable
- ทำจบได้ใน 1 session
- มี acceptance criteria ชัด

**Prompt**
```text
ช่วยแตกงานจาก `docs/ARCHITECTURE.md` เป็น task files ใน `.breakdown/`

กติกา:
- 1 task = 1 deliverable
- แต่ละ task ต้องมี:
  - Task ID
  - Epic
  - Area
  - Status
  - Priority
  - Depends On
  - Summary
  - Scope
  - Out of Scope
  - Acceptance Criteria
  - Files Likely Affected
  - Test Checklist
- อย่าเกิน MVP scope
```

---

### 4) ลงมือทำทีละ task
เวลาจะให้ AI ทำงาน ให้ส่ง:
- `docs/ARCHITECTURE.md`
- `.breakdown/STATUS.md`
- task file ที่กำลังทำ

**Prompt**
```text
ช่วยทำงานตาม task นี้

Use as source of truth:
- `docs/ARCHITECTURE.md`
- `.breakdown/STATUS.md`
- `.breakdown/task-005-<slug>.md`

กติกา:
- ทำเฉพาะ task นี้
- อย่าขยาย scope
- ถ้าต้องสมมติอะไร ให้ระบุชัด
```

---

### 5) ตรวจว่างานเสร็จหรือยัง
เช็กเทียบ acceptance criteria

**Prompt**
```text
ช่วยตรวจว่า task นี้ done หรือยัง

Use:
- `docs/ARCHITECTURE.md`
- `.breakdown/STATUS.md`
- `.breakdown/task-005-<slug>.md`
- code/output ที่เกี่ยวข้อง

ให้เทียบกับ acceptance criteria และบอก:
- อะไรครบแล้ว
- อะไรยังขาด
- ถ้ายังไม่เสร็จ งานที่เหลือน้อยที่สุดคืออะไร
```

---

### 6) เมื่อ task เสร็จ
อัปเดต 2 จุด

#### 6.1 อัปเดต task file
- `Status: done`
- เพิ่ม `Outcome`
- เพิ่ม `Completion Evidence`
- เพิ่ม `Completed At`

**Prompt**
```text
ช่วยอัปเดต `.breakdown/task-005-<slug>.md` ให้เป็นสถานะ done

Requirements:
- change Status to done
- add Outcome
- add Completion Evidence
- add Completed At
- keep scope and acceptance criteria unchanged
```

#### 6.2 อัปเดต `.breakdown/STATUS.md`
- เปลี่ยนสถานะ task
- ปรับ progress
- ปรับ priorities
- อัปเดต blockers

**Prompt**
```text
ช่วยอัปเดต `.breakdown/STATUS.md` หลัง task นี้เสร็จแล้ว

Requirements:
- update task status
- update overall progress
- update current priorities
- remove/update related blockers
- keep unrelated tasks unchanged
```

---

## กฎการใช้

- `docs/ARCHITECTURE.md` = source of truth ด้านระบบ
- `.breakdown/STATUS.md` = source of truth ด้านสถานะงาน
- `.breakdown/task-*.md` = source of truth ด้านงานรายชิ้น
- ทำทีละ task
- ห้ามให้ AI ทำงานนอก task file
- task เสร็จแล้วไม่ต้องลบไฟล์
- update ทั้ง task file และ `.breakdown/STATUS.md` ทุกครั้งที่สถานะเปลี่ยน

---

## โครงขั้นต่ำของแต่ละไฟล์

### `docs/ARCHITECTURE.md`
```markdown
# ARCHITECTURE

## Overview
## Goals
## Non-Goals
## Stack
## Components
## Flow
## Assumptions
```

### `.breakdown/STATUS.md`
```markdown
# Project Status

## Current Phase
## Overall Progress
## Current Priorities
## Blockers
## Epic Summary
## Task Index
## Definition of Done
## Working Rules
```

### `.breakdown/task-template.md`
```markdown
# Task: <title>

## Task ID
task-xxx

## Epic
epic-xx-<name>

## Area
backend / frontend / infra / worker

## Status
todo

## Priority
high / medium / low

## Depends On
- task-...

## Summary
...

## Scope
- ...

## Out of Scope
- ...

## Acceptance Criteria
- ...

## Files Likely Affected
- ...

## Test Checklist
- [ ] ...

## Outcome
...

## Completion Evidence
...

## Completed At
...
```

---

## สรุปสั้น

1. เขียน `docs/ARCHITECTURE.md`
2. สร้าง `.breakdown/STATUS.md`
3. แตก `.breakdown/task-*.md`
4. ให้ AI ทำทีละ task
5. ตรวจตาม acceptance criteria
6. เสร็จแล้ว update task file + `.breakdown/STATUS.md`