"""
工具函数和安全机制模块

该模块负责实现通用工具函数和安全机制，包括缓存策略、日志记录、路径验证和请求限流功能。
"""

import os
import re
import hashlib
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from functools import wraps
import logging
from app.config import settings

# 配置日志记录
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class Cache:
    """
    缓存类，实现内存缓存功能
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        初始化缓存
        
        Args:
            default_ttl: 默认缓存过期时间（秒）
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _get_key(self, key: str) -> str:
        """
        获取缓存键
        
        Args:
            key: 原始键
        
        Returns:
            str: 处理后的缓存键
        """
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            Optional[Any]: 缓存值，如果不存在或已过期返回None
        """
        cache_key = self._get_key(key)
        if cache_key not in self.cache:
            return None
        
        item = self.cache[cache_key]
        if datetime.utcnow() > item["expires_at"]:
            # 缓存已过期，删除缓存项
            del self.cache[cache_key]
            return None
        
        return item["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 缓存过期时间（秒），如果为None则使用默认值
        """
        cache_key = self._get_key(key)
        expires_at = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
        
        self.cache[cache_key] = {
            "value": value,
            "expires_at": expires_at
        }
    
    def delete(self, key: str) -> None:
        """
        删除缓存值
        
        Args:
            key: 缓存键
        """
        cache_key = self._get_key(key)
        if cache_key in self.cache:
            del self.cache[cache_key]
    
    def clear(self) -> None:
        """
        清空所有缓存
        """
        self.cache.clear()
    
    def size(self) -> int:
        """
        获取缓存大小
        
        Returns:
            int: 缓存项数量
        """
        # 清理过期缓存
        self._clean_expired()
        return len(self.cache)
    
    def _clean_expired(self) -> None:
        """
        清理过期缓存
        """
        now = datetime.utcnow()
        expired_keys = [k for k, v in self.cache.items() if now > v["expires_at"]]
        for key in expired_keys:
            del self.cache[key]


# 创建全局缓存实例
cache = Cache()


def cached(ttl: Optional[int] = None):
    """
    缓存装饰器，用于缓存函数结果
    
    Args:
        ttl: 缓存过期时间（秒）
    
    Returns:
        Callable: 装饰后的函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # 尝试从缓存获取结果
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # 执行函数并缓存结果
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


def validate_path(path: str, allowed_dir: str) -> bool:
    """
    验证路径是否安全，防止路径遍历攻击
    
    Args:
        path: 要验证的路径
        allowed_dir: 允许的根目录
    
    Returns:
        bool: 路径是否安全
    """
    # 规范化路径
    normalized_path = os.path.normpath(path)
    
    # 检查路径是否包含不安全的组件
    if '..' in normalized_path.split(os.sep):
        logger.warning(f"Path contains '..' component: {path}")
        return False
    
    # 检查路径是否在允许的目录范围内
    allowed_abs = os.path.abspath(allowed_dir)
    path_abs = os.path.abspath(os.path.join(allowed_abs, normalized_path))
    
    if not path_abs.startswith(allowed_abs):
        logger.warning(f"Path traversal attempt: {path} (resolved to: {path_abs})")
        return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
    
    Returns:
        str: 清理后的文件名
    """
    # 首先移除前导和尾随空格
    sanitized = filename.strip()
    # 移除或替换不安全字符
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', sanitized)
    # 将空格替换为下划线
    sanitized = sanitized.replace(' ', '_')
    # 移除连续的下划线
    sanitized = re.sub(r'_+', '_', sanitized)
    # 限制文件名长度
    max_length = 255
    if len(sanitized) > max_length:
        # 保留扩展名
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:max_length - len(ext)] + ext
    
    return sanitized


class RateLimiter:
    """
    速率限制器，实现基于令牌桶算法的请求限流
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化速率限制器
        
        Args:
            capacity: 令牌桶容量
            refill_rate: 令牌填充速率（每秒）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens: Dict[str, Dict[str, Any]] = {}
    
    def _get_or_create_bucket(self, key: str) -> Dict[str, Any]:
        """
        获取或创建令牌桶
        
        Args:
            key: 令牌桶键
        
        Returns:
            Dict[str, Any]: 令牌桶
        """
        if key not in self.tokens:
            self.tokens[key] = {
                "tokens": self.capacity,
                "last_refill": datetime.utcnow()
            }
        return self.tokens[key]
    
    def _refill_bucket(self, bucket: Dict[str, Any]) -> None:
        """
        填充令牌桶
        
        Args:
            bucket: 令牌桶
        """
        now = datetime.utcnow()
        time_passed = (now - bucket["last_refill"]).total_seconds()
        
        if time_passed > 0:
            tokens_to_add = time_passed * self.refill_rate
            bucket["tokens"] = min(self.capacity, bucket["tokens"] + tokens_to_add)
            bucket["last_refill"] = now
    
    def is_allowed(self, key: str) -> bool:
        """
        检查请求是否允许
        
        Args:
            key: 请求键
        
        Returns:
            bool: 请求是否允许
        """
        bucket = self._get_or_create_bucket(key)
        self._refill_bucket(bucket)
        
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        
        return False
    
    def get_tokens(self, key: str) -> float:
        """
        获取当前令牌数量
        
        Args:
            key: 请求键
        
        Returns:
            float: 当前令牌数量
        """
        bucket = self._get_or_create_bucket(key)
        self._refill_bucket(bucket)
        return bucket["tokens"]
    
    def clear(self) -> None:
        """
        清空所有令牌桶
        """
        self.tokens.clear()


# 创建全局速率限制器实例
# 示例：允许每分钟60个请求
rate_limiter = RateLimiter(capacity=60, refill_rate=1.0)  # 1.0个令牌每秒


def rate_limited(key_func=None):
    """
    速率限制装饰器
    
    Args:
        key_func: 生成速率限制键的函数
    
    Returns:
        Callable: 装饰后的函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成速率限制键
            if key_func:
                rate_key = key_func(*args, **kwargs)
            else:
                # 默认使用函数名作为键
                rate_key = func.__name__
            
            # 检查是否允许请求
            if not rate_limiter.is_allowed(rate_key):
                logger.warning(f"Rate limit exceeded for {rate_key}")
                raise Exception("Rate limit exceeded")
            
            # 执行函数
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_client_ip(request: Any) -> str:
    """
    从请求对象中获取客户端IP地址
    
    Args:
        request: 请求对象
    
    Returns:
        str: 客户端IP地址
    """
    # 尝试从X-Forwarded-For头获取
    if hasattr(request, 'headers'):
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
    
    # 尝试从remote_addr获取
    if hasattr(request, 'client') and hasattr(request.client, 'host'):
        return request.client.host
    
    if hasattr(request, 'remote_addr'):
        return request.remote_addr
    
    return "127.0.0.1"  # 默认值


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
    
    Returns:
        str: 格式化后的文件大小
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名
    
    Args:
        filename: 文件名
    
    Returns:
        str: 文件扩展名（小写）
    """
    return os.path.splitext(filename)[1].lower()


def is_binary_file(content: bytes) -> bool:
    """
    检查文件是否为二进制文件
    
    Args:
        content: 文件内容
    
    Returns:
        bool: 是否为二进制文件
    """
    # 检查文件是否包含空字节
    if b'\x00' in content[:1024]:
        return True
    
    # 检查文件是否包含非ASCII字符
    try:
        content[:1024].decode('utf-8')
        return False
    except UnicodeDecodeError:
        return True