import re
lines = open('D:/MW/GHOST.md', encoding='utf-8').readlines()
content = ''.join(lines)
print('GHOST.md:', len(lines), 'lines\n')
sections = [l.strip() for l in lines if l.strip().startswith('## ')]
for s in sections:
    print(' [OK]', s.replace('## ', ''))
print()
sections_list = re.findall(r'## 第[一二三四五六七八九十]+部分', content)
for i, s in enumerate(sections_list):
    print(f' {i+1}. {s.replace(\"## \", \"\")}')
print()
keywords = {'\u8c46\u5305': 'Input: Doubao', '\u98de\u4e66': 'Input: Feishu', 'Gateway': 'Gateway routes', '\u5ba1\u67e5': 'Review', '\u8d44\u4ea7\u6e05\u518c': 'Inventory', '\u53d1\u5c55\u65b9\u5411': 'Roadmap', '\u51b3\u7b56': 'Decisions'}
for kw, topic in keywords.items():
    if kw in content:
        print(' [OK]', topic)
    else:
        print(' [MISS]', topic)
print()
if len(sections_list) == len(set(sections_list)):
    print('No duplicate sections - OK')
else:
    print('WARNING: duplicate sections found!')
