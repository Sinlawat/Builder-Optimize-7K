# SKRE Equipment Optimizer

![CI](https://github.com/USERNAME/builder-optimize-7k/actions/workflows/ci.yml/badge.svg)

เครื่องมือหาบิลด์อุปกรณ์ที่ดีที่สุดสำหรับ Seven Knights Rebirth แบบ **constraint-based**:
ระบุ "เป้าหมายสเตตัส" (เช่น Crit ≥ 71, Speed ≥ 29) แล้ว solver จะหาบิลด์ที่ไปถึงเป้า
ด้วยช่องน้อยที่สุด แล้วทุ่มช่องที่เหลือให้ objective หลัก (เช่น ATK → Crit Damage)
พร้อม **อธิบายเหตุผลทีละบรรทัด** ไม่ใช่แค่โยนคำตอบ

> เปลี่ยน `USERNAME` ในป้าย CI ด้านบนเป็นชื่อ GitHub ของคุณ

สูตรคำนวณสเตตัสทั้งหมด reverse-engineer มาจาก SKRE Build Maker (BETA.4) ของ Acid Aqua
และยึดค่ากับชีตด้วยเทสต์ (เช่น Vanessa ATK = 6,848)

## Quick start (GitHub Codespaces)

```bash
pip install -r requirements.txt
pytest                                   # 24 passed

python cli.py Vanessa --set Assassin \
    --target CR=71 SPD=29 WK=25 \
    --priority ATK CDM \
    --transcend 6 --atk-lvl 30 --ring 6 --top 3
```

## ใช้เป็นไลบรารี

```python
from solver import top_builds

builds = top_builds("Vanessa", "Assassin",
                    targets={"CR": 71, "SPD": 29},
                    priority=["ATK", "CDM"], n=3,
                    transcend=6, atk_lvl=30, ring=6)
for b in builds:
    print(b.stats["ATK"], b.targets_met)
    for line in b.reasoning:
        print(" ", line)
```

## Architecture

```
target stats ─► [1] base check     เช็ก target ที่ฐานผ่านแล้ว
                [2] allocate        เติม target ด้วย Main → Sub → roll (ถูกสุดก่อน)
                [3] priority fill    ทุ่มช่องที่เหลือให้ ATK → CDM → ...
                [4] verify          compute_stats ยืนยัน + เหตุผลทีละบรรทัด
```
objective เป็นเชิงเส้นและแยกอิสระต่อชิ้น → constraint + greedy ให้ผลที่ดีที่สุดได้ตรง ๆ
ไม่ต้อง brute-force (~10²² แบบ)

## Roadmap

- [x] **Step 1** — data layer: ค่าคงที่จากเกม + ข้อมูลตัวละคร 111 ตัว
- [x] **Step 2** — stat engine: คำนวณสเตตัสสุดท้าย + เทสต์เทียบชีต
- [x] **Step 3** — constraint solver + greedy + reasoning
- [x] **Step 4** — Top-N alternatives + CLI
- [x] **Step 5** — GitHub Actions CI

## Files

| ไฟล์ | หน้าที่ |
|------|---------|
| `constants.py` | ค่าคงที่ทั้งหมด (main/sub/transcend/set/level/ring) |
| `data.py` | `Hero` dataclass + `load_heroes()` |
| `stats.py` | `compute_stats(build)` + `validate_build(build)` |
| `solver.py` | `solve()` + `top_builds()` |
| `cli.py` | command-line interface |
| `test_*.py` | 24 tests (data / stats / solver / alternatives) |

## หมายเหตุ

solver เป็น greedy ที่ optimal สำหรับ objective เชิงเส้น และเข้าเป้าได้ในเคสปกติ
ยังไม่การันตี global optimum ในเคส target ที่ขัดแย้งกันหนัก ๆ — ถ้าเจอเคสแบบนั้น
อัปเกรดเป็น ILP (เช่น PuLP / OR-Tools) ได้ภายหลัง โดย stat engine + เทสต์เดิมใช้ต่อได้เลย
```
```
