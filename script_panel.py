import os
import time
import runpy

import bpy

from . import icon_manager
from . import script_handler
from . import script_edit_box
from . script_panel_preferences import get_preferences, draw_root_path_prefs


def refresh_script_handler():
    prefs = get_preferences()
    script_handler.SCRIPT_HANDLER.populate_scripts(prefs.get_root_dir_paths())


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
        refresh_script_handler()
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


class ScriptPanelAddScript(bpy.types.Operator):
    bl_idname = "scriptpanel.add_script"
    bl_label = "Add Script"
    bl_description = ""

    script_name: bpy.props.StringProperty(default="ScriptName")
    script_dir: bpy.props.StringProperty(subtype="DIR_PATH")
    auto_open: bpy.props.BoolProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        output_path = f"{self.script_dir}/{self.script_name}.py"

        if os.path.exists(output_path):
            self.report({'INFO'}, f"path already exists: {output_path}")
            return {"FINISHED"}

        default_file_content = []
        default_file_content.append(f"# created by: {os.getenv('USERNAME')}\n")
        default_file_content.append(f"# creation date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        default_file_content.append("import bpy\n")
        default_file_content.append("")

        with open(output_path, "w") as fp:
            fp.writelines(default_file_content)
        
        refresh_script_handler()

        if self.auto_open:
            open_script(output_path)

        return {"FINISHED"}


class ScriptPanelOpenScript(bpy.types.Operator):
    bl_idname = "scriptpanel.open_script"
    bl_label = "Open Script"
    bl_description = ""

    target_script_path: bpy.props.StringProperty()

    def execute(self, context):
        open_script(self.target_script_path)
        return {"FINISHED"}


def open_script(script_path):
    open_script_window()

    existing_text = None
    for text in bpy.data.texts:
        if text.filepath == script_path:
            existing_text = text
            break
    
    if not existing_text:
        bpy.ops.text.open(filepath=script_path, check_existing=True)
        existing_text = bpy.data.texts.get(os.path.basename(script_path))
    
    if not existing_text:
        print(f"could not find text block for file: {script_path}")
        return
    
    text_editor_space = find_text_editor_space()
    if text_editor_space:
        text_editor_space.text = existing_text


def find_text_editor_space():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != "TEXT_EDITOR":
                continue

            for space in area.spaces:
                if hasattr(space, "text"):
                    return space


def open_script_window():
    context = bpy.context

    if find_text_editor_space():
        return
    
    current_windows = set(context.window_manager.windows)
    if 'FINISHED' not in bpy.ops.wm.window_new():
        return

    window, = set(context.window_manager.windows) - current_windows
    area = window.screen.areas[0]
    area.ui_type = 'TEXT_EDITOR'


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
        
        add_script_row = layout.row()
        add_script_row.alignment = "RIGHT"
        add_script_op : ScriptPanelAddScript = add_script_row.operator(ScriptPanelAddScript.bl_idname, icon="PLUS", text="")
        add_script_op.script_dir = f"{HANDLER.primary_dir}/scripts"

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


CLASS_LIST = (
    ScriptPanelExecuteScript,
    ScriptPanelRefresh,
    ScriptPanelToggleExpandState,
    ScriptPanelAddScript,
    ScriptPanelOpenScript,
)


class WM_MT_button_context(bpy.types.Menu):
    bl_label = ""
    def draw(self, context):
        pass


def script_panel_right_click(self, context):
    layout = self.layout
    if hasattr(context, "button_operator") and hasattr(context.button_operator, "target_script_path"):
        open_script_op = layout.operator(ScriptPanelOpenScript.bl_idname)
        open_script_op.target_script_path = getattr(context.button_operator, "target_script_path")


def register():
    icon_manager.register()
    script_edit_box.register()
    for cls in CLASS_LIST:
        bpy.utils.register_class(cls)
    bpy.utils.register_class(ScriptPanelPropertyGroup)
    bpy.utils.register_class(RENDER_PT_ScriptPanel)
    bpy.types.Scene.script_panel_props = bpy.props.PointerProperty(type=ScriptPanelPropertyGroup)

    # custom right click https://blenderartists.org/t/add-operator-to-right-click-menu-for-operators/1249718
    rcmenu = getattr(bpy.types, "WM_MT_button_context", None)
    if rcmenu is None:
        bpy.utils.register_class(WM_MT_button_context)
        rcmenu = WM_MT_button_context
    draw_funcs = rcmenu._dyn_ui_initialize()
    draw_funcs.append(script_panel_right_click)

    refresh_script_handler()


def unregister():
    rcmenu = getattr(bpy.types, "WM_MT_button_context", None)
    if rcmenu is not None:
        rcmenu = WM_MT_button_context
        draw_funcs = rcmenu._dyn_ui_initialize()
        draw_funcs.remove(script_panel_right_click)
        bpy.utils.unregister_class(WM_MT_button_context)

    for cls in CLASS_LIST:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_class(RENDER_PT_ScriptPanel)
    bpy.utils.unregister_class(ScriptPanelPropertyGroup)
    del bpy.types.Scene.script_panel_props
    script_edit_box.unregister()
    icon_manager.unregister()
