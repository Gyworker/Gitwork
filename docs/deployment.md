# 市场咨询任务跟踪工具 - 部署文档

## 版本信息

| 项目 | 内容 |
|------|------|
| 应用名称 | 市场咨询任务跟踪工具 |
| 版本号 | V1.0 |
| 发布日期 | 2026-06-16 |
| 技术栈 | Python 3.10 + PyQt5 5.15 + SQLite 3 |

---

## 目录

1. [部署概述](#部署概述)
2. [环境要求](#环境要求)
3. [部署步骤](#部署步骤)
4. [配置说明](#配置说明)
5. [验证部署](#验证部署)
6. [常见问题](#常见问题)

---

## 部署概述

本应用为桌面应用，支持单机部署。

### 部署模式

| 模式 | 适用场景 | 说明 |
|------|----------|------|
| 单机部署 | 个人/小团队 | 每个用户本地运行 |
| 网络共享 | 团队协作 | 数据库放在共享位置 |

---

## 环境要求

### 硬件要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 1 GHz | 2 GHz+ |
| 内存 | 2 GB | 4 GB+ |
| 硬盘 | 500 MB | 1 GB+ |
| 显示器 | 1024x768 | 1920x1080 |

### 软件要求

| 项目 | 版本要求 |
|------|----------|
| 操作系统 | Windows 10/11, macOS 10.14+ |
| Python | 3.10 或更高 |
| 其他 | 无特殊要求 |

---

## 部署步骤

### 第一步：准备环境

#### Windows

1. 下载Python 3.10+
   - 官网：https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

2. 验证Python安装
   ```cmd
   python --version
   ```

#### macOS

1. 使用Homebrew安装Python
   ```bash
   brew install python@3.10
   ```

2. 验证Python安装
   ```bash
   python3 --version
   ```

### 第二步：获取应用

#### 方式一：克隆代码仓库

```bash
git clone https://github.com/Gyworker/Gitwork.git
cd Gitwork
```

#### 方式二：下载发布包

1. 访问 GitHub Releases 页面
2. 下载最新版本的压缩包
3. 解压到目标目录

### 第三步：创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 第四步：安装依赖

```bash
pip install -r requirements.txt
```

依赖说明：

| 依赖包 | 版本 | 说明 |
|--------|------|------|
| PyQt5 | >=5.15.0 | GUI框架 |
| pandas | >=2.0.0 | 数据处理 |
| openpyxl | >=3.1.0 | Excel读写 |
| Pillow | >=10.0.0 | 图片处理（OCR） |
| colorlog | >=6.7.0 | 日志彩色输出 |
| PyYAML | >=6.0.1 | 配置文件 |
| pytest | >=7.4.0 | 单元测试 |

### 第五步：运行应用

```bash
python src/main.py
```

---

## 配置说明

### 配置文件位置

- Windows: `%APPDATA%\Gitwork\config.yaml`
- macOS: `~/Library/Application Support/Gitwork/config.yaml`
- Linux: `~/.config/Gitwork/config.yaml`

### 配置项说明

```yaml
# 应用配置
app:
  name: "市场咨询任务跟踪工具"
  version: "1.0"
  language: "zh_CN"

# 数据库配置
database:
  path: "data/gitwork.db"  # 可使用绝对路径
  backup: true
  backup_interval: 86400   # 备份间隔（秒）

# 日志配置
logging:
  level: "INFO"           # DEBUG, INFO, WARNING, ERROR
  file: "logs/app.log"
  max_size: 10485760       # 最大文件大小（字节）
  backup_count: 5          # 备份文件数量

# 界面配置
ui:
  theme: "light"           # light, dark, blue
  window:
    width: 1200
    height: 800
  font:
    family: "Microsoft YaHei"
    size: 10
```

---

## 验证部署

### 启动验证

1. 运行应用
   ```bash
   python src/main.py
   ```

2. 检查输出
   - 无错误信息
   - 窗口正常显示

### 功能验证

| 功能 | 验证方法 |
|------|----------|
| 创建任务 | 新建任务并保存 |
| 查看任务列表 | 列表显示刚创建的任务 |
| 编辑任务 | 修改任务信息并保存 |
| 删除任务 | 删除任务并确认 |
| 数据导出 | 导出为Excel文件 |

### 日志检查

查看日志文件确认无异常：

```bash
# Windows
type %APPDATA%\Gitwork\logs\app.log

# macOS/Linux
cat ~/.config/Gitwork/logs/app.log
```

---

## 数据管理

### 数据备份

#### 手动备份

1. 关闭应用
2. 复制数据库文件到备份位置
   ```bash
   cp data/gitwork.db backup/gitwork_backup_$(date +%Y%m%d).db
   ```

#### 自动备份

在配置文件中启用自动备份：

```yaml
database:
  backup: true
  backup_interval: 86400  # 每天备份
  backup_path: "backup"
```

### 数据恢复

1. 关闭应用
2. 从备份复制数据库文件
   ```bash
   cp backup/gitwork_backup_20260616.db data/gitwork.db
   ```
3. 启动应用

---

## 常见问题

### Q1: 启动报错 "No module named 'PyQt5'"

**原因**: 未安装PyQt5

**解决方法**:
```bash
pip install PyQt5
```

### Q2: 中文显示为方块

**原因**: 系统缺少中文字体

**解决方法**:
- Windows: 安装中文字体
- macOS: 系统默认支持中文
- Linux: 安装字体
  ```bash
  sudo apt install fonts-wqy-microhei
  ```

### Q3: 数据库锁定

**原因**: 多个实例同时访问

**解决方法**:
1. 关闭所有应用实例
2. 确认没有残留进程
3. 重新启动应用

### Q4: 导入Excel失败

**原因**: Excel文件格式问题

**解决方法**:
1. 确保使用标准Excel格式（.xlsx）
2. 检查列标题是否匹配
3. 确认数据格式正确

---

## 卸载

### 卸载步骤

1. 关闭应用
2. 删除应用目录
3. 删除配置和缓存（可选）
   - Windows: `%APPDATA%\Gitwork`
   - macOS: `~/Library/Application Support/Gitwork`
   - Linux: `~/.config/Gitwork`

### 保留数据

如果需要保留数据，只需备份以下文件：
- `data/gitwork.db` - 数据库文件
- `data/*.csv` - 导出的数据文件

---

## 联系支持

- **GitHub**: https://github.com/Gyworker/Gitwork
- **问题反馈**: https://github.com/Gyworker/Gitwork/issues

---

**文档版本**: V1.0  
**最后更新**: 2026-06-16
