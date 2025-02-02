import bpy

from . import script_handler
from . import icon_manager


class ScriptPanelEditBox(bpy.types.PropertyGroup):
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


class ScriptPanelSaveEditingBox(bpy.types.Operator):
    bl_idname = "scriptpanel.save_script_button_editing"
    bl_label = "Save"
    bl_description = "Save display changes to a local or shared config file"

    script_path: bpy.props.StringProperty()

    to_local : bpy.props.BoolProperty()

    def execute(self, context):
        script : script_handler.Script = script_handler.SCRIPT_HANDLER.get_script_inst_from_path(self.script_path)

        edit_boxes = bpy.context.scene.script_panel_edits

        # remove existing entry if it exists
        found_idx = None
        for i, box in enumerate(edit_boxes):
            if box.script_path == self.script_path:
                found_idx = i
                break
        if found_idx is not None:
            box : ScriptPanelEditBox = edit_boxes[found_idx]
            script.update_from_dict(box.to_config_dict())
            script.save_to_config(to_local=self.to_local)
            edit_boxes.remove(found_idx)
            return {"FINISHED"}
        
        return {"FINISHED"}


class ScriptPanelToggleScriptEditingBox(bpy.types.Operator):
    bl_idname = "scriptpanel.toggle_script_button_editing"
    bl_label = "Toggle Edit Box"
    bl_description = "Open layout for customizing this script button"

    script_path: bpy.props.StringProperty()

    def execute(self, context):
        script : script_handler.Script = script_handler.SCRIPT_HANDLER.get_script_inst_from_path(self.script_path)

        # ensure editing mode is enabled, since the box doesn't show up otherwise
        panel_props = context.scene.script_panel_props
        if not panel_props.edit_mode_enabled:
            panel_props.edit_mode_enabled = True

        edit_boxes = bpy.context.scene.script_panel_edits

        # remove existing entry if it exists
        found_idx = None
        for i, box in enumerate(edit_boxes):
            if box.script_path == self.script_path:
                found_idx = i
                break
        if found_idx is not None:
            box : ScriptPanelEditBox = edit_boxes[found_idx]
            edit_boxes.remove(found_idx)
            return {"FINISHED"}
        
        # or add new entry
        new_box : ScriptPanelEditBox = edit_boxes.add()
        new_box.test_prop = False
        new_box.script_path = self.script_path

        new_box.label = script.label
        new_box.tooltip = script.tooltip
        new_box.icon_name = script.icon_name
        new_box.icon_path = script.icon_path

        return {"FINISHED"}


class ScriptPanelToggleFavorite(bpy.types.Operator):
    bl_idname = "scriptpanel.toggle_script_favorite"
    bl_label = "Toggle Favorite"
    bl_description = "Favorited items show up at the top of the panel"

    script_path: bpy.props.StringProperty()

    def execute(self, context):
        script : script_handler.Script = script_handler.SCRIPT_HANDLER.get_script_inst_from_path(self.script_path)
        script.set_favorited_state(not script.is_favorited)
        script_handler.SCRIPT_HANDLER.update_favorites()
        return {"FINISHED"}


class ScriptPanelReorderFavorite(bpy.types.Operator):
    bl_idname = "scriptpanel.reorder_favorite"
    bl_label = "Reorder Favorite"
    bl_description = "Move favorite around"

    direction: bpy.props.IntProperty()
    script_path: bpy.props.StringProperty()

    def execute(self, context):
        script : script_handler.Script = script_handler.SCRIPT_HANDLER.get_script_inst_from_path(self.script_path)
        script.reorder_in_favorites(self.direction)
        script_handler.SCRIPT_HANDLER.update_favorites()
        return {"FINISHED"}


class IconSearchPopup(bpy.types.Operator):
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
        edit_box : ScriptPanelEditBox = get_edit_box_of_script_path(self.script_path)
        edit_box.icon_name = self.icon_enum
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


def get_edit_box_of_script(script):
    return get_edit_box_of_script_path(script.path)

        
def get_edit_box_of_script_path(script_path):
    for edit_box in bpy.context.scene.script_panel_edits:
        if edit_box.script_path == script_path:
            return edit_box


def draw_script_edit_box(parent, edit_props : ScriptPanelEditBox):
    if not edit_props:
        return

    box = parent.box()
    box.label(text=edit_props.script_path.split("\\")[-1])
    box.prop(edit_props, "label")
    box.prop(edit_props, "tooltip")

    icon_row = box.row()
    icon_row.prop(edit_props, "icon_name")
    search_popup = icon_row.operator(
        IconSearchPopup.bl_idname,
        icon="VIEWZOOM",
        text="",
        )
    search_popup.script_path = edit_props.script_path

    box.prop(edit_props, "icon_path")
    
    save_row = box.row()
    save_row.scale_y = 2
    save_shared = save_row.operator(
        ScriptPanelSaveEditingBox.bl_idname,
        icon="INTERNET",
        text="Shared Save",
        )
    save_shared.to_local = False
    save_shared.script_path = edit_props.script_path

    save_local_op = save_row.operator(
        ScriptPanelSaveEditingBox.bl_idname,
        icon="FILE_TICK",
        text="Local Save",
        )
    save_local_op.to_local = True
    save_local_op.script_path = edit_props.script_path

    box.separator()


CLASSES = (
    ScriptPanelEditBox,
    ScriptPanelToggleScriptEditingBox,
    ScriptPanelSaveEditingBox,
    ScriptPanelToggleFavorite,
    ScriptPanelReorderFavorite,
    IconSearchPopup,
)

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.script_panel_edits = bpy.props.CollectionProperty(type=ScriptPanelEditBox)


def unregister():
    for cls in CLASSES:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.script_panel_edits
