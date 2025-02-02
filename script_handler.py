import os
import json

class Script():
    def __init__(self):
        self.path = ""
        self.label = ""
        self.tooltip = ""
        self.icon_name = ""
        self.icon_path = ""
        self.relative_dir = ""
        self.relative_path = ""
        self.local_config_path = ""
        self.shared_config_path = ""

        self.is_favorited = False

    def update_from_dict(self, config):
        self.label = config.get("label", self.label)
        self.tooltip = config.get("tooltip", self.tooltip)
        self.icon_name = config.get("icon_name", self.icon_name)
        self.icon_path = config.get("icon_path", self.icon_path)

    def to_dict(self):
        out_dict = {}

        if self.label and self.label != get_default_label(self.path):
            out_dict["label"] = self.label

        if self.tooltip:
            out_dict["tooltip"] = self.tooltip

        if self.icon_name:
            out_dict["icon_name"] = self.icon_name

        if self.icon_path:
            out_dict["icon_path"] = self.icon_path

        return out_dict
        
    def get_config_key(self):
        return self.relative_path

    def save_to_config(self, to_local):
        config_path = self.local_config_path if to_local else self.shared_config_path

        full_config_data = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as fp:
                full_config_data = json.load(fp)

        script_configs = full_config_data.get("script_configs", {})
        config_dict = self.to_dict()

        config_key = self.get_config_key()
        if not config_dict and config_key in script_configs.keys():
            # if nothing relevant is in the config, remove the entry entirely
            script_configs.pop(config_key)
        else:
            script_configs[config_key] = config_dict

        full_config_data["script_configs"] = script_configs
        with open(config_path, "w") as fp:
            json.dump(full_config_data, fp, indent=2)

    def set_favorited_state(self, state=True):

        favorites_list = self.get_local_favorites_list()

        config_key = self.get_config_key()
        if state:
            if config_key not in favorites_list:
                favorites_list.append(config_key)
        else:
            if config_key in favorites_list:
                favorites_list.remove(config_key)

        self.set_local_favorites_list(favorites_list)
        self.is_favorited = state

    def reorder_in_favorites(self, direction=1):
        ckey = self.get_config_key()
        favorites_list = self.get_local_favorites_list()
        if ckey not in favorites_list:
            return
        
        current_index = favorites_list.index(ckey)
        new_index = current_index + direction

        # wrap around logic
        if new_index == -1:
            new_index = len(favorites_list) - 1

        if new_index == len(favorites_list):
            new_index = 0

        favorites_list.remove(ckey)
        favorites_list.insert(new_index, ckey)

        self.set_local_favorites_list(favorites_list)

    def get_local_favorites_list(self):
        return self.get_local_config_data().get("favorites", [])

    def set_local_favorites_list(self, new_list):
        full_config_data = self.get_local_config_data()
        full_config_data["favorites"] = new_list

        with open(self.local_config_path, "w") as fp:
            json.dump(full_config_data, fp, indent=2)

    def get_local_config_data(self):
        config_path = self.local_config_path

        full_config_data = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as fp:
                full_config_data = json.load(fp)

        return full_config_data
    

class ScriptHandler():
    def __init__(self):
        self.active_root_paths = []
        self.scripts = {}
        self.favorite_scripts = []
        self.expanded_dirs = {}
        self.primary_dir = None

    def populate_scripts(self, root_paths):
        self.scripts = {}
        self.favorite_scripts = []
        self.primary_dir = None
        self.active_root_paths = root_paths
        # don't reset self.expanded_dirs so we can keep the state when refreshing

        for root_path in root_paths:
            if self.primary_dir is None:
                self.primary_dir = root_path
            
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
                        config_data = json.load(fp)
                    merge_dicts(combined_configs, config_data)

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
                    script_config = combined_configs.get("script_configs", {}).get(script_inst.get_config_key(), {})
                    script_inst.update_from_dict(script_config)

                    self.scripts[script_file_path] = script_inst

        self.update_favorites()

    def get_filtered_scripts(self, filter_text):
        script : Script
        for script in self.scripts.values():
            if filter_text in script.label.lower():
                yield script

    def update_favorites(self):
        self.favorite_scripts = []
        for root_path in self.active_root_paths:
            local_config_path = os.path.join(root_path, "local_config.json")

            if not os.path.exists(local_config_path):
                continue

            with open(local_config_path, "r") as fp:
                config_json = json.load(fp)

            # get script instances for each favorite
            for config_favorite in config_json.get("favorites", []):
                script = self.get_script_inst_from_config_key(config_favorite)
                if script:
                    script.is_favorited = True
                    self.favorite_scripts.append(script)

    def get_favorited_scripts(self):
        return self.favorite_scripts

    def get_filtered_dirs(self, filter_text):
        rel_dirs = set()
        for script in self.get_filtered_scripts(filter_text):
            rel_dirs.add(script.relative_dir)
        return rel_dirs
    
    def get_all_relative_dirs(self):
        return self.expanded_dirs.keys()

    def get_script_inst_from_path(self, path):
        return self.scripts.get(path)

    def get_script_inst_from_config_key(self, path):
        script : Script
        for script in self.scripts.values():
            if script.get_config_key() == path:
                return script

    def get_expanded_dirs(self):
        for dir, state in self.expanded_dirs.items():
            if state:
                yield dir


def merge_dicts(a, b):
    for key, val in b.items():
        if key not in a:
            a[key] = val
            continue

        if isinstance(val, dict):
            merge_dicts(a[key], val)
        else:
            a[key] = val
    return a

def get_default_label(script_path):
    return os.path.splitext(os.path.basename(script_path))[0]


SCRIPT_HANDLER = ScriptHandler()
