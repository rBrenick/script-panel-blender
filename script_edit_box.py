import bpy

from . import script_handler
from . import icon_manager

class ScriptPanelEditBox(bpy.types.PropertyGroup):
    script_path: bpy.props.StringProperty()

    label: bpy.props.StringProperty(
        name="Label",
        )

    icon_enum : bpy.props.EnumProperty(
        name="Icon",
        items=icon_manager.get_default_icon_enum()
        )
    
    icon_path: bpy.props.StringProperty(
        name="Icon Path",
        subtype="FILE_PATH",
        )

    def to_config_dict(self):
        return {
            "label": self.label,
            "icon_name": None if self.icon_enum == "NONE" else self.icon_enum,
            "icon_path": self.icon_path,
        }


class ScriptPanelSaveEditingBox(bpy.types.Operator):
    bl_idname = "scriptpanel.save_script_button_editing"
    bl_label = "Save"
    bl_description = ""

    script_path: bpy.props.StringProperty()

    def execute(self, context):
        script : script_handler.Script = script_handler.SCRIPT_HANDLER.get_script_from_path(self.script_path)

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
            script.save_to_config_file()
            edit_boxes.remove(found_idx)
            return {"FINISHED"}
        
        return {"FINISHED"}


class ScriptPanelToggleScriptEditingBox(bpy.types.Operator):
    bl_idname = "scriptpanel.toggle_script_button_editing"
    bl_label = "Toggle"
    bl_description = ""

    script_path: bpy.props.StringProperty()

    def execute(self, context):
        script : script_handler.Script = script_handler.SCRIPT_HANDLER.get_script_from_path(self.script_path)

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
        if script.icon_name:
            new_box.icon_enum = script.icon_name
        new_box.icon_path = script.icon_path

        return {"FINISHED"}


class ScriptPanelToggleFavorite(bpy.types.Operator):
    bl_idname = "scriptpanel.toggle_script_favorite"
    bl_label = "Toggle"
    bl_description = ""

    script_path: bpy.props.StringProperty()

    def execute(self, context):
        script : script_handler.Script = script_handler.SCRIPT_HANDLER.get_script_from_path(self.script_path)
        script.is_favorite = None if script.is_favorite else True
        script.save_to_config_file()
        return {"FINISHED"}


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
    box.prop(edit_props, "icon_enum")
    box.prop(edit_props, "icon_path")
    
    save_row = box.row()
    save_row.scale_y = 2
    save_op = save_row.operator(
        ScriptPanelSaveEditingBox.bl_idname,
        icon="FILE_TICK",
        text="Save",
        )
    save_op.script_path = edit_props.script_path

    box.separator()


CLASSES = (
    ScriptPanelEditBox,
    ScriptPanelToggleScriptEditingBox,
    ScriptPanelSaveEditingBox,
    ScriptPanelToggleFavorite,
)

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.script_panel_edits = bpy.props.CollectionProperty(type=ScriptPanelEditBox)


def unregister():
    for cls in CLASSES:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.script_panel_edits
