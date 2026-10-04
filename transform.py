#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
果园日常.html  Emoji -> PNG 素材 批量替换工具
- 语义映射表 MAP：Emoji -> ./assets/ui/<name>.png
- 生成 <img class=ui-icon ... onerror=...>，加载失败自动还原为 Emoji
- 注入统一 .ui-icon CSS
- 修正 textContent 槽位为 innerHTML（保证图标在 toast / 对话 / 加载遮罩里也能渲染）
"""
import re, os

SRC       = '/mnt/work/source.html'
CSS_FILE  = '/mnt/work/build/ui-icon.css'
ICON_DIR  = './assets/ui/'      # 若图片与 html 同目录，改成 './'

# ------------------ 1. 语义映射表 ------------------
MAP = {
    # —— 水果 ——
    '🍊':'orange',            '🍉':'watermelon_slice', '🍓':'strawberry',
    '🫐':'blueberries',       '🍋':'lemon',            '🍎':'apple_red',
    '🍏':'apple_green',       '🍇':'grapes_purple',    '🍈':'cantaloupe_whole',
    '🍌':'banana',            '🍐':'pear',             '🍑':'peach',
    '🍍':'pineapple',         '🥭':'mango',            '🥑':'avocado_half',
    # —— 甜点 / 饮品 ——
    '🧃':'juice',             '🍫':'chocolate',        '🍪':'cookie',
    '🍰':'cake_slice_chocolate','🥧':'pie_cherry_slice','🍯':'canned_food_4',
    '🥤':'cup',               '🥂':'cup',              '🍮':'cake_slice_chocolate',
    # —— 烘焙材料 ——
    '🧈':'butter',            '🍬':'candy_cane',       '🌾':'mian',  '🧪':'medical',
    # —— 货币 / 品质 / 时间 / 场景 ——
    '💰':'money',             '🌟':'star',             '⭐':'star',  '💎':'star',
    '📅':'day',               '🌳':'tree',             '💧':'water',
    '🌤️':'weater',            '☀️':'weater',
    # —— 书本 / 书信 / 对话 / 地图 / 清单 / 蜜蜂 ——
    '📖':'book',              '📜':'letter',           '💬':'talk',
    '📝':'todolist',          '📋':'todolist',         '🐝':'bee',
}

def make_img(emoji):
    name = MAP[emoji]
    # 无引号片段：不含空格 / 双引号 / > / =，可安全嵌进 innerHTML、onclick、单引号字符串
    return ('<img class=ui-icon src=%s%s.png alt=%s '
            'onerror=this.replaceWith(document.createTextNode(this.alt))>'
            % (ICON_DIR, name, emoji))

# ------------------ 2. 读取源文件 + 注入 CSS ------------------
src = open(SRC, encoding='utf-8').read()
css = open(CSS_FILE, encoding='utf-8').read().strip()
assert '</style>' in src, 'no </style> found'
src = src.replace('</style>', css + '\n</style>', 1)

# ------------------ 3. textContent -> innerHTML（图标渲染槽位） ------------------
patches = [
    ('t.textContent = msg;',            't.innerHTML = msg;'),
    ('if(text) txt.textContent = text;','if(text) txt.innerHTML = text;'),
    ('if(icon) ic.textContent = icon;', 'if(icon) ic.innerHTML = icon;'),
    ('el.textContent = txt;',           'el.innerHTML = txt;'),
]
for a, b in patches:
    n = src.count(a)
    src = src.replace(a, b)
    print('patch %-34r x%d' % (a, n))

# ------------------ 4. 执行替换（逐行，跳过 console.log） ------------------
keys = sorted(MAP, key=len, reverse=True)
rx = re.compile('|'.join(re.escape(k) for k in keys))
counts = {}
def repl(m):
    e = m.group(0)
    counts[e] = counts.get(e, 0) + 1
    return make_img(e)

out = []
for line in src.split('\n'):
    if 'console.log(' in line:
        out.append(line)
    else:
        out.append(rx.sub(repl, line))
src = '\n'.join(out)

# ------------------ 4b. 含 <img> 的 textContent 赋值改为 innerHTML ------------------
_lines = src.split('\n')
_fixed = 0
for _i, _l in enumerate(_lines):
    if '.textContent' in _l and 'ui-icon' in _l:
        _lines[_i] = _l.replace('.textContent', '.innerHTML')
        _fixed += 1
src = '\n'.join(_lines)
print('textContent->innerHTML fixed lines:', _fixed)

# ------------------ 5. 输出 + 报告 ------------------
print('\n替换总数:', sum(counts.values()), ' 覆盖种类:', len(counts))
for e, n in sorted(counts.items(), key=lambda x: -x[1]):
    print('  %s -> %-16s x%d' % (e, MAP[e], n))

# 未匹配到的 emoji（保留原样，作为兜底）
emoji_rx = re.compile('[\U0001F300-\U0001FAFF\U00002600-\U000027BF\u2B00-\u2BFF\u2190-\u21FF\u2700-\u27BF]'
                      '\uFE0F?')
left = {}
for m in emoji_rx.finditer(src):
    t = m.group(0)
    left[t] = left.get(t, 0) + 1
print('\n未替换(无对应素材/UI图标) 共 %d 种:' % len(left))
print('  ' + ' '.join('%s×%d' % (k, v) for k, v in sorted(left.items(), key=lambda x: -x[1])))

for p in ['/mnt/work/果园日常.html', '/mnt/cos/artifacts/果园日常.html',
          '/mnt/local/assert/果园日常.html']:
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write(src)
        print('wrote', p, len(src), 'bytes')
    except Exception as ex:
        print('FAIL', p, ex)

# 抽出 JS 供语法检查
m = re.search(r'<script>(.*)</script>', src, re.S)
if m:
    open('/mnt/work/build/app.js', 'w', encoding='utf-8').write(m.group(1))
    print('app.js written:', len(m.group(1)), 'bytes')
