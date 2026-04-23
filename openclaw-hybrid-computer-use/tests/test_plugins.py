"""插件系统测试"""

import pytest
from claw_desktop.plugins.loader import PluginLoader
from claw_desktop.plugins.base import PluginInterface
from claw_desktop.core.models import Task


class DummyPlugin(PluginInterface):
    @property
    def name(self):
        return "dummy"

    @property
    def version(self):
        return "0.1.0"

    @property
    def actions(self):
        return {"echo": self.action_echo}

    def action_echo(self, task: Task) -> bool:
        return True


class TestPluginLoader:
    def test_load_and_invoke(self):
        loader = PluginLoader()
        plugin = DummyPlugin()
        plugin.initialize()
        loader.plugins[plugin.name] = plugin

        assert loader.get_plugin("dummy") is not None
        result = loader.invoke_action("dummy", "echo", Task("test"))
        assert result is True

    def test_list_plugins(self):
        loader = PluginLoader()
        plugin = DummyPlugin()
        loader.plugins[plugin.name] = plugin
        plugins = loader.list_plugins()
        assert len(plugins) == 1
        assert plugins[0]["name"] == "dummy"
        assert "echo" in plugins[0]["actions"]


class TestBuiltinPlugins:
    def test_database_plugin_exists(self):
        from claw_desktop.core.executor import TaskExecutor
        te = TaskExecutor()
        plugin = te.plugin_loader.get_plugin("database")
        assert plugin is not None
        assert "connect" in plugin.actions

    def test_api_plugin_exists(self):
        from claw_desktop.core.executor import TaskExecutor
        te = TaskExecutor()
        plugin = te.plugin_loader.get_plugin("api")
        assert plugin is not None
        assert "get" in plugin.actions