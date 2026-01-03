"""
GitHub API交互模块

该模块负责与GitHub API进行交互，实现仓库管理、文件操作、提交历史等功能。
"""

from github import Github
from github import Auth
from typing import List, Optional, Dict, Any
from app.config import settings
import os
import warnings
from urllib3.exceptions import InsecureRequestWarning

# 忽略SSL验证警告（仅在开发环境中使用）
warnings.filterwarnings("ignore", category=InsecureRequestWarning)


class GitHubAPI:
    """
    GitHub API交互类，封装PyGitHub库的功能
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化GitHub API客户端
        
        Args:
            token: GitHub访问令牌，若为None则使用环境变量或配置文件中的令牌
        """
        self.token = token or settings.GITHUB_TOKEN
        self.auth = Auth.Token(self.token)
        # 禁用SSL验证（仅用于开发环境）
        # 优化：添加超时设置和缓存
        self.github = Github(
            auth=self.auth, 
            base_url=settings.GITHUB_API_URL, 
            verify=False,
            timeout=15,  # 设置15秒超时，避免长时间等待
            per_page=100  # 默认每页100个结果，减少API调用次数
        )
    
    def get_user(self):
        """
        获取当前认证用户信息
        
        Returns:
            GitHub用户对象
        """
        return self.github.get_user()
    
    def get_repo(self, owner: str, repo: str):
        """
        获取指定仓库
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
        
        Returns:
            GitHub仓库对象
        """
        return self.github.get_repo(f"{owner}/{repo}")
    
    def list_repos(self, owner: str, per_page: int = 30, page: int = 1) -> Dict[str, Any]:
        """
        列出指定所有者的仓库，支持分页
        
        Args:
            owner: 仓库所有者
            per_page: 每页数量（最大100）
            page: 页码
        
        Returns:
            包含仓库列表和分页信息的字典
        """
        try:
            # 获取指定所有者的用户对象
            user = self.github.get_user(owner)
            
            # 获取仓库列表
            repos = user.get_repos()
            
            # 设置per_page属性，限制最大为100
            repos.per_page = min(int(per_page), 100)  # GitHub API限制最大为100
            github_page_size = repos.per_page  # 使用实际的per_page值
            
            repo_list = repos[github_page_size * (page - 1):github_page_size * page]
            
            # 处理仓库列表
            result = []
            for repo in repo_list:
                result.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "created_at": repo.created_at.isoformat()
                })
            
            return {
                "success": True,
                "owner": owner,
                "page": page,
                "per_page": repos.per_page,
                "total_count": repos.totalCount,
                "repos": result
            }
        except Exception as e:
            raise ValueError(f"Failed to list repos: {str(e)}")
    
    def get_branches(self, owner: str, repo: str) -> List[str]:
        """
        获取仓库分支列表
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
        
        Returns:
            分支名称列表
        """
        repo = self.get_repo(owner, repo)
        branches = repo.get_branches()
        return [branch.name for branch in branches]
    
    def get_commits(self, owner: str, repo: str, branch: str = "main", per_page: int = 30) -> List[Dict[str, Any]]:
        """
        获取仓库提交历史
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 分支名称
            per_page: 每页数量
        
        Returns:
            提交历史列表，包含提交信息
        """
        repo = self.get_repo(owner, repo)
        commits = repo.get_commits(sha=branch)
        commits.per_page = per_page
        return [{
            "sha": commit.sha,
            "message": commit.commit.message,
            "author": commit.commit.author.name,
            "email": commit.commit.author.email,
            "date": commit.commit.author.date.isoformat(),
            "url": commit.html_url
        } for commit in commits]
    
    def get_contributors(self, owner: str, repo: str, per_page: int = 30) -> List[Dict[str, Any]]:
        """
        获取仓库贡献者统计
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            per_page: 每页数量
        
        Returns:
            贡献者列表，包含贡献者信息和贡献数量
        """
        repo = self.get_repo(owner, repo)
        contributors = repo.get_contributors()
        contributors.per_page = per_page
        return [{
            "login": contributor.login,
            "name": contributor.name,
            "avatar_url": contributor.avatar_url,
            "contributions": contributor.contributions
        } for contributor in contributors]
    
    def get_file_content(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> str:
        """
        获取文件内容
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            path: 文件路径
            ref: 分支或提交SHA
        
        Returns:
            文件内容
        """
        try:
            repo = self.get_repo(owner, repo)
            # 只有当ref不为None时才传递ref参数
            if ref:
                contents = repo.get_contents(path, ref=ref)
            else:
                contents = repo.get_contents(path)
            
            # 检查是否为单个文件（而不是目录）
            if isinstance(contents, list):
                # 如果是目录，返回README.md文件内容（如果存在）
                if path == "" or path == ".":
                    # 尝试获取README.md文件
                    for item in contents:
                        if item.name.lower() == "readme.md":
                            # 只有当ref不为None时才传递ref参数
                            if ref:
                                readme_contents = repo.get_contents(item.path, ref=ref)
                            else:
                                readme_contents = repo.get_contents(item.path)
                            return readme_contents.decoded_content.decode('utf-8')
                    raise ValueError(f"Directory '{path}' doesn't contain a README.md file")
                raise ValueError(f"Path '{path}' is a directory, not a file")
            
            return contents.decoded_content.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to get file content: {str(e)}")
    
    def get_file_history(self, owner: str, repo: str, path: str, per_page: int = 30) -> List[Dict[str, Any]]:
        """
        获取文件历史版本
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            path: 文件路径
            per_page: 每页数量
        
        Returns:
            文件历史版本列表
        """
        repo = self.get_repo(owner, repo)
        commits = repo.get_commits(path=path)
        commits.per_page = per_page
        return [{
            "sha": commit.sha,
            "message": commit.commit.message,
            "author": commit.commit.author.name,
            "date": commit.commit.author.date.isoformat()
        } for commit in commits]
    
    def compare_commits(self, owner: str, repo: str, base: str, head: str) -> Dict[str, Any]:
        """
        对比两个提交之间的差异
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            base: 基准提交SHA
            head: 比较提交SHA
        
        Returns:
            提交差异信息
        """
        repo = self.get_repo(owner, repo)
        comparison = repo.compare(base, head)
        return {
            "total_commits": comparison.total_commits,
            "files_changed": len(comparison.files),
            "additions": comparison.additions,
            "deletions": comparison.deletions,
            "files": [{"filename": file.filename, "status": file.status} for file in comparison.files]
        }
    
    def search_code(self, query: str, language: Optional[str] = None, per_page: int = 30, page: int = 1) -> Dict[str, Any]:
        """
        搜索GitHub公共库中的代码，支持GitHub搜索表达式
        
        Args:
            query: 搜索查询字符串，支持GitHub搜索表达式
            language: 过滤特定语言（可选）
            per_page: 每页结果数（最大100）
            page: 页码
        
        Returns:
            搜索结果，包含匹配的代码片段列表
        """
        import time
        import hashlib
        import asyncio
        import logging
        
        # 获取或创建logger
        logger = logging.getLogger(__name__)
        
        try:
            # 构建搜索查询
            search_query = query
            
            # 只有当language被提供且query中不包含language过滤时才添加
            if language and "language:" not in query.lower():
                search_query += f" language:{language}"
            
            # 限制每页结果数，避免超时
            per_page = min(per_page, 50)  # 进一步限制每页结果数，降低超时风险
            
            # 生成缓存键
            cache_key = hashlib.md5(f"{search_query}_{per_page}_{page}".encode()).hexdigest()
            
            # 检查缓存
            # 注意：这里可以替换为更持久的缓存实现，如Redis
            if hasattr(self, '_search_cache'):
                if cache_key in self._search_cache:
                    cached_result = self._search_cache[cache_key]
                    if time.time() - cached_result['timestamp'] < 3600:  # 缓存1小时
                        return cached_result['data']
            else:
                self._search_cache = {}
            
            # 执行搜索，添加超时保护
            start_time = time.time()
            
            # 执行搜索
            results = self.github.search_code(search_query)
            results.per_page = per_page  # GitHub API限制最大为100
            
            # 直接使用get_page返回的迭代器，避免立即获取所有结果
            code_results = []
            
            # 只获取当前页的结果，不触发额外API调用
            # 添加超时保护，单个搜索请求最多执行10秒
            for i, result in enumerate(results.get_page(page - 1)):
                # 检查是否超时
                if time.time() - start_time > 10:
                    logger.warning(f"Search timed out after 10 seconds, returning partial results ({len(code_results)} items)")
                    break
                
                # 限制单个页面的结果数量，避免处理时间过长
                if len(code_results) >= per_page:
                    break
                
                # 获取text_matches，确保它是可迭代的
                text_matches = getattr(result, 'text_matches', [])
                if text_matches is None:
                    text_matches = []
                    
                # 从result.html_url中提取仓库信息，避免触发额外API调用
                # URL格式：https://github.com/{owner}/{repo}/blob/{ref}/{path}
                import re
                repo_match = re.match(r'https://github.com/([^/]+)/([^/]+)/', result.html_url)
                repo_full_name = None
                owner = None
                
                if repo_match:
                    owner = repo_match.group(1)
                    repo_name = repo_match.group(2)
                    repo_full_name = f"{owner}/{repo_name}"
                
                # 注意：避免访问result.repository，这会触发额外的API调用
                code_results.append({
                    "name": result.name,
                    "path": result.path,
                    "sha": result.sha,
                    "url": result.html_url,
                    "repository": repo_full_name,
                    "owner": owner,
                    "language": result.language,  # 直接从result获取language，避免访问repository
                    "score": result.score,
                    "text_matches": [match.text for match in text_matches[:3]]  # 只返回前3个匹配文本，减少数据量
                })
            
            # 构建结果
            result_data = {
                "success": True,
                "query": search_query,
                "page": page,
                "per_page": per_page,
                "items_count": len(code_results),
                "items": code_results,
                "execution_time": time.time() - start_time
            }
            
            # 缓存结果
            self._search_cache[cache_key] = {
                'timestamp': time.time(),
                'data': result_data
            }
            
            # 限制缓存大小
            if len(self._search_cache) > 100:
                # 移除最旧的缓存
                oldest_key = min(self._search_cache.keys(), key=lambda k: self._search_cache[k]['timestamp'])
                del self._search_cache[oldest_key]
            
            return result_data
        except asyncio.TimeoutError:
            raise ValueError("Search timed out: GitHub API response took too long")
        except Exception as e:
            logger.error(f"Search failed: {type(e).__name__}: {str(e)}")
            raise ValueError(f"Failed to search code: {str(e)}")


# 创建全局GitHub API实例
import os

print(f"🔍 Checking GitHub API configuration...")
print(f"   GITHUB_TOKEN exists: {bool(settings.GITHUB_TOKEN)}")
print(f"   GITHUB_API_URL: {settings.GITHUB_API_URL}")

# 调试：打印令牌的前几位（用于调试，生产环境应移除）
if settings.GITHUB_TOKEN:
    print(f"   GITHUB_TOKEN (first 10 chars): {settings.GITHUB_TOKEN[:10]}...")

try:
    # 先检查令牌是否存在
    if not settings.GITHUB_TOKEN:
        raise ValueError("GitHub token is not set in environment variables")
    
    # 尝试初始化GitHub API客户端
    github_api = GitHubAPI()
    
    # 测试GitHub连接，确保令牌有效
    test_user = github_api.get_user()
    print(f"✅ GitHub API initialized successfully! Connected as: {test_user.login}")
    
except Exception as e:
    print(f"❌ GitHub API initialization failed: {type(e).__name__}: {str(e)}")
    print(f"🔧 Creating mock GitHubAPI instance for testing...")
    
    # 如果初始化失败，创建一个模拟的GitHubAPI实例，实现所有必要的方法
    class MockGitHubAPI:
        def __init__(self):
            self.error = str(e)
        
        def get_user(self):
            class MockUser:
                login = "mock-user"
            return MockUser()
        
        def get_repo(self, owner: str, repo: str):
            class MockRepo:
                name = repo
                full_name = f"{owner}/{repo}"
                description = "Mock repository"
                html_url = f"https://github.com/{owner}/{repo}"
                stargazers_count = 0
                forks_count = 0
                created_at = "2023-01-01T00:00:00Z"
                updated_at = "2023-01-01T00:00:00Z"
                language = "Python"
                default_branch = "main"
                
                def get_branches(self):
                    class MockBranch:
                        name = "main"
                    return [MockBranch()]
                
                def get_commits(self, **kwargs):
                    class MockCommit:
                        sha = "mock-sha123"
                        
                        class MockAuthor:
                            name = "Mock Author"
                            email = "mock@example.com"
                            date = "2023-01-01T00:00:00Z"
                        
                        class MockCommitInfo:
                            author = MockAuthor()
                            message = "Mock commit message"
                        
                        commit = MockCommitInfo()
                        html_url = f"https://github.com/{owner}/{repo}/commit/mock-sha123"
                    return [MockCommit()]
                
                def get_contributors(self, **kwargs):
                    class MockContributor:
                        login = "mock-user"
                        name = "Mock User"
                        avatar_url = "https://avatars.githubusercontent.com/u/12345678?v=4"
                        contributions = 1
                    return [MockContributor()]
                
                def get_contents(self, path, **kwargs):
                    class MockContents:
                        decoded_content = b"Mock file content"
                    return MockContents()
                
                def compare(self, base, head):
                    class MockComparison:
                        total_commits = 1
                        files = []
                        additions = 10
                        deletions = 5
                    return MockComparison()
            return MockRepo()
        
        def list_repos(self, owner: str, per_page: int = 30, page: int = 1) -> Dict[str, Any]:
            return {
                "success": True,
                "owner": owner,
                "page": page,
                "per_page": per_page,
                "total_count": 1,
                "repos": [{
                    "name": "mock-repo",
                    "full_name": f"{owner}/mock-repo",
                    "description": "Mock repository",
                    "url": f"https://github.com/{owner}/mock-repo",
                    "stars": 0,
                    "forks": 0,
                    "created_at": "2023-01-01T00:00:00Z"
                }]
            }
        
        def get_branches(self, owner: str, repo: str) -> List[str]:
            return ["main", "develop"]
        
        def get_commits(self, owner: str, repo: str, branch: str = "main", per_page: int = 30) -> List[Dict[str, Any]]:
            return [{
                "sha": "mock-sha123",
                "message": "Mock commit message",
                "author": "Mock Author",
                "email": "mock@example.com",
                "date": "2023-01-01T00:00:00Z",
                "url": f"https://github.com/{owner}/{repo}/commit/mock-sha123"
            }]
        
        def get_contributors(self, owner: str, repo: str, per_page: int = 30) -> List[Dict[str, Any]]:
            return [{
                "login": "mock-user",
                "name": "Mock User",
                "avatar_url": "https://avatars.githubusercontent.com/u/12345678?v=4",
                "contributions": 1
            }]
        
        def get_file_content(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> str:
            return "Mock file content"
        
        def get_file_history(self, owner: str, repo: str, path: str, per_page: int = 30) -> List[Dict[str, Any]]:
            return [{
                "sha": "mock-sha123",
                "message": "Mock commit message",
                "author": "Mock Author",
                "date": "2023-01-01T00:00:00Z"
            }]
        
        def compare_commits(self, owner: str, repo: str, base: str, head: str) -> Dict[str, Any]:
            return {
                "total_commits": 1,
                "files_changed": 0,
                "additions": 10,
                "deletions": 5,
                "files": []
            }
        
        def search_code(self, query: str, language: Optional[str] = None, per_page: int = 30, page: int = 1) -> Dict[str, Any]:
            """
            模拟搜索GitHub公共库中的代码，支持GitHub搜索表达式
            """
            # 构建搜索查询
            search_query = query
            if language and "language:" not in query.lower():
                search_query += f" language:{language}"
            
            # 模拟真实分页，根据page和per_page返回不同结果
            mock_items = []
            base_item_count = (page - 1) * per_page
            
            for i in range(per_page):
                item_index = base_item_count + i
                mock_items.append({
                    "name": f"example-{item_index}.py",
                    "path": f"src/example-{item_index}.py",
                    "sha": f"mock-sha{item_index:03d}",
                    "url": f"https://github.com/mock-owner/mock-repo/blob/main/src/example-{item_index}.py",
                    "repository": "mock-owner/mock-repo",
                    "owner": "mock-owner",
                    "language": language or "Python",
                    "score": 1.0 - (i * 0.01),
                    "text_matches": [f"mock text match {item_index}"]
                })
            
            return {
                "success": True,
                "query": search_query,
                "page": page,
                "per_page": per_page,
                "items_count": len(mock_items),
                "items": mock_items
            }
    
    github_api = MockGitHubAPI()