# =============================================================================
# CI环境配置指南
# =============================================================================
# 市场咨询任务跟踪工具 V1.0
# 最后更新: 2026-06-16
# =============================================================================

## 一、概述

由于当前环境无Python运行时，提供以下三种CI检查方案：

| 方案 | 适用场景 | 复杂度 | 推荐指数 |
|------|----------|--------|----------|
| **方案A：GitHub Actions** | 有GitHub仓库 | 低 | ⭐⭐⭐⭐⭐ |
| **方案B：Docker** | 有Docker环境 | 中 | ⭐⭐⭐⭐ |
| **方案C：本地Python** | 无网络限制 | 低 | ⭐⭐⭐ |

---

## 二、方案A：GitHub Actions（推荐）

### 2.1 优点

- ✅ **完全免费**（公开仓库每月2000分钟）
- ✅ 无需本地Python环境
- ✅ 自动运行，完全托管
- ✅ PR关联检查状态
- ✅ 支持并行测试
- ✅ 历史记录可追溯

### 2.2 实施步骤

#### 步骤1：创建GitHub仓库

1. 访问 https://github.com/new
2. 创建新仓库：
   - 仓库名称：market-task-tracker
   - 选择 Public（免费）或 Private
   - 勾选 "Add a README file"

#### 步骤2：推送代码

```powershell
# 进入项目目录
cd d:/AIapple/工具任务跟踪20260611/src/market_task_tracker

# 初始化git（如果需要）
git init
git add .
git commit -m "Initial commit - Phase 1 complete"

# 添加远程仓库（替换YOUR_USERNAME为你的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/market-task-tracker.git

# 推送代码
git push -u origin main
```

#### 步骤3：查看CI结果

1. 访问你的GitHub仓库
2. 点击 Actions 标签页
3. 查看CI运行状态
4. 点击具体的workflow查看详细日志

### 2.3 CI工作流说明

.github/workflows/ci.yml 已配置以下检查项：

| Job | 检查内容 | 失败是否阻止合并 |
|-----|----------|-----------------|
| code-quality | Pylint代码分析 | 否（建议值7.0）|
| unit-tests | pytest单元测试 | 是 |
| database-tests | 数据库连接测试 | 是 |
| app-startup | 模块导入测试 | 是 |
| ui-components | UI组件语法检查 | 是 |
| integration-report | 测试报告汇总 | 否 |

### 2.4 合入规则

```
PR状态检查 → 所有必检项通过 → 允许合并
              ↓
         任意失败 → 阻止合并
```

---

## 三、方案B：Docker

### 3.1 前置条件

安装 Docker Desktop (Windows):
- 下载地址: https://www.docker.com/products/docker-desktop
- 安装后重启电脑
- 验证安装: docker --version

### 3.2 使用命令

```powershell
# 进入项目目录
cd d:/AIapple/工具任务跟踪20260611/src/market_task_tracker

# 构建并运行CI检查
docker-compose up ci

# 仅检查代码质量（不运行测试）
docker-compose up lint

# 查看详细输出
docker-compose up --abort-on-container-exit ci
```

---

## 四、方案C：本地Python

### 4.1 方式1：自动安装（推荐）

```powershell
# 以管理员身份运行PowerShell
cd d:/AIapple/工具任务跟踪20260611/src/market_task_tracker
.\scripts\install_python.ps1
```

脚本将自动：
1. 检测Python环境
2. 下载Python 3.12 embeddable（约25MB）
3. 配置环境变量
4. 安装项目依赖
5. 运行CI检查

### 4.2 方式2：手动安装

1. 下载Python
   - 官网: https://www.python.org/downloads/
   - 选择: Python 3.12 Windows installer (64-bit)

2. 安装步骤
   - 运行下载的exe文件
   - 勾选 "Add Python to PATH"
   - 点击 "Install Now"

3. 验证安装
   ```powershell
   python --version
   pip --version
   ```

4. 安装依赖
   ```powershell
   cd d:/AIapple/工具任务跟踪20260611/src/market_task_tracker
   pip install -r requirements.txt
   pip install pylint pytest pytest-cov
   ```

5. 运行CI检查
   ```powershell
   .\scripts\local_ci.ps1
   ```

---

## 五、CI检查详细说明

### 5.1 检查项目

| 检查项 | 命令 | 说明 |
|--------|------|------|
| 语法检查 | python -m py_compile file | 检查Python语法错误 |
| 代码导入 | python -c "from module import *" | 验证模块可导入 |
| 单元测试 | python -m pytest | 运行测试用例 |
| 代码质量 | pylint dir | 静态代码分析 |

### 5.2 CI规则

根据项目要求：

| 规则 | 标准 | 说明 |
|------|------|------|
| 语法检查 | 0错误 | 所有.py文件必须通过 |
| 单元测试 | ≥80%通过 | 允许20%失败（预期失败）|
| 代码质量 | ≥7.0分 | Pylint评分（建议值）|
| 代码导入 | 100%成功 | 核心模块必须可导入 |

### 5.3 禁止合入条件

- ❌ CI检查失败
- ❌ 语法错误未修复
- ❌ 核心模块导入失败
- ❌ 单元测试通过率<80%

---

## 六、合入流程图

```
                    开始
                      │
                      ▼
              ┌───────────────┐
              │   编写代码    │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │   本地测试    │ ◄── 可选但推荐
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │   提交代码    │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │   推送GitHub  │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ GitHub Actions│
              │   CI检查     │
              └───────┬───────┘
                      │
              ┌───────┴───────┐
              │               │
              ▼               ▼
         ┌────────┐     ┌─────────┐
         │  失败   │     │  通过   │
         └───┬────┘     └────┬────┘
             │              │
             ▼              ▼
       ┌──────────┐    ┌──────────┐
       │ 修复代码  │    │ 合入主线 │
       └────┬─────┘    └──────────┘
            │
            └────────► 返回提交
```

---

## 七、文件清单

| 文件 | 用途 |
|------|------|
| .github/workflows/ci.yml | GitHub Actions配置 |
| Dockerfile | Docker镜像定义 |
| docker-compose.yml | Docker Compose配置 |
| scripts/local_ci.ps1 | PowerShell CI脚本 |
| scripts/local_ci.sh | Bash CI脚本 |
| scripts/install_python.ps1 | Python自动安装脚本 |
| CI环境配置指南.md | 本文档 |

---

## 八、技术支持

### GitHub Actions
- 官方文档: https://docs.github.com/en/actions
- Python设置: https://github.com/actions/setup-python
- 免费额度: 公开仓库2000分钟/月

### Docker
- 官方文档: https://docs.docker.com/
- 下载地址: https://www.docker.com/products/docker-desktop

### Python
- 官方文档: https://docs.python.org/3/
- PyPI: https://pypi.org/
- pylint: https://pylint.readthedocs.io/
- pytest: https://docs.pytest.org/

---

**报告结束**
