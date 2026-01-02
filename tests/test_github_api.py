"""
GitHub API交互模块测试

该文件包含GitHub API交互模块的单元测试
"""

import unittest
from unittest.mock import patch, MagicMock
from app.github_api import GitHubAPI


class TestGitHubAPI(unittest.TestCase):
    """
    GitHub API交互模块测试类
    """
    
    def setUp(self):
        """
        测试前设置
        """
        self.github_api = GitHubAPI(token="test_token")
    
    @patch('app.github_api.Github')
    def test_get_user(self, mock_github):
        """
        测试获取用户信息
        """
        # 设置模拟
        mock_user = MagicMock()
        mock_github.return_value.get_user.return_value = mock_user
        
        # 调用方法
        result = self.github_api.get_user()
        
        # 验证结果
        self.assertEqual(result, mock_user)
        mock_github.return_value.get_user.assert_called_once()
    
    @patch('app.github_api.Github')
    def test_get_repo(self, mock_github):
        """
        测试获取指定仓库
        """
        # 设置模拟
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # 调用方法
        result = self.github_api.get_repo("owner", "repo")
        
        # 验证结果
        self.assertEqual(result, mock_repo)
        mock_github.return_value.get_repo.assert_called_once_with("owner/repo")
    
    @patch('app.github_api.Github')
    def test_list_repos(self, mock_github):
        """
        测试列出指定所有者的仓库
        """
        # 设置模拟
        mock_user = MagicMock()
        mock_github.return_value.get_user.return_value = mock_user
        
        # 创建模拟仓库对象
        mock_repo1 = MagicMock()
        mock_repo1.name = "repo1"
        mock_repo1.full_name = "owner/repo1"
        mock_repo1.description = "Repo 1 description"
        mock_repo1.html_url = "https://github.com/owner/repo1"
        mock_repo1.stargazers_count = 10
        mock_repo1.forks_count = 5
        mock_repo1.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        
        mock_repo2 = MagicMock()
        mock_repo2.name = "repo2"
        mock_repo2.full_name = "owner/repo2"
        mock_repo2.description = "Repo 2 description"
        mock_repo2.html_url = "https://github.com/owner/repo2"
        mock_repo2.stargazers_count = 20
        mock_repo2.forks_count = 8
        mock_repo2.created_at.isoformat.return_value = "2023-02-01T00:00:00Z"
        
        mock_user.get_repos.return_value = [mock_repo1, mock_repo2]
        
        # 调用方法
        result = self.github_api.list_repos("owner")
        
        # 验证结果
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "repo1")
        self.assertEqual(result[0]["full_name"], "owner/repo1")
        self.assertEqual(result[1]["name"], "repo2")
        self.assertEqual(result[1]["full_name"], "owner/repo2")
        
        mock_github.return_value.get_user.assert_called_once_with("owner")
        mock_user.get_repos.assert_called_once()
    
    @patch('app.github_api.Github')
    def test_get_branches(self, mock_github):
        """
        测试获取仓库分支列表
        """
        # 设置模拟
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # 创建模拟分支对象
        mock_branch1 = MagicMock()
        mock_branch1.name = "main"
        
        mock_branch2 = MagicMock()
        mock_branch2.name = "develop"
        
        mock_repo.get_branches.return_value = [mock_branch1, mock_branch2]
        
        # 调用方法
        result = self.github_api.get_branches("owner", "repo")
        
        # 验证结果
        self.assertEqual(result, ["main", "develop"])
        mock_github.return_value.get_repo.assert_called_once_with("owner/repo")
        mock_repo.get_branches.assert_called_once()
    
    @patch('app.github_api.Github')
    def test_get_file_content(self, mock_github):
        """
        测试获取文件内容
        """
        # 设置模拟
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # 创建模拟文件内容对象
        mock_content = MagicMock()
        mock_content.decoded_content = b"test content"
        mock_repo.get_contents.return_value = mock_content
        
        # 调用方法
        result = self.github_api.get_file_content("owner", "repo", "path/to/file.txt")
        
        # 验证结果
        self.assertEqual(result, "test content")
        mock_github.return_value.get_repo.assert_called_once_with("owner/repo")
        mock_repo.get_contents.assert_called_once_with("path/to/file.txt", ref=None)
    
    @patch('app.github_api.Github')
    def test_get_file_content_with_ref(self, mock_github):
        """
        测试使用ref获取文件内容
        """
        # 设置模拟
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # 创建模拟文件内容对象
        mock_content = MagicMock()
        mock_content.decoded_content = b"test content"
        mock_repo.get_contents.return_value = mock_content
        
        # 调用方法
        result = self.github_api.get_file_content("owner", "repo", "path/to/file.txt", ref="main")
        
        # 验证结果
        self.assertEqual(result, "test content")
        mock_repo.get_contents.assert_called_once_with("path/to/file.txt", ref="main")


if __name__ == '__main__':
    unittest.main()