# -*- coding: utf-8 -*-
import io

def patch(path, anchor, insert, before=True, count=1):
    with io.open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    assert text.count(anchor) >= count, (path, anchor, text.count(anchor))
    if before:
        text = text.replace(anchor, insert + anchor, count)
    else:
        text = text.replace(anchor, anchor + insert, count)
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print('patched', path)

# 1) humanizer (English) — add Chinese operation manual mode before output section
humanizer_insert = '''## Chinese operation manual mode (软著操作手册)

When the input is a Simplified Chinese software operation manual (软著申报/项目交付操作手册), apply the patterns above plus the Chinese manual rules in [references/操作手册去AI味增强规则.md](references/操作手册去AI味增强规则.md). The manual rules add:

- **Chinese manual tells to remove:** 总结腔 (综上所述/由此可见), 元叙述 (本章将详细介绍/如下所示), 万能宣传 (一站式/赋能/闭环), 空壳句 (进入相应模块/保存即可), 提醒腔 (值得注意的是/不难发现).
- **Anchor every step to a real control:** menu, button, field, status word, or error message. "进入相应模块进行操作" is a template sentence; rewrite it as "打开左侧菜单「系统管理」，点击「用户管理」，页面显示用户列表".
- **Freeze facts:** version numbers, PR numbers, dates, module names, button labels, field names, status words, error text, and data scopes must not change. Do not invent missing details.
- **Vary rhythm:** alternate short commands with longer exception notes; do not cast every step in the same 40–70 character mold.
- **No fake humanity:** do not add typos, emoji, slang, or invented first-person experience to sound human.

'''
patch(r'C:\Users\Administrator\.codex\skills\humanizer\SKILL.md', '## How to return the result', humanizer_insert)

# 2) qu-ai-wei — add operation manual scenario before output contract
qu_insert = '''## 操作手册场景（软著申报）

目标文本是软件操作手册（软著申报、项目交付）时，在通用规则之上追加 [`references/操作手册去AI味增强规则.md`](references/操作手册去AI味增强规则.md)：

- 手册站位是「研发组写给现场操作员/复核员」，不是对话答复或产品宣传；每段必须能对上真实页面。
- 追加禁用词：总结腔、元叙述、万能宣传、空壳句、提醒腔（增强规则第二节）；慎用词每本手册合计 ≤3 次且必须绑定具体对象。
- 每步写「定位控件 → 动作 → 可见反馈/状态字」；异常写真实提示文案与处置。
- 冻结事实：软件全称、版本号、菜单、按钮、字段、状态、接口、错误提示、日期、PR/提交号、数据口径；缺证据保留缺口。
- 写入 Word 前执行增强规则第六节检查清单：换行业测试、同级案例换词、公开通用句、禁用词扫描、界面锚点、事实冻结、节奏检查。
- 不得为了「人味」添加错别字、emoji、网语、虚构第一人称经历。

'''
patch(r'C:\Users\Administrator\.codex\skills\qu-ai-wei\SKILL.md', '## 输出契约', qu_insert)

# 3) humanizer-zh-academic — add manual mode before content patterns
acad_insert = '''## 操作手册/软著场景（非学术）

本技能默认面向学术文本；当目标文本是软件操作手册（软著申报、项目交付）时，切换到操作手册模式：

- 学术硬约束表（模式10词表、段末总结套句等）不直接套用，改按 [`references/操作手册去AI味增强规则.md`](references/操作手册去AI味增强规则.md) 执行。
- 手册站位是「研发组写给现场操作员/复核员」；每步写「定位控件 → 动作 → 可见反馈/状态字」。
- 追加禁用词：总结腔、元叙述、万能宣传、空壳句（增强规则第二节）。
- 冻结事实：软件全称、版本号、菜单、按钮、字段、状态、错误提示、日期、PR/提交号。
- 写入 Word 前执行增强规则第六节检查清单。

'''
patch(r'C:\Users\Administrator\.codex\skills\humanizer-zh-academic\SKILL.md', '## 内容层面的AI模式', acad_insert)

# 4) humanizer-zh-next — add matrix row + manual scenario section
row = '| **版本说明 / 迁移指南 / 引用材料** | 保留变更关系和结构，让读者能追踪版本差异 | 不得新增版本、日期、变更原因、兼容性结论或引文内容 | 版本号、改动关系、迁移步骤、原始引文和上下文 |'
new_row = row + '\n| **操作手册 / 软著申报** | 研发组写给现场操作员，中性直接，优先可操作性；每步锚定真实控件与状态 | 不得新增功能、参数、性能数据、兼容性、日期、版本或实现细节 | 菜单、按钮、字段、状态词、错误提示、版本号、PR/提交号、数据口径 |'
patch(r'C:\Users\Administrator\.codex\skills\humanizer-zh-next\SKILL.md', row, new_row, before=False)

next_insert = '''### 操作手册场景（软著申报）

目标文本是软件操作手册时，在通用规则之上追加 [`references/操作手册去AI味增强规则.md`](references/操作手册去AI味增强规则.md)：

- 追加禁用词：总结腔、元叙述、万能宣传、空壳句、提醒腔（增强规则第二节）。
- 每步写「定位控件 → 动作 → 可见反馈/状态字」；异常写真实提示文案。
- 冻结事实：软件全称、版本号、菜单、按钮、字段、状态、接口、错误提示、日期、PR/提交号、数据口径。
- 写入 Word 前执行增强规则第六节检查清单（换行业测试、同级案例换词、公开通用句、禁用词扫描、界面锚点、事实冻结、节奏检查）。

'''
patch(r'C:\Users\Administrator\.codex\skills\humanizer-zh-next\SKILL.md', '### 事实与新增细节', next_insert)

# 5) unslop — add Chinese manual mode before output format
unslop_insert = '''## Chinese operation manual mode (软著操作手册)

When the input is a Simplified Chinese software operation manual (软著申报/项目交付), read [references/操作手册去AI味增强规则.md](references/操作手册去AI味增强规则.md) and apply it on top of the core contract:

- Chinese manual tells: 总结腔 (综上所述/由此可见), 元叙述 (本章将详细介绍/如下所示), 万能宣传 (一站式/赋能/闭环), 空壳句 (进入相应模块/保存即可), 提醒腔 (值得注意的是/不难发现).
- Anchor every step to a real control (menu, button, field, status word, error message); "进入相应模块进行操作" is a template sentence and must be rewritten with the actual control path.
- Freeze facts: version numbers, PR numbers, dates, module names, button labels, field names, status words, error text, data scopes.
- Run the manual checklist in section 6 of the enhancement rules before delivery (industry-swap test, sibling-case word-swap test, public boilerplate scan, banned-word scan, control-anchor check, fact freeze, rhythm check).
- No fake humanity: no typos, emoji, slang, or invented first-person experience.

'''
patch(r'C:\Users\Administrator\.codex\skills\unslop\SKILL.md', '## Output Format', unslop_insert)