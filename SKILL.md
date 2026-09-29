---
name: canvas-gradebook-csv
description: 从学生成绩原始数据 + Canvas 官方 Gradebook 导出 CSV，生成可直接导入 Canvas 的评分 CSV。当用户要求"生成 Canvas 导入文件 / 填 Gradebook CSV / 把成绩导入 Canvas"，或提供 Canvas 导出的评分 CSV 与学生分数数据时使用。核心保证：字节级最小改动，不破坏表头，规避「CSV 标题行无效」错误。
agent_created: true
---

# Canvas Gradebook 导入 CSV 生成

把已有的学生成绩数据填入 Canvas 官方 Gradebook 导出文件，产出可直接导入的 CSV。

## 背景知识（为什么不能随便重写 CSV）

Canvas 对导入文件校验极严，实测踩过的坑：

1. **换行符**：Canvas 导出为 **LF（\n）**。用 Python `csv.writer` 默认的 `\r\n` 重写会让
   最后一个表头变成 `XXX\r`，Canvas 报「CSV 标题行无效」。**必须保留原文件的换行符。**
2. **表头**：作业列带系统 ID，如 `上机作业1 (137101)`。改列名、漏列都会导致校验失败。
3. **第二行是 Points Possible 行**（如 `100.00`、只读列标 `( 只读 )`），必须原样保留。
4. **BOM**（`\xef\xbb\xbf`）：官方文件自带，保留即可。
5. **匹配键**：学生行靠 `SIS Login ID` 列（本课程 = 学号）匹配，注意 strip 并统一大写。
6. **测验学生 / Test Student 行**：Canvas 内置假学生，跳过、不填分。
7. **留空 = 未评分**（不会记 0 分）；填 0 才是 0 分。
8. 只读列（Current Score、Final Grade 等）即使改动也会被 Canvas 忽略，但不要去动它们。

## 工作流

1. **拿两份输入**：
   - Canvas 官方导出 CSV（Gradebook → Export；若无现成列，可先在界面建好作业再导出）。
   - 学生成绩原始数据（CSV：含学号列 + 分数列；或 JSON：`{"学号": 分数}`）。
2. **运行打包脚本**：
   ```bash
   python3 scripts/fill_canvas_csv.py --canvas 官方导出.csv --scores 分数.csv \
       --column 上机作业1 [--out 输出.csv]
   ```
   - `--column` 支持前缀匹配（`上机作业1` 可匹配 `上机作业1 (137101)`）。
   - 成绩表头自动识别：学号列（学号/SIS Login ID/sid…）与分数列（分数/成绩/score/总分…）。
   - JSON 输入用 `--json` 代替 `--scores`。
3. **检查脚本输出的自检报告**：
   - `标题行一致=True | Points行一致=True` —— 必须为 True，否则输出不可用。
   - 变更行数 = 有分数的学生数。
   - 未匹配提示（Canvas 有学生但无成绩 / 有成绩但 Canvas 无此人）必须逐条核对，
     常见原因：学号大小写、全角数字、XH 前缀大小写（脚本已做 strip+upper，仍不匹配则人工查）。
4. **退出码**：0 全部匹配；2 有未匹配项（文件已产出，但需人工确认后再导入）。

## 产出与交付

- 输出文件默认名 `<原文件名>_已填.csv`，放在成绩数据同目录。
- 向用户说明：导入路径为 Gradebook → Import → 选文件 → 核对预览变更数 → Save Changes。
- 预览中若出现"变更数 ≠ 预期学生数"，先不要保存，回来核对未匹配名单。

## 禁止事项

- 禁止用 `csv.writer` / pandas `to_csv` 直接重写整个官方文件（换行符与引号策略都会变）。
- 禁止修改标题行、Points Possible 行、学生姓名/学号列。
- 禁止给未提交学生填 0（留空才是"未评分"）。
- 官方文件若含引号字段（`"`），脚本会拒绝处理——此时需人工用支持引号的编辑方式处理。
