# V2.1 测试检查清单

## 📋 测试执行检查表

**版本：** V2.1  
**日期：** 2026-06-16  
**测试人员：** _______________

---

## 一、单元测试检查

### 1.1 Excel导入模块 (17个测试用例)

| 序号 | 测试用例 | 执行结果 | 备注 |
|------|---------|---------|------|
| 1 | test_find_header_mapping_standard | ☐ 通过 ☐ 失败 | |
| 2 | test_find_header_mapping_english | ☐ 通过 ☐ 失败 | |
| 3 | test_find_header_mapping_mixed | ☐ 通过 ☐ 失败 | |
| 4 | test_find_header_mapping_partial | ☐ 通过 ☐ 失败 | |
| 5 | test_find_header_mapping_empty | ☐ 通过 ☐ 失败 | |
| 6 | test_create_contact | ☐ 通过 ☐ 失败 | |
| 7 | test_to_dict | ☐ 通过 ☐ 失败 | |
| 8 | test_from_dict | ☐ 通过 ☐ 失败 | |
| 9 | test_import_from_file_success | ☐ 通过 ☐ 失败 | |
| 10 | test_import_from_file_empty | ☐ 通过 ☐ 失败 | |
| 11 | test_import_duplicate_detection | ☐ 通过 ☐ 失败 | |
| 12 | test_save_to_database | ☐ 通过 ☐ 失败 | |
| 13 | test_save_to_excel | ☐ 通过 ☐ 失败 | |
| 14 | test_import_unsupported_format | ☐ 通过 ☐ 失败 | |
| 15 | test_export_all | ☐ 通过 ☐ 失败 | |
| 16 | test_export_filtered | ☐ 通过 ☐ 失败 | |
| 17 | test_create_template | ☐ 通过 ☐ 失败 | |

**执行命令：**
```bash
python -m pytest src/tests/test_excel_import.py -v
```

**结果统计：** 通过 _____ / 17

---

### 1.2 OCR处理模块 (20个测试用例)

| 序号 | 测试用例 | 执行结果 | 备注 |
|------|---------|---------|------|
| 1 | test_create_result | ☐ 通过 ☐ 失败 | |
| 2 | test_to_dict | ☐ 通过 ☐ 失败 | |
| 3 | test_from_dict | ☐ 通过 ☐ 失败 | |
| 4 | test_preprocess_returns_image | ☐ 通过 ☐ 失败 | |
| 5 | test_get_supported_formats | ☐ 通过 ☐ 失败 | |
| 6 | test_is_supported_format | ☐ 通过 ☐ 失败 | |
| 7 | test_parse_chinese_card | ☐ 通过 ☐ 失败 | |
| 8 | test_parse_phone_patterns | ☐ 通过 ☐ 失败 | |
| 9 | test_parse_email | ☐ 通过 ☐ 失败 | |
| 10 | test_parse_company | ☐ 通过 ☐ 失败 | |
| 11 | test_parse_empty_text | ☐ 通过 ☐ 失败 | |
| 12 | test_clean_phone | ☐ 通过 ☐ 失败 | |
| 13 | test_extract_name_from_email | ☐ 通过 ☐ 失败 | |
| 14 | test_extract_name_with_prefix | ☐ 通过 ☐ 失败 | |
| 15 | test_init_default | ☐ 通过 ☐ 失败 | |
| 16 | test_init_custom_tesseract_path | ☐ 通过 ☐ 失败 | |
| 17 | test_recognize_image_mock | ☐ 通过 ☐ 失败 | |
| 18 | test_recognize_batch_empty | ☐ 通过 ☐ 失败 | |
| 19 | test_recognize_batch_multiple | ☐ 通过 ☐ 失败 | |
| 20 | test_ocr_processor_can_be_instantiated | ☐ 通过 ☐ 失败 | |

**执行命令：**
```bash
python -m pytest src/tests/test_ocr_handler.py -v
```

**结果统计：** 通过 _____ / 20

---

### 1.3 映射学习模块 (12个测试用例)

| 序号 | 测试用例 | 执行结果 | 备注 |
|------|---------|---------|------|
| 1 | test_create_rule | ☐ 通过 ☐ 失败 | |
| 2 | test_to_dict | ☐ 通过 ☐ 失败 | |
| 3 | test_from_dict | ☐ 通过 ☐ 失败 | |
| 4 | test_init | ☐ 通过 ☐ 失败 | |
| 5 | test_learn_from_excel | ☐ 通过 ☐ 失败 | |
| 6 | test_learn_from_text | ☐ 通过 ☐ 失败 | |
| 7 | test_learn_from_history | ☐ 通过 ☐ 失败 | |
| 8 | test_recommend_exact_match | ☐ 通过 ☐ 失败 | |
| 9 | test_recommend_no_match | ☐ 通过 ☐ 失败 | |
| 10 | test_export_to_excel | ☐ 通过 ☐ 失败 | |
| 11 | test_delete_rule | ☐ 通过 ☐ 失败 | |
| 12 | test_extract_keywords | ☐ 通过 ☐ 失败 | |

**执行命令：**
```bash
python -m pytest src/tests/test_enhanced_mapping.py -v
```

**结果统计：** 通过 _____ / 12

---

## 二、系统测试检查

### 2.1 功能测试

| 序号 | 测试项 | 测试步骤 | 结果 | 签名 |
|------|-------|---------|------|------|
| ST-01 | Excel通讯录导入 | 准备Excel → 点击导入 → 查看结果 | ☐ 通过 ☐ 失败 | |
| ST-02 | Excel数据编辑 | 导入 → 编辑 → 保存 → 重新读取 | ☐ 通过 ☐ 失败 | |
| ST-03 | 图片OCR识别 | 选择图片 → 识别 → 查看结果 | ☐ 通过 ☐ 失败 | |
| ST-04 | OCR结果导出 | 识别完成 → 导出Excel → 查看文件 | ☐ 通过 ☐ 失败 | |
| ST-05 | 映射规则学习 | 导入Excel → 学习 → 查看规则 | ☐ 通过 ☐ 失败 | |
| ST-06 | 智能推荐 | 输入任务 → 查看推荐结果 | ☐ 通过 ☐ 失败 | |

### 2.2 界面交互测试

| 序号 | 测试项 | 测试步骤 | 结果 | 签名 |
|------|-------|---------|------|------|
| ST-07 | 导入进度显示 | 导入大量数据 | ☐ 通过 ☐ 失败 | |
| ST-08 | 错误提示 | 导入无效文件 | ☐ 通过 ☐ 失败 | |
| ST-09 | 空状态处理 | 无数据时导入 | ☐ 通过 ☐ 失败 | |

### 2.3 边界条件测试

| 序号 | 测试项 | 测试步骤 | 结果 | 签名 |
|------|-------|---------|------|------|
| ST-10 | 空Excel文件 | 导入空Excel | ☐ 通过 ☐ 失败 | |
| ST-11 | 损坏的Excel | 导入损坏文件 | ☐ 通过 ☐ 失败 | |
| ST-12 | 超大文件(10000条) | 导入大量数据 | ☐ 通过 ☐ 失败 | |
| ST-13 | 特殊字符姓名 | 姓名含特殊字符 | ☐ 通过 ☐ 失败 | |

---

## 三、集成测试检查

| 序号 | 测试项 | 测试步骤 | 结果 | 签名 |
|------|-------|---------|------|------|
| IT-01 | 完整导入流程 | Excel → 导入 → 编辑 → 保存 → 导出 | ☐ 通过 ☐ 失败 | |
| IT-02 | 完整OCR流程 | 图片 → 识别 → 编辑 → 保存 → 导出 | ☐ 通过 ☐ 失败 | |
| IT-03 | 映射学习流程 | Excel学习 → 规则积累 → 智能推荐 | ☐ 通过 ☐ 失败 | |
| IT-04 | 数据一致性 | 导入后数据与原文件对比 | ☐ 通过 ☐ 失败 | |

---

## 四、代码质量检查

| 检查项 | 检查方法 | 标准 | 结果 |
|-------|---------|------|------|
| Python语法 | py_compile | 无错误 | ☐ 通过 ☐ 失败 |
| 代码规范 | pylint | >= 8.0分 | ☐ 通过 ☐ 失败 |
| 测试覆盖 | pytest-cov | >= 70% | ☐ 通过 ☐ 失败 |
| 圈复杂度 | flake8 | <= 10 | ☐ 通过 ☐ 失败 |

---

## 五、测试汇总

| 测试类型 | 用例数 | 通过数 | 失败数 | 通过率 |
|---------|--------|--------|--------|--------|
| 单元测试 | 49 | | | |
| 系统测试 | 13 | | | |
| 集成测试 | 4 | | | |
| 代码质量 | 4 | | | |
| **总计** | **70** | | | **%** |

---

## 六、发现缺陷

| 缺陷ID | 严重程度 | 模块 | 描述 | 状态 |
|--------|---------|------|------|------|
| (无) | - | - | - | - |

---

## 七、测试结论

| 评估项 | 评估结果 |
|--------|---------|
| Excel导入功能 | ☐ 优秀 ☐ 良好 ☐ 一般 ☐ 需改进 |
| OCR识别功能 | ☐ 优秀 ☐ 良好 ☐ 一般 ☐ 需改进 |
| 映射学习功能 | ☐ 优秀 ☐ 良好 ☐ 一般 ☐ 需改进 |
| 代码质量 | ☐ 优秀 ☐ 良好 ☐ 一般 ☐ 需改进 |

### 发布建议
- [ ] 可以发布
- [ ] 需要修复后发布
- [ ] 需要更多测试

---

## 八、签名确认

| 角色 | 姓名 | 日期 | 签名 |
|------|------|------|------|
| 测试执行 | | 2026-06-16 | |
| 代码审核 | | 2026-06-16 | |
| 产品确认 | | 2026-06-16 | |

---

## 附录：快速测试命令

```bash
# 进入项目目录
cd D:\GITwork

# 生成测试样本数据
python test_data/generate_samples.py

# 运行所有测试（推荐）
python run_tests.py

# 仅运行单元测试
python run_tests.py unit

# 仅运行系统测试
python run_tests.py system

# 仅运行集成测试
python run_tests.py integration

# 生成覆盖率报告
python -m pytest src/tests/ -v --cov=src --cov-report=html
start htmlcov/index.html
```

---

*文档版本：V2.1*
*最后更新：2026-06-16*
