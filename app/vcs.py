"""
版本控制模块

该模块负责处理Git仓库的本地操作，包括克隆、分支切换、提交和推送等功能。
"""

import os
import re
import shutil
from typing import Optional, List, Dict, Any
from git import Repo, GitCommandError
from app.config import settings
import logging

# 配置日志记录
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class VCSManager:
    """
    版本控制管理器，负责处理Git仓库的本地操作
    """
    
    def __init__(self):
        """
        初始化版本控制管理器
        """
        self.local_repo_dir = settings.LOCAL_REPO_DIR
        # 确保本地仓库目录存在
        os.makedirs(self.local_repo_dir, exist_ok=True)
    
    def _validate_path(self, path: str) -> bool:
        """
        验证路径是否安全，防止路径遍历攻击
        
        Args:
            path: 要验证的路径
        
        Returns:
            bool: 路径是否安全
        """
        # 规范化路径
        normalized_path = os.path.normpath(path)
        
        # 检查路径是否包含不安全的组件
        if '..' in normalized_path.split(os.sep):
            return False
        
        # 检查路径是否在允许的目录范围内
        allowed_dir = os.path.abspath(self.local_repo_dir)
        full_path = os.path.abspath(os.path.join(allowed_dir, normalized_path))
        
        return full_path.startswith(allowed_dir)
    
    def _get_repo_path(self, owner: str, repo: str) -> str:
        """
        获取本地仓库路径
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
        
        Returns:
            str: 本地仓库路径
        """
        return os.path.join(self.local_repo_dir, f"{owner}_{repo}")
    
    def clone_repo(self, url: str, owner: str, repo: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """
        克隆远程仓库到本地
        
        Args:
            url: 远程仓库URL
            owner: 仓库所有者
            repo: 仓库名称
            branch: 要克隆的分支，默认为仓库默认分支
        
        Returns:
            Dict[str, Any]: 克隆结果
        """
        repo_path = self._get_repo_path(owner, repo)
        
        # 检查路径是否安全
        if not self._validate_path(os.path.basename(repo_path)):
            raise ValueError("Invalid path for repository")
        
        # 验证URL格式
        if not url or not isinstance(url, str):
            logger.error(f"Invalid URL format: {url}")
            return {
                "success": False,
                "message": f"Invalid URL format: {url}"
            }
        
        # 清理URL中的特殊字符
        url = url.strip()
        # 移除可能存在的反引号
        url = url.replace('`', '')
        # 移除可能存在的引号
        url = url.replace('"', '').replace("'", "")
        
        # 如果URL不完整，尝试构建完整的URL
        # 检查URL是否已经包含完整的owner/repo路径
        expected_full_url = f"https://github.com/{owner}/{repo}"
        if expected_full_url in url:
            # URL已经包含完整的owner/repo路径，只需确保有.git后缀
            if not url.endswith(".git"):
                url = f"{url}.git"
        # 1. 如果URL只是GitHub的根URL，添加owner和repo
        elif url == "https://github.com/" or url == "https://github.com":
            url = f"https://github.com/{owner}/{repo}.git"
        # 2. 如果URL以/结尾，检查是否已经包含owner
        elif url.endswith("/"):
            if f"/{owner}/" in url or url == f"https://github.com/{owner}/":
                # URL已经包含owner，只需添加repo
                url = f"{url}{repo}.git"
            else:
                # URL不包含owner，添加owner和repo
                url = f"{url}{owner}/{repo}.git"
        # 3. 如果URL已经包含owner但缺少repo，添加repo
        elif f"/{owner}" in url and url.count("/") == 3:
            # URL格式类似 https://github.com/owner
            url = f"{url}/{repo}.git"
        # 4. 如果URL是完整的GitHub仓库URL但缺少.git后缀，添加后缀
        elif "github.com" in url and not url.endswith(".git"):
            url = f"{url}.git"
        
        try:
            # 如果仓库已存在，先删除
            if os.path.exists(repo_path):
                # 使用更健壮的方式删除目录，处理权限问题
                try:
                    shutil.rmtree(repo_path, ignore_errors=True)
                    # 检查是否删除成功
                    if os.path.exists(repo_path):
                        # 尝试使用不同的方法删除
                        import subprocess
                        if os.name == 'nt':  # Windows
                            subprocess.run(['rmdir', '/s', '/q', repo_path], shell=True, check=True, capture_output=True)
                        else:  # Linux/Mac
                            subprocess.run(['rm', '-rf', repo_path], shell=True, check=True, capture_output=True)
                except Exception as e:
                    logger.error(f"Failed to delete existing repository: {e}")
                    return {
                        "success": False,
                        "message": f"Failed to delete existing repository: {str(e)}",
                        "details": {
                            "repo_path": repo_path
                        }
                    }
            
            # 克隆仓库
            clone_options = {}
            if branch:
                clone_options['branch'] = branch
            
            repo = Repo.clone_from(url, repo_path, **clone_options)
            
            logger.info(f"Repository cloned successfully: {url} to {repo_path}")
            
            return {
                "success": True,
                "message": f"Repository cloned successfully",
                "repo_path": repo_path,
                "branch": branch or repo.active_branch.name
            }
        except GitCommandError as e:
            logger.error(f"Failed to clone repository: {e}")
            return {
                "success": False,
                "message": f"Failed to clone repository: {str(e)}",
                "details": {
                    "url": url,
                    "owner": owner,
                    "repo": repo,
                    "branch": branch
                }
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete existing repository using subprocess: {e}")
            return {
                "success": False,
                "message": f"Failed to delete existing repository: {str(e)}",
                "details": {
                    "repo_path": repo_path,
                    "output": e.stdout.decode() if e.stdout else "",
                    "error": e.stderr.decode() if e.stderr else ""
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error while cloning repository: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
                "details": {
                    "url": url,
                    "owner": owner,
                    "repo": repo,
                    "branch": branch
                }
            }
    
    def checkout_branch(self, owner: str, repo: str, branch: str, create: bool = False) -> Dict[str, Any]:
        """
        切换分支
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 要切换的分支
            create: 是否创建新分支
        
        Returns:
            Dict[str, Any]: 切换结果
        """
        repo_path = self._get_repo_path(owner, repo)
        
        # 检查路径是否安全
        if not self._validate_path(os.path.basename(repo_path)):
            raise ValueError("Invalid path for repository")
        
        try:
            repo = Repo(repo_path)
            
            if create:
                # 创建并切换分支
                repo.git.checkout('-b', branch)
            else:
                # 切换到现有分支
                repo.git.checkout(branch)
            
            logger.info(f"Switched to branch {branch} in {repo_path}")
            
            return {
                "success": True,
                "message": f"Switched to branch {branch}",
                "current_branch": branch
            }
        except GitCommandError as e:
            logger.error(f"Failed to checkout branch: {e}")
            return {
                "success": False,
                "message": f"Failed to checkout branch: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error while checking out branch: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }
    
    def commit_changes(self, owner: str, repo: str, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        提交本地修改
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            message: 提交信息
            files: 要提交的文件列表，默认为所有修改的文件
        
        Returns:
            Dict[str, Any]: 提交结果
        """
        # 验证提交信息
        if not message or len(message.strip()) < 3:
            return {
                "success": False,
                "message": "Commit message must be at least 3 characters long"
            }
        
        repo_path = self._get_repo_path(owner, repo)
        
        # 检查路径是否安全
        if not self._validate_path(os.path.basename(repo_path)):
            raise ValueError("Invalid path for repository")
        
        try:
            repo = Repo(repo_path)
            
            # 检查是否有未跟踪的文件需要添加
            untracked_files = repo.untracked_files
            if untracked_files:
                if files:
                    # 只添加指定的未跟踪文件
                    for file in files:
                        if file in untracked_files:
                            repo.git.add(file)
                else:
                    # 添加所有未跟踪文件
                    repo.git.add(A=True)
            
            # 提交修改
            if files:
                # 只提交指定文件
                repo.git.commit('-m', message, *files)
            else:
                # 提交所有修改
                repo.git.commit('-m', message, '-a')
            
            logger.info(f"Changes committed successfully in {repo_path}: {message}")
            
            # 获取最新提交信息
            latest_commit = repo.head.commit
            
            return {
                "success": True,
                "message": f"Changes committed successfully",
                "commit_sha": latest_commit.hexsha,
                "commit_message": latest_commit.message.strip(),
                "author": latest_commit.author.name,
                "date": latest_commit.authored_datetime.isoformat()
            }
        except GitCommandError as e:
            logger.error(f"Failed to commit changes: {e}")
            return {
                "success": False,
                "message": f"Failed to commit changes: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error while committing changes: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }
    
    def push_changes(self, owner: str, repo: str, branch: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """
        推送本地修改到远程仓库
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 要推送的分支，默认为当前分支
            force: 是否强制推送
        
        Returns:
            Dict[str, Any]: 推送结果
        """
        repo_path = self._get_repo_path(owner, repo)
        
        # 检查路径是否安全
        if not self._validate_path(os.path.basename(repo_path)):
            raise ValueError("Invalid path for repository")
        
        try:
            repo = Repo(repo_path)
            
            # 获取要推送的分支
            push_branch = branch or repo.active_branch.name
            
            # 推送修改
            push_options = {}
            if force:
                push_options['force'] = True
            
            repo.remotes.origin.push(push_branch, **push_options)
            
            logger.info(f"Changes pushed successfully to {push_branch} in {repo_path}")
            
            return {
                "success": True,
                "message": f"Changes pushed successfully to {push_branch}",
                "branch": push_branch
            }
        except GitCommandError as e:
            logger.error(f"Failed to push changes: {e}")
            return {
                "success": False,
                "message": f"Failed to push changes: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error while pushing changes: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }
    
    def pull_changes(self, owner: str, repo: str, branch: Optional[str] = None, rebase: bool = False) -> Dict[str, Any]:
        """
        从远程仓库拉取更新
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            branch: 要拉取的分支，默认为当前分支
            rebase: 是否使用rebase方式拉取
        
        Returns:
            Dict[str, Any]: 拉取结果
        """
        repo_path = self._get_repo_path(owner, repo)
        
        # 检查路径是否安全
        if not self._validate_path(os.path.basename(repo_path)):
            raise ValueError("Invalid path for repository")
        
        try:
            repo = Repo(repo_path)
            
            # 获取要拉取的分支
            pull_branch = branch or repo.active_branch.name
            
            # 拉取更新
            if rebase:
                repo.remotes.origin.pull(pull_branch, rebase=True)
            else:
                repo.remotes.origin.pull(pull_branch)
            
            logger.info(f"Changes pulled successfully from {pull_branch} in {repo_path}")
            
            return {
                "success": True,
                "message": f"Changes pulled successfully from {pull_branch}",
                "branch": pull_branch
            }
        except GitCommandError as e:
            logger.error(f"Failed to pull changes: {e}")
            return {
                "success": False,
                "message": f"Failed to pull changes: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error while pulling changes: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }
    
    def get_local_branches(self, owner: str, repo: str) -> List[str]:
        """
        获取本地仓库的分支列表
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
        
        Returns:
            List[str]: 分支名称列表
        """
        repo_path = self._get_repo_path(owner, repo)
        
        # 检查路径是否安全
        if not self._validate_path(os.path.basename(repo_path)):
            raise ValueError("Invalid path for repository")
        
        try:
            repo = Repo(repo_path)
            return [branch.name for branch in repo.branches]
        except Exception as e:
            logger.error(f"Failed to get local branches: {e}")
            return []
    
    def get_remote_branches(self, owner: str, repo: str) -> List[str]:
        """
        获取远程仓库的分支列表
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
        
        Returns:
            List[str]: 分支名称列表
        """
        repo_path = self._get_repo_path(owner, repo)
        
        # 检查路径是否安全
        if not self._validate_path(os.path.basename(repo_path)):
            raise ValueError("Invalid path for repository")
        
        try:
            repo = Repo(repo_path)
            return [branch.name.replace('origin/', '') for branch in repo.remotes.origin.refs if branch.name != 'origin/HEAD']
        except Exception as e:
            logger.error(f"Failed to get remote branches: {e}")
            return []
    
    def get_status(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        获取本地仓库状态
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
        
        Returns:
            Dict[str, Any]: 仓库状态信息
        """
        repo_path = self._get_repo_path(owner, repo)
        
        # 检查路径是否安全
        if not self._validate_path(os.path.basename(repo_path)):
            raise ValueError("Invalid path for repository")
        
        try:
            repo = Repo(repo_path)
            status = repo.git.status('--porcelain')
            
            # 解析状态信息
            modified_files = []
            added_files = []
            deleted_files = []
            untracked_files = []
            
            for line in status.split('\n'):
                if not line.strip():
                    continue
                
                status_code = line[:2].strip()
                file_path = line[3:].strip()
                
                if status_code == 'M':
                    modified_files.append(file_path)
                elif status_code == 'A':
                    added_files.append(file_path)
                elif status_code == 'D':
                    deleted_files.append(file_path)
                elif status_code == '??':
                    untracked_files.append(file_path)
            
            return {
                "current_branch": repo.active_branch.name,
                "modified_files": modified_files,
                "added_files": added_files,
                "deleted_files": deleted_files,
                "untracked_files": untracked_files
            }
        except Exception as e:
            logger.error(f"Failed to get repository status: {e}")
            return {}


# 创建全局VCS管理器实例
vcs_manager = VCSManager()