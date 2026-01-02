"""
工具函数和安全机制模块测试

该文件包含工具函数和安全机制模块的单元测试
"""

import unittest
import os
import tempfile
from app.utils import Cache, cached, validate_path, sanitize_filename, RateLimiter, rate_limited, format_size, get_file_extension, is_binary_file


class TestCache(unittest.TestCase):
    """
    缓存类测试
    """
    
    def setUp(self):
        """
        测试前设置
        """
        self.cache = Cache(default_ttl=1)
    
    def test_set_get(self):
        """
        测试设置和获取缓存
        """
        # 设置缓存
        self.cache.set("key1", "value1")
        self.cache.set("key2", 123)
        self.cache.set("key3", {"a": 1, "b": 2})
        
        # 获取缓存
        self.assertEqual(self.cache.get("key1"), "value1")
        self.assertEqual(self.cache.get("key2"), 123)
        self.assertEqual(self.cache.get("key3"), {"a": 1, "b": 2})
        
        # 获取不存在的缓存
        self.assertIsNone(self.cache.get("key4"))
    
    def test_expire(self):
        """
        测试缓存过期
        """
        # 设置缓存
        self.cache.set("key", "value", ttl=1)  # 1秒后过期
        
        # 立即获取
        self.assertEqual(self.cache.get("key"), "value")
        
        # 等待2秒后再次获取
        import time
        time.sleep(2)
        self.assertIsNone(self.cache.get("key"))
    
    def test_delete(self):
        """
        测试删除缓存
        """
        # 设置缓存
        self.cache.set("key", "value")
        self.assertEqual(self.cache.get("key"), "value")
        
        # 删除缓存
        self.cache.delete("key")
        self.assertIsNone(self.cache.get("key"))
    
    def test_clear(self):
        """
        测试清空缓存
        """
        # 设置多个缓存
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.assertEqual(self.cache.size(), 2)
        
        # 清空缓存
        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))


class TestDecorators(unittest.TestCase):
    """
    装饰器测试
    """
    
    def test_cached_decorator(self):
        """
        测试缓存装饰器
        """
        # 计数器，用于跟踪函数调用次数
        call_count = 0
        
        @cached(ttl=1)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # 第一次调用，应该执行函数
        result1 = expensive_function(1, 2)
        self.assertEqual(result1, 3)
        self.assertEqual(call_count, 1)
        
        # 第二次调用相同参数，应该使用缓存
        result2 = expensive_function(1, 2)
        self.assertEqual(result2, 3)
        self.assertEqual(call_count, 1)
        
        # 调用不同参数，应该执行函数
        result3 = expensive_function(3, 4)
        self.assertEqual(result3, 7)
        self.assertEqual(call_count, 2)
        
        # 等待2秒，缓存过期
        import time
        time.sleep(2)
        
        # 再次调用，应该执行函数
        result4 = expensive_function(1, 2)
        self.assertEqual(result4, 3)
        self.assertEqual(call_count, 3)
    
    def test_rate_limited_decorator(self):
        """
        测试速率限制装饰器
        """
        # 创建速率限制器，容量为2，填充速率为1/秒
        from app.utils import rate_limiter
        original_capacity = rate_limiter.capacity
        original_refill_rate = rate_limiter.refill_rate
        
        # 修改速率限制器配置
        rate_limiter.capacity = 2
        rate_limiter.refill_rate = 1.0
        rate_limiter.clear()
        
        # 计数器，用于跟踪函数调用次数
        call_count = 0
        
        @rate_limited()
        def limited_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        # 第一次调用，应该允许
        result1 = limited_function()
        self.assertEqual(result1, "success")
        self.assertEqual(call_count, 1)
        
        # 第二次调用，应该允许
        result2 = limited_function()
        self.assertEqual(result2, "success")
        self.assertEqual(call_count, 2)
        
        # 第三次调用，应该被限制
        with self.assertRaises(Exception) as context:
            limited_function()
        self.assertIn("Rate limit exceeded", str(context.exception))
        self.assertEqual(call_count, 2)
        
        # 恢复原始配置
        rate_limiter.capacity = original_capacity
        rate_limiter.refill_rate = original_refill_rate


class TestPathValidation(unittest.TestCase):
    """
    路径验证测试
    """
    
    def test_validate_path(self):
        """
        测试路径验证
        """
        allowed_dir = "/allowed/dir"
        
        # 测试安全路径
        self.assertTrue(validate_path("safe/path", allowed_dir))
        self.assertTrue(validate_path("file.txt", allowed_dir))
        self.assertTrue(validate_path("./relative/path", allowed_dir))
        
        # 测试不安全路径
        self.assertFalse(validate_path("../unsafe/path", allowed_dir))
        self.assertFalse(validate_path("../../../../etc/passwd", allowed_dir))
        self.assertFalse(validate_path("/absolute/path", allowed_dir))
        self.assertFalse(validate_path("C:\\windows\\system32", allowed_dir))
    
    def test_sanitize_filename(self):
        """
        测试文件名清理
        """
        # 测试正常文件名
        self.assertEqual(sanitize_filename("normal_file.txt"), "normal_file.txt")
        
        # 测试包含不安全字符的文件名
        self.assertEqual(sanitize_filename("file<with>unsafe:chars.txt"), "file_with_unsafe_chars.txt")
        
        # 测试包含空格的文件名
        self.assertEqual(sanitize_filename("  file with spaces  .txt  "), "file_with_spaces_.txt")
        
        # 测试长文件名
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)
        self.assertLessEqual(len(result), 255)
        self.assertTrue(result.endswith(".txt"))


class TestRateLimiter(unittest.TestCase):
    """
    速率限制器测试
    """
    
    def setUp(self):
        """
        测试前设置
        """
        self.rate_limiter = RateLimiter(capacity=2, refill_rate=1.0)  # 容量2，填充速率1/秒
    
    def test_is_allowed(self):
        """
        测试是否允许请求
        """
        # 第一次请求，应该允许
        self.assertTrue(self.rate_limiter.is_allowed("key"))
        
        # 第二次请求，应该允许
        self.assertTrue(self.rate_limiter.is_allowed("key"))
        
        # 第三次请求，应该被限制
        self.assertFalse(self.rate_limiter.is_allowed("key"))
        
        # 等待1秒，应该恢复1个令牌
        import time
        time.sleep(1)
        self.assertTrue(self.rate_limiter.is_allowed("key"))
        
        # 再次请求，应该被限制
        self.assertFalse(self.rate_limiter.is_allowed("key"))
    
    def test_get_tokens(self):
        """
        测试获取当前令牌数量
        """
        # 初始状态，应该有2个令牌
        self.assertAlmostEqual(self.rate_limiter.get_tokens("key"), 2.0, delta=0.0001)
        
        # 消耗1个令牌
        self.rate_limiter.is_allowed("key")
        self.assertAlmostEqual(self.rate_limiter.get_tokens("key"), 1.0, delta=0.0001)
        
        # 消耗另1个令牌
        self.rate_limiter.is_allowed("key")
        self.assertAlmostEqual(self.rate_limiter.get_tokens("key"), 0.0, delta=0.0001)
        
        # 等待1秒，应该恢复1个令牌
        import time
        time.sleep(1)
        # 增加delta值以容忍更大的误差范围
        self.assertAlmostEqual(self.rate_limiter.get_tokens("key"), 1.0, delta=0.001)
    
    def test_clear(self):
        """
        测试清空令牌桶
        """
        # 消耗令牌
        self.rate_limiter.is_allowed("key")
        self.assertAlmostEqual(self.rate_limiter.get_tokens("key"), 1.0, delta=0.0001)
        
        # 清空令牌桶
        self.rate_limiter.clear()
        self.assertAlmostEqual(self.rate_limiter.get_tokens("key"), 2.0, delta=0.0001)  # 应该恢复到初始状态


class TestUtilityFunctions(unittest.TestCase):
    """
    工具函数测试
    """
    
    def test_format_size(self):
        """
        测试文件大小格式化
        """
        self.assertEqual(format_size(0), "0.00 B")
        self.assertEqual(format_size(1023), "1023.00 B")
        self.assertEqual(format_size(1024), "1.00 KB")
        # 1024 * 1024 - 1 = 1048575 bytes = 1023.99609375 KB，四舍五入为1024.00 KB
        self.assertEqual(format_size(1024 * 1024 - 1), "1024.00 KB")
        self.assertEqual(format_size(1024 * 1024), "1.00 MB")
        self.assertEqual(format_size(1024 * 1024 * 1024), "1.00 GB")
    
    def test_get_file_extension(self):
        """
        测试获取文件扩展名
        """
        self.assertEqual(get_file_extension("file.txt"), ".txt")
        self.assertEqual(get_file_extension("document.pdf"), ".pdf")
        self.assertEqual(get_file_extension("image.jpg"), ".jpg")
        self.assertEqual(get_file_extension("archive.tar.gz"), ".gz")
        self.assertEqual(get_file_extension("no_extension"), "")
        # 对于隐藏文件，os.path.splitext()返回('.hidden_file', '')
        self.assertEqual(get_file_extension(".hidden_file"), "")
    
    def test_is_binary_file(self):
        """
        测试检查二进制文件
        """
        # 测试文本文件
        self.assertFalse(is_binary_file(b"text content\nwith multiple lines"))
        self.assertFalse(is_binary_file(b"ascii content test"))
        
        # 测试二进制文件
        self.assertTrue(is_binary_file(b"\x00binary\x00content"))
        
        # 测试混合内容
        self.assertTrue(is_binary_file(b"text with\x00binary\x00content"))
        
        # 测试空文件
        self.assertFalse(is_binary_file(b""))


if __name__ == '__main__':
    unittest.main()