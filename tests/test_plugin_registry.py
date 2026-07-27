from plexai_verify.app.plugins.registry import PluginRegistry


class FakePlugin:
    key = "fake"
    name = "Fake"

    def is_available(self) -> bool:
        return True


def test_plugin_registry_status():
    registry = PluginRegistry()
    registry.register(FakePlugin())
    statuses = registry.statuses()
    assert len(statuses) == 1
    assert statuses[0].key == "fake"
    assert statuses[0].available is True
