#!/usr/bin/env python3
"""Build trial.html: single self-contained page, engine + data inlined."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
engine = (BASE / "trial-engine.js").read_text()
data = json.loads(Path("/tmp/skill-data.json").read_text())

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>xhs-zhenduan 在线试用：发笔记前，先诊断一下</title>
<style>
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;max-width:720px;margin:0 auto;padding:20px 16px;color:#222}
h1{font-size:20px} h2{font-size:16px;margin:18px 0 6px}
input,textarea,select{width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;font-size:15px;box-sizing:border-box}
textarea{min-height:180px}
button{background:#ff2442;color:#fff;border:0;border-radius:8px;padding:12px 28px;font-size:16px;cursor:pointer}
.score{font-size:40px;font-weight:700}.ok{color:#1a9e4b}.mid{color:#d48806}.bad{color:#d4380d}
ul{padding-left:20px;line-height:1.7}.dim{font-weight:700}
.note{color:#666;font-size:13px;line-height:1.6}
</style></head><body>
<h1>发笔记前，先诊断一下</h1>
<p class="note">xhs-zhenduan 在线试用：和本地版同一套评分规则（标题 30 / 正文 25 / 标签 15 / 合规 20），浏览器里直接跑，不上传、不收费。80 分以上再发，60 分以下先改。</p>
<h2>标题</h2><input id="title" placeholder="例如：简历上这3个错误，HR一眼就筛掉你">
<h2>正文（标签直接写正文里，如 #求职）</h2>
<textarea id="body" placeholder="第一行之后写正文，分段、加 emoji、结尾加一句提问，分数会更高"></textarea>
<h2>垂类</h2><select id="niche"></select>
<h2>核心关键词（逗号分隔）</h2><input id="keywords" placeholder="例如：简历,HR,面试">
<p><button onclick="run()">开始诊断</button></p>
<div id="out"></div>
<script>
var DATA = __DATA__;
__ENGINE__
var sel = document.getElementById('niche');
Object.keys(DATA.niches).forEach(function (k) {
  var o = document.createElement('option'); o.text = k; o.value = k; sel.add(o);
});
sel.value = '职场';
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function run(){
  var title = document.getElementById('title').value.trim();
  var body = document.getElementById('body').value.trim();
  var niche = sel.value;
  var kw = document.getElementById('keywords').value.split(/[,，、\s]+/).filter(Boolean);
  if(!title || !body){ alert('标题和正文都填一下再诊断'); return; }
  var r = XhsSkill.diagnose(title, body, niche, kw, DATA);
  var cls = r.total >= 80 ? 'ok' : r.total >= 60 ? 'mid' : 'bad';
  var h = '<h2>综合评分：<span class="score ' + cls + '">' + r.total + ' / 100</span> ' + esc(r.verdict) + '</h2>';
  h += '<ul><li><span class="dim">标题吸引力：' + r.dims.title + '/30</span><ul>' + r.notes.title.map(function (n){return '<li>'+esc(n)+'</li>';}).join('') + '</ul></li>';
  h += '<li><span class="dim">正文质量：' + r.dims.body + '/25</span><ul>' + r.notes.body.map(function (n){return '<li>'+esc(n)+'</li>';}).join('') + '</ul></li>';
  h += '<li><span class="dim">标签曝光：' + r.dims.tags + '/15</span><ul>' + r.notes.tags.map(function (n){return '<li>'+esc(n)+'</li>';}).join('') + '</ul></li>';
  h += '<li><span class="dim">合规安全：' + r.dims.risk + '/20</span><ul>' + r.notes.risk.map(function (n){return '<li>'+esc(n)+'</li>';}).join('') + '</ul></li></ul>';
  h += '<h2>标题改写建议</h2><ul>' + r.rewrites.map(function (w){
    return '<li><b>' + esc(w.name) + '：</b>' + esc(w.title) + (w.missing.length ? '（缺：' + esc(w.missing.join('、')) + '，补上对应关键词）' : '') + '<br><span class="note">' + esc(w.tip) + ' 例：' + esc(w.example) + '</span></li>';
  }).join('') + '</ul>';
  h += '<h2>发布时间建议</h2><ul>' + r.times.general.map(function (t){return '<li>'+esc(t)+'</li>';}).join('') + '<li>' + esc(r.times.weekend) + '</li><li>' + esc(r.times.tip) + '</li></ul>';
  h += '<p class="note">风险词库是示例版，命中请人工复核。本地版（可改规则、批量跑、生成 HTML 诊断卡片）见 CodeArts 代码仓 xhs-optimizer。</p>';
  document.getElementById('out').innerHTML = h;
}
</script></body></html>
"""

out = HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False)).replace("__ENGINE__", engine)
p = BASE / "trial.html"
p.write_text(out, encoding="utf-8")
print("wrote", p, len(out), "bytes")
