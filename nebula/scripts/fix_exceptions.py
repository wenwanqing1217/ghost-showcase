import re
import os

base = r'D:\mindflow-workspace\AID\projects\src'
for path in ['entrypoints/daemon.py', 'fairy_agent.py']:
    full = os.path.join(base, path)
    with open(full, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    replaced = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped == 'except Exception:' and i + 1 < len(lines) and lines[i + 1].strip() == 'pass':
            indent = len(line) - len(line.lstrip())
            new_lines.append(line)
            new_lines.append(' ' * (indent + 4) + 'logger.exception("Unhandled exception")')
            replaced += 1
            i += 2
        else:
            new_lines.append(line)
            i += 1
    
    with open(full, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print(f'Fixed {path}: {replaced} replacements')
