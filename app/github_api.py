"""
GitHub API交互模块

该模块负责与GitHub API进行交互，实现仓库管理、文件操作、提交历史等功能。
"""

from github import Github
from github import Auth
from typing import List, Optional, Dict, Any
from app.config import settings
import os


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
        self.github = Github(auth=self.auth, base_url=settings.GITHUB_API_URL, verify=False)
    
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
    
    def list_repos(self, owner: str, per_page: int = 30) -> List[Dict[str, Any]]:
        """
        列出指定所有者的仓库
        
        Args:
            owner: 仓库所有者
            per_page: 每页数量
        
        Returns:
            仓库列表，包含仓库元数据
        """
        print(f"🔍 Listing repos for owner: {owner}")
        
        # 调试：先打印当前认证用户
        current_user = self.github.get_user()
        print(f"   Current authenticated user: {current_user.login}")
        
        # 获取指定所有者的用户对象
        user = self.github.get_user(owner)
        print(f"   Target user: {user.login}")
        
        # 获取仓库列表
        repos = user.get_repos()
        repos.per_page = per_page
        
        # 调试：打印仓库数量
        repo_list = list(repos)
        print(f"   Found {len(repo_list)} repos for {owner}")
        
        # 返回仓库列表
        result = []
        for repo in repo_list:
            repo_info = {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "created_at": repo.created_at.isoformat()
            }
            result.append(repo_info)
            print(f"   - Repo: {repo.full_name}")
        
        return result
    
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
        repo = self.get_repo(owner, repo)
        contents = repo.get_contents(path, ref=ref)
        return contents.decoded_content.decode('utf-8')
    
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
        
        def list_repos(self, owner: str, per_page: int = 30) -> List[Dict[str, Any]]:
            return [{
                "name": "mock-repo",
                "full_name": f"{owner}/mock-repo",
                "description": "Mock repository",
                "url": f"https://github.com/{owner}/mock-repo",
                "stars": 0,
                "forks": 0,
                "created_at": "2023-01-01T00:00:00Z"
            }]
        
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
    
    github_api = MockGitHubAPI()