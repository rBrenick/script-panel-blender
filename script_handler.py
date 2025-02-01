import os


class Script():
    def __init__(self):
        self.path = ""
        self.label = ""
        self.icon_name = ""
        self.icon_path = ""
        self.relative_dir = ""


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
                    script_file_path = os.path.join(parent_dir, script_file_name)

                    script_inst = Script()
                    script_inst.path = script_file_path
                    script_inst.label = os.path.splitext(script_file_name)[0]
                    # script_inst.icon_name = "FILE_REFRESH"
                    script_inst.relative_dir = display_relative_dir
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

    def get_expanded_dirs(self):
        for dir, state in self.expanded_dirs.items():
            if state:
                yield dir
