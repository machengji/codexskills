# 可复用脚本模板

从水利案（2026-09-11）固化的实测脚本。**复制到本案工作目录后，先把 `{{占位符}}` 替换成本案实际值再用。**

占位符对照：

| 占位符 | 含义 | 示例 |
|---|---|---|
| `{{WORKDIR}}` | 工作区根（存临时文件） | `E:\已完成的案例-可做参考\_soft_work` |
| `{{PROJECT}}` | 本案项目根 | `E:\已完成的案例-可做参考\某软件` |
| `{{NAME}}` | 软件全称（逐字） | `某软件` |
| `{{SHOTS_DIR}}` | 本案截图输出目录 | `...\_soft_shots\某软件短名` |
| `{{PKG}}` | 后端包名 | `damctrl` / `sigtrace` / `voceng` |
| `{{APP}}` | 后端应用入口 | `damctrl.app:app` |
| `{{DB}}` | SQLite 库文件名 | `damctrl.sqlite3` |

## 脚本清单

| 文件 | 用途 | 运行方式 |
|---|---|---|
| `measure_pages.ps1` | **Word/WPS COM 实测页数** | `pwsh -NoProfile -File measure_pages.ps1 -DocxPath <docx>` |
| `export_pdf_for_review.ps1` | 导 PDF 供逐页渲染检查（交付目录不留 PDF） | `pwsh -NoProfile -File export_pdf_for_review.ps1 -DocxPath <docx> -PdfPath <pdf>` |
| `check_manual_blank.py` | 手册逐页尾部空白量化（>45% 需返工） | `& $env:MIMO_PYTHON check_manual_blank.py` |
| `check_page_blank.py` | 页面截图空白块量化 | `& $env:MIMO_PYTHON check_page_blank.py` |
| `check_shot_diff.py` | 相邻截图差异度（筛 <1.2% 的组再肉眼核对） | `& $env:MIMO_PYTHON check_shot_diff.py` |
| `rebuild_shot_manifest.py` | 从采集脚本正则重建 manifest（脚本崩溃后修复） | `& $env:MIMO_PYTHON rebuild_shot_manifest.py` |
| `reset_db_template.py` | 重置数据库到初始态（**截图前必跑**） | `& $env:MIMO_PYTHON reset_db_template.py` |
| `capture-statechain-template.mjs` | **截图采集模板**（状态链编排 + 元数据登记） | 在 `shotkit` 目录下 `node capture-statechain-template.mjs` |
| `build_code_docx.py` | 代码文档生成（零注释、只收后端、字号可调） | `& $env:MIMO_PYTHON build_code_docx.py` |
| `build_manual_docx.py` | 操作手册生成（图文交错、首页纯文字、表格字典） | `& $env:MIMO_PYTHON build_manual_docx.py` |

## 使用顺序

```
1. reset_db_template.py          # 截图前重置库
2. capture-statechain-template.mjs  # 采集状态链截图
3. rebuild_shot_manifest.py      # 校验图与元数据对齐
4. check_shot_diff.py            # 筛出差异过小的组，逐张肉眼核对
5. build_code_docx.py            # 生成代码文档
6. measure_pages.ps1             # 实测页数，不达标调字号重跑第 5 步
7. build_manual_docx.py          # 生成操作手册
8. measure_pages.ps1             # 实测页数
9. export_pdf_for_review.ps1     # 导 PDF
10. check_manual_blank.py        # 逐页空白检查，>45% 返工
```

## 关键参数（水利案实测值，可作起点）

- 代码文档：Consolas **12.5pt**、行距 250、边距 18–19mm → 2718 行源码 73 页
- 操作手册：正文 **13pt**、行距 2.0、图片宽 **6.1 英寸**、边距 20mm → 48 图 44 页、16.94MB
- 截图：viewport `1920×1080`、`deviceScaleFactor: 1.5` → 2880×1620
