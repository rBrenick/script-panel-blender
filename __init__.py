bl_info = {
    "name": "Script Panel",
    "author": "Richard Brenick",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "",
    "description": "",
    "warning": "",
    "doc_url": "",
    "category": "Interface",
}


def register():

    from . import script_panel_extension_system
    script_panel_extension_system.import_extensions()

    from . import script_panel
    script_panel.register()


def unregister():
    from . import script_panel_extension_system
    script_panel_extension_system.pop_extension_modules()
    
    from . import script_panel
    script_panel.unregister()

