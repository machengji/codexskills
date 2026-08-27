# -*- coding: utf-8 -*-
import io
path = r'C:\Users\Administrator\.codex\skills\software-copyright-deliverables\references\去AI味自然写作编译规范.md'
with io.open(path, 'r', encoding='utf-8') as f:
    text = f.read()
section = '''

## 七、与已安装去AI味技能的衔接

本机已安装以下去 AI 味技能，手册撰稿与复核时按需调用；规则冲突时以本规范与 R23 为准：

| 技能 | 用途 | 调用时机 |
|------|------|----------|
| `qu-ai-wei` | 简体中文通用去 AI 味，带 17KB 模式目录 | 手册段落/长文重写、结构重建 |
| `humanizer` | 英文通用去 AI 味（Wikipedia Signs of AI writing） | 手册中英文界面文案、代码注释、README 类文本 |
| `humanizer-zh-academic` | 中文学术去 AI 味 | 不用于手册正文；手册含算法说明/技术论证段落时可参考其「现象先行、结论后置」写法 |
| `humanizer-zh-next` | 中文通用去 AI 味（blader/humanizer 中文适配） | 手册初稿改写、逐段自检 |
| `unslop` | 通用 de-AI（audit/rewrite 双流程） | 手册终稿审计、AI 痕迹扫描 |

五个技能均带 `references/操作手册去AI味增强规则.md`（软著场景专用增强规则），手册撰稿时优先按该文件执行禁用词、人味写法与检查清单；与本规范冲突时，以本规范（R23）为准。
'''
text = text.rstrip() + '\n' + section
with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)
print('patched', path)