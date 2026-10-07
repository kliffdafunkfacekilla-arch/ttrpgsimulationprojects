import re

with open("ui/settings_dialogs.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

out_lines = []
in_dialog = False
dialog_name = ""
skip_lines = False

for i in range(len(lines)):
    line = lines[i]
    stripped = line.strip()

    if stripped.startswith("def edit_") and stripped.endswith("_dialog(viewer):"):
        # e.g., def edit_calendar_dialog(viewer):
        dialog_name = stripped.split("def edit_")[1].split("_dialog")[0]
        # Rename function
        out_lines.append(f"def build_{dialog_name}_tab(root, settings):\n")
        in_dialog = True
        skip_lines = False
        continue

    if in_dialog:
        if stripped == "settings = load_all_settings()":
            continue # skip loading settings, passed in

        if stripped == "root = tk.Tk()":
            continue # skip creating root

        if stripped.startswith("root.title(") or stripped.startswith("root.geometry(") or stripped.startswith("root.attributes("):
            continue # skip window config

        if stripped.startswith("def save_all():"):
            out_lines.append("    def get_save_data():\n")
            continue

        if stripped == "if save_all_settings(settings):":
            # Replace the save logic with return
            # We must skip the following indented lines
            out_lines.append("            return True, None\n")
            skip_lines = True
            continue

        if skip_lines and stripped == "except ValueError:":
            skip_lines = False
            out_lines.append(line)
            continue

        if skip_lines and stripped.startswith("except Exception:"):
            skip_lines = False
            out_lines.append(line)
            continue

        if skip_lines and stripped == "viewer.world_settings = settings": continue
        if skip_lines and stripped == "viewer.reload_in_memory_constants()": continue
        if skip_lines and stripped == "viewer.sync_data()": continue
        if skip_lines and stripped == "root.destroy()": continue

        # When catching errors inside the old save_all
        if stripped.startswith("messagebox.showerror("):
            # Extract error message
            msg = line.split('", "')[1].split('")')[0]
            out_lines.append(f'            return False, "{msg}"\n')
            continue

        if stripped.startswith('ttk.Button(root, text="Save & Apply All Settings"'):
            # This marks the end of the dialog
            out_lines.append("    return get_save_data\n")
            in_dialog = False
            continue

        if stripped == "root.mainloop()":
            continue # skip

    out_lines.append(line)

master_dialog = """
def edit_master_settings_dialog(viewer):
    settings = load_all_settings()
    root = tk.Tk()
    root.title("Master Settings Hub")
    root.geometry("1100x700")
    root.attributes("-topmost", True)

    nb = ttk.Notebook(root)
    nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    tabs = [
        ("Calendar", build_calendar_tab),
        ("Physics", build_elevation_tab),
        ("Factions", build_factions_tab),
        ("Settlements", build_settlements_tab),
        ("Ecology", build_ecology_tab),
        ("Resources/Recipes", build_resources_recipes_tab),
        ("Cults", build_cults_tab),
        ("Fringe", build_fringe_tab)
    ]

    save_callbacks = []

    for title, builder in tabs:
        f = ttk.Frame(nb)
        nb.add(f, text=title)
        cb = builder(f, settings)
        save_callbacks.append((title, cb))

    def master_save():
        for title, cb in save_callbacks:
            success, err = cb()
            if not success:
                messagebox.showerror("Error", f"Error in {title} tab: {err}")
                return

        if save_all_settings(settings):
            viewer.world_settings = settings
            viewer.reload_in_memory_constants()
            viewer.sync_data()
            root.destroy()
        else:
            messagebox.showerror("Error", "Failed to save world_settings.json")

    ttk.Button(root, text="Save & Apply All Settings", command=master_save).pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
    root.mainloop()
"""

# Find the end of the imports/globals to insert master dialog, or just append it at the end
out_lines.append(master_dialog)

with open("ui/settings_dialogs_refactored.py", "w", encoding="utf-8") as f:
    f.writelines(out_lines)

print("Refactored file generated.")
