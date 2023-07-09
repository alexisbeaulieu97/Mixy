import pluggy

from mixy.constants import PLUGIN_PROJECT_NAME

hook_impl = pluggy.HookimplMarker(PLUGIN_PROJECT_NAME)
