"""
版本控制模块测试

该文件包含版本控制模块的单元测试
"""

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from app.vcs import VCSManager


class TestVCSManager(unittest.TestCase):
    """
    版本控制模块测试类
    """
    
    def setUp(self):
        """
        测试前设置
        """
        # 创建临时目录作为本地仓库目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 保存原始环境变量
        self.original_repo_dir = os.environ.get('LOCAL_REPO_DIR')
        os.environ['LOCAL_REPO_DIR'] = self.temp_dir
        
        # 创建VCSManager实例
        self.vcs_manager = VCSManager()
    
    def tearDown(self):
        """
        测试后清理
        """
        # 恢复原始环境变量
        if self.original_repo_dir:
            os.environ['LOCAL_REPO_DIR'] = self.original_repo_dir
        else:
            os.environ.pop('LOCAL_REPO_DIR', None)
        
        # 删除临时目录
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_validate_path(self):
        """
        测试路径验证
        """
        # 测试安全路径
        self.assertTrue(self.vcs_manager._validate_path("safe/path"))
        self.assertTrue(self.vcs_manager._validate_path("file.txt"))
        
        # 测试不安全路径
        self.assertFalse(self.vcs_manager._validate_path("../unsafe/path"))
        self.assertFalse(self.vcs_manager._validate_path("../../../../etc/passwd"))
    
    def test_get_repo_path(self):
        """
        测试获取本地仓库路径
        """
        expected_path = os.path.join(self.temp_dir, "owner_repo")
        result = self.vcs_manager._get_repo_path("owner", "repo")
        self.assertEqual(result, expected_path)
    
    @patch('app.vcs.Repo')
    def test_clone_repo(self, mock_repo):
        """
        测试克隆远程仓库
        """
        # 设置模拟
        mock_repo_instance = MagicMock()
        mock_repo.clone_from.return_value = mock_repo_instance
        mock_repo_instance.active_branch.name = "main"
        
        # 调用方法
        result = self.vcs_manager.clone_repo("https://github.com/owner/repo.git", "owner", "repo")
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Repository cloned successfully")
        self.assertEqual(result["branch"], "main")
        mock_repo.clone_from.assert_called_once()
    
    @patch('app.vcs.Repo')
    def test_checkout_branch(self, mock_repo):
        """
        测试切换分支
        """
        # 设置模拟
        mock_repo_instance = MagicMock()
        mock_repo.return_value = mock_repo_instance
        
        # 调用方法
        result = self.vcs_manager.checkout_branch("owner", "repo", "develop")
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Switched to branch develop")
        self.assertEqual(result["current_branch"], "develop")
        mock_repo_instance.git.checkout.assert_called_once_with("develop")
    
    @patch('app.vcs.Repo')
    def test_checkout_new_branch(self, mock_repo):
        """
        测试创建并切换新分支
        """
        # 设置模拟
        mock_repo_instance = MagicMock()
        mock_repo.return_value = mock_repo_instance
        
        # 调用方法
        result = self.vcs_manager.checkout_branch("owner", "repo", "new-branch", create=True)
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Switched to branch new-branch")
        self.assertEqual(result["current_branch"], "new-branch")
        mock_repo_instance.git.checkout.assert_called_once_with('-b', "new-branch")
    
    @patch('app.vcs.Repo')
    def test_get_status(self, mock_repo):
        """
        测试获取仓库状态
        """
        # 设置模拟
        mock_repo_instance = MagicMock()
        mock_repo.return_value = mock_repo_instance
        mock_repo_instance.active_branch.name = "main"
        mock_repo_instance.git.status.return_value = "M modified_file.txt\nA added_file.txt\nD deleted_file.txt\n?? untracked_file.txt"
        
        # 调用方法
        result = self.vcs_manager.get_status("owner", "repo")
        
        # 验证结果
        self.assertEqual(result["current_branch"], "main")
        self.assertEqual(result["modified_files"], ["modified_file.txt"])
        self.assertEqual(result["added_files"], ["added_file.txt"])
        self.assertEqual(result["deleted_files"], ["deleted_file.txt"])
        self.assertEqual(result["untracked_files"], ["untracked_file.txt"])
    
    @patch('app.vcs.Repo')
    def test_get_local_branches(self, mock_repo):
        """
        测试获取本地分支列表
        """
        # 设置模拟
        mock_repo_instance = MagicMock()
        mock_repo.return_value = mock_repo_instance
        
        # 创建模拟分支对象
        mock_branch1 = MagicMock()
        mock_branch1.name = "main"
        
        mock_branch2 = MagicMock()
        mock_branch2.name = "develop"
        
        mock_repo_instance.branches = [mock_branch1, mock_branch2]
        
        # 调用方法
        result = self.vcs_manager.get_local_branches("owner", "repo")
        
        # 验证结果
        self.assertEqual(result, ["main", "develop"])
    
    @patch('app.vcs.Repo')
    def test_get_remote_branches(self, mock_repo):
        """
        测试获取远程分支列表
        """
        # 设置模拟
        mock_repo_instance = MagicMock()
        mock_repo.return_value = mock_repo_instance
        
        # 创建模拟远程分支对象
        mock_remote_branch1 = MagicMock()
        mock_remote_branch1.name = "origin/main"
        
        mock_remote_branch2 = MagicMock()
        mock_remote_branch2.name = "origin/develop"
        
        mock_remote_branch3 = MagicMock()
        mock_remote_branch3.name = "origin/HEAD"
        
        mock_repo_instance.remotes.origin.refs = [mock_remote_branch1, mock_remote_branch2, mock_remote_branch3]
        
        # 调用方法
        result = self.vcs_manager.get_remote_branches("owner", "repo")
        
        # 验证结果
        self.assertEqual(result, ["main", "develop"])


if __name__ == '__main__':
    unittest.main()