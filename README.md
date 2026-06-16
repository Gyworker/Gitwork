# 市场咨询任务跟踪工具

市场咨询任务跟踪工具是一个基于PyQt5的桌面应用程序，帮助市场咨询团队高效管理和跟踪任务进度。

## 功能特性

- 📋 **任务信息管理** - 创建、编辑、删除任务
- 📊 **任务跟踪** - 实时跟踪任务进度
- 🔮 **智能推荐** - AI驱动的任务推荐
- 🔔 **提醒通知** - 及时的任务提醒
- 📁 **数据导入导出** - 支持Excel/CSV导入导出
- 📈 **统计分析** - 可视化数据分析

## 技术栈

- Python 3.10+
- PyQt5 5.15+
- SQLite 3
- pytest

## 项目状态

| 指标 | 状态 |
|------|------|
| CI检查 | ![CI](https://github.com/YOUR_USERNAME/market-task-tracker/actions/workflows/ci.yml/badge.svg) |
| 代码质量 | 通过 |
| 测试覆盖 | 进行中 |

## 快速开始

### 环境要求

- Python 3.10 或更高版本
- Windows 10/11, macOS 10.14+, Linux

### 安装依赖

```bash
pip install -r requirements.txt
```

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
│   ├── config.py             # 配置管理
│   ├── database/             # 数据库层
│   │   ├── connection.py     # 数据库连接
│   │   └── models.py         # 数据模型
│   ├── ui/                   # 界面层
│   │   ├── main_window.py    # 主窗口
│   │   └── widgets/          # UI组件
│   └── utils/                # 工具层
│       ├── logger.py         # 日志工具
│       ├── helpers.py        # 辅助函数
│       ├── exceptions.py     # 异常定义
│       └── validators.py     # 数据验证
├── tests/                    # 测试用例
├── scripts/                  # 脚本工具
├── data/                     # 数据目录
├── logs/                     # 日志目录
├── .github/
│   └── workflows/
│       └── ci.yml           # CI/CD配置
├── Dockerfile               # Docker配置
├── docker-compose.yml       # Docker Compose配置
└── requirements.txt         # Python依赖
```

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
| T-1.1 | 环境准备与项目初始化 | ✅ | - |
| T-1.2 | 数据库设计与实现 | ✅ | - |
| T-1.3 | 主框架搭建与导航结构 | ✅ | - |
| T-1.4 | 基础工具类与公共模块 | ✅ | - |
| **阶段二** | 核心功能开发 | 🔄 开发中 | - |
| T-2.1 | 任务信息管理模块 | 📋 待开始 | - |
| T-2.2 | 任务跟踪管理模块 | 📋 待开始 | - |
| T-2.3 | 智能推荐模块 | 📋 待开始 | - |
| T-2.4 | 提醒通知模块 | 📋 待开始 | - |
| **阶段三** | 高级功能与扩展 | 📋 待开始 | - |
| **阶段四** | 测试与优化 | 📋 待开始 | - |
| **阶段五** | 验收与交付 | 📋 待开始 | - |

## 里程碑

| 里程碑 | 名称 | 状态 | 验收标准 |
|--------|------|------|----------|
| M1 | 基础框架完成 | ✅ | 主窗口可启动，基本导航可用 |
| M2 | 核心功能完成 | 🔄 | 任务信息/跟踪/推荐/提醒功能可用 |
| M3 | 全部功能完成 | 📋 | 所有功能开发完成，测试通过 |
| M4 | 测试通过 | 📋 | 所有170个测试用例通过，性能达标 |
| M5 | 项目交付 | 📋 | 验收测试通过，文档完整 |

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

- 项目主页: https://github.com/YOUR_USERNAME/market-task-tracker
- 问题反馈: https://github.com/YOUR_USERNAME/market-task-tracker/issues

---

**市场咨询任务跟踪工具开发团队**
