"""
代码检索模块

该模块负责实现代码检索功能，支持基于关键词、文件类型和代码片段的搜索。
"""

import os
import re
from typing import List, Dict, Any, Optional
import fnmatch
import logging
from app.config import settings

# 配置日志记录
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class CodeSearcher:
    """
    代码检索器，负责实现代码搜索功能
    """
    
    def __init__(self):
        """
        初始化代码检索器
        """
        self.supported_file_types = {
            "python": [".py"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "csharp": [".cs"],
            "cpp": [".cpp", ".h", ".hpp"],
            "go": [".go"],
            "rust": [".rs"],
            "html": [".html"],
            "css": [".css"],
            "markdown": [".md"],
            "json": [".json"],
            "yaml": [".yaml", ".yml"],
            "xml": [".xml"]
        }
    
    def _get_file_extensions(self, file_type: str) -> List[str]:
        """
        根据文件类型获取对应的文件扩展名
        
        Args:
            file_type: 文件类型
        
        Returns:
            List[str]: 文件扩展名列表
        """
        return self.supported_file_types.get(file_type.lower(), [])
    
    def _is_file_type_matched(self, file_path: str, file_types: List[str]) -> bool:
        """
        检查文件是否匹配指定的文件类型
        
        Args:
            file_path: 文件路径
            file_types: 文件类型列表
        
        Returns:
            bool: 文件是否匹配
        """
        if not file_types:
            return True
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        for file_type in file_types:
            extensions = self._get_file_extensions(file_type)
            if file_ext in extensions:
                return True
        
        return False
    
    def search_in_file(self, file_path: str, keyword: str, case_sensitive: bool = False, snippet_context: int = 3) -> List[Dict[str, Any]]:
        """
        在单个文件中搜索关键词
        
        Args:
            file_path: 文件路径
            keyword: 搜索关键词
            case_sensitive: 是否区分大小写
            snippet_context: 代码片段上下文行数
        
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except (UnicodeDecodeError, PermissionError) as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return results
        
        # 编译正则表达式
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(re.escape(keyword), flags)
        
        # 搜索关键词
        for line_num, line in enumerate(lines, 1):
            matches = pattern.finditer(line)
            
            for match in matches:
                # 获取上下文
                start_line = max(0, line_num - snippet_context - 1)
                end_line = min(len(lines), line_num + snippet_context)
                
                context = {
                    "pre": [{
                        "line_num": i + 1,
                        "content": lines[i].rstrip()
                    } for i in range(start_line, line_num - 1)],
                    "match": {
                        "line_num": line_num,
                        "content": line.rstrip(),
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    },
                    "post": [{
                        "line_num": i + 1,
                        "content": lines[i].rstrip()
                    } for i in range(line_num, end_line)]
                }
                
                results.append({
                    "file_path": file_path,
                    "line_num": line_num,
                    "match_text": match.group(),
                    "context": context
                })
        
        return results
    
    def search_in_directory(self, directory: str, keyword: str, file_types: Optional[List[str]] = None, 
                           case_sensitive: bool = False, snippet_context: int = 3, 
                           max_results: int = 100) -> List[Dict[str, Any]]:
        """
        在目录中搜索关键词
        
        Args:
            directory: 搜索目录
            keyword: 搜索关键词
            file_types: 文件类型列表，为空则搜索所有文件
            case_sensitive: 是否区分大小写
            snippet_context: 代码片段上下文行数
            max_results: 最大结果数量
        
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        results = []
        
        # 遍历目录
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                
                # 检查文件类型
                if not self._is_file_type_matched(file_path, file_types or []):
                    continue
                
                # 搜索文件
                file_results = self.search_in_file(file_path, keyword, case_sensitive, snippet_context)
                results.extend(file_results)
                
                # 检查是否达到最大结果数量
                if len(results) >= max_results:
                    return results[:max_results]
        
        return results
    
    def search_code_snippet(self, directory: str, snippet: str, file_types: Optional[List[str]] = None, 
                           case_sensitive: bool = False, snippet_context: int = 3, 
                           max_results: int = 100) -> List[Dict[str, Any]]:
        """
        搜索代码片段
        
        Args:
            directory: 搜索目录
            snippet: 代码片段
            file_types: 文件类型列表，为空则搜索所有文件
            case_sensitive: 是否区分大小写
            snippet_context: 代码片段上下文行数
            max_results: 最大结果数量
        
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        results = []
        
        # 编译正则表达式，支持多行匹配
        flags = re.DOTALL | re.MULTILINE
        if not case_sensitive:
            flags |= re.IGNORECASE
        
        pattern = re.compile(re.escape(snippet), flags)
        
        # 遍历目录
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                
                # 检查文件类型
                if not self._is_file_type_matched(file_path, file_types or []):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except (UnicodeDecodeError, PermissionError) as e:
                    logger.error(f"Error reading file {file_path}: {e}")
                    continue
                
                # 搜索代码片段
                matches = pattern.finditer(content)
                
                for match in matches:
                    # 获取匹配位置的行号
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # 获取匹配上下文
                    lines = content.split('\n')
                    start_line = max(0, line_num - snippet_context - 1)
                    end_line = min(len(lines), line_num + snippet_context)
                    
                    context = {
                        "pre": [{
                            "line_num": i + 1,
                            "content": lines[i]
                        } for i in range(start_line, line_num - 1)],
                        "match": {
                            "line_num": line_num,
                            "content": '\n'.join(lines[line_num - 1:line_num - 1 + snippet.count('\n') + 1]),
                            "start_pos": match.start() - content[:match.start()].rfind('\n') - 1,
                            "end_pos": match.end() - content[:match.start()].rfind('\n') - 1
                        },
                        "post": [{
                            "line_num": i + 1,
                            "content": lines[i]
                        } for i in range(line_num + snippet.count('\n'), end_line)]
                    }
                    
                    results.append({
                        "file_path": file_path,
                        "line_num": line_num,
                        "match_text": match.group(),
                        "context": context
                    })
                    
                    # 检查是否达到最大结果数量
                    if len(results) >= max_results:
                        return results[:max_results]
        
        return results
    
    def get_file_structure(self, directory: str, file_types: Optional[List[str]] = None, 
                          max_depth: int = 3) -> Dict[str, Any]:
        """
        获取目录的文件结构
        
        Args:
            directory: 目录路径
            file_types: 文件类型列表，为空则包含所有文件
            max_depth: 最大目录深度
        
        Returns:
            Dict[str, Any]: 文件结构
        """
        def _build_structure(current_dir: str, current_depth: int) -> Dict[str, Any]:
            structure = {
                "name": os.path.basename(current_dir),
                "type": "directory",
                "children": []
            }
            
            if current_depth > max_depth:
                return structure
            
            try:
                for item in sorted(os.listdir(current_dir)):
                    item_path = os.path.join(current_dir, item)
                    
                    if os.path.isdir(item_path):
                        # 递归构建子目录结构
                        child_structure = _build_structure(item_path, current_depth + 1)
                        structure["children"].append(child_structure)
                    else:
                        # 检查文件类型
                        if self._is_file_type_matched(item_path, file_types or []):
                            structure["children"].append({
                                "name": item,
                                "type": "file",
                                "size": os.path.getsize(item_path)
                            })
            except PermissionError as e:
                logger.error(f"Permission denied accessing {current_dir}: {e}")
            
            return structure
        
        return _build_structure(directory, 0)
    
    def search_by_regex(self, directory: str, regex_pattern: str, file_types: Optional[List[str]] = None, 
                       snippet_context: int = 3, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        使用正则表达式搜索代码
        
        Args:
            directory: 搜索目录
            regex_pattern: 正则表达式模式
            file_types: 文件类型列表，为空则搜索所有文件
            snippet_context: 代码片段上下文行数
            max_results: 最大结果数量
        
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        results = []
        
        # 编译正则表达式
        try:
            pattern = re.compile(regex_pattern, re.DOTALL | re.MULTILINE)
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            return []
        
        # 遍历目录
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                
                # 检查文件类型
                if not self._is_file_type_matched(file_path, file_types or []):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                except (UnicodeDecodeError, PermissionError) as e:
                    logger.error(f"Error reading file {file_path}: {e}")
                    continue
                
                # 搜索文件
                content = '\n'.join(lines)
                matches = pattern.finditer(content)
                
                for match in matches:
                    # 获取匹配位置的行号
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # 获取上下文
                    start_line = max(0, line_num - snippet_context - 1)
                    end_line = min(len(lines), line_num + snippet_context)
                    
                    context = {
                        "pre": [{
                            "line_num": i + 1,
                            "content": lines[i].rstrip()
                        } for i in range(start_line, line_num - 1)],
                        "match": {
                            "line_num": line_num,
                            "content": match.group().rstrip(),
                            "start_pos": match.start() - content[:match.start()].rfind('\n') - 1,
                            "end_pos": match.end() - content[:match.start()].rfind('\n') - 1
                        },
                        "post": [{
                            "line_num": i + 1,
                            "content": lines[i].rstrip()
                        } for i in range(line_num, end_line)]
                    }
                    
                    results.append({
                        "file_path": file_path,
                        "line_num": line_num,
                        "match_text": match.group(),
                        "context": context
                    })
                    
                    # 检查是否达到最大结果数量
                    if len(results) >= max_results:
                        return results[:max_results]
        
        return results


# 创建全局代码检索器实例
code_searcher = CodeSearcher()