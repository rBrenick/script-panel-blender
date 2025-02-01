import os
import json
import bpy
import runpy


class Script():
    def __init__(self):
        self.path = ""
        self.icon = ""
        self.label = ""
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


class ScriptPanelExecuteScript(bpy.types.Operator):
    bl_idname = "screen.script_panel_exec"
    bl_label = "ExecuteScript"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    target_script_path: bpy.props.StringProperty()

    def execute(self, context):
        runpy.run_path(self.target_script_path)
        return {"FINISHED"}
    

class ScriptPanelRefresh(bpy.types.Operator):
    bl_idname = "scriptpanel.refresh_scripts"
    bl_label = "Refresh ScriptPanel scripts"
    bl_description = ""

    def execute(self, context):
        SCRIPT_HANDLER.populate_scripts()
        return {"FINISHED"}


class ScriptPanelToggleExpandState(bpy.types.Operator):
    bl_idname = "scriptpanel.toggle_dir_expand_state"
    bl_label = "Toggle"
    bl_description = ""

    rel_dir: bpy.props.StringProperty()

    def execute(self, context):
        current_state = SCRIPT_HANDLER.expanded_dirs.get(self.rel_dir, False)
        SCRIPT_HANDLER.expanded_dirs[self.rel_dir] = not current_state
        return {"FINISHED"}


class RENDER_PT_ScriptPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_ScriptPanel"
    bl_label = "Script Panel"

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ScriptPanel"

    bl_options = {"HEADER_LAYOUT_EXPAND"}

    def draw(self, context):
        layout = self.layout

        panel_props: ScriptPanelPropertyGroup = context.scene.script_panel_props 

        top_row = layout.row()
        top_row.scale_y = 1.2
        top_row.prop(panel_props, "search_text", placeholder="search")
        top_row.operator(ScriptPanelRefresh.bl_idname, text="", icon="FILE_REFRESH")
        filter_text = panel_props.search_text.lower()

        main_box = layout.box()
        filtered_dirs = SCRIPT_HANDLER.get_filtered_dirs(filter_text)
        expanded_dirs = SCRIPT_HANDLER.get_all_relative_dirs() if filter_text else list(SCRIPT_HANDLER.get_expanded_dirs())
        dir_boxes = self.create_dir_boxes(main_box, filtered_dirs, expanded_dirs)
        
        found_script = False
        script: Script
        for script in SCRIPT_HANDLER.get_filtered_scripts(filter_text):
            if script.relative_dir not in expanded_dirs:
                continue

            dir_box = dir_boxes.get(script.relative_dir)
            if script.relative_dir == "":
                dir_box = main_box

            if not dir_box:
                continue
            
            op = dir_box.operator(ScriptPanelExecuteScript.bl_idname, text=script.label)
            op.target_script_path = script.path
            found_script = True

        if not found_script and filter_text:
            main_box.label(text="Found no scripts")

    def create_dir_boxes(self, main_box, relative_dirs, expanded_dirs = list()):
        dir_boxes = {}

        sorted_dirs = reversed(sorted(relative_dirs, key=lambda x: x.count("/")))
        for dir_path in sorted_dirs:

            parent_box = main_box

            creation_path = ""
            for path_token in dir_path.split("/"):
                parent_dir = creation_path
                parent_is_collapsed = parent_dir not in expanded_dirs if parent_dir else False
                if parent_is_collapsed:
                    continue
                    
                creation_path = f"{creation_path}/{path_token}" if creation_path else path_token

                # can skip creating a box for the root dir
                if not creation_path:
                    continue

                dir_is_collapsed = creation_path not in expanded_dirs

                if not dir_boxes.get(creation_path):
                    dir_box = parent_box.box()

                    toggle_icon = "RIGHTARROW" if dir_is_collapsed else "DOWNARROW_HLT"
                    expand_toggle = dir_box.operator(
                        ScriptPanelToggleExpandState.bl_idname,
                        text=path_token,
                        emboss=False,
                        icon=toggle_icon,
                        )
                    expand_toggle.rel_dir = creation_path

                    dir_boxes[creation_path] = dir_box

                # update variable for next token
                parent_box = dir_boxes.get(creation_path)

        return dir_boxes


class ScriptPanelPropertyGroup(bpy.types.PropertyGroup):
    search_text: bpy.props.StringProperty(name="", options={'TEXTEDIT_UPDATE'})


SCRIPT_HANDLER = ScriptHandler()

CLASS_LIST = [
    ScriptPanelExecuteScript,
    ScriptPanelRefresh,
    ScriptPanelToggleExpandState,
]

def register():
    for cls in CLASS_LIST:
        bpy.utils.register_class(cls)
    bpy.utils.register_class(ScriptPanelPropertyGroup)
    bpy.utils.register_class(RENDER_PT_ScriptPanel)
    bpy.types.Scene.script_panel_props = bpy.props.PointerProperty(type=ScriptPanelPropertyGroup)


def unregister():
    for cls in CLASS_LIST:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_class(RENDER_PT_ScriptPanel)
    bpy.utils.unregister_class(ScriptPanelPropertyGroup)
    del bpy.types.Scene.script_panel_props
