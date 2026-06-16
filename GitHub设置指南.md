# GitHub 仓库设置指南

## 前置要求

在运行设置脚本之前，请确保已完成以下准备：

### 1. 安装 Git

**Windows:**
- 访问 https://git-scm.com/download/win
- 下载并运行安装程序
- 安装选项建议：
  - ✅ 选择 "Git Bash Here"
  - ✅ 选择 "Add Git to PATH"
  - ✅ 选择 "Use OpenSSL library"
  - ✅ 选择 "Checkout Windows-style, commit Unix-style"

**验证安装：**
```powershell
git --version
# 应该显示类似: git version 2.40.0.windows.1
```

### 2. 创建 GitHub 账号

1. 访问 https://github.com/
2. 点击 "Sign up"
3. 填写用户名、邮箱、密码
4. 验证邮箱

### 3. 创建空仓库（重要！）

1. 登录 GitHub
2. 点击右上角 "+" → "New repository"
3. 填写仓库信息：
   - **Repository name:** `market-task-tracker`
   - **Description:** `市场咨询任务跟踪工具 - 基于PyQt5的桌面应用`
   - **Public/Private:** 选择 Public（免费使用Actions）
   - **❌ 不要勾选** "Add a README file"
   - **❌ 不要勾选** "Add .gitignore"
4. 点击 "Create repository"
5. **复制仓库URL**（备用）

---

## 运行设置脚本

### 方式一：使用脚本（推荐）

```powershell
# 进入项目目录
cd d:\AIapple\工具任务跟踪20260611\src\market_task_tracker

# 运行设置脚本（替换YOUR_GITHUB_USERNAME为你的GitHub用户名）
.\scripts\setup_github.ps1 -GitHubUsername "YOUR_GITHUB_USERNAME"
```

### 方式二：手动设置

如果脚本运行失败，请按以下步骤手动设置：

```powershell
# 1. 进入项目目录
cd d:\AIapple\工具任务跟踪20260611\src\market_task_tracker

# 2. 初始化Git仓库
git init

# 3. 配置用户信息（替换为你的信息）
git config --global user.name "YOUR_NAME"
git config --global user.email "YOUR_EMAIL@email.com"

# 4. 添加所有文件
git add .

# 5. 提交
git commit -m "Initial commit - Phase 1 complete"

# 6. 添加远程仓库（替换URL）
git remote add origin https://github.com/YOUR_USERNAME/market-task-tracker.git

# 7. 推送
git branch -M main
git push -u origin main
```

---

## GitHub Token 认证（可选但推荐）

为了避免每次推送都需要输入密码，建议使用 Personal Access Token：

### 创建 Token

1. 进入 GitHub → Settings → Developer settings
2. 点击 "Personal access tokens" → "Tokens (classic)"
3. 点击 "Generate new token"
4. 填写信息：
   - **Name:** `market-task-tracker-ci`
   - **Expiration:** 选择 30 days 或 90 days
   - **Scopes:** ✅ 勾选 `repo` (全部)
5. 点击 "Generate token"
6. **⚠️ 立即复制Token**，关闭页面后将无法查看

### 使用 Token

```powershell
# 运行脚本时传入Token
.\scripts\setup_github.ps1 -GitHubUsername "YOUR_USERNAME" -GitHubToken "ghp_XXXXXXXXXXXX"

# 或手动设置
git remote set-url origin https://ghp_XXXXXXXXXXXX@github.com/YOUR_USERNAME/market-task-tracker.git
```

---

## 验证 CI 检查

### 查看 Actions

1. 推送成功后，访问你的 GitHub 仓库
2. 点击 **Actions** 标签页
3. 应该可以看到自动运行的 CI 工作流
4. 点击具体的工作流查看详细日志

### 预期结果

| Job | 状态 | 说明 |
|-----|------|------|
| code-quality | ✅ 绿色 | 代码质量检查通过 |
| unit-tests | ✅ 绿色 | 单元测试通过 |
| database-tests | ✅ 绿色 | 数据库测试通过 |
| app-startup | ✅ 绿色 | 应用启动测试通过 |
| ui-components | ✅ 绿色 | UI组件检查通过 |

### CI 检查失败怎么办？

1. 点击失败的 Job
2. 查看详细日志
3. 根据错误信息修复代码
4. 重新提交并推送

---

## 分支管理策略

```
main          ← 生产环境代码（受保护）
  ↑
  │  PR合并
  │
develop       ← 开发分支
  ↑
  │  PR合并
  │
feature/xxx   ← 功能分支（每个任务一个分支）
```

### 创建功能分支

```powershell
# 创建并切换到新分支
git checkout -b feature/T-2.1-task-info

# 开发完成后提交
git add .
git commit -m "feat: 实现任务信息管理模块"

# 推送到远程
git push -u origin feature/T-2.1-task-info

# 在GitHub上创建Pull Request
```

---

## 常见问题

### Q: 推送时提示 "Authentication failed"

**原因:** 没有配置认证凭据

**解决方案:**
1. 使用 Personal Access Token（推荐）
2. 或安装 Git Credential Manager

### Q: GitHub Actions 没有自动运行

**检查项:**
1. 确认 `.github/workflows/ci.yml` 文件存在
2. 确认仓库是 Public（Private仓库Actions有分钟限制）
3. 检查 Actions 是否被禁用

### Q: CI 检查失败如何处理

**步骤:**
1. 查看失败日志
2. 在本地修复问题
3. 提交并推送
4. CI 会自动重新运行

---

## 下一步

CI 检查通过后，可以：

1. **继续开发** - 阶段二任务
2. **添加协作者** - Settings → Manage access
3. **配置保护分支** - Settings → Branches → Add rule
4. **配置 Issues 模板** - 创建 `.github/ISSUE_TEMPLATE/` 目录

---

**如有问题，请提交 Issue: https://github.com/YOUR_USERNAME/market-task-tracker/issues**
