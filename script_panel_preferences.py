import os
import bpy

from . import script_handler
from . import script_panel_extension_system


class ScriptPanel_RootPath(bpy.types.PropertyGroup):
    dir_path: bpy.props.StringProperty(subtype="DIR_PATH")


class ScriptPanel_AddDirEntry(bpy.types.Operator):
    bl_idname = "scriptpanel.add_root_dir_entry"
    bl_label = "Add Root Dir"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = get_preferences()
        prefs.root_paths.add()
        return {'FINISHED'}
    

class ScriptPanel_RemoveDirEntry(bpy.types.Operator):
    bl_idname = "scriptpanel.remove_root_dir_entry"
    bl_label = "Remove Dir"
    bl_options = {'REGISTER', 'UNDO'}

    idx: bpy.props.IntProperty()

    def execute(self, context):
        prefs = get_preferences()
        prefs.root_paths.remove(self.idx)
        return {'FINISHED'}
    

class ScriptPanel_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    
    button_scale: bpy.props.FloatProperty(
        name="Buttons Scale",
        default = 1,
        description="Scale of button row",
        min=0.05,
        )
    
    root_paths: bpy.props.CollectionProperty(
        name="Root Paths",
        type=ScriptPanel_RootPath,
        )
    
    external_editor_path: bpy.props.StringProperty(
        name="External Code Editor",
        subtype="FILE_PATH",
        )
    
    favorites_layout_horizontal: bpy.props.BoolProperty(
        name="Layout Horizontal",
        description="Put all the favorites in a single row, jumping to the next row at the threshold.\n(Disables the edit and favorite buttons. Functionallity can still be accessed via right click)",
        )
    
    favorites_show_label: bpy.props.BoolProperty(
        name="Show Labels",
        default=True,
        description="Toggle button labels visibility",
        )
    
    favorites_button_scale: bpy.props.FloatProperty(
        name="Favorites Buttons Scale",
        default = 1,
        description="Scale of button row",
        min=0.05,
        )
    
    favorites_row_threshold: bpy.props.IntProperty(
        name="Row Threshold",
        default = 3,
        description="How many buttons in a row before jumping to the next one.",
        min=1,
        )

    def draw(self, context):
        layout = self.layout
        draw_preferences(layout)

    def get_root_dir_paths(self):
        root_path : ScriptPanel_RootPath
        output_paths = []
        for root_path in self.root_paths:
            output_paths.append(root_path.dir_path)
        return output_paths


def draw_preferences(layout):
    prefs = get_preferences()
    has_favorites = len(script_handler.instance.favorite_scripts) > 0
    
    layout.prop(prefs, "button_scale")

    favorites_header, favorites_body = layout.panel("Favorites", default_closed=True)
    favorites_header.label(text="Favorites")
    favorites_header.enabled = has_favorites
    if favorites_body:
        favorites_body.enabled = has_favorites
        favorites_body.prop(prefs, "favorites_button_scale")
        horizontal_row = favorites_body.row()
        horizontal_row.prop(prefs, "favorites_layout_horizontal", expand=True)
        if prefs.favorites_layout_horizontal:
            horizontal_row.prop(prefs, "favorites_row_threshold", expand=True)
        favorites_body.prop(prefs, "favorites_show_label")
    
    root_paths_header, root_paths_body = layout.panel("RootPaths", default_closed=True)
    root_paths_header.label(text="Root Dirs")

    if root_paths_body:
        operator_row = root_paths_body.row()
        operator_row.alignment = "RIGHT"
        operator_row.operator(ScriptPanel_AddDirEntry.bl_idname, icon="PLUS", text="Add Root Dir")

        root_path : ScriptPanel_RootPath
        for i, root_path in enumerate(prefs.root_paths):
            row = root_paths_body.row()
            row.prop(root_path, "dir_path", text="")
            remove_op = row.operator(ScriptPanel_RemoveDirEntry.bl_idname, icon="X", text="")
            remove_op.idx = i

    editing_header, editing_body = layout.panel("EditingPrefs", default_closed=True)
    editing_header.label(text="Editing Prefs")

    if editing_body:
        editing_body.label(text="External Code Editor")
        editing_body.prop(prefs, "external_editor_path", text="")


def get_preferences() -> ScriptPanel_Preferences: 
    return bpy.context.preferences.addons[__package__].preferences


CLASS_LIST = (
    ScriptPanel_RootPath,
    ScriptPanel_AddDirEntry,
    ScriptPanel_RemoveDirEntry,
    ScriptPanel_Preferences,
)


def register():
    for cls in CLASS_LIST:
        bpy.utils.register_class(cls)

    # default prefs
    prefs = get_preferences()
    if len(prefs.root_paths) == 0:
    
        default_root_paths = script_panel_extension_system.get_extension_cls().get_default_root_paths()
        for root_path in default_root_paths:
            item : ScriptPanel_RootPath = prefs.root_paths.add()
            item.dir_path = root_path


def unregister():
    for cls in CLASS_LIST:
        bpy.utils.unregister_class(cls)
