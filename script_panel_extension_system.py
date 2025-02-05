import importlib
import os
import sys
import traceback

from . import script_panel_logger
from . import script_panel_extension_interface

log = script_panel_logger.get_logger()


class ModuleConstants:
    extension_file_prefix = "script_panel_ext_"


def import_extensions(refresh=False):
    if refresh:
        modules_to_pop = []
        for mod_key in sys.modules.keys():
            if mod_key.startswith(ModuleConstants.extension_file_prefix):
                modules_to_pop.append(mod_key)

        for mod_key in modules_to_pop:
            sys.modules.pop(mod_key)

    # look through sys.path for extension modules
    modules_to_import = list()
    for sys_path in sys.path:
        if not os.path.isdir(sys_path):
            continue

        # for every .py file with the proper prefix, import it
        for sys_path_name in os.listdir(sys_path):
            if not sys_path_name.startswith(ModuleConstants.extension_file_prefix):
                continue

            module_name = os.path.splitext(sys_path_name)[0]
            modules_to_import.append(module_name)

    modules_to_import = list(set(modules_to_import))

    for module_import_str in modules_to_import:
        if not module_import_str:
            continue

        try:
            importlib.import_module(module_import_str)
            log.info("Imported extension: {}".format(module_import_str))
        except Exception as e:
            traceback.print_exc()


try:
    import_extensions()
except Exception as e:
    traceback.print_exc()

extension_sub_classes = script_panel_extension_interface.ScriptPanelExtension.__subclasses__()
if extension_sub_classes:
    instance = extension_sub_classes[0]()  # type: script_panel_extension_interface.ScriptPanelExtension
else:
    instance = script_panel_extension_interface.ScriptPanelExtension()

log.info("Extension class: {}".format(instance))
