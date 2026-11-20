# ledger-harness

账本式工程闭环最小件。把「目标写进文件、每次执行都验收、失败可回退、所有结果留档」变成一个 200 行以内、零依赖、任何人可复跑的命令行工具。

它不解决任何新问题——它把开源世界早已验证的工程实践压缩成一件小到读完源码就能信的工具。

## 为什么是它

AI 时代的工程协作里，最贵的不是算力，而是「宣称」与「事实」的差距：说做完了，但没有可复跑的验收；说改好了，但没有留痕的记录；说稳定了，但没有可回退的锚点。

ledger-harness 用五个命令补上这条链：

```
init    生成 spec.md（目标与验收条件）+ constitution.md（纪律）+ LEDGER.tsv（只追加账本）
run     执行验收命令（pytest / promptfoo / 任意命令），结果追加进账本
check   体检：账本完整性、指纹抽查、脚本语法、git 卫生（只读，不改任何文件）
last    打印最近一次通过验收的记录（回退锚点）
verify  复算账本中全部指纹，验证账本未被篡改
```

## 快速开始

```bash
python3 harness.py init
python3 harness.py run -- "pytest -q"        # 任何退出码可判定的命令都行
python3 harness.py run -- "promptfoo eval"   # LLM 场景同样适用
python3 harness.py check
python3 harness.py last
python3 harness.py verify
```

## 四条纪律

1. **只增不覆盖**：账本只追加，历史行永不修改；勘误以新行注明修正对象。
2. **文件即真相**：spec 与 constitution 的 sha256 随每一行入账，改动即留痕。
3. **宣称与事实分离**：验收命令的退出码是唯一事实来源，不做任何美化。
4. **凭据不入档**：任何密钥、令牌、口令不进入账本与 spec。

## 与主流开源栈的对照

| 工程环节 | 通用开源实践 | ledger-harness 对应 |
| --- | --- | --- |
| 目标与验收条件 | spec / RFC / ADR | `spec.md`（哈希入账） |
| 固定流程与纪律 | CONTRIBUTING / 治理文档 | `constitution.md`（哈希入账） |
| 自动验收 | pytest / promptfoo / CI | `run -- <任意命令>` |
| 执行记录 | CI 日志 / 实验跟踪（MLflow 等） | `LEDGER.tsv` 只追加账本 |
| 健康巡检 | lint / git hooks | `check`（只读体检） |
| 回退锚点 | git tag / release | `last`（最近 PASS 行） |
| 防篡改 | 签名 / 不可变存储 | `verify`（指纹复算） |

它不替代上述任何一件，而是给它们一个共同的、最小的事实底座：无论验收命令是什么，结果都以同一种格式留档、可校验、可回溯。

## 设计取舍

- **零依赖**：只用 Python 标准库，任何装了 Python 3 的机器直接可跑。
- **文件即数据库**：账本就是 TSV，`git diff` 可读，`cat` 可读，不引入任何服务。
- **只读体检**：`check` 与 `verify` 不写任何文件，可以放心接进 CI。
- **末行豁免**：`verify` 允许末行与当前 spec 不同——行后修订属只增惯例，勘误走新行。

## 边界

- 它不评判验收命令写得好不好——垃圾进、垃圾出，退出码说了算。
- 它不管理密钥、不联网、不部署。
- 它不是审计工具，只是让「宣称」变得可核验的最小装置。

## License

MIT
