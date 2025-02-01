import os
import bpy.utils.previews

__icon_manager__ = None

class IconManager():
    icons = None

    def __init__(self):
        self.registered_icons = {}
        self.icons = bpy.utils.previews.new()

    def register_icon(self, icon_path):
        icon_name = get_icon_name_from_path(icon_path)
        self.icons.load(icon_name, icon_path, 'IMAGE')
        self.registered_icons[icon_path] = icon_name

    def unregister(self):
        bpy.utils.previews.remove(self.icons)
        self.icons = None


def get_icon_name_from_path(icon_path):
    return os.path.splitext(os.path.basename(icon_path))[0]


def get_icon(icon_path):
    if not __icon_manager__.registered_icons.get(icon_path):
        __icon_manager__.register_icon(icon_path)

    try:
        icon_name = __icon_manager__.registered_icons[icon_path]
        return __icon_manager__.icons[icon_name].icon_id
    except KeyError:
        print(f"Error: Failed to find registered icon for '{icon_path}'!")
        return None


def register():
    global __icon_manager__ 
    if __icon_manager__ is None:
        __icon_manager__ = IconManager()


def unregister():
    global __icon_manager__
    __icon_manager__.unregister()
    __icon_manager__ = None
