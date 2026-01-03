# MCP (Mod Control Panel) 服务器与 GitHub 集成

一个功能全面的 MCP 服务器应用，集成了 GitHub 功能，提供仓库管理、版本控制和代码搜索等工具。

## 功能特性

### GitHub 集成
- GitHub API 访问的 OAuth 2.0 认证
- 仓库元数据检索（仓库、分支、提交、贡献者）
- 文件内容和历史访问
- 提交比较功能

### 版本控制
- Git 仓库克隆和管理
- 分支创建、检出和管理
- 本地和远程分支同步
- 提交和推送操作
- 仓库状态监控

### 代码搜索
- 支持大小写敏感选项的关键词搜索
- 代码片段匹配
- 正则表达式支持
- 文件类型过滤
- 文件结构可视化

### 安全特性
- OAuth 2.0 资源服务器功能
- JWT 令牌验证
- 路径遍历防护
- API 请求速率限制
- 操作日志和审计跟踪
- 输入验证和清理

## 架构设计

应用采用模块化架构，清晰分离关注点：

```
app/
├── main.py          # MCP 服务器入口点和工具/资源定义
├── config.py        # Pydantic 设置管理
├── github_api.py    # 使用 PyGitHub 的 GitHub API 交互
├── vcs.py           # 使用 GitPython 的本地 Git 操作
├── code_search.py   # 代码搜索功能
├── auth.py          # 认证和授权工具
└── utils.py         # 通用工具（缓存、速率限制等）
```

## 快速开始

### 前提条件

- Python 3.10+
- Git
- GitHub 个人访问令牌（用于 GitHub API 访问）

### 安装步骤

1. 克隆仓库：

   ```bash
   git clone https://github.com/tiub/mcp_servers.git
   cd mcp_servers
   ```

2. 创建虚拟环境并安装依赖：

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows 系统：venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. 配置环境变量：

   在项目根目录创建 `.env` 文件，内容如下：

   ```env
   # 服务器配置
   HOST=0.0.0.0
   PORT=8000
   LOG_LEVEL=INFO
   
   # GitHub 配置
   GITHUB_TOKEN=your_github_token_here
   GITHUB_API_URL=https://api.github.com
   
   # 本地仓库设置
   LOCAL_REPO_DIR=./repos
   
   # JWT 配置
   JWT_SECRET_KEY=your_jwt_secret_key_here
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
   ```

### 运行服务器

```bash
python -m app.main
```

服务器默认将在 `http://localhost:8000` 启动，使用 streamable HTTP 传输。

## 使用说明

### MCP 工具

服务器提供以下工具：

#### GitHub 工具
- `get_github_repos`: 列出 GitHub 用户/组织的仓库
- `get_github_repo_info`: 获取仓库详细信息
- `get_github_branches`: 列出仓库分支
- `get_github_commits`: 获取分支的提交历史
- `get_github_contributors`: 列出仓库贡献者
- `get_github_file_content`: 获取仓库中文件的内容
- `get_github_file_history`: 获取文件的历史
- `compare_github_commits`: 比较两个提交

#### 版本控制工具
- `clone_repository`: 将远程仓库克隆到本地
- `checkout_branch`: 切换或创建分支
- `commit_changes`: 提交本地修改
- `push_changes`: 将修改推送到远程仓库
- `get_local_branches`: 列出本地分支
- `get_remote_branches`: 列出远程分支
- `get_repo_status`: 获取仓库状态

#### 代码搜索工具
- `search_code`: 在仓库中搜索关键词
- `search_code_snippet`: 搜索代码片段
- `search_by_regex`: 使用正则表达式搜索
- `get_repo_file_structure`: 获取仓库文件结构

### MCP 资源

- `github://repos/{owner}`: 获取 GitHub 用户/组织的仓库列表
- `github://repo/{owner}/{repo}`: 获取仓库详细信息
- `github://file/{owner}/{repo}/{path}`: 获取仓库中的文件内容

## 安全考虑

1. **令牌安全**：始终保持 GitHub 令牌和 JWT 密钥安全。切勿将它们提交到版本控制。

2. **速率限制**：服务器实现了速率限制以防止滥用。根据需要调整 `config.py` 中的 `RATE_LIMIT_CAPACITY` 和 `RATE_LIMIT_REFILL_RATE`。

3. **路径验证**：服务器验证所有文件路径，防止路径遍历攻击。

4. **操作日志**：所有关键操作都记录了用户信息，用于审计目的。

5. **输入清理**：所有用户输入都经过清理，防止注入攻击。

## 配置选项

应用使用 Pydantic 设置管理，支持环境变量。配置选项在 `app/config.py` 中定义：

- `HOST`: 服务器主机地址
- `PORT`: 服务器端口
- `LOG_LEVEL`: 日志级别（DEBUG, INFO, WARNING, ERROR）
- `GITHUB_TOKEN`: GitHub 个人访问令牌
- `GITHUB_API_URL`: GitHub API 基础 URL
- `LOCAL_REPO_DIR`: 存储本地仓库的目录
- `JWT_SECRET_KEY`: JWT 令牌验证的密钥
- `JWT_ALGORITHM`: 用于 JWT 令牌的算法
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: JWT 令牌过期时间

## 测试

使用 pytest 运行测试套件：

```bash
python -m pytest
```

测试套件包括：
- GitHub API 交互测试
- 版本控制操作测试
- 工具函数测试
- 安全机制测试

## 贡献指南

欢迎贡献！请遵循以下指南：

1. Fork 仓库
2. 创建特性分支
3. 实现你的更改
4. 为你的更改添加测试
5. 运行测试套件，确保所有测试通过
6. 提交拉取请求

## 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 致谢

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) - 用于服务器-客户端通信的协议
- [PyGitHub](https://pygithub.readthedocs.io/) - Python 的 GitHub API 客户端
- [GitPython](https://gitpython.readthedocs.io/) - Python 的 Git 包装器
- [FastMCP](https://modelcontextprotocol.io/sdk/python) - MCP 服务器实现
- [Pydantic](https://pydantic.dev/) - 数据验证和设置管理
- [Python-jose](https://python-jose.readthedocs.io/) - Python 的 JWT 实现

## 支持

如有问题、疑问或功能请求，请在 [GitHub 仓库](https://github.com/tiub/mcp_servers/issues) 上打开问题。
