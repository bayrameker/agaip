# agaip/utils/plugin_loader.py
import importlib


def load_plugin(plugin_path: str):
    """
    Örnek plugin path: "agaip.plugins.dummy_model.DummyModelPlugin"
    İlgili modülü dinamik olarak yükler ve sınıfı döner.
    """
    module_name, class_name = plugin_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    plugin_class = getattr(module, class_name)
    return plugin_class
