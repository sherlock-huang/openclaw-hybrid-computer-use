"""插件加载器

支持从以下位置加载插件：
1. src/plugins/builtin/ — 内置插件
2. plugins/ — 用户自定义插件目录（项目根目录）
3. 通过 Python 路径动态导入
"""

import importlib
import inspect
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import PluginInterface, PluginContext

logger = logging.getLogger(__name__)


class PluginLoader:
    """插件加载器"""

    BUILTIN_DIR = Path(__file__).parent / "builtin"
    USER_DIR = Path.cwd() / "plugins"

    def __init__(self):
        self.plugins: Dict[str, PluginInterface] = {}
        self.context = PluginContext()
        self.logger = logging.getLogger(__name__)

    def load_builtin_plugins(self):
        """加载内置插件"""
        if not self.BUILTIN_DIR.exists():
            self.logger.warning(f"内置插件目录不存在: {self.BUILTIN_DIR}")
            return
        self._load_from_directory(self.BUILTIN_DIR)

    def load_user_plugins(self):
        """加载用户自定义插件"""
        if not self.USER_DIR.exists():
            self.logger.info(f"用户插件目录不存在，跳过: {self.USER_DIR}")
            return
        self._load_from_directory(self.USER_DIR)

    def _load_from_directory(self, directory: Path):
        """从目录加载所有插件"""
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))

        for file_path in directory.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            self._load_module(file_path)

        # 也支持子目录（含 __init__.py 的包）
        for pkg_path in directory.iterdir():
            if pkg_path.is_dir() and (pkg_path / "__init__.py").exists():
                self._load_module(pkg_path / "__init__.py", package_name=pkg_path.name)

    def _load_module(self, file_path: Path, package_name: Optional[str] = None):
        """加载单个模块并注册插件"""
        try:
            module_name = file_path.stem
            if package_name:
                module_name = f"{package_name}.{module_name}"
                spec = importlib.util.spec_from_file_location(
                    module_name, file_path,
                    submodule_search_locations=[str(file_path.parent)]
                )
            else:
                spec = importlib.util.spec_from_file_location(module_name, file_path)

            if spec is None or spec.loader is None:
                return

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 查找插件类
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj)
                    and issubclass(obj, PluginInterface)
                    and obj is not PluginInterface
                    and not inspect.isabstract(obj)):
                    self._register_plugin(obj)

        except Exception as e:
            self.logger.warning(f"加载插件模块失败 {file_path}: {e}")

    def _register_plugin(self, plugin_cls: Type[PluginInterface]):
        """注册插件实例"""
        try:
            instance = plugin_cls()
            instance.initialize()

            if not instance.health_check():
                self.logger.warning(f"插件 {instance.name} 健康检查失败，跳过注册")
                return

            self.plugins[instance.name] = instance
            self.logger.info(f"插件注册成功: {instance.name} v{instance.version}")

        except Exception as e:
            self.logger.error(f"注册插件失败 {plugin_cls.__name__}: {e}")

    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        return self.plugins.get(name)

    def list_plugins(self) -> List[Dict]:
        """列出所有已加载插件"""
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "actions": list(p.actions.keys()),
            }
            for p in self.plugins.values()
        ]

    def unload_all(self):
        """卸载所有插件"""
        for plugin in self.plugins.values():
            try:
                plugin.shutdown()
            except Exception as e:
                self.logger.warning(f"卸载插件 {plugin.name} 出错: {e}")
        self.plugins.clear()

    def invoke_action(self, plugin_name: str, action_name: str, task) -> bool:
        """调用插件 action

        Args:
            plugin_name: 插件名
            action_name: action 名
            task: Task 对象

        Returns:
            是否成功
        """
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            self.logger.error(f"插件未找到: {plugin_name}")
            return False

        handler = plugin.actions.get(action_name)
        if not handler:
            self.logger.error(f"插件 {plugin_name} 没有 action: {action_name}")
            return False

        try:
            return handler(task)
        except Exception as e:
            self.logger.error(f"插件 action 执行失败 {plugin_name}.{action_name}: {e}")
            return False