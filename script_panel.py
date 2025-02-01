import runpy

import bpy

from . import icon_manager
from . import script_handler
from . import script_edit_box
from . script_panel_preferences import get_preferences, draw_root_path_prefs


class ScriptPanelExecuteScript(bpy.types.Operator):
    bl_idname = "wm.script_panel_exec"
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
        prefs = get_preferences()
        script_handler.SCRIPT_HANDLER.populate_scripts(prefs.get_root_dir_paths())
        return {"FINISHED"}


class ScriptPanelToggleExpandState(bpy.types.Operator):
    bl_idname = "scriptpanel.toggle_dir_expand_state"
    bl_label = "Toggle"
    bl_description = ""

    rel_dir: bpy.props.StringProperty()

    def execute(self, context):
        current_state = script_handler.SCRIPT_HANDLER.expanded_dirs.get(self.rel_dir, False)
        script_handler.SCRIPT_HANDLER.expanded_dirs[self.rel_dir] = not current_state
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
        top_row.prop(panel_props, "edit_mode_enabled", icon="GREASEPENCIL", text="")
        filter_text = panel_props.search_text.lower()

        main_box = layout.box()

        if panel_props.edit_mode_enabled:
            draw_root_path_prefs(main_box)
            main_box.separator(factor=2, type="LINE")

        HANDLER = script_handler.SCRIPT_HANDLER

        for favorite_script in HANDLER.get_favorited_scripts():
            self.draw_script_layout(main_box, favorite_script, panel_props.edit_mode_enabled)

        filtered_dirs = HANDLER.get_filtered_dirs(filter_text)
        expanded_dirs = HANDLER.get_all_relative_dirs() if filter_text else list(HANDLER.get_expanded_dirs())
        dir_boxes = self.create_dir_boxes(main_box, filtered_dirs, expanded_dirs)
        
        found_script = False
        script : script_handler.Script
        for script in HANDLER.get_filtered_scripts(filter_text):
            if script.is_favorite:
                continue

            if script.relative_dir not in expanded_dirs:
                continue

            dir_box = dir_boxes.get(script.relative_dir)
            if script.relative_dir == "":
                dir_box = main_box

            if not dir_box:
                continue
            
            self.draw_script_layout(dir_box, script, panel_props.edit_mode_enabled)

            found_script = True

        if not found_script and filter_text:
            main_box.label(text="Found no scripts")

    def draw_script_layout(self, parent, script, in_edit_mode = False):
        operator_kwargs = {}

        if script.icon_name:
            operator_kwargs["icon"] = script.icon_name

        if script.icon_path:
            operator_kwargs["icon_value"] = icon_manager.get_icon(script.icon_path)

        op_row = parent.row()
        op = op_row.operator(
            ScriptPanelExecuteScript.bl_idname,
            text=script.label,
            **operator_kwargs
            )
        op.target_script_path = script.path

        if in_edit_mode:
            edit_group = script_edit_box.get_edit_box_of_script(script)
            
            edit_op = op_row.operator(
                script_edit_box.ScriptPanelToggleScriptEditingBox.bl_idname,
                icon="CANCEL_LARGE" if edit_group else "GREASEPENCIL",
                text="",
                emboss=True,
                )
            edit_op.script_path = script.path
            
            favorite_op = op_row.operator(
                script_edit_box.ScriptPanelToggleFavorite.bl_idname,
                icon="ORPHAN_DATA" if script.is_favorite else "HEART",
                text="",
                emboss=True,
                )
            favorite_op.script_path = script.path
            
            script_edit_box.draw_script_edit_box(parent, edit_group)
    
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

                    toggle_icon = "FILE_FOLDER" if dir_is_collapsed else "DOWNARROW_HLT"
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
    edit_mode_enabled: bpy.props.BoolProperty()


CLASS_LIST = [
    ScriptPanelExecuteScript,
    ScriptPanelRefresh,
    ScriptPanelToggleExpandState,
]

def register():
    icon_manager.register()
    script_edit_box.register()
    for cls in CLASS_LIST:
        bpy.utils.register_class(cls)
    bpy.utils.register_class(ScriptPanelPropertyGroup)
    bpy.utils.register_class(RENDER_PT_ScriptPanel)
    bpy.types.Scene.script_panel_props = bpy.props.PointerProperty(type=ScriptPanelPropertyGroup)

    prefs = get_preferences()
    script_handler.SCRIPT_HANDLER.populate_scripts(prefs.get_root_dir_paths())


def unregister():
    for cls in CLASS_LIST:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_class(RENDER_PT_ScriptPanel)
    bpy.utils.unregister_class(ScriptPanelPropertyGroup)
    del bpy.types.Scene.script_panel_props
    script_edit_box.unregister()
    icon_manager.unregister()
