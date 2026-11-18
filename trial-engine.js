// xhs-optimizer 诊断引擎（JS 版）
// 与 scripts/optimize.py 同一套评分规则逐项对照移植，
// 唯一差别：不含 --cover 封面初检与 --style 对标改写（在线试用不需要）。
// 字符数按 code point 计（Array.from），与 Python len() 一致。
(function (root) {
  'use strict';

  var DIGITS = /\d+/;
  var EMOJI = /[\u{1F300}-\u{1FAFF}\u2600-\u27BF\u2B00-\u2BFF]/gu;
  var INTERACT = /(你们|姐妹们|评论区|留言|投票|你怎么看|试过吗|有用吗)/;
  var CLICKBAIT_OVER = /(震惊|竟然|天啊|救命|离谱|吓死)/;
  var HOOK_KEYS = ['怎么', '为什么', '避雷', '秘密', '天', '块'];
  var TIME_UNITS = ['天', '周', '月', '年', '小时', '分钟'];

  function charLen(s) { return Array.from(s.replace(/\s+/g, '')).length; }

  function diagnoseTitle(title, patterns) {
    var score = 30, notes = [];
    var n = Array.from(title).length;
    if (n <= 20) notes.push('✅ 标题 ' + n + ' 字，长度合适（小红书标题建议≤20字）');
    else { score -= 8; notes.push('⚠️ 标题 ' + n + ' 字偏长，信息流中会被折叠，建议压缩到20字内'); }
    if (DIGITS.test(title)) notes.push('✅ 含数字，具体感强');
    else { score -= 4; notes.push('⚠️ 标题无数字，加上具体数字点击率更高'); }
    if (title.indexOf('?') !== -1 || title.indexOf('？') !== -1 || title.indexOf('!') !== -1 || title.indexOf('！') !== -1)
      notes.push('✅ 有疑问/感叹语气，情绪钩子到位');
    else { score -= 3; notes.push('⚠️ 缺情绪钩子，试试反问或感叹句式'); }
    if (CLICKBAIT_OVER.test(title)) { score -= 5; notes.push('⚠️ 标题党词汇过重，易被限流且伤信任'); }
    var hit = patterns.filter(function (p) {
      return HOOK_KEYS.some(function (k) { return title.indexOf(k) !== -1; });
    });
    notes.push(hit.length ? '✅ 命中高点击句式特征' : 'ℹ️ 未明显命中高点击句式，见下方改写建议');
    return { score: Math.max(score, 0), notes: notes };
  }

  function diagnoseBody(body) {
    var score = 25, notes = [];
    var n = charLen(body);
    if (n >= 300 && n <= 800) notes.push('✅ 正文 ' + n + ' 字，信息量适中');
    else if (n < 300) { score -= 6; notes.push('⚠️ 正文仅 ' + n + ' 字，偏单薄，加细节/过程/感受'); }
    else { score -= 4; notes.push('⚠️ 正文 ' + n + ' 字偏长，注意分段，重点前置'); }
    var paras = body.split('\n').filter(function (p) { return p.trim(); });
    if (paras.length >= 3) notes.push('✅ 分 ' + paras.length + ' 段，阅读节奏好');
    else { score -= 4; notes.push('⚠️ 几乎没分段，手机端阅读压力大，回车分段'); }
    var em = (body.match(EMOJI) || []).length;
    if (em >= 3) notes.push('✅ emoji ' + em + ' 个，氛围感够');
    else if (em > 0) notes.push('ℹ️ emoji ' + em + ' 个，可再加2-3个作段落分隔');
    else { score -= 3; notes.push('⚠️ 零 emoji，小红书体感偏"严肃"，适当加'); }
    if (INTERACT.test(body)) notes.push('✅ 有互动引导（提问/喊话），利评论区');
    else { score -= 4; notes.push('⚠️ 无互动引导，结尾加一句提问（如\'你们试过吗\'）'); }
    return { score: Math.max(score, 0), notes: notes };
  }

  function diagnoseTags(body, niche, tagsDb) {
    var score = 15, notes = [], rec = [];
    var found = (body.match(/#(\S+)/g) || []).map(function (t) { return t.slice(1); });
    if (found.length >= 3 && found.length <= 8) notes.push('✅ 标签 ' + found.length + ' 个，数量合适');
    else if (found.length < 3) { score -= 6; notes.push('⚠️ 只有 ' + found.length + ' 个标签，曝光入口太少'); }
    else { score -= 3; notes.push('⚠️ ' + found.length + ' 个标签偏多，堆砌会被降权'); }
    if (tagsDb[niche]) {
      rec = tagsDb[niche].filter(function (t) { return found.indexOf(t) === -1; }).slice(0, 8 - found.length);
      if (rec.length) notes.push('💡 推荐补标签：' + rec.map(function (t) { return '#' + t; }).join(' '));
    }
    return { score: Math.max(score, 0), notes: notes, found: found, rec: rec };
  }

  function diagnoseRisk(text, risks) {
    var score = 20, notes = [];
    var hit = risks.filter(function (w) { return text.indexOf(w) !== -1; });
    if (!hit.length) notes.push('✅ 未命中风险词库');
    else {
      score -= Math.min(5 * hit.length, 18);
      notes.push('🚨 命中风险词 ' + hit.length + ' 个：' + hit.join('、'));
      notes.push("   → 站外引流词（微信/私聊）易限流，改'主页简介有方式'；极限词改温和表达");
    }
    return { score: Math.max(score, 0), notes: notes };
  }

  function pickNumbers(keywords) {
    var joined = keywords.join('');
    var nums = joined.match(/\d+/g) || [];
    for (var i = 0; i < nums.length; i++) {
      var n = nums[i];
      var bad = TIME_UNITS.some(function (u) { return joined.indexOf(n + u) !== -1; });
      if (!bad) return n;
    }
    return nums.length ? nums[0] : '3';
  }

  function pickTimes(keywords) {
    for (var i = 0; i < keywords.length; i++) {
      var k = keywords[i];
      if (TIME_UNITS.some(function (u) { return k.indexOf(u) !== -1; })) return k;
    }
    return '30天';
  }

  function rewriteTitles(keywords, patterns) {
    var kw = keywords[0] || '关键词';
    var fill = { '{kw}': kw, '{n}': pickNumbers(keywords), '{时间}': pickTimes(keywords) };
    return patterns.slice(0, 3).map(function (p) {
      var t = p.template, missing = [];
      (t.match(/\{[^}]+\}/g) || []).forEach(function (slot) {
        if (fill[slot] !== undefined) t = t.split(slot).join(fill[slot]);
        else { missing.push(slot.replace(/[{}]/g, '')); t = t.split(slot).join('…'); }
      });
      return { name: p.name, title: t, missing: missing, tip: p.tip, example: p.example };
    });
  }

  function diagnose(title, body, niche, keywords, DATA) {
    var s1 = diagnoseTitle(title, DATA.patterns);
    var s2 = diagnoseBody(body);
    var s3 = diagnoseTags(body, niche, DATA.niches);
    var s4 = diagnoseRisk(title + '\n' + body, DATA.risks);
    var total = s1.score + s2.score + s3.score + s4.score;
    var verdict = total >= 80 ? '优秀，直接发' : total >= 60 ? '可发，建议按下面优化' : '先改再发';
    return {
      total: total, verdict: verdict,
      dims: { title: s1.score, body: s2.score, tags: s3.score, risk: s4.score },
      notes: { title: s1.notes, body: s2.notes, tags: s3.notes, risk: s4.notes },
      rewrites: rewriteTitles(keywords, DATA.patterns),
      tagPool: (DATA.niches[niche] || []).slice(0, 8),
      times: DATA.times
    };
  }

  var api = { diagnose: diagnose };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.XhsSkill = api;
})(typeof window !== 'undefined' ? window : globalThis);
