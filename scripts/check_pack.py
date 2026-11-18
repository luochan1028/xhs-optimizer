#!/usr/bin/env python3
"""提交前合规自检：文件数≤30、总大小≤40MB、必需文件齐全"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REQUIRED = ["SKILL.md", "README.md", "scripts/optimize.py"]
MAX_FILES, MAX_MB = 30, 40

files = [p for p in BASE.rglob("*") if p.is_file()
         and ".git" not in p.parts and "__pycache__" not in p.parts]
total_mb = sum(p.stat().st_size for p in files) / 1024 / 1024
ok = True

print(f"文件数：{len(files)}/{MAX_FILES}", "✅" if len(files) <= MAX_FILES else "❌ 超限")
ok &= len(files) <= MAX_FILES
print(f"总大小：{total_mb:.2f}MB/{MAX_MB}MB", "✅" if total_mb <= MAX_MB else "❌ 超限")
ok &= total_mb <= MAX_MB
for r in REQUIRED:
    has = (BASE / r).exists()
    print(f"必需文件 {r}：", "✅" if has else "❌ 缺失")
    ok &= has
print("\n自检通过，可提交 ✅" if ok else "\n自检未通过 ❌，请处理后再提交")
raise SystemExit(0 if ok else 1)
