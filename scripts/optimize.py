#!/usr/bin/env python3
"""
小红书笔记诊断优化 Skill 主脚本
用法: python3 optimize.py --note 笔记.txt --niche 美食 --keywords 减脂餐,30天,8斤 --output 报告.md
笔记文件格式：第一行为标题，空一行后为正文（含#标签）
"""
import argparse, re
from pathlib import Path
import yaml

BASE = Path(__file__).resolve().parent.parent
DIGITS = re.compile(r"\d+")
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]")
INTERACT = re.compile(r"(你们|姐妹们|评论区|留言|投票|你怎么看|试过吗|有用吗)")
CLICKBAIT_OVER = re.compile(r"(震惊|竟然|天啊|救命|离谱|吓死)")

def load_data():
    d = BASE / "data"
    patterns = yaml.safe_load((d / "title_patterns.yaml").read_text(encoding="utf-8"))["patterns"]
    risks = [w.strip() for w in (d / "risk_words.txt").read_text(encoding="utf-8").split("\n")
             if w.strip() and not w.strip().startswith("#")]
    tags = yaml.safe_load((d / "tags.yaml").read_text(encoding="utf-8"))["niches"]
    times = yaml.safe_load((d / "post_times.yaml").read_text(encoding="utf-8"))
    return patterns, risks, tags, times

def diagnose_title(title, patterns):
    score, notes = 30, []
    n = len(title)
    if n <= 20: notes.append(f"✅ 标题 {n} 字，长度合适（小红书标题建议≤20字）")
    else:
        score -= 8; notes.append(f"⚠️ 标题 {n} 字偏长，信息流中会被折叠，建议压缩到20字内")
    if DIGITS.search(title): score += 0; notes.append("✅ 含数字，具体感强")
    else: score -= 4; notes.append("⚠️ 标题无数字，加上具体数字点击率更高")
    if "?" in title or "？" in title or "!" in title or "！" in title:
        notes.append("✅ 有疑问/感叹语气，情绪钩子到位")
    else: score -= 3; notes.append("⚠️ 缺情绪钩子，试试反问或感叹句式")
    if CLICKBAIT_OVER.search(title):
        score -= 5; notes.append("⚠️ 标题党词汇过重，易被限流且伤信任")
    hit = [p["name"] for p in patterns if any(k in title for k in ("怎么", "为什么", "避雷", "秘密", "天", "块"))]
    notes.append("✅ 命中高点击句式特征" if hit else "ℹ️ 未明显命中高点击句式，见下方改写建议")
    return max(score, 0), notes

def diagnose_body(body):
    score, notes = 25, []
    n = len(re.sub(r"\s+", "", body))
    if 300 <= n <= 800: notes.append(f"✅ 正文 {n} 字，信息量适中")
    elif n < 300: score -= 6; notes.append(f"⚠️ 正文仅 {n} 字，偏单薄，加细节/过程/感受")
    else: score -= 4; notes.append(f"⚠️ 正文 {n} 字偏长，注意分段，重点前置")
    paras = [p for p in body.split("\n") if p.strip()]
    if len(paras) >= 3: notes.append(f"✅ 分 {len(paras)} 段，阅读节奏好")
    else: score -= 4; notes.append("⚠️ 几乎没分段，手机端阅读压力大，回车分段")
    em = len(EMOJI.findall(body))
    if em >= 3: notes.append(f"✅ emoji {em} 个，氛围感够")
    elif em > 0: notes.append(f"ℹ️ emoji {em} 个，可再加2-3个作段落分隔")
    else: score -= 3; notes.append('⚠️ 零 emoji，小红书体感偏"严肃"，适当加')
    if INTERACT.search(body): notes.append("✅ 有互动引导（提问/喊话），利评论区")
    else: score -= 4; notes.append("⚠️ 无互动引导，结尾加一句提问（如'你们试过吗'）")
    return max(score, 0), notes

def diagnose_tags(body, niche, tags_db):
    score, notes, rec = 15, [], []
    found = re.findall(r"#(\S+)", body)
    if 3 <= len(found) <= 8: notes.append(f"✅ 标签 {len(found)} 个，数量合适")
    elif len(found) < 3:
        score -= 6; notes.append(f"⚠️ 只有 {len(found)} 个标签，曝光入口太少")
    else: score -= 3; notes.append(f"⚠️ {len(found)} 个标签偏多，堆砌会被降权")
    if niche in tags_db:
        rec = [t for t in tags_db[niche] if t not in found][:8 - len(found)]
        if rec: notes.append(f"💡 推荐补标签：{' '.join('#'+t for t in rec)}")
    return max(score, 0), notes, found

def diagnose_risk(text, risks):
    score, notes = 20, []
    hit = [w for w in risks if w in text]
    if not hit: notes.append("✅ 未命中风险词库")
    else:
        score -= min(5 * len(hit), 18)
        notes.append(f"🚨 命中风险词 {len(hit)} 个：{'、'.join(hit)}")
        notes.append("   → 站外引流词（微信/私聊）易限流，改'主页简介有方式'；极限词改温和表达")
    return max(score, 0), notes

def pick_numbers(keywords):
    """选数字：优先取不带时间单位的数字（如 8斤 的 8），避免“30天→30个变化”"""
    joined = "".join(keywords)
    nums = re.findall(r"\d+", joined)
    for n in nums:
        if not re.search(n + r"\s*(天|周|月|年|小时|分钟)", joined):
            return n
    return nums[0] if nums else "3"

def pick_times(keywords):
    ts = [k for k in keywords if any(u in k for u in ("天", "周", "月", "年", "小时", "分钟"))]
    return ts[0] if ts else "30天"

def rewrite_titles(keywords, patterns):
    """用关键词填充句式槽位；填不上的槽位明确标出待填项"""
    kw = keywords[0] if keywords else "关键词"
    fill = {"{kw}": kw, "{n}": pick_numbers(keywords), "{时间}": pick_times(keywords)}
    out = []
    for p in patterns[:3]:
        t = p["template"]
        missing = []
        for slot in re.findall(r"\{[^}]+\}", t):
            if slot in fill:
                t = t.replace(slot, fill[slot])
            else:
                missing.append(slot.strip("{}"))
                t = t.replace(slot, "…")
        out.append((p["name"], t, missing, p["tip"], p["example"]))
    return out


# ---- 对标改写（--style）：单篇吃透，不取平均 ----
STYLE_HOOKS = [
    ("数字钩", re.compile(r"\d+"), "{kw}{时间}实测：{n}个变化", "数字放前，具体感强"),
    ("时间钩", re.compile(r"(天|周|月|年|小时|分钟)"), "{时间}，我靠{kw}{改变}", "时间越短、改变越大，点击越高"),
    ("反问钩", re.compile(r"[？?]|吗\b|呢|怎么|为什么|如何"), "{kw}真的有用吗？{时间}亲测告诉你", "用反问制造认知冲突"),
    ("对比钩", re.compile(r"[vV][sS]|PK|对比|差别|差距|前后"), "{kw}前后对比：{时间}差别有多大", "对比结构天然带悬念"),
    ("悬念钩", re.compile(r"秘密|真相|避雷|内幕|不会告诉你|建议收藏"), "没人告诉你的{kw}真相，{n}条", "利他型标题，收藏率最高"),
    ("情绪钩", re.compile(r"[!！]|天啊|救命|竟然|离谱"), "{kw}{时间}亲测，效果分享", "情绪词慎用：过重会被判标题党"),
]

def analyze_style(ref_title):
    """拆解对标爆款标题的钩子结构：返回命中的钩子 + 分段数"""
    hits = []
    for name, pat, template, tip in STYLE_HOOKS:
        if pat.search(ref_title):
            hits.append({"name": name, "template": template, "tip": tip})
    segs = [s for s in re.split(r"[，。！？；、,]", ref_title) if s.strip()]
    return hits, len(segs)

def rewrite_with_style(keywords, style_hits):
    """用用户的关键词，套对标爆款的钩子结构（学结构，不抄文案）"""
    kw = keywords[0] if keywords else "关键词"
    fill = {"{kw}": kw, "{n}": pick_numbers(keywords),
            "{时间}": pick_times(keywords), "{改变}": "大变样"}
    out = []
    for h in style_hits[:3]:
        t = h["template"]
        missing = []
        for slot in re.findall(r"\{[^}]+\}", t):
            if slot in fill:
                t = t.replace(slot, fill[slot])
            else:
                missing.append(slot.strip("{}"))
                t = t.replace(slot, "…")
        out.append((h["name"], t, missing, h["tip"]))
    return out


def diagnose_cover(cover_path):
    """封面初检（PIL）：尺寸比例/文件大小。不计入总分，附加项。"""
    notes = []
    if not cover_path:
        return ["ℹ️ 未提供封面图（--cover），跳过封面检查"]
    try:
        from PIL import Image
        img = Image.open(cover_path)
        w, h = img.size
        ratio = w / h
        size_kb = Path(cover_path).stat().st_size / 1024
        if 0.70 <= ratio <= 0.80:
            notes.append(f"✅ 封面 {w}×{h}（{ratio:.2f}），3:4 竖版，信息流展示面积最大")
        elif 0.95 <= ratio <= 1.05:
            notes.append(f"ℹ️ 封面 {w}×{h}（{ratio:.2f}），1:1 方形；重要笔记建议改 3:4 竖版")
        else:
            notes.append(f"⚠️ 封面 {w}×{h}（{ratio:.2f}），非主流比例，信息流中可能被裁剪，建议 3:4")
        if size_kb > 5120:
            notes.append(f"⚠️ 文件 {size_kb:.0f}KB 偏大，压到 5MB 内上传更快")
        else:
            notes.append(f"✅ 文件 {size_kb:.0f}KB，大小合适")
        notes.append("ℹ️ 文字占比/配色情绪需人工或多模态大模型复核（--llm 预留）")
    except ImportError:
        notes.append("⚠️ 未装 Pillow，跳过封面检查（pip install pillow）")
    except Exception as e:
        notes.append(f"⚠️ 封面读取失败：{e}")
    return notes


def render_html_card(title, total, dims, top_rewrites, out_path):
    """生成可晒的诊断卡片 HTML（小红书风格，截图即发）"""
    bars = "".join(
        f"<div class='row'><span>{k}</span><div class='bar'><i style='width:{v}%'></i></div><b>{v}</b></div>"
        for k, v in dims)
    rewrites = "".join(f"<li><b>{n}</b>：{t}</li>" for n, t, _, _, _ in top_rewrites)
    color = "#16a34a" if total >= 80 else "#d97706" if total >= 60 else "#dc2626"
    html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<style>body{{font-family:sans-serif;background:#fff;margin:0;padding:24px;max-width:480px}}
.card{{border:2px solid #ff2442;border-radius:16px;padding:20px}}
h2{{color:#ff2442;margin:0 0 4px}}.score{{font-size:56px;color:{color};font-weight:800}}
.row{{display:flex;align-items:center;gap:8px;margin:6px 0;font-size:14px}}
.row span{{width:90px}}.bar{{flex:1;background:#f1f1f1;border-radius:6px;height:10px}}
.bar i{{display:block;background:#ff2442;height:10px;border-radius:6px}}
li{{font-size:14px;margin:6px 0}}.foot{{font-size:12px;color:#999;margin-top:12px}}</style></head>
<body><div class="card"><h2>📕 笔记诊断卡</h2><div style="font-size:14px;color:#555">{title}</div>
<div class="score">{total}<span style="font-size:20px">/100</span></div>{bars}
<h3>✍️ 标题改写</h3><ul>{rewrites}</ul>
<div class="foot">由 xhs-optimizer 生成 · 参赛作品</div></div></body></html>"""
    Path(out_path).write_text(html, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser(description="小红书笔记诊断优化")
    ap.add_argument("--note", required=True, help="笔记文件（第一行=标题）")
    ap.add_argument("--niche", default="美食", help="垂类（见 data/tags.yaml）")
    ap.add_argument("--keywords", default="", help="核心关键词，逗号分隔，用于标题改写")
    ap.add_argument("--cover", default="", help="封面图路径（可选，PIL 初检尺寸比例）")
    ap.add_argument("--card", default="", help="同时生成可晒的 HTML 诊断卡片路径（可选）")
    ap.add_argument("--style", default="", help="对标爆款笔记文件（可选，第一行=标题）：单篇吃透，学它的钩子结构")
    ap.add_argument("--output", required=True, help="诊断报告输出路径")
    a = ap.parse_args()

    patterns, risks, tags_db, times = load_data()
    raw = Path(a.note).read_text(encoding="utf-8").strip().split("\n")
    title = raw[0].strip()
    body = "\n".join(raw[1:]).strip()
    keywords = [k.strip() for k in a.keywords.split(",") if k.strip()]

    s1, n1 = diagnose_title(title, patterns)
    s2, n2 = diagnose_body(body)
    s3, n3, found_tags = diagnose_tags(body, a.niche, tags_db)
    s4, n4 = diagnose_risk(title + "\n" + body, risks)
    total = s1 + s2 + s3 + s4

    L = [f"# 小红书笔记诊断报告", "", f"**综合评分：{total} / 100**",
         ("🟢 优秀，直接发" if total >= 80 else "🟡 可发，建议按下面优化" if total >= 60 else "🔴 先改再发"),
         "", f"原标题：{title}", f"垂类：{a.niche}", "",
         "## 四维雷达", "",
         f"- 标题吸引力：{s1}/30", f"- 正文质量：{s2}/25",
         f"- 标签曝光：{s3}/15", f"- 合规安全：{s4}/20", "",
         "## 标题诊断"]
    L += [f"- {x}" for x in n1] + ["", "## 正文诊断"] + [f"- {x}" for x in n2]
    L += ["", "## 标签诊断"] + [f"- {x}" for x in n3]
    L += ["", "## 合规检查"] + [f"- {x}" for x in n4]
    L += ["", "## ✍️ 标题改写建议（套用高点击句式）", ""]
    rewrites = rewrite_titles(keywords, patterns)
    for name, t, missing, tip, ex in rewrites:
        L += [f"**{name}**：{t}"]
        if missing:
            L += [f"  - 待填：{'、'.join(missing)}（越具体越好）"]
        L += [f"  - 要点：{tip}", f"  - 示例：{ex}", ""]
    L += ["（以上为句式模板改写，给出优化方向；深度语义改写可接盘古大模型 --llm，见 SKILL.md）",
          ""]

    # ---- 对标改写：单篇吃透 ----
    style_rewrites, style_note = [], None
    if a.style:
        try:
            ref_raw = Path(a.style).read_text(encoding="utf-8").strip().split("\n")
            ref_title = ref_raw[0].strip()
            style_hits, seg_n = analyze_style(ref_title)
            L += ["## 🎯 对标改写（单篇吃透，不取平均）", "",
                  f"对标爆款标题：{ref_title}",
                  f"拆解：{seg_n} 个分句" + (f"，命中钩子：{'、'.join(h['name'] for h in style_hits)}" if style_hits else "，未识别出明显钩子")]
            if CLICKBAIT_OVER.search(ref_title):
                L += ["⚠️ 对标标题含标题党词汇（限流风险）：学它的结构，不学它的用词"]
            L += [""]
            if style_hits:
                style_rewrites = rewrite_with_style(keywords, style_hits)
                for name, t, missing, tip in style_rewrites:
                    L += [f"**学了「{name}」**：{t}"]
                    if missing:
                        L += [f"  - 待填：{'、'.join(missing)}（越具体越好）"]
                    L += [f"  - 要点：{tip}", ""]
                style_note = f"（改写学自对标爆款的钩子结构，非模板套用）"
            else:
                L += ["ℹ️ 这篇对标没拆出可用钩子，建议换一篇数据更好的爆款（点赞/收藏更高的）再试。", ""]
        except Exception as e:
            L += ["## 🎯 对标改写", "", f"⚠️ 对标文件读取失败（{e}），已跳过对标改写。", ""]
    L += ["## 🖼️ 封面初检（附加项，不计入总分）", ""]
    L += [f"- {x}" for x in diagnose_cover(a.cover)]
    L += ["", "## 🏷️ 标签推荐"]
    if a.niche in tags_db:
        L += [" ".join("#" + t for t in tags_db[a.niche][:8])]
    L += ["", "## 🕐 发布时间建议", ""]
    for g in times["general"]: L.append(f"- {g['time']}：{g['note']}")
    for g in times["weekend"]: L.append(f"- {g['time']}：{g['note']}")
    L += [f"- {times['tip']}", "", "---",
          "本报告由 xhs-optimizer 生成（规则库版本见 data/，可扩展）；风险词库为示例版，命中请人工复核。"]
    Path(a.output).write_text("\n".join(L), encoding="utf-8")
    print(f"诊断完成：{total}/100，报告已输出至 {a.output}")
    if a.card:
        dims = [("标题吸引力", s1), ("正文质量", s2), ("标签曝光", s3), ("合规安全", s4)]
        card_rewrites = [(n, t, m, tip, "") for (n, t, m, tip) in style_rewrites] if style_rewrites else rewrites
        render_html_card(title, total, dims, card_rewrites, a.card)
        print(f"诊断卡片已生成：{a.card}（浏览器打开截图即发小红书）")

if __name__ == "__main__":
    main()
