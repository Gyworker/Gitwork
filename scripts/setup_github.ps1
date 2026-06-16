# =============================================================================
# GitHub 仓库设置脚本
# =============================================================================
# 功能：
# 1. 初始化Git仓库
# 2. 配置Git用户信息
# 3. 创建必要的配置文件
# 4. 提交代码
# 5. 推送到GitHub
# 6. 触发GitHub Actions CI检查
# =============================================================================
# 使用前提：
# 1. 安装 Git: https://git-scm.com/download/win
# 2. 创建 GitHub 账号: https://github.com/
# 3. 在GitHub上创建空仓库（不要勾选README）
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubUsername,
    
    [Parameter(Mandatory=$true)]
    [string]$RepositoryName = "market-task-tracker",
    
    [string]$GitHubToken = "",
    
    [switch]$SkipPush
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$RepoRoot = Join-Path $ProjectRoot "src\$RepositoryName"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "========================================================================" -ForegroundColor Cyan
}

function Write-Success { param([string]$Text); Write-Host "[OK] $Text" -ForegroundColor Green }
function Write-ErrorMsg { param([string]$Text); Write-Host "[FAIL] $Text" -ForegroundColor Red }
function Write-Info { param([string]$Text); Write-Host "[INFO] $Text" -ForegroundColor Yellow }

Write-Header "GitHub 仓库设置脚本"

# ============================================================================
# 第0步：检查Git安装
# ============================================================================
Write-Header "步骤0: 检查Git安装"

$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-ErrorMsg "Git未安装"
    Write-Host ""
    Write-Host "请先安装Git：" -ForegroundColor Yellow
    Write-Host "  1. 访问 https://git-scm.com/download/win" -ForegroundColor Gray
    Write-Host "  2. 下载并安装Git for Windows" -ForegroundColor Gray
    Write-Host "  3. 安装时选择 'Git Bash Here' 和 'Add to PATH'" -ForegroundColor Gray
    Write-Host "  4. 重新打开PowerShell后再次运行此脚本" -ForegroundColor Gray
    exit 1
}

$gitVersion = git --version
Write-Success "Git已安装: $gitVersion"

# ============================================================================
# 第1步：配置Git用户信息
# ============================================================================
Write-Header "步骤1: 配置Git用户信息"

# 检查是否已配置
$currentUser = git config --global user.name 2>$null
$currentEmail = git config --global user.email 2>$null

if ([string]::IsNullOrEmpty($currentUser)) {
    Write-Info "请输入GitHub用户名（用于提交记录）:"
    $gitUser = Read-Host
    if ([string]::IsNullOrWhiteSpace($gitUser)) {
        $gitUser = $GitHubUsername
    }
    git config --global user.name $gitUser
    Write-Success "已设置用户名: $gitUser"
} else {
    Write-Success "用户名已配置: $currentUser"
}

if ([string]::IsNullOrEmpty($currentEmail)) {
    Write-Info "请输入GitHub邮箱:"
    $gitEmail = Read-Host
    if ([string]::IsNullOrWhiteSpace($gitEmail)) {
        $gitEmail = "$GitHubUsername@users.noreply.github.com"
    }
    git config --global user.email $gitEmail
    Write-Success "已设置邮箱: $gitEmail"
} else {
    Write-Success "邮箱已配置: $currentEmail"
}

# ============================================================================
# 第2步：初始化Git仓库
# ============================================================================
Write-Header "步骤2: 初始化Git仓库"

Set-Location $RepoRoot

# 检查是否已是Git仓库
if (Test-Path ".git") {
    Write-Info "已是Git仓库，跳过初始化"
} else {
    Write-Info "初始化Git仓库..."
    git init
    Write-Success "Git仓库初始化完成"
}

# ============================================================================
# 第3步：创建.gitignore文件
# ============================================================================
Write-Header "步骤3: 配置.gitignore"

$gitignoreContent = @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/
.venv/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# PyQt
*.pyc
*.pyo

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# Data
data/

# OS
.DS_Store
Thumbs.db

# Test
.pytest_cache/
.coverage
htmlcov/

# Confidential
*.conf
secrets.json
"@

if (-not (Test-Path ".gitignore")) {
    Set-Content -Path ".gitignore" -Value $gitignoreContent -Encoding UTF8
    Write-Success ".gitignore已创建"
} else {
    Write-Info ".gitignore已存在"
}

# ============================================================================
# 第4步：创建LICENSE文件
# ============================================================================
Write-Header "步骤4: 创建LICENSE文件"

if (-not (Test-Path "LICENSE")) {
    $licenseContent = @"
MIT License

Copyright (c) 2026 Market Task Tracker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"@
    Set-Content -Path "LICENSE" -Value $licenseContent -Encoding UTF8
    Write-Success "LICENSE (MIT) 已创建"
}

# ============================================================================
# 第5步：创建README.md
# ============================================================================
Write-Header "步骤5: 创建README.md"

$readmeContent = @"
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

## 项目结构

\`\`\`
market_task_tracker/
├── src/
│   ├── main.py              # 程序入口
│   ├── config.py             # 配置管理
│   ├── database/             # 数据库层
│   ├── ui/                   # 界面层
│   └── utils/                # 工具层
├── tests/                    # 测试
├── scripts/                  # 脚本
├── data/                     # 数据目录
└── logs/                     # 日志目录
\`\`\`

## 快速开始

### 安装依赖

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 运行应用

\`\`\`bash
python src/main.py
\`\`\`

### 运行测试

\`\`\`bash
pytest src/tests/ -v
\`\`\`

## CI/CD

本项目使用GitHub Actions进行持续集成：

- ✅ 代码质量检查 (Pylint)
- ✅ 单元测试 (pytest)
- ✅ 数据库测试
- ✅ 应用启动测试

## 开发计划

| 阶段 | 任务 | 状态 |
|------|------|------|
| 阶段一 | 基础设施搭建 | ✅ 完成 |
| 阶段二 | 核心功能开发 | 🔄 开发中 |
| 阶段三 | 高级功能 | 📋 待开始 |
| 阶段四 | 测试与优化 | 📋 待开始 |
| 阶段五 | 验收与交付 | 📋 待开始 |

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 作者

市场咨询任务跟踪工具开发团队
"@

Set-Content -Path "README.md" -Value $readmeContent -Encoding UTF8
Write-Success "README.md已创建"

# ============================================================================
# 第6步：提交代码
# ============================================================================
Write-Header "步骤6: 提交代码"

Write-Info "添加所有文件到暂存区..."
git add .
Write-Success "文件已添加到暂存区"

Write-Info "提交代码..."
git commit -m "Phase 1: 基础设施搭建完成

- T-1.1: 环境准备与项目初始化
- T-1.2: 数据库设计与实现
- T-1.3: 主框架搭建与导航结构
- T-1.4: 基础工具类与公共模块

包含:
- GitHub Actions CI/CD配置
- Docker容器化配置
- 完整的项目结构
- 基础单元测试

Milestone: M1 基础框架完成"
Write-Success "代码已提交"

# ============================================================================
# 第7步：推送到GitHub
# ============================================================================
if (-not $SkipPush) {
    Write-Header "步骤7: 推送到GitHub"
    
    $remoteUrl = "https://github.com/$GitHubUsername/$RepositoryName.git"
    
    # 检查远程仓库是否已配置
    $currentRemote = git remote get-url origin 2>$null
    
    if ([string]::IsNullOrEmpty($currentRemote)) {
        Write-Info "添加远程仓库..."
        git remote add origin $remoteUrl
        Write-Success "远程仓库已添加: $remoteUrl"
    } else {
        Write-Info "远程仓库已配置: $currentRemote"
    }
    
    # 如果有Token，使用Token认证
    if (-not [string]::IsNullOrWhiteSpace($GitHubToken)) {
        $tokenUrl = "https://$GitHubToken@github.com/$GitHubUsername/$RepositoryName.git"
        git remote set-url origin $tokenUrl
        Write-Info "已配置Token认证"
    }
    
    Write-Info "推送代码到GitHub..."
    Write-Host ""
    Write-Host "提示: 如果这是第一次推送，可能需要输入GitHub凭据" -ForegroundColor Yellow
    Write-Host "      或使用 Personal Access Token 进行认证" -ForegroundColor Yellow
    Write-Host ""
    
    git branch -M main
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "代码已成功推送到GitHub!"
        Write-Host ""
        Write-Host "📋 下一步操作：" -ForegroundColor Cyan
        Write-Host "  1. 访问 https://github.com/$GitHubUsername/$RepositoryName" -ForegroundColor Gray
        Write-Host "  2. 查看 Actions 标签页，查看CI检查状态" -ForegroundColor Gray
        Write-Host "  3. CI检查通过后，可以创建Pull Request合并" -ForegroundColor Gray
    } else {
        Write-ErrorMsg "推送失败"
        Write-Host ""
        Write-Host "请手动完成以下步骤：" -ForegroundColor Yellow
        Write-Host "  1. 在GitHub上创建仓库: https://github.com/new" -ForegroundColor Gray
        Write-Host "  2. 复制仓库URL" -ForegroundColor Gray
        Write-Host "  3. 运行: git remote add origin YOUR_REPO_URL" -ForegroundColor Gray
        Write-Host "  4. 运行: git push -u origin main" -ForegroundColor Gray
    }
} else {
    Write-Info "跳过推送（使用 -SkipPush 参数）"
    Write-Host ""
    Write-Host "📋 后续步骤：" -ForegroundColor Cyan
    Write-Host "  1. 在GitHub上创建仓库" -ForegroundColor Gray
    Write-Host "  2. 运行: git remote add origin YOUR_REPO_URL" -ForegroundColor Gray
    Write-Host "  3. 运行: git push -u origin main" -ForegroundColor Gray
}

# ============================================================================
# 完成
# ============================================================================
Write-Header "设置完成!"

Write-Host ""
Write-Host "✅ Git仓库已配置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📁 仓库路径: $RepoRoot" -ForegroundColor Cyan
Write-Host ""
