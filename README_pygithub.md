# PyGithub 学习指南

本指南将帮助你学习和使用 PyGithub 库与 GitHub API 进行交互。

## 目录

- [1. 环境准备](#1-环境准备)
- [2. 获取 GitHub 个人访问令牌](#2-获取-github-个人访问令牌)
- [3. 运行 Demo 脚本](#3-运行-demo-脚本)
- [4. 安全最佳实践](#4-安全最佳实践)
- [5. 常用操作指南](#5-常用操作指南)
- [6. 进一步学习资源](#6-进一步学习资源)

## 1. 环境准备

### 安装 PyGithub 库

使用 pip 安装 PyGithub 库：

```bash
pip install PyGithub
```

### 验证安装

```bash
python -c "from github import Github; print('PyGithub 安装成功')"
```

## 2. 获取 GitHub 个人访问令牌

PyGithub 需要 GitHub 个人访问令牌来与 GitHub API 进行交互。按照以下步骤获取令牌：

### 2.1 登录 GitHub

首先登录你的 GitHub 账号。

### 2.2 进入令牌设置页面

访问以下链接进入令牌设置页面：

**[GitHub 令牌设置](https://github.com/settings/tokens)**

或者通过以下路径导航：
1. 点击右上角头像 → **Settings**
2. 在左侧菜单中选择 **Developer settings**
3. 选择 **Personal access tokens** → **Tokens (classic)**
4. 点击 **Generate new token** → **Generate new token (classic)**

### 2.3 设置令牌权限

1. 输入令牌描述（例如："PyGithub Demo"）
2. 设置令牌过期时间（根据你的需求选择）
3. 选择需要的权限（scope）：

   **建议选择的权限：**
   - `repo` - 完整的仓库访问权限（如果你需要操作仓库）
   - `user` - 读取用户信息
   - `gist` - 如果你需要操作 Gist

   **注意：** 只选择你实际需要的权限，遵循最小权限原则。

### 2.4 生成并保存令牌

1. 点击 **Generate token** 按钮
2. 复制生成的令牌（**非常重要**）
3. **立即保存**这个令牌，因为你以后无法再次查看它

## 3. 运行 Demo 脚本

### 3.1 配置 Demo 脚本

1. 打开 `pygithub_demo.py` 文件
2. 找到以下行：

   ```python
   GITHUB_TOKEN = "your_github_token_here"
   ```

3. 将 `your_github_token_here` 替换为你刚刚获取的 GitHub 个人访问令牌

### 3.2 修改仓库名称

找到以下行，将 `your-repo-name` 替换为你自己的仓库名称：

```python
repo_name = f"{user.login}/your-repo-name"
```

### 3.3 运行脚本

```bash
python pygithub_demo.py
```

### 3.4 查看结果

脚本将输出各种 GitHub 操作的结果，包括：
- 身份验证状态
- 用户信息
- 仓库列表
- Issue 列表
- 文件内容

## 4. 安全最佳实践

### 4.1 不要硬编码令牌

在生产环境中，不要将令牌硬编码到代码中。建议使用：

1. **环境变量**：
   ```python
   import os
   GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
   ```

2. **配置文件**：
   ```python
   import configparser
   config = configparser.ConfigParser()
   config.read('config.ini')
   GITHUB_TOKEN = config['github']['token']
   ```

3. **密钥管理服务**：如 AWS Secrets Manager、HashiCorp Vault 等

### 4.2 遵循最小权限原则

只给令牌授予实际需要的权限，不要授予不必要的权限。

### 4.3 定期轮换令牌

定期生成新令牌，废弃旧令牌，特别是当令牌可能被泄露时。

### 4.4 不要将令牌提交到版本控制系统

确保将包含令牌的文件添加到 `.gitignore` 中，避免将令牌提交到 GitHub。

## 5. 常用操作指南

### 5.1 创建仓库

```python
# 创建公开仓库
repo = user.create_repo(
    name="new-repo",
    description="This is a new repository",
    private=False,
    auto_init=True
)

# 创建私有仓库
repo = user.create_repo(
    name="private-repo",
    description="This is a private repository",
    private=True
)
```

### 5.2 管理 Issue

```python
# 创建 Issue
issue = repo.create_issue(
    title="Bug Report",
    body="This is a bug report",
    labels=["bug"]
)

# 关闭 Issue
issue.edit(state="closed")
```

### 5.3 管理 Pull Request

```python
# 获取 PR
pr = repo.get_pull(1)

# 合并 PR
pr.merge()
```

### 5.4 文件操作

```python
# 创建文件
repo.create_file(
    path="test.txt",
    message="Create test file",
    content="Hello, PyGithub!"
)

# 更新文件
contents = repo.get_contents("test.txt")
repo.update_file(
    path="test.txt",
    message="Update test file",
    content="Updated content",
    sha=contents.sha
)

# 删除文件
contents = repo.get_contents("test.txt")
repo.delete_file(
    path="test.txt",
    message="Delete test file",
    sha=contents.sha
)
```

## 6. 进一步学习资源

### 官方文档

- **PyGithub 文档**：https://pygithub.readthedocs.io/
- **GitHub API 文档**：https://docs.github.com/en/rest

### 教程和示例

- **PyGithub GitHub 仓库**：https://github.com/PyGithub/PyGithub
- **GitHub API 示例**：https://docs.github.com/en/rest/guides

### 视频教程

- YouTube 上搜索 "PyGithub tutorial"
- Bilibili 上搜索 "PyGithub 教程"

## 7. 常见问题

### Q: 为什么获取不到仓库信息？
A: 请检查：
1. 令牌是否具有 `repo` 权限
2. 仓库名称是否正确
3. 你是否有访问该仓库的权限

### Q: 为什么创建 Issue 失败？
A: 请检查：
1. 令牌是否具有 `repo` 权限
2. 仓库是否存在
3. 你是否有创建 Issue 的权限

### Q: 为什么脚本运行很慢？
A: GitHub API 有速率限制，免费用户每小时最多 60 个请求。你可以通过以下方式查看剩余请求数：

```python
from github import Github

GITHUB_TOKEN = "your_token_here"
g = Github(GITHUB_TOKEN)

# 查看速率限制
rate_limit = g.get_rate_limit()
print(f"剩余请求数: {rate_limit.core.remaining}")
print(f"重置时间: {rate_limit.core.reset}")
```

### Q: 如何处理分页？
A: PyGithub 自动处理分页，你可以直接使用列表推导式或循环：

```python
# 获取所有仓库（自动处理分页）
repos = list(user.get_repos())

# 或者使用循环
for repo in user.get_repos():
    print(repo.name)
```

## 结语

PyGithub 是一个强大的库，可以帮助你自动化各种 GitHub 操作。通过本指南的学习，你应该已经掌握了基本的使用方法。

建议你先运行 Demo 脚本，然后根据自己的需求修改和扩展功能。

祝你学习愉快！
