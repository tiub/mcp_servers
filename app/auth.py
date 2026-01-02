"""
认证授权模块

该模块负责实现认证授权功能，包括OAuth 2.0资源服务器功能、JWT令牌验证和用户权限管理。
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
import logging

# 配置日志记录
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class TokenVerifier:
    """
    令牌验证器，实现MCP的TokenVerifier协议
    """
    
    async def verify_token(self, token: str) -> Optional["AccessToken"]:
        """
        验证访问令牌
        
        Args:
            token: 访问令牌
        
        Returns:
            Optional[AccessToken]: 验证成功返回AccessToken对象，否则返回None
        """
        # 这里应该实现实际的令牌验证逻辑
        # 例如，对于GitHub OAuth令牌，可以调用GitHub API验证令牌有效性
        logger.info(f"Verifying token: {token[:10]}...")
        
        # 简化实现：假设令牌有效，返回模拟的AccessToken对象
        return AccessToken(
            token=token,
            scopes=["repo", "user"],
            expires_at=datetime.utcnow() + timedelta(hours=1),
            user_id="test_user",
            username="test_username"
        )


class AccessToken:
    """
    访问令牌类，包含令牌信息
    """
    
    def __init__(self, token: str, scopes: list, expires_at: datetime, user_id: str, username: str):
        """
        初始化访问令牌
        
        Args:
            token: 令牌字符串
            scopes: 令牌作用域
            expires_at: 过期时间
            user_id: 用户ID
            username: 用户名
        """
        self.token = token
        self.scopes = scopes
        self.expires_at = expires_at
        self.user_id = user_id
        self.username = username
    
    def is_expired(self) -> bool:
        """
        检查令牌是否过期
        
        Returns:
            bool: 令牌是否过期
        """
        return datetime.utcnow() > self.expires_at
    
    def has_scope(self, scope: str) -> bool:
        """
        检查令牌是否包含指定作用域
        
        Args:
            scope: 作用域
        
        Returns:
            bool: 是否包含指定作用域
        """
        return scope in self.scopes


class AuthManager:
    """
    认证管理器，负责JWT令牌生成和验证
    """
    
    def __init__(self):
        """
        初始化认证管理器
        """
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.jwt_secret_key = settings.JWT_SECRET_KEY
        self.jwt_algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
        
        Returns:
            bool: 密码是否匹配
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        获取密码哈希值
        
        Args:
            password: 明文密码
        
        Returns:
            str: 密码哈希值
        """
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        
        Args:
            data: 令牌数据
            expires_delta: 过期时间增量
        
        Returns:
            str: JWT令牌
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret_key, algorithm=self.jwt_algorithm)
        return encoded_jwt
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证访问令牌
        
        Args:
            token: JWT令牌
        
        Returns:
            Optional[Dict[str, Any]]: 令牌数据，如果验证失败返回None
        """
        try:
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=[self.jwt_algorithm])
            return payload
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            return None


class PermissionManager:
    """
    权限管理器，负责用户权限管理
    """
    
    def __init__(self):
        """
        初始化权限管理器
        """
        self.roles = {
            "admin": ["read", "write", "delete", "admin"],
            "user": ["read", "write"]
        }
    
    def has_permission(self, user_role: str, permission: str) -> bool:
        """
        检查用户是否具有指定权限
        
        Args:
            user_role: 用户角色
            permission: 权限
        
        Returns:
            bool: 用户是否具有指定权限
        """
        user_permissions = self.roles.get(user_role, ["read"])
        return permission in user_permissions or "admin" in user_permissions
    
    def get_user_permissions(self, user_role: str) -> list:
        """
        获取用户的所有权限
        
        Args:
            user_role: 用户角色
        
        Returns:
            list: 用户权限列表
        """
        return self.roles.get(user_role, ["read"])


class OperationLogger:
    """
    操作日志记录器，记录所有关键操作
    """
    
    def __init__(self):
        """
        初始化操作日志记录器
        """
        self.logger = logging.getLogger("operation_logger")
        self.logger.setLevel(logging.INFO)
        
        # 添加文件处理器
        file_handler = logging.FileHandler("operation.log")
        file_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # 添加处理器到logger
        self.logger.addHandler(file_handler)
    
    def log_operation(self, user_id: str, operation: str, resource: str, success: bool, details: Optional[Dict[str, Any]] = None):
        """
        记录操作日志
        
        Args:
            user_id: 用户ID
            operation: 操作类型
            resource: 操作资源
            success: 操作是否成功
            details: 操作详细信息
        """
        log_message = f"User: {user_id}, Operation: {operation}, Resource: {resource}, Success: {success}"
        if details:
            log_message += f", Details: {details}"
        
        self.logger.info(log_message)
        logger.info(log_message)


# 创建全局实例
token_verifier = TokenVerifier()
auth_manager = AuthManager()
permission_manager = PermissionManager()
operation_logger = OperationLogger()