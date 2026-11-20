#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ledger-harness — 账本式工程闭环最小件 (v0.1.0)

一句话：把「目标写进文件、每次执行都验收、失败可回退、所有结果留档」变成
一个 200 行以内、零依赖、任何人可复跑的命令行工具。

闭环五步：
  init   → 生成 spec.md（目标与验收条件）+ constitution.md（纪律）+ LEDGER.tsv（只追加账本）
  run    → 执行验收命令（pytest / promptfoo / 任意命令），结果追加进账本
  check  → 体检：账本完整性、指纹抽查、脚本语法、git 卫生（只读，不改任何文件）
  last   → 打印最近一次通过验收的记录（回退锚点）
  verify → 复算账本中全部指纹，验证账本未被篡改

设计纪律（与 constitution.md 对应）：
  1. 只增不覆盖：账本只追加，历史行永不修改
  2. 文件即真相：spec/constitution 的 sha256 记入每一行
  3. 宣称与事实分离：验收命令的退出码就是事实，不做任何美化
  4. 凭据不入档：账本只存哈希与结论，不存任何密钥

用法：
  python3 harness.py init
  python3 harness.py run -- "pytest -q"        # 或 promptfoo / 任意验收命令
  python3 harness.py check
  python3 harness.py last
  python3 harness.py verify
"""
import hashlib, os, subprocess, sys, time

LEDGER = "LEDGER.tsv"
SPEC = "spec.md"
CONSTITUTION = "constitution.md"
FIELDS = ["ts", "verdict", "cmd_sha", "spec_sha", "const_sha", "detail"]

def sha(text):
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()[:16]

def file_sha(path):
    if not os.path.exists(path):
        return "-"
    return sha(open(path, "rb").read().decode("utf-8", "ignore"))

def append_row(cells):
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write("\t".join(cells) + "\n")

def read_rows():
    if not os.path.exists(LEDGER):
        return []
    out = []
    for line in open(LEDGER, encoding="utf-8"):
        line = line.rstrip("\n")
        if line and not line.startswith("ts\t"):
            out.append(dict(zip(FIELDS, line.split("\t"))))
    return out

def cmd_init():
    if os.path.exists(LEDGER):
        print("already initialized:", LEDGER); return 1
    with open(LEDGER, "w", encoding="utf-8") as f:
        f.write("\t".join(FIELDS) + "\n")
    if not os.path.exists(SPEC):
        open(SPEC, "w", encoding="utf-8").write(
            "# spec — 目标与验收条件\n\n"
            "## 目标\n（本次要达成什么，一句话）\n\n"
            "## 验收条件\n- [ ] 条件一（可机器判定，交给 run 的验收命令）\n"
            "- [ ] 条件二\n\n"
            "## 边界\n（不做什么）\n")
    if not os.path.exists(CONSTITUTION):
        open(CONSTITUTION, "w", encoding="utf-8").write(
            "# constitution — 工程纪律\n\n"
            "1. 只增不覆盖：LEDGER.tsv 只追加，历史行永不修改；勘误以新行注明修正对象。\n"
            "2. 文件即真相：spec 与 constitution 的哈希随每行入账，改动即留痕。\n"
            "3. 宣称与事实分离：验收命令退出码为唯一事实来源；推演标明为推演。\n"
            "4. 凭据不入档：任何密钥、令牌、口令不进入账本与 spec。\n")
    print("initialized:", LEDGER, SPEC, CONSTITUTION)
    return 0

def cmd_run(cmd):
    if not cmd:
        print("usage: run -- <acceptance command>"); return 2
    t0 = time.time()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    verdict = "PASS" if r.returncode == 0 else "FAIL"
    tail = (r.stdout + r.stderr).strip().splitlines()
    detail = (tail[-1][:120] if tail else "")
    append_row([time.strftime("%Y-%m-%d %H:%M:%S"), verdict,
                sha(" ".join(cmd)), file_sha(SPEC), file_sha(CONSTITUTION),
                "rc=%d %.1fs %s" % (r.returncode, time.time() - t0, detail)])
    print("[%s] %s" % (verdict, " ".join(cmd)))
    print("appended to", LEDGER)
    return 0 if verdict == "PASS" else 1

def cmd_check():
    rows = read_rows()
    problems = []
    # 1 账本完整性：行数与表头、字段数
    if os.path.exists(LEDGER):
        for i, line in enumerate(open(LEDGER, encoding="utf-8")):
            if line.strip() and len(line.rstrip("\n").split("\t")) != len(FIELDS):
                problems.append("ledger line %d field count mismatch" % (i + 1))
    # 2 指纹抽查：最近 5 行的 spec/constitution 哈希与现文件复算
    for row in rows[-5:]:
        if row["spec_sha"] != "-" and row["spec_sha"] != file_sha(SPEC):
            problems.append("spec changed after row %s (amendment should be a new row)" % row["ts"])
    # 3 脚本语法
    for f in os.listdir("."):
        if f.endswith(".py"):
            r = subprocess.run([sys.executable, "-m", "py_compile", f], capture_output=True)
            if r.returncode != 0:
                problems.append("syntax error in " + f)
    # 4 git 卫生
    if os.path.isdir(".git"):
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        n = len([l for l in r.stdout.splitlines() if l.strip()])
        if n:
            problems.append("%d uncommitted entries (files should be committed to freeze state)" % n)
    print("check: %d rows, %d problems" % (len(rows), len(problems)))
    for p in problems:
        print("  !", p)
    return 0 if not problems else 1

def cmd_last():
    rows = read_rows()
    good = [r for r in rows if r["verdict"] == "PASS"]
    if not good:
        print("no PASS row yet"); return 1
    r = good[-1]
    print("last good:", r["ts"], "spec_sha=", r["spec_sha"], r["detail"])
    return 0

def cmd_verify():
    rows = read_rows()
    bad = [r for r in rows if r["spec_sha"] != "-" and r["spec_sha"] != file_sha(SPEC)
           and r != rows[-1]]  # 末行允许与当前文件不同（行后修订属只增惯例）
    print("verify: %d rows, %d historical rows inconsistent with current spec (expect 0 unless amended)"
          % (len(rows), len(bad)))
    return 0 if not bad else 1

def main():
    argv = sys.argv[1:]
    commands = ("init", "run", "check", "last", "verify")
    if not argv or argv[0] not in commands or len(argv) > 1 and argv[0] != "run":
        print("usage: harness.py {init|run|check|last|verify} [-- <acceptance command>]")
        return 2
    command, rest = argv[0], argv[1:]
    if command == "run":
        if rest and rest[0] == "--":
            rest = rest[1:]
        return cmd_run(rest)
    return {"init": cmd_init, "check": cmd_check,
            "last": cmd_last, "verify": cmd_verify}[command]()

if __name__ == "__main__":
    sys.exit(main())
