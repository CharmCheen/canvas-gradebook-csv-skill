# canvas-gradebook-csv

把学生成绩填入 Canvas 官方 Gradebook 导出 CSV，生成**可直接导入**的评分文件。
对官方文件做字节级最小改动（保留 LF 换行、BOM、标题行、Points Possible 行），自带校验，规避「CSV 标题行无效」等导入报错。

## 用法

```bash
python3 scripts/fill_canvas_csv.py \
    --canvas  Canvas评分-课程示例.csv \
    --scores  分数.csv \
    --column  作业1
```

| 参数 | 说明 |
|---|---|
| `--canvas` | Canvas 官方导出的 Gradebook CSV（Gradebook → Export） |
| `--scores` | 成绩 CSV：需含学号列 + 分数列，表头自动识别（`学号` / `SIS Login ID` / `分数` / `成绩` / `score` 等） |
| `--json` | 也可传 `{"学号": 分数}` 的 JSON（与 `--scores` 二选一） |
| `--column` | 目标作业列名，支持前缀匹配（`作业1` 可匹配 `作业1 (12345)`） |
| `--out` | 输出路径，默认 `<canvas文件名>_已填.csv` |

纯 Python 标准库，无第三方依赖。

## 导入 Canvas

Gradebook → **Import** → 选择输出的 `_已填.csv` → 核对预览变更数 → **Save Changes**。

运行结束后核对自检报告：`标题行一致=True | Points行一致=True` 必须为 True；退出码 `0` = 全部匹配，`2` = 有未匹配项（先核对名单再导入）。留空即"未评分"，不会记 0 分。

## 作为 AI 助手技能安装

`SKILL.md` 遵循开放的 Agent Skills 标准，以下工具均原生支持，放入对应目录即自动注册（不出现就重启一次）：

| 工具 | 目录 | 显式调用 |
|---|---|---|
| WorkBuddy | `~/.workbuddy/skills/canvas-gradebook-csv/` | — |
| Claude Code | `~/.claude/skills/canvas-gradebook-csv/` | `/canvas-gradebook-csv` |
| Codex CLI / IDE / ChatGPT 桌面端 | `~/.agents/skills/canvas-gradebook-csv/`（或 `~/.codex/skills/`） | `$canvas-gradebook-csv` |

Codex 会按 description 隐式匹配，也可在提示词里用 `$canvas-gradebook-csv` 显式调用；可用 `agents/openai.yaml` 声明展示信息（可选）。
