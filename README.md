# SKRE Equipment Optimizer

เครื่องมือหาบิลด์อุปกรณ์ที่ดีที่สุดสำหรับ Seven Knights Rebirth แบบ **constraint-based**:
ระบุ "เป้าหมายสเตตัส" (เช่น Crit ≥ 71, Speed ≥ 29) แล้ว solver จะหาบิลด์ที่ไปถึงเป้า
ด้วยช่องน้อยที่สุด แล้วทุ่มช่องที่เหลือให้ objective หลัก (เช่น ATK → Crit Damage)
พร้อม **อธิบายเหตุผลทีละบรรทัด** ไม่ใช่แค่โยนคำตอบ

สูตรคำนวณสเตตัสทั้งหมด reverse-engineer มาจาก SKRE Build Maker (BETA.4) ของ Acid Aqua

## Architecture

```
target stats ─► [1] เช็ก target ที่ฐานผ่านแล้ว
                [2] คำนวณช่องขั้นต่ำต่อ target = ceil((target − ฐาน) / ค่าต่อช่อง)
                [3] greedy จัดสรรช่องที่เหลือตามลำดับความสำคัญ (ATK → CDM → HP/DEF)
                [4] คืน build + เหตุผล + Top-N alternatives
```
ไม่ใช้ brute-force เพราะ objective เป็นเชิงเส้นและแยกอิสระต่อชิ้น → constraint + greedy ให้ผลที่ดีที่สุดได้ตรง ๆ

## Roadmap

- [x] **Step 1** — data layer: ค่าคงที่จากเกม + ข้อมูลตัวละคร 111 ตัว + เทสต์
- [ ] **Step 2** — stat engine: คำนวณสเตตัสสุดท้ายจากบิลด์ + เทสต์เทียบชีต
- [ ] **Step 3** — constraint solver + greedy + reasoning
- [ ] **Step 4** — Top-N alternatives + CLI
- [ ] **Step 5** — GitHub Actions CI

## Setup (GitHub Codespaces)

```bash
pip install -r requirements.txt
pytest -q
```

## Project layout

```
skre-optimizer/
├── skre_optimizer/
│   ├── constants.py   # ตารางค่าคงที่ทั้งหมด (main/sub/transcend/set/level/ring)
│   └── data.py        # Hero dataclass + load_heroes()
├── data/heroes.json   # ข้อมูลตัวละคร
└── tests/
```
