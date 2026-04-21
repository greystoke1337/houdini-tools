"""
Paste this into a Houdini shelf button (Script tab, Language: Python).

Creates three shelf tools:
  - "JOY Start"  -> starts joystick listener
  - "JOY Stop"   -> stops joystick listener
  - "JOY Tune"   -> opens physics tuning panel

Or manually paste the *_code strings into shelf buttons.
"""

HOUDINI_TOOLS_PATH = r"C:\Users\maxim\houdini-tools"

start_code = f"""
import sys
if r"{HOUDINI_TOOLS_PATH}" not in sys.path:
    sys.path.insert(0, r"{HOUDINI_TOOLS_PATH}")

from houdini_hotas_control import throw
throw.start("null")
"""

stop_code = f"""
import sys
if r"{HOUDINI_TOOLS_PATH}" not in sys.path:
    sys.path.insert(0, r"{HOUDINI_TOOLS_PATH}")

from houdini_hotas_control import throw
throw.stop()
"""

tune_code = f"""
import sys
if r"{HOUDINI_TOOLS_PATH}" not in sys.path:
    sys.path.insert(0, r"{HOUDINI_TOOLS_PATH}")

from houdini_hotas_control import gui
gui.show()
"""

thr_start_code = f"""
import sys
if r"{HOUDINI_TOOLS_PATH}" not in sys.path:
    sys.path.insert(0, r"{HOUDINI_TOOLS_PATH}")

from houdini_hotas_control import node_sizer
node_sizer.start()
"""

thr_stop_code = f"""
import sys
if r"{HOUDINI_TOOLS_PATH}" not in sys.path:
    sys.path.insert(0, r"{HOUDINI_TOOLS_PATH}")

from houdini_hotas_control import node_sizer
node_sizer.stop()
"""

reload_code = f"""
import sys

_throw = sys.modules.get("houdini_hotas_control.throw")
if _throw and _throw._joystick is not None:
    _throw.stop()

_sizer = sys.modules.get("houdini_hotas_control.node_sizer")
if _sizer and _sizer._throttle is not None:
    _sizer.stop()

for key in [k for k in sys.modules if k.startswith("houdini_hotas_control")]:
    del sys.modules[key]

print("[hotas] Modules reloaded. Hit JOY Start / THR Start to restart.")
"""

# --- Auto-install shelf tools into current Houdini session ---
# Run this file once via hython or Houdini's Python shell to create the shelf tools.

if __name__ == "__main__" or "hou" in dir():
    try:
        import hou

        shelf_name = "houdini_hotas_control"
        existing = hou.shelves.shelves().get(shelf_name)
        shelf = existing or hou.shelves.newShelf(file_path="", name=shelf_name, label="Houdini HOTAS")

        t_start = hou.shelves.newTool(
            file_path="",
            name="hotas_start",
            label="JOY Start",
            script=start_code,
            language=hou.scriptLanguage.Python,
            help="Start joystick node shooter",
        )
        t_stop = hou.shelves.newTool(
            file_path="",
            name="hotas_stop",
            label="JOY Stop",
            script=stop_code,
            language=hou.scriptLanguage.Python,
            help="Stop joystick node shooter",
        )
        t_tune = hou.shelves.newTool(
            file_path="",
            name="hotas_tune",
            label="JOY Tune",
            script=tune_code,
            language=hou.scriptLanguage.Python,
            help="Open physics tuning panel",
        )
        t_reload = hou.shelves.newTool(
            file_path="",
            name="hotas_reload",
            label="JOY Reload",
            script=reload_code,
            language=hou.scriptLanguage.Python,
            help="Reload Houdini HOTAS tools from disk",
        )
        shelf.setTools([t_start, t_stop, t_tune, t_reload])
        print("[hotas] Shelf tools installed on shelf:", shelf_name)
        print("  -> Look for 'Houdini HOTAS' shelf tab in Houdini.")

    except Exception as e:
        print(f"[hotas] Shelf install failed: {e}")
        print("Paste start_code / stop_code / tune_code manually into shelf buttons.")
        print()
        print("--- START ---")
        print(start_code)
        print("--- STOP ---")
        print(stop_code)
        print("--- TUNE ---")
        print(tune_code)
