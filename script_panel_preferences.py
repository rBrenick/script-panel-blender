import os
import bpy


class ScriptPanelRootPath(bpy.types.PropertyGroup):
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
    

class ScriptPanelPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    root_paths: bpy.props.CollectionProperty(
        name="Root Paths",
        type=ScriptPanelRootPath,
        )
    
    favorites_horizontal: bpy.props.BoolProperty(
        name="Layout Horizontal"
        )
    
    favorites_show_label: bpy.props.BoolProperty(
        name="Show Labels",
        default=True,
        )

    horizontal_row_threshold: bpy.props.IntProperty(
        name="Row Threshold",
        default = 3,
        description="How many buttons in a row before jumping to the next one.",
        )
    
    def draw(self, context):
        layout = self.layout
        draw_root_path_prefs(layout)

    def get_root_dir_paths(self):
        root_path : ScriptPanelRootPath
        output_paths = []
        for root_path in self.root_paths:
            output_paths.append(root_path.dir_path)
        return output_paths


def draw_root_path_prefs(layout):
    prefs = get_preferences()
    
    favorites_header, favorites_body = layout.panel("Favorites")
    favorites_header.label(text="Favorites")
    if favorites_body:
        favorites_body.prop(prefs, "favorites_show_label")
        horizontal_row = favorites_body.row()
        horizontal_row.prop(prefs, "favorites_horizontal", expand=True)
        if prefs.favorites_horizontal:
            horizontal_row.prop(prefs, "horizontal_row_threshold", expand=True)
    
    root_paths_header, root_paths_body = layout.panel("RootPaths")
    root_paths_header.label(text="Root Dirs")

    if root_paths_body:
        operator_row = root_paths_body.row()
        operator_row.alignment = "RIGHT"
        operator_row.operator(ScriptPanel_AddDirEntry.bl_idname, icon="PLUS", text="Add Root Dir")

        root_path : ScriptPanelRootPath
        for i, root_path in enumerate(prefs.root_paths):
            row = root_paths_body.row()
            row.prop(root_path, "dir_path", text="")
            remove_op = row.operator(ScriptPanel_RemoveDirEntry.bl_idname, icon="X", text="")
            remove_op.idx = i


def get_preferences() -> ScriptPanelPreferences: 
    return bpy.context.preferences.addons[__package__].preferences


CLASS_LIST = (
    ScriptPanelRootPath,
    ScriptPanel_AddDirEntry,
    ScriptPanel_RemoveDirEntry,
    ScriptPanelPreferences,
)


def register():
    for cls in CLASS_LIST:
        bpy.utils.register_class(cls)

    # default prefs
    prefs = get_preferences()
    if len(prefs.root_paths) == 0:
        item : ScriptPanelRootPath = prefs.root_paths.add()
        item.dir_path = os.path.join(os.path.dirname(__file__), "example_dir")


def unregister():
    for cls in CLASS_LIST:
        bpy.utils.unregister_class(cls)
