bl_info = {
    "name": "Script Panel",
    "author": "Richard Brenick",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "",
    "description": "",
    "warning": "",
    "doc_url": "",
    "category": "Rigging",
}

from . import script_panel, script_panel_preferences

def register():
    script_panel_preferences.register()
    script_panel.register()

def unregister():
    script_panel.unregister()
    script_panel_preferences.unregister()
