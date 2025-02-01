import os
import json

class Script():
    def __init__(self):
        self.path = ""
        self.label = ""
        self.icon_name = ""
        self.icon_path = ""
        self.relative_dir = ""
        self.relative_path = ""
        self.config_path = ""

    def update_from_dict(self, config):
        self.label = config.get("label", self.label)
        self.icon_name = config.get("icon_name", self.icon_name)
        self.icon_path = config.get("icon_path", self.icon_path)

    def to_dict(self):
        out_dict = {}

        if self.label:
            out_dict["label"] = self.label

        if self.icon_name:
            out_dict["icon_name"] = self.icon_name

        if self.icon_path:
            out_dict["icon_path"] = self.icon_path

        return out_dict
    
    def save_to_config_file(self):
        configs = {}
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as fp:
                configs = json.load(fp)

        configs[self.relative_path] = self.to_dict()

        with open(self.config_path, "w") as fp:
            json.dump(configs, fp, indent=2)


class ScriptHandler():
    def __init__(self):
        self.scripts = []
        self.expanded_dirs = {}
        self.populate_scripts()

    def populate_scripts(self):
        self.scripts = []
        # don't reset expanded_dirs so we can keep the state when refreshing

        root_paths = [
            os.path.join(os.path.dirname(__file__), "example_dir"),
            ]

        for root_path in root_paths:
            scripts_root_path = os.path.join(root_path, "scripts")
            if not os.path.exists(scripts_root_path):
                print(f"failed to find: {scripts_root_path}")
                continue

            config_path = os.path.join(root_path, "config.json")
            configs = {}
            if os.path.exists(config_path):
                with open(config_path, "r") as fp:
                    configs = json.load(fp)

            root_path_name = os.path.basename(root_path)
            if len(root_paths) == 1:
                root_path_name = ""

            for parent_dir, _, files in os.walk(scripts_root_path):
                relative_dir = os.path.relpath(parent_dir, scripts_root_path).replace("\\", "/")

                # calculate relative_dir for grouping display
                default_expand_state = False
                display_relative_dir = f"{root_path_name}/{relative_dir}" if root_path_name else relative_dir
                if relative_dir == ".":
                    display_relative_dir = root_path_name
                    default_expand_state = True

                # set default expand state
                if not self.expanded_dirs.get(display_relative_dir):
                    self.expanded_dirs[display_relative_dir] = default_expand_state

                for script_file_name in files:
                    if ".py" not in script_file_name:
                        continue

                    script_file_path = os.path.join(parent_dir, script_file_name)
                    script_relative_path = os.path.relpath(script_file_path, root_path)

                    script_inst = Script()
                    script_inst.path = script_file_path
                    script_inst.label = os.path.splitext(script_file_name)[0]
                    # script_inst.icon_name = "FILE_REFRESH"
                    script_inst.relative_dir = display_relative_dir
                    script_inst.relative_path = script_relative_path
                    script_inst.config_path = config_path

                    # update any extra settings that have been saved in a config
                    script_config = configs.get(script_relative_path, {})
                    script_inst.update_from_dict(script_config)

                    self.scripts.append(script_inst)

    def get_filtered_scripts(self, filter_text):
        script : Script
        for script in self.scripts:
            if filter_text in script.label.lower():
                yield script

    def get_filtered_dirs(self, filter_text):
        rel_dirs = set()
        for script in self.get_filtered_scripts(filter_text):
            rel_dirs.add(script.relative_dir)
        return rel_dirs
    
    def get_all_relative_dirs(self):
        return self.expanded_dirs.keys()

    def get_script_from_path(self, path):
        for script in self.scripts:
            if script.path == path:
                return script

    def get_expanded_dirs(self):
        for dir, state in self.expanded_dirs.items():
            if state:
                yield dir


SCRIPT_HANDLER = ScriptHandler()
