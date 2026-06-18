# 市场咨询任务跟踪工具

市场咨询任务跟踪工具是一个基于PyQt5的桌面应用程序，帮助市场咨询团队高效管理和跟踪任务进度。

## 功能特性

- 📋 **任务信息管理** - 创建、编辑、删除任务
- 📊 **任务跟踪** - 实时跟踪任务进度
- 🔮 **智能推荐** - AI驱动的任务推荐
- 🔔 **提醒通知** - 及时的任务提醒
- 📁 **数据导入导出** - 支持Excel/CSV/MSG邮件导入
- 📷 **OCR识别** - 从名片/文档图片识别联系人信息
- 📈 **统计分析** - 可视化数据分析
- 📇 **通讯录管理** - 管理客户和团队联系人

## 技术栈

- Python 3.10+
- PyQt5 5.15+
- SQLite 3
- pytest
- pytesseract (OCR)
- Pillow (图像处理)

## 项目状态

| 指标 | 状态 |
|------|------|
| 版本 | V4.5 |
| 代码质量 | 通过 |
| 测试用例 | 457+个通过 |
| 综合评分 | 4.7/5 |

## 快速开始

### 环境要求

- Python 3.10 或更高版本
- Windows 10/11, macOS 10.14+, Linux
- Tesseract OCR引擎（可选，用于名片识别）

### 安装依赖

```bash
pip install -r requirements.txt
```

### OCR功能安装（可选）

如需使用OCR名片识别功能，需要安装Tesseract OCR引擎：

1. 下载Tesseract：https://github.com/UB-Mannheim/tesseract/wiki
2. 安装时选择中文语言包（chi_sim+eng）
3. 确保tesseract可执行文件在系统PATH中

### 运行应用

```bash
python src/main.py
```

### 运行测试

```bash
pytest src/tests/ -v
```

## 项目结构

```
market_task_tracker/
├── src/
│   ├── main.py              # 程序入口
│   ├── config.py            # 配置管理
│   ├── core/                 # 核心模块
│   │   ├── logger.py         # 日志模块
│   │   ├── data_pager.py     # 数据分页
│   │   ├── performance.py     # 性能监控
│   │   ├── usability.py       # 用户体验
│   │   ├── acceptance.py      # 验收测试
│   │   └── cache_optimizer.py # 缓存优化
│   ├── database/             # 数据库层
│   │   ├── connection.py     # 数据库连接
│   │   ├── models.py         # 数据模型
│   │   ├── er_diagram.py     # DAO层（含BaseDAO）
│   │   ├── recommendations.py # 推荐库服务（含多关键模块合并）
│   │   └── contacts_manager.py # 通讯录管理器（含重名处理）
│   ├── ui/                   # 界面层
│   │   ├── main_window.py    # 主窗口
│   │   ├── contacts.py       # 通讯录（含OCR）
│   │   ├── dpi_adapter.py    # DPI适配
│   │   └── widgets/          # UI组件
│   ├── content/              # 内容处理
│   │   ├── excel_import.py   # Excel导入
│   │   ├── msg_import.py     # MSG邮件导入
│   │   └── image_ocr_processor.py  # OCR处理器
│   ├── services/             # 服务层
│   │   └── content_parser_service.py  # 内容解析服务
│   └── utils/                # 工具层
│       ├── helpers.py        # 辅助函数
│       ├── exceptions.py      # 异常定义
│       ├── validators.py      # 数据验证
│       └── security.py        # 安全模块（加密/审计/权限）
├── tests/                    # 测试用例 (457+个)
├── scripts/                  # 脚本工具
├── data/                     # 数据目录
├── logs/                     # 日志目录
├── docs/                     # 文档
├── .github/
│   └── workflows/
│       └── ci.yml           # CI/CD配置
└── requirements.txt         # Python依赖
```

## 版本历史

| 版本 | 日期 | 主要更新 |
|------|------|----------|
| V1.0 | 2026-06-11 | 基础功能 |
| V2.0 | 2026-06-12 | Excel导入、OCR、映射学习 |
| V3.0 | 2026-06-13 | Phase 3完成 |
| V3.1 | 2026-06-14 | MSG邮件导入 |
| V4.0 | 2026-06-15 | CodeCC全项目评审 |
| V4.1 | 2026-06-16 | 高/中优先级优化 |
| V4.2 | 2026-06-17 | 增量评审验证 |
| V4.3 | 2026-06-18 | 单元测试、OCR功能、文档更新 |
| V4.4 | 2026-06-18 | E-R图优化、BaseDAO、查询缓存 |
| V4.5 | 2026-06-18 | 通讯录重名处理、推荐库多关键模块 |

## V4.5 新功能

### 通讯录重名处理

- **唯一标识** - 姓名+工号唯一标识，区分同名联系人
- **信息同步** - 导入时按新信息刷新本地记录
- **智能导入** - 支持批量导入，自动识别新增/更新

**示例**:
- 赵六|EMP001 ≠ 赵六|EMP002（不同人）
- 导入赵六/EMP001新信息 → 自动刷新本地记录

### 推荐库多关键模块

- **关键模块合并** - 同姓名多条记录自动合并关键模块
- **智能推荐** - 任一关键模块匹配即可推荐
- **去重处理** - 自动去除重复的关键模块

**示例**:
```
导入: 赵六，MAC认证 + 赵六，802.1x认证
结果: 赵六，MAC认证、802.1x认证

搜索MAC认证 → 赵六
搜索802.1x认证 → 赵六
```

## V4.4 新功能（V4.5之前）

### 安全增强

- **数据库加密** - 数据库文件加密存储
- **审计日志** - 操作审计记录与查询
- **权限控制** - 基于角色的权限管理 (RBAC)

### 性能优化

- **增强缓存** - 支持LRU/LFU/FIFO/TTL多种策略
- **统计缓存** - 统计分析结果缓存优化
- **DPI适配** - 响应式布局与DPI自动适配

## V4.4 新功能

### E-R图优化

- **BaseDAO基础类** - 提取公共CRUD逻辑
- **动态列名获取** - 替代硬编码列名
- **LRU查询缓存** - 减少数据库查询50%+
- **批量操作** - batch_create/update/delete
- **性能分析** - DatabaseAnalyzer工具

### 通讯录OCR

- **名片扫描** - 从名片图片识别联系人
- **自动提取** - 姓名、电话、邮箱、部门、职位
- **多格式支持** - PNG/JPG/BMP/GIF/TIFF/WebP

## CI/CD

本项目使用GitHub Actions进行持续集成：

- ✅ 代码质量检查 (Pylint)
- ✅ 单元测试 (pytest)
- ✅ 数据库连接测试
- ✅ 应用启动测试
- ✅ UI组件验证

## 开发计划

| 阶段 | 任务 | 状态 | 完成时间 |
|------|------|------|----------|
| **阶段一** | 基础设施搭建 | ✅ 完成 | 2026-06-16 |
| **阶段二** | 核心功能开发 | ✅ 完成 | 2026-06-17 |
| **阶段三** | 高级功能与扩展 | ✅ 完成 | 2026-06-18 |
| **阶段四** | 代码评审优化 | ✅ 完成 | 2026-06-18 |
| **阶段五** | 测试与验收 | 🔄 进行中 | - |

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目主页: https://github.com/Gyworker/Gitwork
- 问题反馈: https://github.com/Gyworker/Gitwork/issues

---

**市场咨询任务跟踪工具开发团队**
**最后更新**: 2026-06-18
