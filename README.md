# canvas-gradebook-csv

把学生成绩原始数据填入 Canvas 官方 Gradebook 导出 CSV，生成**可直接导入**的评分文件。
这也是一个 [WorkBuddy](https://www.workbuddy.cn) 技能（Skill），导入后 AI 助手可以自动完成整个流程。

## 为什么需要它

Canvas 对 Gradebook 导入文件校验极严，直接用脚本重写导出文件几乎必翻车。实测踩过的坑：

| 坑 | 后果 |
|---|---|
| 用 `csv.writer` 重写，换行符 LF → CRLF | 最后一个表头变成 `XXX\r`，Canvas 报 **「CSV 标题行无效」** |
| 改动/丢失作业列的系统 ID（如 `作业1 (12345)`） | 列无法识别 |
| 丢失第二行 Points Possible（`100.00`、`( 只读 )`） | 导入校验失败 |
| 丢失 BOM | 中文环境下 Excel/Canvas 识别异常 |
| 忘记跳过 Canvas 内置的"测验学生 / Test Student"行 | 出现幽灵学生的分数记录 |
| 给未提交学生填 0 | "未评分"变成了"0 分"（留空才是未评分） |

本工具对官方导出文件做**字节级最小改动**：只替换目标作业列的分数格，其余一切（换行符、BOM、标题行、Points Possible 行、只读列）原样保留，并自带逐项校验。

## 快速开始

```bash
python3 scripts/fill_canvas_csv.py \
    --canvas  Canvas评分-课程示例.csv \
    --scores  分数.csv \
    --column  作业1
```

### 输入

| 参数 | 说明 |
|---|---|
| `--canvas` | Canvas 官方导出的 Gradebook CSV（Gradebook → Export 下载，UTF-8 带 BOM） |
| `--scores` | 成绩原始数据 CSV：需含**学号列**和**分数列**，表头自动识别（`学号` / `SIS Login ID` / `sid`；`分数` / `成绩` / `score` / `总分` 等） |
| `--json` | 也可传 `{"学号": 分数}` 形式的 JSON（与 `--scores` 二选一） |
| `--column` | 目标作业列名，**支持前缀匹配**（`上机作业1` 可匹配 `作业1 (12345)`） |
| `--out` | 输出路径，默认 `<canvas文件名>_已填.csv` |

### 输出与自检

脚本运行后打印自检报告，务必核对：

```
作业列: 作业1 (12345)
填入 84 人，留空 1 人
[提示] Canvas 中有 1 名学生无成绩数据(留空): 学生A(20250000001)
校验: 标题行一致=True | Points行一致=True | 变更行=84 | 换行=原样('\n')
```

- `标题行一致=True | Points行一致=True` **必须为 True**，否则输出不可用
- 退出码 `0` = 全部匹配；`2` = 存在未匹配项（文件已产出，需人工核对后再导入）

### 导入 Canvas

Gradebook → **Import** → 选择输出的 `_已填.csv` → 核对预览变更数（应等于填入人数）→ **Save Changes**。

## 作为 WorkBuddy 技能使用

把整个目录（或仓库）放入 `~/.workbuddy/skills/canvas-gradebook-csv/`，
之后对 AI 助手说"**这是 Canvas 导出的 Gradebook 和学生分数，生成导入文件**"即可自动执行。
`SKILL.md` 内含完整的工作流与禁止事项，供 AI 按规范操作。

## 注意事项

- 官方导出通常**不含引号字段**；若文件中出现 `"`，脚本会拒绝处理以防静默出错，需人工编辑
- 多评分周期（grading periods）开启时，CSV 不能新建作业，需先在 Canvas 界面建好作业列再导出
- 匹配键为 `SIS Login ID` 列（本课程 = 学号），脚本会自动 strip 并统一大写

## 文件结构

```
canvas-gradebook-csv/
├── README.md              # 本文件
├── SKILL.md               # WorkBuddy 技能定义（AI 读取的工作流）
└── scripts/
    └── fill_canvas_csv.py # 核心脚本（纯标准库，无第三方依赖）
```
