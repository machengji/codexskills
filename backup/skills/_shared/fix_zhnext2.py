# -*- coding: utf-8 -*-
import io
path = r'C:\Users\Administrator\.codex\skills\humanizer-zh-next\SKILL.md'
with io.open(path, 'r', encoding='utf-8') as f:
    text = f.read()
row = '| **版本说明 / 迁移指南 / 引用材料** | 保留变更关系和结构，让读者能追踪版本差异 | 不得新增版本、日期、变更原因、兼容性结论或引文内容 | 版本号、改动关系、迁移步骤、原始引文和上下文 |'
dup = row + '\n' + row
assert text.count(dup) == 1, text.count(dup)
text = text.replace(dup, row)
with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)
print('deduped')