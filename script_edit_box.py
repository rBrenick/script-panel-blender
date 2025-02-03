import bpy

from . import script_handler
from . import icon_manager


class ScriptPanel_EditBox(bpy.types.PropertyGroup):
    script_path: bpy.props.StringProperty()

    label: bpy.props.StringProperty(
        name="Label",
        )
    
    tooltip: bpy.props.StringProperty(
        name="Tool tip",
        )

    icon_name : bpy.props.StringProperty(
        name="Icon Name",
        )
    
    icon_path: bpy.props.StringProperty(
        name="Icon Path",
        subtype="FILE_PATH",
        )

    def to_config_dict(self):
        return {
            "label": self.label,
            "tooltip": self.tooltip,
            "icon_name": self.icon_name,
            "icon_path": self.icon_path,
        }


class ScriptPanel_SaveEditingBox(bpy.types.Operator):
    bl_idname = "scriptpanel.save_script_button_editing"
    bl_label = "Save"
    bl_description = "Save display changes to a local or shared config file"

    script_path: bpy.props.StringProperty()

    to_local : bpy.props.BoolProperty()

    def execute(self, context):
        script = script_handler.instance.get_script_from_path(self.script_path)
        edit_box = get_edit_box_of_script(script)

        script.update_from_dict(edit_box.to_config_dict())
        script.save_to_config(to_local=self.to_local)

        remove_edit_box(edit_box)
        return {"FINISHED"}


class ScriptPanel_ToggleScriptEditingBox(bpy.types.Operator):
    bl_idname = "scriptpanel.toggle_script_button_editing"
    bl_label = "Toggle Edit Box"
    bl_description = "Open layout for customizing this script button"

    script_path: bpy.props.StringProperty()

    def execute(self, context):
        # ensure editing mode is enabled, since the box doesn't show up otherwise
        panel_props = context.scene.script_panel_props
        if not panel_props.edit_mode_enabled:
            panel_props.edit_mode_enabled = True

        # if the box is already open, just close it.
        edit_box = get_edit_box_of_script_path(self.script_path)
        if edit_box:
            remove_edit_box(edit_box)
        else:
            # otherwise, add a new box
            new_box : ScriptPanel_EditBox = bpy.context.scene.script_panel_edits.add()
            new_box.script_path = self.script_path

            script = script_handler.instance.get_script_from_path(self.script_path)
            new_box.label = script.label
            new_box.tooltip = script.tooltip
            new_box.icon_name = script.icon_name
            new_box.icon_path = script.icon_path

        return {"FINISHED"}


class ScriptPanel_ToggleFavorite(bpy.types.Operator):
    bl_idname = "scriptpanel.toggle_script_favorite"
    bl_label = "Toggle Favorite"
    bl_description = "Favorited items show up at the top of the panel"

    script_path: bpy.props.StringProperty()

    def execute(self, context):
        script = script_handler.instance.get_script_from_path(self.script_path)
        script.set_favorited_state(not script.is_favorited)
        script_handler.instance.update_favorites()
        return {"FINISHED"}


class ScriptPanel_ReorderFavorite(bpy.types.Operator):
    bl_idname = "scriptpanel.reorder_favorite"
    bl_label = "Reorder Favorite"
    bl_description = "Move favorite around"

    direction: bpy.props.IntProperty()
    script_path: bpy.props.StringProperty()

    def execute(self, context):
        script = script_handler.instance.get_script_from_path(self.script_path)
        script.reorder_in_favorites(self.direction)
        script_handler.instance.update_favorites()
        return {"FINISHED"}


class ScriptPanel_IconSearchPopup(bpy.types.Operator):
    bl_idname = "script_panel.icon_search_popup"
    bl_label = "Icon Search"
    bl_property = "icon_enum"

    icon_enum: bpy.props.EnumProperty(
        name="Objects",
        description="",
        items=icon_manager.get_default_icon_enum(),
        )
    
    script_path: bpy.props.StringProperty()

    def execute(self, context):
        self.report({'INFO'}, "You've selected: %s" % self.icon_enum)
        edit_box = get_edit_box_of_script_path(self.script_path)
        edit_box.icon_name = self.icon_enum
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


def get_edit_box_of_script(script) -> ScriptPanel_EditBox:
    return get_edit_box_of_script_path(script.path)

        
def get_edit_box_of_script_path(script_path) -> ScriptPanel_EditBox:
    for edit_box in bpy.context.scene.script_panel_edits:
        if edit_box.script_path == script_path:
            return edit_box


def remove_edit_box(tgt_edit_box):
    """CollectionProperty doesn't have a .index() method, so we need to find the the index manually"""
    idx = None
    scene_edit_box : ScriptPanel_EditBox
    for i, scene_edit_box in enumerate(bpy.context.scene.script_panel_edits):
        if scene_edit_box.script_path == tgt_edit_box.script_path:
            idx = i
            break

    if idx is not None:
        bpy.context.scene.script_panel_edits.remove(idx)
        return True
    
    return False


def draw_script_edit_box(parent, edit_box : ScriptPanel_EditBox):
    if not edit_box:
        return

    box = parent.box()
    box.label(text=edit_box.script_path.split("\\")[-1])
    box.prop(edit_box, "label")
    box.prop(edit_box, "tooltip")

    icon_row = box.row()
    icon_row.prop(edit_box, "icon_name")
    search_popup = icon_row.operator(
        ScriptPanel_IconSearchPopup.bl_idname,
        icon="VIEWZOOM",
        text="",
        )
    search_popup.script_path = edit_box.script_path

    box.prop(edit_box, "icon_path")
    
    save_row = box.row()
    save_row.scale_y = 2
    save_shared = save_row.operator(
        ScriptPanel_SaveEditingBox.bl_idname,
        icon="URL",
        text="Shared Save",
        )
    save_shared.to_local = False
    save_shared.script_path = edit_box.script_path

    save_local_op = save_row.operator(
        ScriptPanel_SaveEditingBox.bl_idname,
        icon="FILE_TICK",
        text="Local Save",
        )
    save_local_op.to_local = True
    save_local_op.script_path = edit_box.script_path

    box.separator()


CLASSES = (
    ScriptPanel_EditBox,
    ScriptPanel_ToggleScriptEditingBox,
    ScriptPanel_SaveEditingBox,
    ScriptPanel_ToggleFavorite,
    ScriptPanel_ReorderFavorite,
    ScriptPanel_IconSearchPopup,
)

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.script_panel_edits = bpy.props.CollectionProperty(type=ScriptPanel_EditBox)


def unregister():
    for cls in CLASSES:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.script_panel_edits
