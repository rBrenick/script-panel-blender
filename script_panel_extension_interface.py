import os

class ScriptPanelExtension(object):

    def get_default_root_paths(self):
        return [os.path.join(os.path.dirname(__file__), "example_dir")]
