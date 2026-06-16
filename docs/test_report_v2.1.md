# 市场咨询任务跟踪工具 V2.1 测试报告
## 第一阶段补充开发测试文档

**版本：** V2.1  
**日期：** 2026-06-16  
**测试范围：** Excel导入、OCR识别、映射学习增强模块

---

## 1. 测试概述

### 1.1 测试目标

验证V2.1优化版本的核心功能是否正常运行，包括：
- Excel导入/导出功能
- OCR图片识别功能
- 映射学习增强功能
- 代码优化效果验证

### 1.2 测试环境

| 项目 | 要求 |
|------|------|
| Python版本 | >= 3.8 |
| 操作系统 | Windows/Linux/macOS |
| 依赖包 | pytest, pandas, openpyxl, Pillow, pytesseract |

### 1.3 测试数据准备

#### 单元测试数据（自动生成）

```python
# 测试用Excel文件字段
test_headers = ['姓名', '电话', '邮箱', '公司', '部门', '职位', '备注']

# 测试数据
test_contacts = [
    ['张三', '13800138000', 'zhangsan@example.com', '公司A', '市场部', '经理', 'VIP'],
    ['李四', '13900139000', 'lisi@example.com', '公司B', '销售部', '主管', ''],
    ['王五', '13700137000', 'wangwu@example.com', '公司C', '技术部', '工程师', ''],
]
```

#### OCR测试数据（需手动准备）

| 测试图片 | 内容 | 预期识别结果 |
|---------|------|-------------|
| `test_card_1.jpg` | 中文名片（清晰） | 张三、13800138000、test@example.com |
| `test_card_2.jpg` | 英文名片 | John Doe、+1-234-567-8900 |
| `test_card_3.jpg` | 混合格式 | 公司信息完整 |

---

## 2. 单元测试用例

### 2.1 Excel导入模块测试

| 用例ID | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|---------|---------|---------|---------|--------|
| UT-EXCEL-001 | 标准表头识别 | Excel文件存在 | 调用find_header_mapping | 正确映射到标准字段 | P0 |
| UT-EXCEL-002 | 英文表头识别 | Excel使用英文表头 | 调用find_header_mapping | name→姓名, phone→电话 | P0 |
| UT-EXCEL-003 | 混合表头识别 | 中英文混合 | 调用find_header_mapping | 正确匹配 | P1 |
| UT-EXCEL-004 | 部分表头识别 | 仅姓名和电话 | 调用find_header_mapping | 部分字段有效 | P1 |
| UT-EXCEL-005 | 联系人创建 | 参数完整 | ExcelContact实例化 | 所有字段正确 | P0 |
| UT-EXCEL-006 | 字典转换 | 联系人对象 | 调用to_dict() | 返回正确字典 | P0 |
| UT-EXCEL-007 | 字典反解析 | 字典数据 | 调用from_dict() | 还原联系人对象 | P0 |
| UT-EXCEL-008 | 成功导入 | 3条测试数据 | import_from_file | total=3, added=3 | P0 |
| UT-EXCEL-009 | 重复检测 | 数据库已有相同数据 | import_from_file | duplicate=1 | P0 |
| UT-EXCEL-010 | 保存到数据库 | 已导入数据 | save_to_database | db.add_contact调用3次 | P0 |
| UT-EXCEL-011 | 保存到Excel | 已导入数据 | save_to_excel | 生成xlsx文件 | P0 |
| UT-EXCEL-012 | 不支持格式 | .txt文件 | import_from_file | success=False | P1 |

**执行命令：**
```bash
cd D:\GITwork
python -m pytest src/tests/test_excel_import.py -v --cov=src.content.excel_import
```

**预期输出：**
```
tests/test_excel_import.py::TestExcelHeaderMapper::test_find_header_mapping_standard PASSED
tests/test_excel_import.py::TestExcelHeaderMapper::test_find_header_mapping_english PASSED
tests/test_excel_import.py::TestExcelHeaderMapper::test_find_header_mapping_mixed PASSED
tests/test_excel_import.py::TestExcelHeaderMapper::test_find_header_mapping_partial PASSED
tests/test_excel_import.py::TestExcelHeaderMapper::test_find_header_mapping_empty PASSED
tests/test_excel_import.py::TestExcelContact::test_create_contact PASSED
tests/test_excel_import.py::TestExcelContact::test_to_dict PASSED
tests/test_excel_import.py::TestExcelContact::test_from_dict PASSED
tests/test_excel_import.py::TestExcelImporter::test_import_from_file_success PASSED
tests/test_excel_import.py::TestExcelImporter::test_import_from_file_empty PASSED
tests/test_excel_import.py::TestExcelImporter::test_import_duplicate_detection PASSED
tests/test_excel_import.py::TestExcelImporter::test_save_to_database PASSED
tests/test_excel_import.py::TestExcelImporter::test_save_to_excel PASSED
tests/test_excel_import.py::TestExcelImporter::test_import_unsupported_format PASSED
tests/test_excel_import.py::TestExcelExporter::test_export_all PASSED
tests/test_excel_import.py::TestExcelExporter::test_export_filtered PASSED
tests/test_excel_import.py::TestExcelExporter::test_create_template PASSED

========================== 17 passed ==========================
```

---

### 2.2 OCR处理模块测试

| 用例ID | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|---------|---------|---------|---------|--------|
| UT-OCR-001 | 结果数据创建 | 参数完整 | OCRResult实例化 | 所有字段正确 | P0 |
| UT-OCR-002 | 结果字典转换 | 结果对象 | 调用to_dict() | 返回正确字典 | P0 |
| UT-OCR-003 | 预处理返回图像 | 图片文件 | preprocess()调用 | 返回PIL.Image | P0 |
| UT-OCR-004 | 中文名片解析 | 中文名片文本 | parse()调用 | 正确提取姓名电话 | P0 |
| UT-OCR-005 | 电话号码提取 | 包含多种电话格式 | _extract_phone() | 正确提取 | P0 |
| UT-OCR-006 | 邮箱提取 | 邮箱文本 | _extract_email() | 正确提取 | P0 |
| UT-OCR-007 | 公司名称提取 | 包含公司关键词 | _extract_company() | 正确提取 | P1 |
| UT-OCR-008 | 空文本解析 | 空字符串 | parse()调用 | 返回空值 | P0 |
| UT-OCR-009 | 电话清理 | 带格式的电话 | _clean_phone() | 标准化格式 | P0 |
| UT-OCR-010 | 从邮箱提取姓名 | info@example.com | _extract_name_from_email() | 移除info前缀 | P1 |
| UT-OCR-011 | 默认初始化 | 无参数 | OCRProcessor() | 正常实例化 | P0 |
| UT-OCR-012 | 批量识别空列表 | 空列表 | recognize_batch() | 返回空列表 | P0 |
| UT-OCR-013 | 支持的格式检查 | 图片路径 | is_supported_format() | 正确判断 | P0 |

**执行命令：**
```bash
cd D:\GITwork
python -m pytest src/tests/test_ocr_handler.py -v --cov=src.content.ocr_handler
```

**预期输出：**
```
tests/test_ocr_handler.py::TestOCRResult::test_create_result PASSED
tests/test_ocr_handler.py::TestOCRResult::test_to_dict PASSED
tests/test_ocr_handler.py::TestOCRResult::test_from_dict PASSED
tests/test_ocr_handler.py::TestImagePreprocessor::test_preprocess_returns_image PASSED
tests/test_ocr_handler.py::TestImagePreprocessor::test_get_supported_formats PASSED
tests/test_ocr_handler.py::TestImagePreprocessor::test_is_supported_format PASSED
tests/test_ocr_handler.py::TestBusinessCardParser::test_parse_chinese_card PASSED
tests/test_ocr_handler.py::TestBusinessCardParser::test_parse_phone_patterns PASSED
tests/test_ocr_handler.py::TestBusinessCardParser::test_parse_email PASSED
tests/test_ocr_handler.py::TestBusinessCardParser::test_parse_company PASSED
tests/test_ocr_handler.py::TestBusinessCardParser::test_parse_empty_text PASSED
tests/test_ocr_handler.py::TestBusinessCardParser::test_clean_phone PASSED
tests/test_ocr_handler.py::TestBusinessCardParser::test_extract_name_from_email PASSED
tests/test_ocr_handler.py::TestBusinessCardParser::test_extract_name_with_prefix PASSED
tests/test_ocr_handler.py::TestOCRProcessor::test_init_default PASSED
tests/test_ocr_handler.py::TestOCRProcessor::test_init_custom_tesseract_path PASSED
tests/test_ocr_handler.py::TestOCRProcessor::test_recognize_image_mock PASSED
tests/test_ocr_handler.py::TestOCRProcessor::test_recognize_batch_empty PASSED
tests/test_ocr_handler.py::TestOCRProcessor::test_recognize_batch_multiple PASSED
tests/test_ocr_handler.py::TestOCRIntegration::test_ocr_processor_can_be_instantiated PASSED

========================== 20 passed ==========================
```

---

### 2.3 映射学习模块测试

| 用例ID | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|---------|---------|---------|---------|--------|
| UT-MAP-001 | 规则创建 | 参数完整 | MappingRule实例化 | 所有字段正确 | P0 |
| UT-MAP-002 | 规则字典转换 | 规则对象 | to_dict()调用 | 返回正确字典 | P0 |
| UT-MAP-003 | 字典反解析 | 规则字典 | from_dict()调用 | 还原规则对象 | P0 |
| UT-MAP-004 | 从Excel学习 | 映射Excel文件 | learn_from_excel() | 导入3条规则 | P0 |
| UT-MAP-005 | 从文本学习 | 任务文本+责任人 | learn_from_text() | 创建规则 | P0 |
| UT-MAP-006 | 从历史学习 | 历史任务列表 | learn_from_history() | 统计生成规则 | P0 |
| UT-MAP-007 | 精确匹配推荐 | 存在匹配规则 | recommend() | 返回责任人+置信度 | P0 |
| UT-MAP-008 | 无匹配推荐 | 无相关规则 | recommend() | 返回None, 0.0 | P0 |
| UT-MAP-009 | 导出Excel | 存在规则 | export_to_excel() | 生成xlsx文件 | P0 |
| UT-MAP-010 | 删除规则 | 存在规则 | delete_rule() | 规则被删除 | P1 |
| UT-MAP-011 | 关键词提取 | 任务文本 | _extract_keywords() | 返回关键词列表 | P0 |

**执行命令：**
```bash
cd D:\GITwork
python -m pytest src/tests/test_enhanced_mapping.py -v --cov=src.learning.enhanced_mapping
```

**预期输出：**
```
tests/test_enhanced_mapping.py::TestMappingRule::test_create_rule PASSED
tests/test_enhanced_mapping.py::TestMappingRule::test_to_dict PASSED
tests/test_enhanced_mapping.py::TestMappingRule::test_from_dict PASSED
tests/test_enhanced_mapping.py::TestMappingLearner::test_init PASSED
tests/test_enhanced_mapping.py::TestMappingLearner::test_learn_from_excel PASSED
tests/test_enhanced_mapping.py::TestMappingLearner::test_learn_from_text PASSED
tests/test_enhanced_mapping.py::TestMappingLearner::test_learn_from_history PASSED
tests/test_enhanced_mapping.py::TestMappingLearner::test_recommend_exact_match PASSED
tests/test_enhanced_mapping.py::TestMappingLearner::test_recommend_no_match PASSED
tests/test_enhanced_mapping.py::TestMappingLearner::test_export_to_excel PASSED
tests/test_enhanced_mapping.py::TestMappingLearner::test_delete_rule PASSED
tests/test_enhanced_mapping.py::TestMappingLearner::test_extract_keywords PASSED

========================== 12 passed ==========================
```

---

### 2.4 代码质量测试

| 测试项 | 检查内容 | 质量标准 | 执行命令 |
|--------|---------|---------|---------|
| 代码规范 | pylint检查 | >= 8.0分 | `pylint src/content/*.py src/learning/*.py` |
| 测试覆盖 | pytest-cov | >= 70% | `pytest --cov` |
| 圈复杂度 | MCCCabe | 最大值 <= 10 | `flake8 --max-complexity=10` |

---

## 3. 系统测试用例

### 3.1 功能测试

| 用例ID | 用例名称 | 测试步骤 | 预期结果 | 状态 |
|--------|---------|---------|---------|------|
| ST-FUNC-001 | Excel通讯录导入 | 1.准备Excel文件<br>2.点击导入<br>3.查看导入结果 | 成功导入，显示统计 | 待测试 |
| ST-FUNC-002 | Excel数据编辑 | 1.导入后编辑<br>2.保存到Excel<br>3.重新读取 | 数据一致 | 待测试 |
| ST-FUNC-003 | 图片OCR识别 | 1.选择名片图片<br>2.点击识别<br>3.查看结果 | 提取联系人信息 | 待测试 |
| ST-FUNC-004 | OCR结果导出 | 1.识别完成后<br>2.点击导出Excel<br>3.查看文件 | 生成Excel文件 | 待测试 |
| ST-FUNC-005 | 映射规则学习 | 1.导入带映射的Excel<br>2.点击学习<br>3.查看规则列表 | 规则被学习 | 待测试 |
| ST-FUNC-006 | 智能推荐 | 1.输入任务名称<br>2.查看推荐结果 | 显示推荐责任人 | 待测试 |

### 3.2 界面交互测试

| 用例ID | 用例名称 | 测试步骤 | 预期结果 | 状态 |
|--------|---------|---------|---------|------|
| ST-UI-001 | 导入进度显示 | 导入大量数据 | 显示进度条 | 待测试 |
| ST-UI-002 | 错误提示 | 导入无效文件 | 显示错误信息 | 待测试 |
| ST-UI-003 | 空状态处理 | 无数据时导入 | 显示友好提示 | 待测试 |

### 3.3 边界条件测试

| 用例ID | 用例名称 | 测试步骤 | 预期结果 | 状态 |
|--------|---------|---------|---------|------|
| ST-BOUND-001 | 空Excel文件 | 导入空Excel | 提示无数据 | 待测试 |
| ST-BOUND-002 | 损坏的Excel | 导入损坏文件 | 提示文件错误 | 待测试 |
| ST-BOUND-003 | 超大文件 | 导入10000条数据 | 正常处理，不崩溃 | 待测试 |
| ST-BOUND-004 | 特殊字符 | 姓名含特殊字符 | 正常保存 | 待测试 |
| ST-BOUND-005 | OCR图片模糊 | 低质量图片 | 给出提示或低置信度 | 待测试 |

---

## 4. 集成测试

### 4.1 端到端流程测试

| 用例ID | 流程名称 | 测试步骤 | 预期结果 | 状态 |
|--------|---------|---------|---------|------|
| E2E-001 | 完整导入流程 | Excel→导入→编辑→保存→导出 | 全流程正常 | 待测试 |
| E2E-002 | 完整OCR流程 | 图片→识别→编辑→保存→导出 | 全流程正常 | 待测试 |
| E2E-003 | 映射学习流程 | Excel学习→规则积累→智能推荐 | 推荐准确 | 待测试 |

### 4.2 数据一致性测试

| 测试项 | 验证方法 | 预期结果 | 状态 |
|--------|---------|---------|------|
| Excel导入数据一致性 | 导入后数据与原文件对比 | 完全一致 | 待测试 |
| OCR识别准确性 | 识别结果与原图对比 | 关键字段准确 | 待测试 |
| 映射规则持久化 | 重启后规则仍存在 | 规则完整 | 待测试 |

---

## 5. 性能测试

| 测试项 | 测试数据量 | 性能标准 | 实际结果 | 状态 |
|--------|-----------|---------|---------|------|
| Excel导入速度 | 1000条 | < 5秒 | 秒 | 待测试 |
| OCR识别速度 | 1张图片 | < 3秒 | 秒 | 待测试 |
| 批量OCR处理 | 10张图片 | < 30秒 | 秒 | 待测试 |
| 映射推荐响应 | 100条规则 | < 0.1秒 | 秒 | 待测试 |

---

## 6. 测试执行记录

### 6.1 执行环境

| 项目 | 值 |
|------|---|
| 测试日期 | 2026-06-16 |
| 测试人员 | |
| Python版本 | |
| 操作系统 | Windows |

### 6.2 测试结果汇总

| 模块 | 用例数 | 通过 | 失败 | 阻塞 | 通过率 |
|------|--------|------|------|------|--------|
| Excel导入 | 17 | | | | |
| OCR处理 | 20 | | | | |
| 映射学习 | 12 | | | | |
| **合计** | **49** | | | | **%** |

### 6.3 缺陷记录

| 缺陷ID | 严重程度 | 模块 | 描述 | 状态 |
|--------|---------|------|------|------|
| (无) | - | - | - | - |

---

## 7. 测试结论

### 7.1 功能评估

| 评估项 | 评估结果 |
|--------|---------|
| Excel导入功能 | ☐ 优秀 ☐ 良好 ☐ 一般 ☐ 需改进 |
| OCR识别功能 | ☐ 优秀 ☐ 良好 ☐ 一般 ☐ 需改进 |
| 映射学习功能 | ☐ 优秀 ☐ 良好 ☐ 一般 ☐ 需改进 |
| 代码质量 | ☐ 优秀 ☐ 良好 ☐ 一般 ☐ 需改进 |

### 7.2 发布建议

- [ ] 可以发布
- [ ] 需要修复后发布
- [ ] 需要更多测试

### 7.3 签名

| 角色 | 姓名 | 日期 | 签名 |
|------|------|------|------|
| 测试执行 | | 2026-06-16 | |
| 测试审核 | | 2026-06-16 | |
| 产品确认 | | 2026-06-16 | |

---

## 附录A：快速测试命令

```bash
# 进入项目目录
cd D:\GITwork

# 运行所有单元测试（生成覆盖率报告）
python -m pytest src/tests/test_excel_import.py src/tests/test_ocr_handler.py src/tests/test_enhanced_mapping.py -v --cov=src --cov-report=html --cov-report=term

# 仅运行单元测试
python -m pytest src/tests/test_*.py -v

# 运行特定模块测试
python -m pytest src/tests/test_excel_import.py -v

# 生成覆盖率报告
python -m pytest --cov=src --cov-report=html
start htmlcov/index.html
```

---

*文档版本：V2.1*
*最后更新：2026-06-16*
