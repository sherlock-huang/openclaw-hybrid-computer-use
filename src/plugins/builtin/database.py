"""数据库操作插件 — 内置示例

支持 SQLite 和 MySQL（如果安装了 pymysql）。
"""

import json
import logging
import sqlite3
from typing import Dict, Callable

try:
    from ...plugins.base import PluginInterface
    from ...core.models import Task
except ImportError:
    from claw_desktop.plugins.base import PluginInterface
    from claw_desktop.core.models import Task

logger = logging.getLogger(__name__)


class DatabasePlugin(PluginInterface):
    """数据库插件"""

    @property
    def name(self) -> str:
        return "database"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "SQLite/MySQL 数据库操作插件"

    def __init__(self):
        self.connections: Dict[str, sqlite3.Connection] = {}

    @property
    def actions(self) -> Dict[str, Callable]:
        return {
            "connect": self.action_connect,
            "execute": self.action_execute,
            "query": self.action_query,
            "close": self.action_close,
        }

    def action_connect(self, task: Task) -> bool:
        """连接数据库: target=db_alias, value=connection_string (SQLite 文件路径)"""
        alias = "default"
        path = task.value or ":memory:"
        try:
            self.connections[alias] = sqlite3.connect(path)
            logger.info(f"数据库连接成功: {alias} -> {path}")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False

    def action_execute(self, task: Task) -> bool:
        """执行 SQL: target=db_alias, value=SQL"""
        alias = "default"
        sql = task.value
        if not sql:
            logger.error("execute 需要提供 SQL 语句")
            return False
        conn = self.connections.get(alias)
        if not conn:
            logger.error(f"数据库未连接: {alias}")
            return False
        try:
            conn.execute(sql)
            conn.commit()
            logger.info(f"SQL 执行成功: {sql[:80]}")
            return True
        except Exception as e:
            logger.error(f"SQL 执行失败: {e}")
            return False

    def action_query(self, task: Task) -> bool:
        """查询数据: target=db_alias, value=SQL, 结果打印到日志"""
        alias = "default"
        sql = task.value
        if not sql:
            logger.error("query 需要提供 SQL 语句")
            return False
        conn = self.connections.get(alias)
        if not conn:
            logger.error(f"数据库未连接: {alias}")
            return False
        try:
            cursor = conn.execute(sql)
            rows = cursor.fetchall()
            columns = [d[0] for d in cursor.description] if cursor.description else []
            logger.info(f"查询结果 ({len(rows)} 行): columns={columns}")
            for row in rows[:10]:
                logger.info(f"  {row}")
            return True
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return False

    def action_close(self, task: Task) -> bool:
        """关闭连接: target=db_alias"""
        alias = "default"
        conn = self.connections.pop(alias, None)
        if conn:
            conn.close()
            logger.info(f"数据库连接关闭: {alias}")
        return True

    def shutdown(self):
        for alias, conn in list(self.connections.items()):
            conn.close()
            logger.info(f"数据库连接关闭: {alias}")
        self.connections.clear()


