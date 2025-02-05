import os
import time
import runpy

import bpy

from . import icon_manager
from . import script_handler
from . import script_edit_box
from . import script_panel_preferences
from . import script_panel_logger

log = script_panel_logger.get_logger()


def refresh_script_handler():
    prefs = script_panel_preferences.get_preferences()
    script_handler.instance.populate_scripts(prefs.get_root_dir_paths())


class ScriptPanel_ExecuteScript(bpy.types.Operator):
    bl_idname = "wm.script_panel_exec"
    bl_label = "ExecuteScript"
    bl_description = "Execute script"
    bl_options = {'REGISTER', 'UNDO'}

    target_script_path: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        script = script_handler.instance.get_script_from_path(properties.target_script_path)
        return f"{script.label} - {script.tooltip}"
    
    def execute(self, context):
        runpy.run_path(self.target_script_path)
        return {"FINISHED"}


class ScriptPanel_Refresh(bpy.types.Operator):
    bl_idname = "scriptpanel.refresh_scripts"
    bl_label = "Refresh ScriptPanel scripts"
    bl_description = "Refresh from disk"

    def execute(self, context):
        refresh_script_handler()
        return {"FINISHED"}


class ScriptPanel_ToggleDirExpandState(bpy.types.Operator):
    bl_idname = "scriptpanel.toggle_dir_expand_state"
    bl_label = "Collapse/Expand Folder"
    bl_description = "Show/Hide folder content"

    rel_dir: bpy.props.StringProperty()

    def execute(self, context):
        current_state = script_handler.instance.expanded_dirs.get(self.rel_dir, False)
        script_handler.instance.expanded_dirs[self.rel_dir] = not current_state
        return {"FINISHED"}


class ScriptPanel_AddScript(bpy.types.Operator):
    bl_idname = "scriptpanel.add_script"
    bl_label = "Add Script"
    bl_description = "Add a new python script to the folder"

    script_name: bpy.props.StringProperty(default="ScriptName")
    script_dir: bpy.props.StringProperty(subtype="DIR_PATH")
    auto_open: bpy.props.BoolProperty(default=True)

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


class ScriptPanel_OpenScript(bpy.types.Operator):
    bl_idname = "scriptpanel.open_script"
    bl_label = "Open Script"
    bl_description = "Open the target script in the text editor"

    target_script_path: bpy.props.StringProperty()

    def execute(self, context):
        open_script(self.target_script_path)
        return {"FINISHED"}


class ScriptPanel_OpenFolder(bpy.types.Operator):
    bl_idname = "scriptpanel.open_folder"
    bl_label = "Open Folder in Explorer"
    bl_description = "Open an explorer window to this folder"

    dir_path: bpy.props.StringProperty()

    def execute(self, context):
        import webbrowser
        webbrowser.open(self.dir_path)
        return {"FINISHED"}


def open_script(script_path):
    open_script_window()

    existing_text = None
    for text in bpy.data.texts:
        if text.filepath.replace("\\", "/") == script_path.replace("\\", "/"):
            existing_text = text
            break
    
    if not existing_text:
        bpy.ops.text.open(filepath=script_path, check_existing=True)
        existing_text = bpy.data.texts.get(os.path.basename(script_path))
    
    if not existing_text:
        log.warning(f"Could not find text block for file: {script_path}")
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

    # hijack a preference window since it's smaller by default
    bpy.ops.screen.userpref_show()

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

        panel_props: ScriptPanel_SceneProperties = context.scene.script_panel_props
        prefs = script_panel_preferences.get_preferences()

        top_row = layout.row()
        top_row.scale_y = 1.2
        top_row.prop(panel_props, "search_text", placeholder="search")
        top_row.operator(ScriptPanel_Refresh.bl_idname, text="", icon="FILE_REFRESH")
        top_row.prop(panel_props, "edit_mode_enabled", icon="GREASEPENCIL", text="")
        filter_text = panel_props.search_text.lower()

        main_box = layout.box()

        if panel_props.edit_mode_enabled:
            pref_box = main_box.box()
            script_panel_preferences.draw_preferences(pref_box)

        HANDLER = script_handler.instance

        favorites_layout = main_box
        if prefs.favorites_layout_horizontal:
            favorites_layout = main_box.row()
        
        fav_row_counter = 0
        for favorite_script in HANDLER.get_favorited_scripts():

            # add new row past a certain threshold
            if prefs.favorites_layout_horizontal:
                if fav_row_counter >= prefs.favorites_row_threshold:
                    favorites_layout = main_box.row()
                    fav_row_counter = 0
            
            self.draw_script_layout(
                favorite_script,
                favorites_layout,
                main_box,
                in_edit_mode = panel_props.edit_mode_enabled,
                horizontal_layout = prefs.favorites_layout_horizontal,
                show_label = prefs.favorites_show_label,
                button_scale = prefs.favorites_button_scale,
                in_favorites_panel = True
                )
            fav_row_counter += 1

        filtered_dirs = HANDLER.get_filtered_dirs(filter_text)
        expanded_dirs = HANDLER.get_all_relative_dirs() if filter_text else list(HANDLER.get_expanded_dirs())
        dir_boxes = self.draw_dir_boxes(main_box, filtered_dirs, expanded_dirs)
        
        found_script = False
        script : script_handler.Script
        for script in HANDLER.get_filtered_scripts(filter_text):
            if script.is_favorited:
                continue

            # if the folder is collapsed we can skip drawing this script
            if script.relative_dir not in expanded_dirs:
                continue

            dir_box = dir_boxes.get(script.relative_dir) if script.relative_dir else main_box
            if not dir_box:
                log.warning(f"Failed to find folder layout for button: {script.relative_path}")
                continue

            self.draw_script_layout(
                script,
                dir_box,
                dir_box,
                in_edit_mode=panel_props.edit_mode_enabled,
                button_scale=prefs.button_scale
                )

            found_script = True

        if not found_script and filter_text:
            main_box.label(text="Found no scripts")
        
        if HANDLER.primary_dir:
            bottom_row = layout.row()
            bottom_row.alignment = "RIGHT"

            add_script_op : ScriptPanel_AddScript = bottom_row.operator(ScriptPanel_AddScript.bl_idname, icon="PLUS", text="")
            add_script_op.script_dir = f"{HANDLER.primary_dir}/scripts"

            open_folder_op : ScriptPanel_OpenFolder = bottom_row.operator(ScriptPanel_OpenFolder.bl_idname, icon="FILE_FOLDER", text="")
            open_folder_op.dir_path = f"{HANDLER.primary_dir}/scripts"

        else:
            main_box.label(text="No root paths found.")
            main_box.label(text="Enter 'Edit' mode in the top right to set them.")
        
    def draw_script_layout(
            self,
            script : script_handler.Script,
            parent : bpy.types.UILayout,
            editbox_parent : bpy.types.UILayout,
            in_edit_mode = False,
            horizontal_layout = False,
            show_label = True,
            button_scale = 1,
            in_favorites_panel = False,
            ):
        operator_kwargs = {}

        has_icon = False
        if script.icon_name:
            operator_kwargs["icon"] = script.icon_name
            has_icon = True

        if script.icon_path:
            operator_kwargs["icon_value"] = icon_manager.get_icon(script.icon_path)
            has_icon = True

        # assign a default icon if there's nothing defined
        if not has_icon and not show_label:
            operator_kwargs["icon"] = "SCRIPT"

        op_row = parent.row()
        op_row.scale_y = button_scale
        op_layout = op_row
        
        if in_favorites_panel:
            op_col = op_row.column()
            op_col.scale_x = button_scale
            op_layout = op_col

        exec_op = op_layout.operator(
            ScriptPanel_ExecuteScript.bl_idname,
            text=script.label if show_label else "",
            **operator_kwargs
            )
        exec_op.target_script_path = script.path

        if in_edit_mode:

            edit_box = script_edit_box.get_edit_box_of_script(script)

            if not horizontal_layout:
                edit_buttons = op_row.row()
                edit_buttons.scale_x = 0.82

                edit_op = edit_buttons.operator(
                    script_edit_box.ScriptPanel_ToggleScriptEditingBox.bl_idname,
                    icon="CANCEL" if edit_box else "GREASEPENCIL",
                    text="",
                    emboss=True,
                    )
                edit_op.script_path = script.path
                
                favorite_op = edit_buttons.operator(
                    script_edit_box.ScriptPanel_ToggleFavorite.bl_idname,
                    icon="ORPHAN_DATA" if in_favorites_panel else "HEART",
                    text="",
                    emboss=True,
                    )
                favorite_op.script_path = script.path
                
                if in_favorites_panel:
                    reorder_up: script_edit_box.ScriptPanel_ReorderFavorite = edit_buttons.operator(
                        script_edit_box.ScriptPanel_ReorderFavorite.bl_idname,
                        icon="TRIA_UP",
                        text="",
                        emboss=True,
                        )
                    reorder_up.script_path = script.path
                    reorder_up.direction = -1
                    
                    reorder_down: script_edit_box.ScriptPanel_ReorderFavorite = edit_buttons.operator(
                        script_edit_box.ScriptPanel_ReorderFavorite.bl_idname,
                        icon="TRIA_DOWN",
                        text="",
                        emboss=True,
                        )
                    reorder_down.script_path = script.path
                    reorder_down.direction = 1
                
            script_edit_box.draw_script_edit_box(editbox_parent, edit_box)
    
    def draw_dir_boxes(self, main_box, relative_dirs, expanded_dirs = list()):
        """Create full hierarchy of folders, and subfolders for those that are expanded"""
        dir_boxes = {}

        for dir_path in sorted(relative_dirs):

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
                        ScriptPanel_ToggleDirExpandState.bl_idname,
                        text=path_token,
                        emboss=False,
                        icon=toggle_icon,
                        )
                    expand_toggle.rel_dir = creation_path

                    dir_boxes[creation_path] = dir_box

                # update variable for next token
                parent_box = dir_boxes.get(creation_path)

        return dir_boxes


class ScriptPanel_SceneProperties(bpy.types.PropertyGroup):
    search_text : bpy.props.StringProperty(name="", options={'TEXTEDIT_UPDATE'})
    edit_mode_enabled : bpy.props.BoolProperty()


CLASS_LIST = (
    ScriptPanel_ExecuteScript,
    ScriptPanel_Refresh,
    ScriptPanel_AddScript,
    ScriptPanel_OpenScript,
    ScriptPanel_OpenFolder,
    ScriptPanel_ToggleDirExpandState,
    ScriptPanel_SceneProperties,
    RENDER_PT_ScriptPanel
)


class WM_MT_button_context(bpy.types.Menu):
    bl_label = ""
    def draw(self, context):
        pass


def script_panel_right_click(self, context):
    layout = self.layout
    if hasattr(context, "button_operator") and hasattr(context.button_operator, "target_script_path"):
        script_path = getattr(context.button_operator, "target_script_path")

        edit_op = layout.operator(
            script_edit_box.ScriptPanel_ToggleScriptEditingBox.bl_idname,
            text="ScriptPanel - Customize Button",
            icon="GREASEPENCIL",
            )
        edit_op.script_path = script_path

        favorite_op = layout.operator(
            script_edit_box.ScriptPanel_ToggleFavorite.bl_idname,
            text="ScriptPanel - Toggle Favorite",
            icon="HEART",
            )
        favorite_op.script_path = script_path

        open_script_op = layout.operator(
            ScriptPanel_OpenScript.bl_idname,
            text="ScriptPanel - Open Script",
            icon="TEXT"
            )
        open_script_op.target_script_path = script_path


def register():
    script_panel_preferences.register()
    icon_manager.register()
    script_edit_box.register()

    for cls in CLASS_LIST:
        bpy.utils.register_class(cls)

    bpy.types.Scene.script_panel_props = bpy.props.PointerProperty(type=ScriptPanel_SceneProperties)

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

    del bpy.types.Scene.script_panel_props

    script_edit_box.unregister()
    icon_manager.unregister()
    script_panel_preferences.unregister()
