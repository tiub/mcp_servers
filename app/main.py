"""
MCP服务器主入口文件

该文件负责初始化和运行MCP服务器，配置服务器参数和传输方式，
并定义所有可用的工具和资源。
"""

from mcp.server.fastmcp import FastMCP
from app.config import settings
from app.github_api import github_api
from app.vcs import vcs_manager
from app.code_search import code_searcher
from app.auth import token_verifier
from typing import Optional, List, Dict, Any

# 创建MCP服务器实例
mcp = FastMCP(
    name="MCP Server",
    json_response=True,
    stateless_http=True,
    instructions="""
    这是一个基于Model Context Protocol的Mod Control Panel服务器，
    提供与GitHub平台的交互功能，包括仓库管理、文件操作、
    版本控制和代码检索等功能。
    """
    # 注意：token_verifier需要配合auth设置使用，暂时移除
)


# -------------------------- GitHub工具 --------------------------


@mcp.tool()
def get_github_repos(owner: str, per_page: int = 30) -> List[Dict[str, Any]]:
    """
    获取指定所有者的GitHub仓库列表
    
    Args:
        owner: GitHub仓库所有者
        per_page: 每页返回的仓库数量
    
    Returns:
        仓库列表，包含仓库元数据
    """
    return github_api.list_repos(owner, per_page)


@mcp.tool()
def get_github_repo_info(owner: str, repo: str) -> Dict[str, Any]:
    """
    获取指定GitHub仓库的详细信息
    
    Args:
        owner: GitHub仓库所有者
        repo: 仓库名称
    
    Returns:
        仓库详细信息
    """
    repo_obj = github_api.get_repo(owner, repo)
    return {
        "name": repo_obj.name,
        "full_name": repo_obj.full_name,
        "description": repo_obj.description,
        "url": repo_obj.html_url,
        "stars": repo_obj.stargazers_count,
        "forks": repo_obj.forks_count,
        "created_at": repo_obj.created_at.isoformat(),
        "updated_at": repo_obj.updated_at.isoformat(),
        "language": repo_obj.language,
        "default_branch": repo_obj.default_branch
    }


@mcp.tool()
def get_github_branches(owner: str, repo: str) -> List[str]:
    """
    获取指定GitHub仓库的分支列表
    
    Args:
        owner: GitHub仓库所有者
        repo: 仓库名称
    
    Returns:
        分支名称列表
    """
    return github_api.get_branches(owner, repo)


@mcp.tool()
def get_github_commits(owner: str, repo: str, branch: str = "main", per_page: int = 30) -> List[Dict[str, Any]]:
    """
    获取指定GitHub仓库的提交历史
    
    Args:
        owner: GitHub仓库所有者
        repo: 仓库名称
        branch: 分支名称，默认为main
        per_page: 每页返回的提交数量
    
    Returns:
        提交历史列表
    """
    return github_api.get_commits(owner, repo, branch, per_page)


@mcp.tool()
def get_github_contributors(owner: str, repo: str, per_page: int = 30) -> List[Dict[str, Any]]:
    """
    获取指定GitHub仓库的贡献者列表
    
    Args:
        owner: GitHub仓库所有者
        repo: 仓库名称
        per_page: 每页返回的贡献者数量
    
    Returns:
        贡献者列表
    """
    return github_api.get_contributors(owner, repo, per_page)


@mcp.tool()
def get_github_file_content(owner: str, repo: str, path: str, ref: Optional[str] = None) -> str:
    """
    获取指定GitHub仓库中文件的内容
    
    Args:
        owner: GitHub仓库所有者
        repo: 仓库名称
        path: 文件路径
        ref: 分支或提交SHA，默认为仓库默认分支
    
    Returns:
        文件内容
    """
    return github_api.get_file_content(owner, repo, path, ref)


@mcp.tool()
def get_github_file_history(owner: str, repo: str, path: str, per_page: int = 30) -> List[Dict[str, Any]]:
    """
    获取指定GitHub仓库中文件的历史版本
    
    Args:
        owner: GitHub仓库所有者
        repo: 仓库名称
        path: 文件路径
        per_page: 每页返回的版本数量
    
    Returns:
        文件历史版本列表
    """
    return github_api.get_file_history(owner, repo, path, per_page)


@mcp.tool()
def compare_github_commits(owner: str, repo: str, base: str, head: str) -> Dict[str, Any]:
    """
    对比两个GitHub提交之间的差异
    
    Args:
        owner: GitHub仓库所有者
        repo: 仓库名称
        base: 基准提交SHA
        head: 比较提交SHA
    
    Returns:
        提交差异信息
    """
    return github_api.compare_commits(owner, repo, base, head)


# -------------------------- 版本控制工具 --------------------------


@mcp.tool()
def clone_repository(url: str, owner: str, repo: str, branch: Optional[str] = None) -> Dict[str, Any]:
    """
    克隆远程仓库到本地
    
    Args:
        url: 远程仓库URL
        owner: 仓库所有者
        repo: 仓库名称
        branch: 要克隆的分支，默认为仓库默认分支
    
    Returns:
        克隆结果
    """
    return vcs_manager.clone_repo(url, owner, repo, branch)


@mcp.tool()
def checkout_branch(owner: str, repo: str, branch: str, create: bool = False) -> Dict[str, Any]:
    """
    切换分支
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        branch: 要切换的分支
        create: 是否创建新分支
    
    Returns:
        切换结果
    """
    return vcs_manager.checkout_branch(owner, repo, branch, create)


@mcp.tool()
def commit_changes(owner: str, repo: str, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    提交本地修改
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        message: 提交信息
        files: 要提交的文件列表，默认为所有修改的文件
    
    Returns:
        提交结果
    """
    return vcs_manager.commit_changes(owner, repo, message, files)


@mcp.tool()
def push_changes(owner: str, repo: str, branch: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """
    推送本地修改到远程仓库
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        branch: 要推送的分支，默认为当前分支
        force: 是否强制推送
    
    Returns:
        推送结果
    """
    return vcs_manager.push_changes(owner, repo, branch, force)


@mcp.tool()
def pull_changes(owner: str, repo: str, branch: Optional[str] = None, rebase: bool = False) -> Dict[str, Any]:
    """
    从远程仓库拉取更新
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        branch: 要拉取的分支，默认为当前分支
        rebase: 是否使用rebase方式拉取
    
    Returns:
        拉取结果
    """
    return vcs_manager.pull_changes(owner, repo, branch, rebase)


@mcp.tool()
def get_local_branches(owner: str, repo: str) -> List[str]:
    """
    获取本地仓库的分支列表
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
    
    Returns:
        分支名称列表
    """
    return vcs_manager.get_local_branches(owner, repo)


@mcp.tool()
def get_remote_branches(owner: str, repo: str) -> List[str]:
    """
    获取远程仓库的分支列表
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
    
    Returns:
        分支名称列表
    """
    return vcs_manager.get_remote_branches(owner, repo)


@mcp.tool()
def get_repo_status(owner: str, repo: str) -> Dict[str, Any]:
    """
    获取本地仓库状态
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
    
    Returns:
        仓库状态信息
    """
    return vcs_manager.get_status(owner, repo)


# -------------------------- 代码检索工具 --------------------------


@mcp.tool()
def search_code(keyword: str, owner: str, repo: str, file_types: Optional[List[str]] = None, 
              case_sensitive: bool = False, snippet_context: int = 3, 
              max_results: int = 100) -> List[Dict[str, Any]]:
    """
    在本地仓库中搜索关键词
    
    Args:
        keyword: 搜索关键词
        owner: 仓库所有者
        repo: 仓库名称
        file_types: 文件类型列表，为空则搜索所有文件
        case_sensitive: 是否区分大小写
        snippet_context: 代码片段上下文行数
        max_results: 最大结果数量
    
    Returns:
        搜索结果列表
    """
    repo_path = vcs_manager._get_repo_path(owner, repo)
    return code_searcher.search_in_directory(repo_path, keyword, file_types, case_sensitive, snippet_context, max_results)


@mcp.tool()
def search_code_snippet(snippet: str, owner: str, repo: str, file_types: Optional[List[str]] = None, 
                       case_sensitive: bool = False, snippet_context: int = 3, 
                       max_results: int = 100) -> List[Dict[str, Any]]:
    """
    在本地仓库中搜索代码片段
    
    Args:
        snippet: 代码片段
        owner: 仓库所有者
        repo: 仓库名称
        file_types: 文件类型列表，为空则搜索所有文件
        case_sensitive: 是否区分大小写
        snippet_context: 代码片段上下文行数
        max_results: 最大结果数量
    
    Returns:
        搜索结果列表
    """
    repo_path = vcs_manager._get_repo_path(owner, repo)
    return code_searcher.search_code_snippet(repo_path, snippet, file_types, case_sensitive, snippet_context, max_results)


@mcp.tool()
def search_by_regex(regex_pattern: str, owner: str, repo: str, file_types: Optional[List[str]] = None, 
                   snippet_context: int = 3, max_results: int = 100) -> List[Dict[str, Any]]:
    """
    使用正则表达式在本地仓库中搜索代码
    
    Args:
        regex_pattern: 正则表达式模式
        owner: 仓库所有者
        repo: 仓库名称
        file_types: 文件类型列表，为空则搜索所有文件
        snippet_context: 代码片段上下文行数
        max_results: 最大结果数量
    
    Returns:
        搜索结果列表
    """
    repo_path = vcs_manager._get_repo_path(owner, repo)
    return code_searcher.search_by_regex(repo_path, regex_pattern, file_types, snippet_context, max_results)


@mcp.tool()
def get_repo_file_structure(owner: str, repo: str, file_types: Optional[List[str]] = None, 
                           max_depth: int = 3) -> Dict[str, Any]:
    """
    获取本地仓库的文件结构
    
    Args:
        owner: 仓库所有者
        repo: 仓库名称
        file_types: 文件类型列表，为空则包含所有文件
        max_depth: 最大目录深度
    
    Returns:
        文件结构
    """
    repo_path = vcs_manager._get_repo_path(owner, repo)
    return code_searcher.get_file_structure(repo_path, file_types, max_depth)


# -------------------------- GitHub资源 --------------------------


@mcp.resource("github://repos/{owner}")
def github_repos_resource(owner: str) -> List[Dict[str, Any]]:
    """
    获取指定所有者的GitHub仓库列表资源
    
    Args:
        owner: GitHub仓库所有者
    
    Returns:
        仓库列表，包含仓库元数据
    """
    return github_api.list_repos(owner, per_page=30)


@mcp.resource("github://repo/{owner}/{repo}")
def github_repo_resource(owner: str, repo: str) -> Dict[str, Any]:
    """
    获取指定GitHub仓库的详细信息资源
    
    Args:
        owner: GitHub仓库所有者
        repo: 仓库名称
    
    Returns:
        仓库详细信息
    """
    repo_obj = github_api.get_repo(owner, repo)
    return {
        "name": repo_obj.name,
        "full_name": repo_obj.full_name,
        "description": repo_obj.description,
        "url": repo_obj.html_url,
        "stars": repo_obj.stargazers_count,
        "forks": repo_obj.forks_count,
        "created_at": repo_obj.created_at.isoformat(),
        "updated_at": repo_obj.updated_at.isoformat(),
        "language": repo_obj.language,
        "default_branch": repo_obj.default_branch
    }


@mcp.resource("github://file/{owner}/{repo}/{path}")
def github_file_resource(owner: str, repo: str, path: str) -> str:
    """
    获取指定GitHub仓库中文件的内容资源
    
    Args:
        owner: GitHub仓库所有者
        repo: 仓库名称
        path: 文件路径
    
    Returns:
        文件内容
    """
    return github_api.get_file_content(owner, repo, path, ref=None)


# 服务器运行入口
if __name__ == "__main__":
    # 使用默认配置运行服务器
    mcp.run(transport="streamable-http")