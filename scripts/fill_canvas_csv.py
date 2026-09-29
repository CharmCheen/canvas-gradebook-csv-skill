#!/usr/bin/env python3
"""
把学生成绩原始数据填入 Canvas 官方 Gradebook 导出 CSV，生成可直接导入的文件。

核心原则：对官方导出文件做"字节级最小改动"——
只替换目标作业列的分数格，标题行、Points Possible 行、换行符(LF)、BOM 全部原样保留。
绝不能用 csv.writer 重写整个文件（会把 LF 变 CRLF，污染最后一个表头，导致 Canvas 报「标题行无效」）。

用法:
  python3 fill_canvas_csv.py --canvas 官方导出.csv --scores 分数.csv \
      --column 上机作业1 [--out 输出.csv]

--canvas  Canvas Gradebook 导出的 CSV（UTF-8 带 BOM，LF 换行）
--scores  成绩原始数据 CSV，需包含学号列与分数列，表头支持:
          学号 / 学生学号 / SIS Login ID / sid  和  分数 / 成绩 / score / 总分
          （也可用 --json 传入 {"学号": 分数} 形式的 JSON）
--column  目标作业列名，支持前缀匹配（如 "上机作业1" 匹配 "上机作业1 (137101)"）
--out     输出路径（默认: <canvas文件名>_已填.csv 放在 scores 文件同目录）
退出码: 0 成功；1 参数/结构错误；2 有未匹配学生（仍会产出文件，供人工复核）
"""
import argparse, json, sys, os

SCORE_KEY_CANDIDATES = ['学号', '学生学号', 'sis login id', 'sis_login_id', 'sid', '登录id']
VAL_KEY_CANDIDATES = ['分数', '成绩', 'score', '总分', 'curve', 'curved_total', '最终分']


def load_scores(args):
    """返回 {学号(大写字符串): 分数或None}。"""
    scores = {}
    if args.json:
        data = json.load(open(args.json, encoding='utf-8-sig'))
        for k, v in data.items():
            scores[str(k).strip().upper()] = None if v in (None, '') else v
        return scores
    raw = open(args.scores, 'rb').read().decode('utf-8-sig')
    lines = [ln for ln in raw.replace('\r\n', '\n').split('\n') if ln.strip()]
    header = [h.strip() for h in lines[0].split(',')]
    key_i = val_i = None
    for i, h in enumerate(header):
        hl = h.lower()
        if key_i is None and any(k in hl for k in SCORE_KEY_CANDIDATES):
            key_i = i
        if val_i is None and any(v in hl for v in VAL_KEY_CANDIDATES):
            val_i = i
    if key_i is None or val_i is None:
        sys.exit('[错误] 成绩文件表头需包含学号列(%s)和分数列(%s)，实际: %s'
                 % (SCORE_KEY_CANDIDATES, VAL_KEY_CANDIDATES, header))
    for ln in lines[1:]:
        parts = ln.split(',')
        if len(parts) <= max(key_i, val_i):
            continue
        sid = parts[key_i].strip().upper()
        val = parts[val_i].strip()
        scores[sid] = None if val == '' else val
    return scores


def find_column(header, wanted):
    """精确匹配优先，其次前缀匹配（忽略大小写）。"""
    for i, h in enumerate(header):
        if h.strip() == wanted:
            return i, h
    for i, h in enumerate(header):
        if h.strip().lower().startswith(wanted.lower()):
            return i, h
    sys.exit('[错误] 在 Canvas 文件中找不到作业列 %r，现有列: %s' % (wanted, header))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--canvas', required=True, help='Canvas 官方导出 CSV')
    ap.add_argument('--scores', help='成绩原始数据 CSV')
    ap.add_argument('--json', help='成绩 JSON（{"学号": 分数}），与 --scores 二选一')
    ap.add_argument('--column', required=True, help='目标作业列名（支持前缀匹配）')
    ap.add_argument('--out', help='输出路径')
    args = ap.parse_args()
    if not args.scores and not args.json:
        sys.exit('[错误] 需要 --scores 或 --json 之一')

    raw = open(args.canvas, 'rb').read()
    had_bom = raw[:3] == b'\xef\xbb\xbf'
    text = raw.decode('utf-8-sig')

    # 只支持无引号字段的文件（Canvas 导出通常如此）；有引号则拒绝，防止切分出错
    if '"' in text:
        sys.exit('[错误] Canvas 文件含引号字段，无法安全按逗号切分，请人工处理')

    eol = '\r\n' if '\r\n' in text else '\n'
    if eol != '\n':
        print('[警告] 官方文件使用 %s 换行，将原样保留' % repr(eol))
    trailing = text.endswith('\n')
    lines = text.split(eol)
    if trailing:
        lines = lines[:-1]
    if len(lines) < 3:
        sys.exit('[错误] 文件行数不足（应至少含表头、Points Possible、学生行）')

    header = lines[0].split(',')
    ci, col_name = find_column(header, args.column)
    li = next((i for i, h in enumerate(header) if h.strip() == 'SIS Login ID'), None)
    if li is None:
        sys.exit('[错误] 找不到 SIS Login ID 列')

    scores = load_scores(args)
    filled = blank_kept = 0
    unmatched_students, unmatched_scores = [], []
    matched_sids = set()
    for i in range(2, len(lines)):
        parts = lines[i].split(',')
        name = parts[0].strip() if parts else ''
        if not name or '测验学生' in name or 'Test Student' in name:
            continue  # 空行 / Canvas 内置 Test Student，一律跳过
        sid = parts[li].strip().upper() if len(parts) > li else ''
        if sid in scores:
            matched_sids.add(sid)
            val = scores[sid]
            parts[ci] = '' if val is None else str(val)
            if val is None:
                blank_kept += 1
            else:
                filled += 1
            lines[i] = ','.join(parts)
        else:
            unmatched_students.append('%s(%s)' % (name, sid))

    for sid in scores:
        if sid not in matched_sids:
            unmatched_scores.append(sid)

    out_lines = lines + ([''] if trailing else [])
    out_text = eol.join(out_lines)
    data = out_text.encode('utf-8')
    if had_bom:
        data = b'\xef\xbb\xbf' + data
    out = args.out or os.path.splitext(args.canvas)[0] + '_已填.csv'
    with open(out, 'wb') as f:
        f.write(data)

    # 校验：标题行与 Points Possible 行必须与原文件逐字节一致，且无新增 \r
    new_text = open(out, 'rb').read().decode('utf-8-sig')
    ok_header = new_text.split(eol)[0] == text.split(eol)[0]
    ok_points = new_text.split(eol)[1] == text.split(eol)[1]
    diff = sum(1 for a, b in zip(text.split(eol), new_text.split(eol)) if a != b)
    print('作业列: %s' % col_name)
    print('填入 %d 人，留空 %d 人' % (filled, blank_kept))
    if unmatched_students:
        print('[提示] Canvas 中有 %d 名学生无成绩数据(留空): %s'
              % (len(unmatched_students), '、'.join(unmatched_students)))
    if unmatched_scores:
        print('[提示] %d 条成绩未匹配到 Canvas 学生: %s'
              % (len(unmatched_scores), '、'.join(unmatched_scores)))
    print('校验: 标题行一致=%s | Points行一致=%s | 变更行=%d | 换行=原样(%s)'
          % (ok_header, ok_points, diff, repr(eol)))
    if not (ok_header and ok_points):
        sys.exit('[错误] 表头校验失败，输出文件不可用！')
    print('输出:', out)
    sys.exit(0 if not (unmatched_students or unmatched_scores) else 2)


if __name__ == '__main__':
    main()
