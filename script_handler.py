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
        self.local_config_path = ""
        self.shared_config_path = ""

        self.is_favorite = None

    def update_from_dict(self, config):
        self.label = config.get("label", self.label)
        self.icon_name = config.get("icon_name", self.icon_name)
        self.icon_path = config.get("icon_path", self.icon_path)
        self.is_favorite = config.get("is_favorite", self.is_favorite)

    def to_dict(self):
        out_dict = {}

        if self.label and self.label != get_default_label(self.path):
            out_dict["label"] = self.label

        if self.icon_name:
            out_dict["icon_name"] = self.icon_name

        if self.icon_path:
            out_dict["icon_path"] = self.icon_path
        
        if self.is_favorite is not None:
            out_dict["is_favorite"] = self.is_favorite

        return out_dict
    
    def save_to_config(self, to_local):
        config_path = self.local_config_path if to_local else self.shared_config_path

        configs = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as fp:
                configs = json.load(fp)

        config_dict = self.to_dict()

        # ensure we don't accidentally save favorites to shared config
        if not to_local and "is_favorite" in config_dict.keys():
            config_dict.pop("is_favorite")

        if not config_dict and self.relative_path in configs.keys():
            # if nothing relevant is in the config, remove the entry entirely
            configs.pop(self.relative_path)
        else:
            configs[self.relative_path] = config_dict

        with open(config_path, "w") as fp:
            json.dump(configs, fp, indent=2)


class ScriptHandler():
    def __init__(self):
        self.scripts = []
        self.expanded_dirs = {}

    def populate_scripts(self, root_paths):
        self.scripts = []
        # don't reset self.expanded_dirs so we can keep the state when refreshing

        for root_path in root_paths:
            scripts_root_path = os.path.join(root_path, "scripts")
            if not os.path.exists(scripts_root_path):
                print(f"failed to find: {scripts_root_path}")
                continue

            shared_config_path = os.path.join(root_path, "shared_config.json")
            local_config_path = os.path.join(root_path, "local_config.json")
            combined_configs = {}
            for config_path in [shared_config_path, local_config_path]:
                if os.path.exists(config_path):
                    with open(config_path, "r") as fp:
                        combined_configs.update(json.load(fp))

            # recalculate folder name since blender chucks an extra slash on a folder path
            root_path_name = os.path.basename(os.path.dirname(scripts_root_path))

            # if there's only one root path can skip a level of indendation in the UI
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
                    script_inst.label = get_default_label(script_file_path)
                    script_inst.relative_dir = display_relative_dir
                    script_inst.relative_path = script_relative_path
                    script_inst.shared_config_path = shared_config_path
                    script_inst.local_config_path = local_config_path

                    # update any extra settings that have been saved in a config
                    script_config = combined_configs.get(script_relative_path, {})
                    script_inst.update_from_dict(script_config)

                    self.scripts.append(script_inst)

    def get_filtered_scripts(self, filter_text):
        script : Script
        for script in self.scripts:
            if filter_text in script.label.lower():
                yield script

    def get_favorited_scripts(self):
        script : Script
        for script in self.scripts:
            if script.is_favorite:
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


def get_default_label(script_path):
    return os.path.splitext(os.path.basename(script_path))[0]


SCRIPT_HANDLER = ScriptHandler()
