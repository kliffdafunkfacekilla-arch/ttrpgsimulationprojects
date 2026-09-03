# settings_dialogs.py
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import json
import os

def load_all_settings():
    # Priority: world_settings.json > default_settings.json
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    for fname in ['world_settings.json', 'default_settings.json']:
        path = os.path.join(root_dir, fname)
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
    return {}

def save_all_settings(settings):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path = os.path.join(root_dir, 'world_settings.json')
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:
        messagebox.showerror("Save Error", f"Could not save settings: {e}")
        return False

# ==========================================================
# 1. CALENDAR EDITOR
# ==========================================================
def edit_calendar_dialog(viewer):
    settings = load_all_settings()
    cal = settings.setdefault('calendar', {})
    
    root = tk.Tk()
    root.title("Calendar & Cosmology Editor")
    root.geometry("750x500")
    root.attributes("-topmost", True)
    
    # Left: Months
    left_frame = ttk.LabelFrame(root, text="Months List")
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    months_list = list(cal.setdefault('months', []))
    months_box = tk.Listbox(left_frame, selectmode=tk.SINGLE)
    months_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    for m in months_list: months_box.insert(tk.END, m)
    
    def update_months_box():
        months_box.delete(0, tk.END)
        for m in months_list: months_box.insert(tk.END, m)
        
    def add_month():
        name = ask_simple_string("Add Month", "Enter month name:")
        if name:
            months_list.append(name)
            update_months_box()
            
    def rename_month():
        sel = months_box.curselection()
        if sel:
            idx = sel[0]
            new_name = ask_simple_string("Rename Month", "Enter new name:", months_list[idx])
            if new_name:
                months_list[idx] = new_name
                update_months_box()
                
    def delete_month():
        sel = months_box.curselection()
        if sel:
            idx = sel[0]
            months_list.pop(idx)
            update_months_box()
            
    btn_f = ttk.Frame(left_frame)
    btn_f.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(btn_f, text="Add", command=add_month, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_f, text="Rename", command=rename_month, width=8).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_f, text="Del", command=delete_month, width=6).pack(side=tk.LEFT, padx=2)
    
    # Middle: Seasons
    mid_frame = ttk.LabelFrame(root, text="Seasons")
    mid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    seasons = list(cal.setdefault('seasons', []))
    seasons_box = tk.Listbox(mid_frame)
    seasons_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_seasons_box():
        seasons_box.delete(0, tk.END)
        for s in seasons:
            seasons_box.insert(tk.END, f"{s.get('name')} ({s.get('start_day')}-{s.get('end_day')})")
    update_seasons_box()
    
    # Form details for season
    form_s = ttk.Frame(mid_frame)
    form_s.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(form_s, text="Name:").grid(row=0, column=0, sticky=tk.W)
    s_name_var = tk.StringVar()
    ttk.Entry(form_s, textvariable=s_name_var, width=15).grid(row=0, column=1)
    
    ttk.Label(form_s, text="Start Day:").grid(row=1, column=0, sticky=tk.W)
    s_start_var = tk.StringVar()
    ttk.Entry(form_s, textvariable=s_start_var, width=15).grid(row=1, column=1)
    
    ttk.Label(form_s, text="End Day:").grid(row=2, column=0, sticky=tk.W)
    s_end_var = tk.StringVar()
    ttk.Entry(form_s, textvariable=s_end_var, width=15).grid(row=2, column=1)
    
    ttk.Label(form_s, text="Growth Mod:").grid(row=3, column=0, sticky=tk.W)
    s_growth_var = tk.StringVar()
    ttk.Entry(form_s, textvariable=s_growth_var, width=15).grid(row=3, column=1)
    
    ttk.Label(form_s, text="Travel Mod:").grid(row=4, column=0, sticky=tk.W)
    s_travel_var = tk.StringVar()
    ttk.Entry(form_s, textvariable=s_travel_var, width=15).grid(row=4, column=1)
    
    def load_season_details(evt):
        sel = seasons_box.curselection()
        if sel:
            s = seasons[sel[0]]
            s_name_var.set(s.get('name', ''))
            s_start_var.set(str(s.get('start_day', 0)))
            s_end_var.set(str(s.get('end_day', 359)))
            s_growth_var.set(str(s.get('growth_mod', 1.0)))
            s_travel_var.set(str(s.get('travel_cost_mod', 1.0)))
            
    seasons_box.bind("<<ListboxSelect>>", load_season_details)
    
    def save_season():
        sel = seasons_box.curselection()
        if sel:
            idx = sel[0]
            try:
                seasons[idx] = {
                    "name": s_name_var.get(),
                    "start_day": int(s_start_var.get()),
                    "end_day": int(s_end_var.get()),
                    "growth_mod": float(s_growth_var.get()),
                    "travel_cost_mod": float(s_travel_var.get())
                }
                update_seasons_box()
            except ValueError:
                messagebox.showerror("Error", "Check that numeric values are formatted correctly.")
                
    def add_season():
        seasons.append({"name": "New Season", "start_day": 0, "end_day": 30, "growth_mod": 1.0, "travel_cost_mod": 1.0})
        update_seasons_box()
        
    def delete_season():
        sel = seasons_box.curselection()
        if sel:
            seasons.pop(sel[0])
            update_seasons_box()
            
    btn_s = ttk.Frame(mid_frame)
    btn_s.pack(fill=tk.X, padx=5, pady=2)
    ttk.Button(btn_s, text="Add", command=add_season, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_s, text="Save", command=save_season, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_s, text="Del", command=delete_season, width=6).pack(side=tk.LEFT, padx=2)
    
    # Right: Moons & Global Days
    right_frame = ttk.LabelFrame(root, text="Moons & Year Length")
    right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    ttk.Label(right_frame, text="Days Per Year:").pack(anchor=tk.W, padx=5, pady=2)
    days_var = tk.StringVar(value=str(cal.setdefault('days_per_year', 360)))
    ttk.Entry(right_frame, textvariable=days_var, width=15).pack(anchor=tk.W, padx=5, pady=2)
    
    moons = list(cal.setdefault('moons', []))
    moons_box = tk.Listbox(right_frame, height=5)
    moons_box.pack(fill=tk.X, padx=5, pady=5)
    def update_moons_box():
        moons_box.delete(0, tk.END)
        for m in moons:
            moons_box.insert(tk.END, f"{m.get('name')} ({m.get('cycle_days')} days)")
    update_moons_box()
    
    form_m = ttk.Frame(right_frame)
    form_m.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(form_m, text="Moon Name:").grid(row=0, column=0, sticky=tk.W)
    m_name_var = tk.StringVar()
    ttk.Entry(form_m, textvariable=m_name_var, width=15).grid(row=0, column=1)
    
    ttk.Label(form_m, text="Cycle Days:").grid(row=1, column=0, sticky=tk.W)
    m_cycle_var = tk.StringVar()
    ttk.Entry(form_m, textvariable=m_cycle_var, width=15).grid(row=1, column=1)
    
    def load_moon_details(evt):
        sel = moons_box.curselection()
        if sel:
            m = moons[sel[0]]
            m_name_var.set(m.get('name', ''))
            m_cycle_var.set(str(m.get('cycle_days', 30)))
    moons_box.bind("<<ListboxSelect>>", load_moon_details)
    
    def save_moon():
        sel = moons_box.curselection()
        if sel:
            idx = sel[0]
            try:
                moons[idx]['name'] = m_name_var.get()
                moons[idx]['cycle_days'] = int(m_cycle_var.get())
                update_moons_box()
            except ValueError:
                messagebox.showerror("Error", "Cycle days must be an integer.")
                
    def add_moon():
        moons.append({"name": "New Moon", "cycle_days": 30, "phases": ["New", "Waxing Crescent", "First Quarter", "Waxing Gibbous", "Full", "Waning Gibbous", "Third Quarter", "Waning Crescent"]})
        update_moons_box()
        
    def delete_moon():
        sel = moons_box.curselection()
        if sel:
            moons.pop(sel[0])
            update_moons_box()
            
    btn_m = ttk.Frame(right_frame)
    btn_m.pack(fill=tk.X, padx=5, pady=2)
    ttk.Button(btn_m, text="Add", command=add_moon, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_m, text="Save", command=save_moon, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_m, text="Del", command=delete_moon, width=6).pack(side=tk.LEFT, padx=2)
    
    # Save All button at bottom
    def save_all():
        try:
            cal['days_per_year'] = int(days_var.get())
            cal['months'] = months_list
            cal['seasons'] = seasons
            cal['moons'] = moons
            settings['calendar'] = cal
            if save_all_settings(settings):
                viewer.world_settings = settings
                viewer.reload_in_memory_constants()
                viewer.sync_data()
                root.destroy()
        except ValueError:
            messagebox.showerror("Error", "Year length must be an integer.")
            
    ttk.Button(root, text="Save & Apply All Settings", command=save_all).pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
    root.mainloop()

# ==========================================================
# 2. CLIMATE EDITOR (ELEVATION, WIND ZONES, CHAOS)
# ==========================================================
def edit_elevation_dialog(viewer):
    settings = load_all_settings()
    wt = settings.setdefault('winds_and_temps', {})
    
    root = tk.Tk()
    root.title("Climate, Winds, & Reality Anchor Editor")
    root.geometry("850x550")
    root.attributes("-topmost", True)
    
    # Top: Global climate parameters
    top_f = ttk.Frame(root)
    top_f.pack(fill=tk.X, padx=10, pady=10)
    
    ttk.Label(top_f, text="Precipitation Multiplier:").grid(row=0, column=0, sticky=tk.W, padx=5)
    precip_var = tk.StringVar(value=str(wt.setdefault('precipitation_multiplier', 1.0)))
    ttk.Entry(top_f, textvariable=precip_var, width=10).grid(row=0, column=1, padx=5)
    
    ttk.Label(top_f, text="Global Lat Min:").grid(row=0, column=2, sticky=tk.W, padx=5)
    lat_min_var = tk.StringVar(value=str(wt.setdefault('global_latitude_min', -90.0)))
    ttk.Entry(top_f, textvariable=lat_min_var, width=10).grid(row=0, column=3, padx=5)
    
    ttk.Label(top_f, text="Global Lat Max:").grid(row=0, column=4, sticky=tk.W, padx=5)
    lat_max_var = tk.StringVar(value=str(wt.setdefault('global_latitude_max', 90.0)))
    ttk.Entry(top_f, textvariable=lat_max_var, width=10).grid(row=0, column=5, padx=5)
    
    # Bottom split: Left = 7 zones, Right = Chaos / Convergence Nodes
    paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # Left pane: Wind/Temp Zones
    left_p = ttk.LabelFrame(paned, text="7 Climate & Prevailing Wind Zones")
    paned.add(left_p, weight=3)
    
    zones = list(wt.setdefault('zones', []))
    zones_box = tk.Listbox(left_p)
    zones_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    for z in zones:
        zones_box.insert(tk.END, f"{z.get('name', 'Zone')} (y:{z.get('y_min')}-{z.get('y_max')})")
        
    def update_zones_box():
        zones_box.delete(0, tk.END)
        for z in zones:
            zones_box.insert(tk.END, f"{z.get('name', 'Zone')} (y:{z.get('y_min')}-{z.get('y_max')})")
            
    form_z = ttk.Frame(left_p)
    form_z.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(form_z, text="Name:").grid(row=0, column=0, sticky=tk.W)
    z_name_var = tk.StringVar()
    ttk.Entry(form_z, textvariable=z_name_var, width=12).grid(row=0, column=1)
    
    ttk.Label(form_z, text="Y Min:").grid(row=0, column=2, sticky=tk.W)
    z_ymin_var = tk.StringVar()
    ttk.Entry(form_z, textvariable=z_ymin_var, width=8).grid(row=0, column=3)
    
    ttk.Label(form_z, text="Y Max:").grid(row=0, column=4, sticky=tk.W)
    z_ymax_var = tk.StringVar()
    ttk.Entry(form_z, textvariable=z_ymax_var, width=8).grid(row=0, column=5)
    
    ttk.Label(form_z, text="Wind Dir:").grid(row=1, column=0, sticky=tk.W)
    z_wdir_var = tk.StringVar()
    wdir_cb = ttk.Combobox(form_z, textvariable=z_wdir_var, values=["N", "NE", "E", "SE", "S", "SW", "W", "NW"], width=8)
    wdir_cb.grid(row=1, column=1)
    
    ttk.Label(form_z, text="Wind Speed:").grid(row=1, column=2, sticky=tk.W)
    z_wspeed_var = tk.StringVar()
    ttk.Entry(form_z, textvariable=z_wspeed_var, width=8).grid(row=1, column=3)
    
    ttk.Label(form_z, text="Temp Min:").grid(row=2, column=0, sticky=tk.W)
    z_tmin_var = tk.StringVar()
    ttk.Entry(form_z, textvariable=z_tmin_var, width=8).grid(row=2, column=1)
    
    ttk.Label(form_z, text="Temp Max:").grid(row=2, column=2, sticky=tk.W)
    z_tmax_var = tk.StringVar()
    ttk.Entry(form_z, textvariable=z_tmax_var, width=8).grid(row=2, column=3)
    
    def load_zone(evt):
        sel = zones_box.curselection()
        if sel:
            z = zones[sel[0]]
            z_name_var.set(z.get('name', ''))
            z_ymin_var.set(str(z.get('y_min', 0.0)))
            z_ymax_var.set(str(z.get('y_max', 100.0)))
            z_wdir_var.set(z.get('wind_dir', 'W'))
            z_wspeed_var.set(str(z.get('wind_speed', 0.5)))
            z_tmin_var.set(str(z.get('temp_min', 0.0)))
            z_tmax_var.set(str(z.get('temp_max', 20.0)))
            
    zones_box.bind("<<ListboxSelect>>", load_zone)
    
    def save_zone():
        sel = zones_box.curselection()
        if sel:
            idx = sel[0]
            try:
                zones[idx] = {
                    "name": z_name_var.get(),
                    "y_min": float(z_ymin_var.get()),
                    "y_max": float(z_ymax_var.get()),
                    "wind_dir": z_wdir_var.get(),
                    "wind_speed": float(z_wspeed_var.get()),
                    "temp_min": float(z_tmin_var.get()),
                    "temp_max": float(z_tmax_var.get())
                }
                update_zones_box()
            except ValueError:
                messagebox.showerror("Error", "Ensure numeric fields are formatted correctly.")
                
    ttk.Button(left_p, text="Apply Zone Changes", command=save_zone).pack(fill=tk.X, padx=5, pady=5)
    
    # Right pane: Chaos Nodes & Convergence Spires
    right_p = ttk.LabelFrame(paned, text="Chaos Nodes & Convergence Spires")
    paned.add(right_p, weight=2)
    
    # Tabs inside right pane
    r_tabs = ttk.Notebook(right_p)
    r_tabs.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Chaos tab
    chaos_tab = ttk.Frame(r_tabs)
    r_tabs.add(chaos_tab, text="Chaos Nodes")
    
    nodes = list(wt.setdefault('chaos_nodes', []))
    nodes_box = tk.Listbox(chaos_tab)
    nodes_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_nodes_box():
        nodes_box.delete(0, tk.END)
        for n in nodes:
            nodes_box.insert(tk.END, f"Cell {n.get('cell_id')} (x:{n.get('x',0):.1f}, y:{n.get('y',0):.1f})")
    update_nodes_box()
    
    def add_chaos_node():
        cid = ask_simple_int("Add Chaos Node", "Enter Cell ID:")
        if cid is not None:
            # find coords
            cell = next((c for c in viewer.cells if c['id'] == cid), None)
            if cell:
                nodes.append({"cell_id": cid, "x": cell['center'][0], "y": cell['center'][1]})
                update_nodes_box()
            else:
                messagebox.showerror("Error", f"Cell ID {cid} not found on the map.")
                
    def delete_chaos_node():
        sel = nodes_box.curselection()
        if sel:
            nodes.pop(sel[0])
            update_nodes_box()
            
    btn_c = ttk.Frame(chaos_tab)
    btn_c.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(btn_c, text="Add Node", command=add_chaos_node).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_c, text="Delete selected", command=delete_chaos_node).pack(side=tk.LEFT, padx=5)
    
    # Convergence tab
    conv_tab = ttk.Frame(r_tabs)
    r_tabs.add(conv_tab, text="Convergence Spires")
    
    convs = list(wt.setdefault('convergence_locations', []))
    convs_box = tk.Listbox(conv_tab)
    convs_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_convs_box():
        convs_box.delete(0, tk.END)
        for c in convs:
            convs_box.insert(tk.END, f"Cell {c.get('cell_id')} (x:{c.get('x',0):.1f}, y:{c.get('y',0):.1f})")
    update_convs_box()
    
    def add_conv():
        cid = ask_simple_int("Add Convergence Spire", "Enter Cell ID:")
        if cid is not None:
            cell = next((c for c in viewer.cells if c['id'] == cid), None)
            if cell:
                convs.append({"cell_id": cid, "x": cell['center'][0], "y": cell['center'][1]})
                update_convs_box()
            else:
                messagebox.showerror("Error", f"Cell ID {cid} not found.")
                
    def delete_conv():
        sel = convs_box.curselection()
        if sel:
            convs.pop(sel[0])
            update_convs_box()
            
    btn_cv = ttk.Frame(conv_tab)
    btn_cv.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(btn_cv, text="Add Spire", command=add_conv).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_cv, text="Delete selected", command=delete_conv).pack(side=tk.LEFT, padx=5)
    
    # Save All
    def save_all():
        try:
            wt['precipitation_multiplier'] = float(precip_var.get())
            wt['global_latitude_min'] = float(lat_min_var.get())
            wt['global_latitude_max'] = float(lat_max_var.get())
            wt['zones'] = zones
            wt['chaos_nodes'] = nodes
            wt['convergence_locations'] = convs
            settings['winds_and_temps'] = wt
            if save_all_settings(settings):
                viewer.world_settings = settings
                viewer.reload_in_memory_constants()
                viewer.sync_data()
                root.destroy()
        except ValueError:
            messagebox.showerror("Error", "Check all numeric values.")
            
    ttk.Button(root, text="Save & Apply All Settings", command=save_all).pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
    root.mainloop()

# ==========================================================
# 3. FACTIONS & TECH UNLOCKS EDITOR
# ==========================================================
def edit_factions_dialog(viewer):
    settings = load_all_settings()
    ent = settings.setdefault('entities', {})
    
    root = tk.Tk()
    root.title("Factions, Tech Unlocks & Town Tiers Editor")
    root.geometry("850x500")
    root.attributes("-topmost", True)
    
    # Paned split: Factions list on left, Unlocks/Tiers on right
    paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    left_p = ttk.LabelFrame(paned, text="Factions")
    paned.add(left_p, weight=2)
    
    factions = list(ent.setdefault('factions', []))
    fac_box = tk.Listbox(left_p)
    fac_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_fac_box():
        fac_box.delete(0, tk.END)
        for f in factions:
            fac_box.insert(tk.END, f"{f.get('name')} (ID: {f.get('id')})")
    update_fac_box()
    
    form_f = ttk.Frame(left_p)
    form_f.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(form_f, text="Name:").grid(row=0, column=0, sticky=tk.W)
    f_name_var = tk.StringVar()
    ttk.Entry(form_f, textvariable=f_name_var, width=15).grid(row=0, column=1)
    
    f_color_var = tk.StringVar(value="#888888")
    color_btn = tk.Button(form_f, text="Pick Color", bg="#888888", width=12)
    color_btn.grid(row=1, column=0, columnspan=2, pady=5)
    
    def select_color():
        c = colorchooser.askcolor(title="Pick Faction Color", initialcolor=f_color_var.get(), parent=root)
        if c[1]:
            f_color_var.set(c[1])
            color_btn.config(bg=c[1])
    color_btn.config(command=select_color)
    
    def load_faction(evt):
        sel = fac_box.curselection()
        if sel:
            f = factions[sel[0]]
            f_name_var.set(f.get('name', ''))
            f_color_var.set(f.get('color', '#888888'))
            color_btn.config(bg=f.get('color', '#888888'))
    fac_box.bind("<<ListboxSelect>>", load_faction)
    
    def save_faction():
        sel = fac_box.curselection()
        if sel:
            idx = sel[0]
            factions[idx]['name'] = f_name_var.get()
            factions[idx]['color'] = f_color_var.get()
            update_fac_box()
            
    def add_faction():
        new_id = max([f.get('id', 0) for f in factions]) + 1 if factions else 1
        factions.append({"id": new_id, "name": "New Faction", "color": "#888888"})
        update_fac_box()
        
    def delete_faction():
        sel = fac_box.curselection()
        if sel:
            factions.pop(sel[0])
            update_fac_box()
            
    btn_f = ttk.Frame(left_p)
    btn_f.pack(fill=tk.X, padx=5, pady=2)
    ttk.Button(btn_f, text="Add", command=add_faction, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_f, text="Save", command=save_faction, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_f, text="Del", command=delete_faction, width=6).pack(side=tk.LEFT, padx=2)
    
    # Right pane: Unlocks & Tiers Notebook
    right_p = ttk.LabelFrame(paned, text="Tech Unlocks & Town Tiers")
    paned.add(right_p, weight=3)
    
    nb = ttk.Notebook(right_p)
    nb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 1. Transport unlocks
    trans_tab = ttk.Frame(nb)
    nb.add(trans_tab, text="Transports")
    transports = list(settings.setdefault('transport_unlocks', []))
    trans_box = tk.Listbox(trans_tab)
    trans_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_trans_box():
        trans_box.delete(0, tk.END)
        for t in transports:
            trans_box.insert(tk.END, f"{t.get('name')} (Min Tech: {t.get('min_tech')})")
    update_trans_box()
    
    form_tr = ttk.Frame(trans_tab)
    form_tr.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(form_tr, text="Name:").grid(row=0, column=0)
    tr_name_var = tk.StringVar()
    ttk.Entry(form_tr, textvariable=tr_name_var, width=12).grid(row=0, column=1)
    ttk.Label(form_tr, text="Min Tech:").grid(row=0, column=2)
    tr_tech_var = tk.StringVar()
    ttk.Entry(form_tr, textvariable=tr_tech_var, width=6).grid(row=0, column=3)
    
    def load_trans(evt):
        sel = trans_box.curselection()
        if sel:
            t = transports[sel[0]]
            tr_name_var.set(t.get('name', ''))
            tr_tech_var.set(str(t.get('min_tech', 1)))
    trans_box.bind("<<ListboxSelect>>", load_trans)
    
    def save_trans():
        sel = trans_box.curselection()
        if sel:
            idx = sel[0]
            try:
                transports[idx] = {"name": tr_name_var.get(), "min_tech": int(tr_tech_var.get())}
                update_trans_box()
            except ValueError: pass
            
    def add_trans():
        transports.append({"name": "New Transport", "min_tech": 1})
        update_trans_box()
        
    def delete_trans():
        sel = trans_box.curselection()
        if sel:
            transports.pop(sel[0])
            update_trans_box()
            
    btn_tr = ttk.Frame(trans_tab)
    btn_tr.pack(fill=tk.X, padx=5, pady=2)
    ttk.Button(btn_tr, text="Add", command=add_trans, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_tr, text="Save", command=save_trans, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_tr, text="Del", command=delete_trans, width=6).pack(side=tk.LEFT, padx=2)
    
    # 2. Building unlocks
    bld_tab = ttk.Frame(nb)
    nb.add(bld_tab, text="Building Tech")
    bld_uns = list(settings.setdefault('building_unlocks', []))
    bld_un_box = tk.Listbox(bld_tab)
    bld_un_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_bld_un_box():
        bld_un_box.delete(0, tk.END)
        for bu in bld_uns:
            bld_un_box.insert(tk.END, f"{bu.get('name')} (Min Tech: {bu.get('min_tech')})")
    update_bld_un_box()
    
    form_bu = ttk.Frame(bld_tab)
    form_bu.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(form_bu, text="Name:").grid(row=0, column=0)
    bu_name_var = tk.StringVar()
    ttk.Entry(form_bu, textvariable=bu_name_var, width=12).grid(row=0, column=1)
    ttk.Label(form_bu, text="Min Tech:").grid(row=0, column=2)
    bu_tech_var = tk.StringVar()
    ttk.Entry(form_bu, textvariable=bu_tech_var, width=6).grid(row=0, column=3)
    
    def load_bld_un(evt):
        sel = bld_un_box.curselection()
        if sel:
            bu = bld_uns[sel[0]]
            bu_name_var.set(bu.get('name', ''))
            bu_tech_var.set(str(bu.get('min_tech', 1)))
    bld_un_box.bind("<<ListboxSelect>>", load_bld_un)
    
    def save_bld_un():
        sel = bld_un_box.curselection()
        if sel:
            idx = sel[0]
            try:
                bld_uns[idx] = {"name": bu_name_var.get(), "min_tech": int(bu_tech_var.get())}
                update_bld_un_box()
            except ValueError: pass
            
    def add_bld_un():
        bld_uns.append({"name": "New Tech Tier", "min_tech": 1})
        update_bld_un_box()
        
    def delete_bld_un():
        sel = bld_un_box.curselection()
        if sel:
            bld_uns.pop(sel[0])
            update_bld_un_box()
            
    btn_bu = ttk.Frame(bld_tab)
    btn_bu.pack(fill=tk.X, padx=5, pady=2)
    ttk.Button(btn_bu, text="Add", command=add_bld_un, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_bu, text="Save", command=save_bld_un, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_bu, text="Del", command=delete_bld_un, width=6).pack(side=tk.LEFT, padx=2)
    
    # 3. Town tiers
    tiers_tab = ttk.Frame(nb)
    nb.add(tiers_tab, text="Town Tiers")
    tiers = list(settings.setdefault('town_tiers', []))
    tiers_box = tk.Listbox(tiers_tab)
    tiers_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_tiers_box():
        tiers_box.delete(0, tk.END)
        for t in tiers:
            max_p = "inf" if t.get('max_pop') is None else str(t.get('max_pop'))
            tiers_box.insert(tk.END, f"{t.get('name')} (Pop: {t.get('min_pop')}-{max_p}, Score: {t.get('score')})")
    update_tiers_box()
    
    form_t = ttk.Frame(tiers_tab)
    form_t.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(form_t, text="Name:").grid(row=0, column=0)
    t_name_var = tk.StringVar()
    ttk.Entry(form_t, textvariable=t_name_var, width=10).grid(row=0, column=1)
    
    ttk.Label(form_t, text="Min Pop:").grid(row=0, column=2)
    t_min_var = tk.StringVar()
    ttk.Entry(form_t, textvariable=t_min_var, width=6).grid(row=0, column=3)
    
    ttk.Label(form_t, text="Max Pop:").grid(row=1, column=0)
    t_max_var = tk.StringVar()
    ttk.Entry(form_t, textvariable=t_max_var, width=10).grid(row=1, column=1)
    
    ttk.Label(form_t, text="Score:").grid(row=1, column=2)
    t_score_var = tk.StringVar()
    ttk.Entry(form_t, textvariable=t_score_var, width=6).grid(row=1, column=3)
    
    def load_tier(evt):
        sel = tiers_box.curselection()
        if sel:
            t = tiers[sel[0]]
            t_name_var.set(t.get('name', ''))
            t_min_var.set(str(t.get('min_pop', 0)))
            max_p = '' if t.get('max_pop') is None else str(t.get('max_pop'))
            t_max_var.set(max_p)
            t_score_var.set(str(t.get('score', 1)))
    tiers_box.bind("<<ListboxSelect>>", load_tier)
    
    def save_tier():
        sel = tiers_box.curselection()
        if sel:
            idx = sel[0]
            try:
                max_val = None if not t_max_var.get() else int(t_max_var.get())
                tiers[idx] = {
                    "name": t_name_var.get(),
                    "min_pop": int(t_min_var.get()),
                    "max_pop": max_val,
                    "score": int(t_score_var.get())
                }
                update_tiers_box()
            except ValueError: pass
            
    def add_tier():
        tiers.append({"name": "New Tier", "min_pop": 0, "max_pop": 100, "score": 1})
        update_tiers_box()
        
    def delete_tier():
        sel = tiers_box.curselection()
        if sel:
            tiers.pop(sel[0])
            update_tiers_box()
            
    btn_t = ttk.Frame(tiers_tab)
    btn_t.pack(fill=tk.X, padx=5, pady=2)
    ttk.Button(btn_t, text="Add", command=add_tier, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_t, text="Save", command=save_tier, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_t, text="Del", command=delete_tier, width=6).pack(side=tk.LEFT, padx=2)
    
    # Save All button
    def save_all():
        ent['factions'] = factions
        settings['entities'] = ent
        settings['transport_unlocks'] = transports
        settings['building_unlocks'] = bld_uns
        settings['town_tiers'] = tiers
        if save_all_settings(settings):
            viewer.world_settings = settings
            viewer.reload_in_memory_constants()
            viewer.sync_data()
            root.destroy()
            
    ttk.Button(root, text="Save & Apply All Settings", command=save_all).pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
    root.mainloop()

# ==========================================================
# 4. SETTLEMENTS & BUILDINGS EDITOR
# ==========================================================
def edit_settlements_dialog(viewer):
    settings = load_all_settings()
    buildings = list(settings.setdefault('building_types', []))
    coeffs = settings.setdefault('wellbeing_coefficients', {})
    
    root = tk.Tk()
    root.title("Building Requirements, Costs & Wellbeing Editor")
    root.geometry("850x550")
    root.attributes("-topmost", True)
    
    paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Left Pane: Buildings list and cost editing
    left_p = ttk.LabelFrame(paned, text="Buildings & Construction Costs")
    paned.add(left_p, weight=3)
    
    bld_box = tk.Listbox(left_p)
    bld_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_bld_box():
        bld_box.delete(0, tk.END)
        for b in buildings:
            bld_box.insert(tk.END, f"{b.get('label')} ({b.get('name')})")
    update_bld_box()
    
    form_b = ttk.Frame(left_p)
    form_b.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(form_b, text="Name code:").grid(row=0, column=0, sticky=tk.W)
    b_name_var = tk.StringVar()
    ttk.Entry(form_b, textvariable=b_name_var, width=12).grid(row=0, column=1)
    
    ttk.Label(form_b, text="UI Label:").grid(row=0, column=2, sticky=tk.W)
    b_lbl_var = tk.StringVar()
    ttk.Entry(form_b, textvariable=b_lbl_var, width=12).grid(row=0, column=3)
    
    ttk.Label(form_b, text="Effect Desc:").grid(row=1, column=0, sticky=tk.W)
    b_effect_var = tk.StringVar()
    ttk.Entry(form_b, textvariable=b_effect_var, width=28).grid(row=1, column=1, columnspan=3, pady=5)
    
    # Cost listbox for this building
    ttk.Label(left_p, text="Resource Cost list:").pack(anchor=tk.W, padx=5)
    cost_box = tk.Listbox(left_p, height=4)
    cost_box.pack(fill=tk.X, padx=5, pady=2)
    
    current_cost_dict = {}
    
    def load_bld_details(evt):
        sel = bld_box.curselection()
        if sel:
            b = buildings[sel[0]]
            b_name_var.set(b.get('name', ''))
            b_lbl_var.set(b.get('label', ''))
            b_effect_var.set(b.get('effect', ''))
            
            nonlocal current_cost_dict
            current_cost_dict = dict(b.get('cost', {}))
            
            update_cost_box()
            
    bld_box.bind("<<ListboxSelect>>", load_bld_details)
    
    def update_cost_box():
        cost_box.delete(0, tk.END)
        for res, qty in current_cost_dict.items():
            cost_box.insert(tk.END, f"{res}: {qty}")
            
    def add_cost():
        res = ask_simple_string("Cost Material", "Enter resource name:")
        if res:
            qty = ask_simple_int("Cost Quantity", f"Enter quantity for {res}:")
            if qty is not None:
                current_cost_dict[res] = qty
                update_cost_box()
                
    def delete_cost():
        sel = cost_box.curselection()
        if sel:
            line = cost_box.get(sel[0])
            res = line.split(':')[0].strip()
            current_cost_dict.pop(res, None)
            update_cost_box()
            
    cost_btn_f = ttk.Frame(left_p)
    cost_btn_f.pack(fill=tk.X, padx=5)
    ttk.Button(cost_btn_f, text="Add Material", command=add_cost, width=12).pack(side=tk.LEFT, padx=2)
    ttk.Button(cost_btn_f, text="Remove", command=delete_cost, width=8).pack(side=tk.LEFT, padx=2)
    
    def save_building():
        sel = bld_box.curselection()
        if sel:
            idx = sel[0]
            buildings[idx] = {
                "name": b_name_var.get(),
                "label": b_lbl_var.get(),
                "effect": b_effect_var.get(),
                "cost": current_cost_dict
            }
            update_bld_box()
            
    def add_building():
        buildings.append({"name": "new_building", "label": "New Building", "cost": {"Lumber": 10}, "effect": "Provides general shelter"})
        update_bld_box()
        
    def delete_building():
        sel = bld_box.curselection()
        if sel:
            buildings.pop(sel[0])
            update_bld_box()
            
    btn_b = ttk.Frame(left_p)
    btn_b.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(btn_b, text="Add Building", command=add_building).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_b, text="Save Selected", command=save_building).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_b, text="Delete selected", command=delete_building).pack(side=tk.LEFT, padx=2)
    
    # Right Pane: Wellbeing Coefficients
    right_p = ttk.LabelFrame(paned, text="Wellbeing Coefficients & Limits")
    paned.add(right_p, weight=2)
    
    # Scrollable container for coefficients
    canvas = tk.Canvas(right_p, borderwidth=0, highlightthickness=0)
    scrollbar = ttk.Scrollbar(right_p, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)
    
    scroll_frame.bind(
        "<Configure>",
        lambda event: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    scrollbar.pack(side="right", fill="y")
    
    # List of Wellbeing keys
    coeff_keys = [
        "wellbeing_decay_rate", "food_per_farm", "food_per_kelp_farm", "food_per_dock",
        "safety_per_tower", "safety_per_wall", "safety_per_reef_wall", "security_per_barracks",
        "riot_discontent_limit", "riot_crime_limit", "revolution_discontent_limit",
        "revolution_crime_limit", "trade_abundance_level", "winter_travel_cost",
        "summer_growth_mult", "baseline_chaos", "moon_phase_effect"
    ]
    
    entries_dict = {}
    for r_idx, key in enumerate(coeff_keys):
        ttk.Label(scroll_frame, text=key.replace("_", " ").title() + ":").grid(row=r_idx, column=0, sticky=tk.W, padx=5, pady=3)
        var = tk.StringVar(value=str(coeffs.setdefault(key, 0.1)))
        ttk.Entry(scroll_frame, textvariable=var, width=10).grid(row=r_idx, column=1, padx=5, pady=3)
        entries_dict[key] = var
        
    def save_all():
        try:
            for key, var in entries_dict.items():
                coeffs[key] = float(var.get())
            settings['building_types'] = buildings
            settings['wellbeing_coefficients'] = coeffs
            if save_all_settings(settings):
                viewer.world_settings = settings
                viewer.reload_in_memory_constants()
                viewer.sync_data()
                root.destroy()
        except ValueError:
            messagebox.showerror("Error", "All wellbeing values must be numbers.")
            
    ttk.Button(root, text="Save & Apply All Settings", command=save_all).pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
    root.mainloop()

# ==========================================================
# 5. ECOLOGY SPECIES EDITOR (FLORA / FAUNA)
# ==========================================================
def edit_ecology_dialog(viewer):
    settings = load_all_settings()
    eco = settings.setdefault('ecology', {})
    
    species_params = eco.setdefault('species_params', {})
    predation_matrix = eco.setdefault('predation_matrix', {})
    harvest_table = eco.setdefault('harvest_table', {})
    domestication_table = eco.setdefault('domestication_table', {})
    biome_species = eco.setdefault('biome_species', {})
    
    root = tk.Tk()
    root.title("Ecology & Wildlife Species Editor")
    root.geometry("950x600")
    root.attributes("-topmost", True)
    
    paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Left: List of all species
    left_p = ttk.LabelFrame(paned, text="Flora & Fauna Species")
    paned.add(left_p, weight=2)
    
    species_box = tk.Listbox(left_p)
    species_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_species_box():
        species_box.delete(0, tk.END)
        for k in sorted(species_params.keys()):
            species_box.insert(tk.END, k)
    update_species_box()
    
    # Right: species parameters editor in tabs
    right_p = ttk.LabelFrame(paned, text="Selected Species Details")
    paned.add(right_p, weight=4)
    
    nb = ttk.Notebook(right_p)
    nb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Tab 1: Base stats
    stats_tab = ttk.Frame(nb)
    nb.add(stats_tab, text="Growth & Chain")
    
    ttk.Label(stats_tab, text="Base Growth Rate:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    growth_var = tk.StringVar()
    ttk.Entry(stats_tab, textvariable=growth_var, width=12).grid(row=0, column=1)
    
    ttk.Label(stats_tab, text="Carrying Cap:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    cap_var = tk.StringVar()
    ttk.Entry(stats_tab, textvariable=cap_var, width=12).grid(row=1, column=1)
    
    ttk.Label(stats_tab, text="Chaos Affinity:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    chaos_aff_var = tk.StringVar()
    ttk.Entry(stats_tab, textvariable=chaos_aff_var, width=12).grid(row=2, column=1)
    
    ttk.Label(stats_tab, text="Food Chain Role:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    chain_var = tk.StringVar()
    chain_cb = ttk.Combobox(stats_tab, textvariable=chain_var, values=["prey", "predator", "herbivore", "apex", "scavenger", "pest", "flora"], width=10)
    chain_cb.grid(row=3, column=1)
    
    # Predation prey list
    ttk.Label(stats_tab, text="Preys on:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
    prey_listbox = tk.Listbox(stats_tab, height=3)
    prey_listbox.grid(row=4, column=1, sticky=tk.NSEW, pady=5)
    
    active_prey_list = []
    
    def update_prey_listbox():
        prey_listbox.delete(0, tk.END)
        for p in active_prey_list:
            prey_listbox.insert(tk.END, p)
            
    def add_prey():
        p_name = ask_simple_string("Hunt Prey", "Enter prey species key:")
        if p_name:
            active_prey_list.append(p_name)
            update_prey_listbox()
            
    def delete_prey():
        sel = prey_listbox.curselection()
        if sel:
            active_prey_list.pop(sel[0])
            update_prey_listbox()
            
    btn_pr = ttk.Frame(stats_tab)
    btn_pr.grid(row=4, column=2, sticky=tk.NW, padx=5, pady=5)
    ttk.Button(btn_pr, text="+", command=add_prey, width=3).pack()
    ttk.Button(btn_pr, text="-", command=delete_prey, width=3).pack(pady=2)
    
    # Tab 2: Wild Harvesting
    harvest_tab_f = ttk.Frame(nb)
    nb.add(harvest_tab_f, text="Wild Harvesting")
    
    ttk.Label(harvest_tab_f, text="Primary Resource:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    har_res_var = tk.StringVar()
    ttk.Entry(harvest_tab_f, textvariable=har_res_var, width=15).grid(row=0, column=1)
    
    ttk.Label(harvest_tab_f, text="Amount Yielded:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    har_amt_var = tk.StringVar()
    ttk.Entry(harvest_tab_f, textvariable=har_amt_var, width=15).grid(row=1, column=1)
    
    ttk.Label(harvest_tab_f, text="Is Lethal Hunt/Cut:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    lethal_var = tk.BooleanVar()
    ttk.Checkbutton(harvest_tab_f, variable=lethal_var).grid(row=2, column=1, sticky=tk.W)
    
    ttk.Label(harvest_tab_f, text="Sec Resource (optional):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    har_sec_res_var = tk.StringVar()
    ttk.Entry(harvest_tab_f, textvariable=har_sec_res_var, width=15).grid(row=3, column=1)
    
    ttk.Label(harvest_tab_f, text="Sec Amount Yielded:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
    har_sec_amt_var = tk.StringVar()
    ttk.Entry(harvest_tab_f, textvariable=har_sec_amt_var, width=15).grid(row=4, column=1)
    
    # Tab 3: Domestication
    dom_tab_f = ttk.Frame(nb)
    nb.add(dom_tab_f, text="Domestication")
    
    ttk.Label(dom_tab_f, text="Facility Count Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    dom_fac_var = tk.StringVar()
    ttk.Entry(dom_tab_f, textvariable=dom_fac_var, width=20).grid(row=0, column=1)
    
    ttk.Label(dom_tab_f, text="Input Material:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    dom_in_res_var = tk.StringVar()
    ttk.Entry(dom_tab_f, textvariable=dom_in_res_var, width=15).grid(row=1, column=1)
    
    ttk.Label(dom_tab_f, text="Input Qty:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
    dom_in_amt_var = tk.StringVar()
    ttk.Entry(dom_tab_f, textvariable=dom_in_amt_var, width=8).grid(row=1, column=3)
    
    ttk.Label(dom_tab_f, text="Output Commodity:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    dom_out_res_var = tk.StringVar()
    ttk.Entry(dom_tab_f, textvariable=dom_out_res_var, width=15).grid(row=2, column=1)
    
    ttk.Label(dom_tab_f, text="Output Qty:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
    dom_out_amt_var = tk.StringVar()
    ttk.Entry(dom_tab_f, textvariable=dom_out_amt_var, width=8).grid(row=2, column=3)
    
    ttk.Label(dom_tab_f, text="Tool Benefit:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    dom_tool_var = tk.StringVar()
    dom_tool_cb = ttk.Combobox(dom_tab_f, textvariable=dom_tool_var, values=["transport", "fast_transport", "heavy_transport", "guard", "pest_control", "messenger", "None"], width=12)
    dom_tool_cb.grid(row=3, column=1)
    
    def load_species(evt):
        sel = species_box.curselection()
        if sel:
            k = species_box.get(sel[0])
            p = species_params.get(k, {})
            growth_var.set(str(p.get('growth', 0.05)))
            cap_var.set(str(p.get('cap', 300.0)))
            chaos_aff_var.set(str(p.get('chaos_aff', 0.0)))
            chain_var.set(p.get('food_chain', 'prey'))
            
            nonlocal active_prey_list
            active_prey_list = list(predation_matrix.get(k, []))
            update_prey_listbox()
            
            h = harvest_table.get(k, {})
            har_res_var.set(h.get('resource', ''))
            har_amt_var.set(str(h.get('amount', 0.0)))
            lethal_var.set(h.get('lethal', False))
            
            sec = h.get('secondary')
            if sec and isinstance(sec, (list, tuple)) and len(sec) == 2:
                har_sec_res_var.set(sec[0])
                har_sec_amt_var.set(str(sec[1]))
            else:
                har_sec_res_var.set('')
                har_sec_amt_var.set('0.0')
                
            d = domestication_table.get(k, {})
            dom_fac_var.set(d.get('facility', ''))
            inp = d.get('input')
            if inp:
                dom_in_res_var.set(inp[0])
                dom_in_amt_var.set(str(inp[1]))
            else:
                dom_in_res_var.set('')
                dom_in_amt_var.set('0.0')
            out = d.get('output')
            if out:
                dom_out_res_var.set(out[0])
                dom_out_amt_var.set(str(out[1]))
            else:
                dom_out_res_var.set('')
                dom_out_amt_var.set('0.0')
            dom_tool_var.set(str(d.get('tool_bonus', 'None')))
            
    species_box.bind("<<ListboxSelect>>", load_species)
    
    def save_species_changes():
        sel = species_box.curselection()
        if sel:
            k = species_box.get(sel[0])
            try:
                # 1. Save base stats
                species_params[k] = {
                    "growth": float(growth_var.get()),
                    "cap": float(cap_var.get()),
                    "chaos_aff": float(chaos_aff_var.get()),
                    "food_chain": chain_var.get()
                }
                # 2. Save predation
                if active_prey_list:
                    predation_matrix[k] = active_prey_list
                else:
                    predation_matrix.pop(k, None)
                    
                # 3. Save harvest
                sec_res = har_sec_res_var.get()
                sec_amt = float(har_sec_amt_var.get() or 0.0)
                sec_tuple = [sec_res, sec_amt] if sec_res else None
                
                harvest_table[k] = {
                    "resource": har_res_var.get(),
                    "amount": float(har_amt_var.get()),
                    "lethal": lethal_var.get(),
                    "secondary": sec_tuple
                }
                
                # 4. Save domestication
                fac = dom_fac_var.get()
                if fac:
                    in_res = dom_in_res_var.get()
                    in_amt = float(dom_in_amt_var.get() or 0)
                    out_res = dom_out_res_var.get()
                    out_amt = float(dom_out_amt_var.get() or 0)
                    tool_b = dom_tool_var.get()
                    if tool_b == 'None': tool_b = None
                    
                    domestication_table[k] = {
                        "facility": fac,
                        "input": [in_res, in_amt] if in_res else None,
                        "output": [out_res, out_amt] if out_res else None,
                        "secondary": None,
                        "tool_bonus": tool_b
                    }
                else:
                    domestication_table.pop(k, None)
                
                messagebox.showinfo("Saved", f"Changes for {k} applied to editor cache.")
            except ValueError:
                messagebox.showerror("Error", "Verify number formats.")
                
    def add_species():
        name = ask_simple_string("Add Species", "Enter species key (e.g. fauna_elk, flora_berry):")
        if name:
            if not (name.startswith("fauna_") or name.startswith("flora_")):
                messagebox.showwarning("Warning", "Species name should start with 'fauna_' or 'flora_'")
            species_params[name] = {"growth": 0.05, "cap": 300.0, "chaos_aff": 0.0, "food_chain": "prey"}
            update_species_box()
            
    def delete_species():
        sel = species_box.curselection()
        if sel:
            k = species_box.get(sel[0])
            species_params.pop(k, None)
            predation_matrix.pop(k, None)
            harvest_table.pop(k, None)
            domestication_table.pop(k, None)
            update_species_box()
            
    # Bottom actions for tab editing
    btn_sp = ttk.Frame(right_p)
    btn_sp.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(btn_sp, text="Add Species", command=add_species).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_sp, text="Delete selected", command=delete_species).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_sp, text="Save Selected Changes", command=save_species_changes).pack(side=tk.LEFT, padx=2)
    
    # Save All to file
    def save_all():
        eco['species_params'] = species_params
        eco['predation_matrix'] = predation_matrix
        eco['harvest_table'] = harvest_table
        eco['domestication_table'] = domestication_table
        # Maintain biome default distributions if new species aren't in them
        eco['biome_species'] = biome_species
        settings['ecology'] = eco
        if save_all_settings(settings):
            viewer.world_settings = settings
            # Copy to rules engine namespace variables via viewer
            viewer.reload_in_memory_constants()
            viewer.sync_data()
            root.destroy()
            
    ttk.Button(root, text="Save & Apply All Settings", command=save_all).pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
    root.mainloop()

# ==========================================================
# 6. RESOURCES & CRAFTING RECIPES EDITOR
# ==========================================================
def edit_resources_recipes_dialog(viewer):
    settings = load_all_settings()
    resources = list(settings.setdefault('resources_and_materials', []))
    recipes = list(settings.setdefault('production_recipes', []))
    
    root = tk.Tk()
    root.title("Resource Materials & Production Recipes Editor")
    root.geometry("850x500")
    root.attributes("-topmost", True)
    
    paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Left: Raw materials
    left_p = ttk.LabelFrame(paned, text="Raw Resource Materials")
    paned.add(left_p, weight=2)
    
    res_box = tk.Listbox(left_p)
    res_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_res_box():
        res_box.delete(0, tk.END)
        for r in resources:
            res_box.insert(tk.END, f"{r.get('name')} (value: {r.get('cost')})")
    update_res_box()
    
    form_r = ttk.Frame(left_p)
    form_r.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(form_r, text="Name:").grid(row=0, column=0, sticky=tk.W)
    r_name_var = tk.StringVar()
    ttk.Entry(form_r, textvariable=r_name_var, width=12).grid(row=0, column=1)
    
    ttk.Label(form_r, text="Source:").grid(row=0, column=2, sticky=tk.W)
    r_src_var = tk.StringVar()
    ttk.Entry(form_r, textvariable=r_src_var, width=10).grid(row=0, column=3)
    
    ttk.Label(form_r, text="Base Cost:").grid(row=1, column=0, sticky=tk.W)
    r_cost_var = tk.StringVar()
    ttk.Entry(form_r, textvariable=r_cost_var, width=12).grid(row=1, column=1)
    
    def load_resource(evt):
        sel = res_box.curselection()
        if sel:
            r = resources[sel[0]]
            r_name_var.set(r.get('name', ''))
            r_src_var.set(r.get('harvested_from', 'General'))
            r_cost_var.set(str(r.get('cost', 10.0)))
    res_box.bind("<<ListboxSelect>>", load_resource)
    
    def save_resource():
        sel = res_box.curselection()
        if sel:
            idx = sel[0]
            try:
                resources[idx] = {
                    "name": r_name_var.get(),
                    "harvested_from": r_src_var.get(),
                    "cost": float(r_cost_var.get())
                }
                update_res_box()
            except ValueError: pass
            
    def add_resource():
        resources.append({"name": "New Resource", "harvested_from": "Mine/Forest", "cost": 10.0})
        update_res_box()
        
    def delete_resource():
        sel = res_box.curselection()
        if sel:
            resources.pop(sel[0])
            update_res_box()
            
    btn_r = ttk.Frame(left_p)
    btn_r.pack(fill=tk.X, padx=5, pady=2)
    ttk.Button(btn_r, text="Add", command=add_resource, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_r, text="Save", command=save_resource, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_r, text="Del", command=delete_resource, width=6).pack(side=tk.LEFT, padx=2)
    
    # Right: Production recipes
    right_p = ttk.LabelFrame(paned, text="Production / Crafting Recipes")
    paned.add(right_p, weight=3)
    
    rec_box = tk.Listbox(right_p)
    rec_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_rec_box():
        rec_box.delete(0, tk.END)
        for r in recipes:
            rec_box.insert(tk.END, f"{r.get('name')} (yield: {r.get('output')})")
    update_rec_box()
    
    form_rc = ttk.Frame(right_p)
    form_rc.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(form_rc, text="Output name:").grid(row=0, column=0, sticky=tk.W)
    rc_name_var = tk.StringVar()
    ttk.Entry(form_rc, textvariable=rc_name_var, width=15).grid(row=0, column=1)
    
    ttk.Label(form_rc, text="Output Qty:").grid(row=0, column=2, sticky=tk.W)
    rc_qty_var = tk.StringVar()
    ttk.Entry(form_rc, textvariable=rc_qty_var, width=6).grid(row=0, column=3)
    
    ttk.Label(form_rc, text="Desc:").grid(row=1, column=0, sticky=tk.W)
    rc_desc_var = tk.StringVar()
    ttk.Entry(form_rc, textvariable=rc_desc_var, width=28).grid(row=1, column=1, columnspan=3, pady=5)
    
    # Ingredients listbox for the recipe
    ttk.Label(right_p, text="Required Inputs:").pack(anchor=tk.W, padx=5)
    inputs_box = tk.Listbox(right_p, height=4)
    inputs_box.pack(fill=tk.X, padx=5, pady=2)
    
    current_inputs_dict = {}
    
    def load_recipe(evt):
        sel = rec_box.curselection()
        if sel:
            r = recipes[sel[0]]
            rc_name_var.set(r.get('name', ''))
            rc_qty_var.set(str(r.get('output', 1.0)))
            rc_desc_var.set(r.get('description', ''))
            
            nonlocal current_inputs_dict
            current_inputs_dict = dict(r.get('inputs', {}))
            update_inputs_box()
            
    rec_box.bind("<<ListboxSelect>>", load_recipe)
    
    def update_inputs_box():
        inputs_box.delete(0, tk.END)
        for res, qty in current_inputs_dict.items():
            inputs_box.insert(tk.END, f"{res}: {qty}")
            
    def add_input():
        res = ask_simple_string("Add Input Material", "Enter resource name:")
        if res:
            qty = ask_simple_float("Add Input Qty", f"Enter quantity for {res}:")
            if qty is not None:
                current_inputs_dict[res] = qty
                update_inputs_box()
                
    def delete_input():
        sel = inputs_box.curselection()
        if sel:
            line = inputs_box.get(sel[0])
            res = line.split(':')[0].strip()
            current_inputs_dict.pop(res, None)
            update_inputs_box()
            
    inp_btn_f = ttk.Frame(right_p)
    inp_btn_f.pack(fill=tk.X, padx=5)
    ttk.Button(inp_btn_f, text="Add Input", command=add_input, width=10).pack(side=tk.LEFT, padx=2)
    ttk.Button(inp_btn_f, text="Remove", command=delete_input, width=8).pack(side=tk.LEFT, padx=2)
    
    def save_recipe():
        sel = rec_box.curselection()
        if sel:
            idx = sel[0]
            try:
                recipes[idx] = {
                    "name": rc_name_var.get(),
                    "inputs": current_inputs_dict,
                    "output": float(rc_qty_var.get()),
                    "description": rc_desc_var.get()
                }
                update_rec_box()
            except ValueError: pass
            
    def add_recipe():
        recipes.append({"name": "New Commodity", "inputs": {"Iron Ore": 2.0}, "output": 1.0, "description": "Refined good"})
        update_rec_box()
        
    def delete_recipe():
        sel = rec_box.curselection()
        if sel:
            recipes.pop(sel[0])
            update_rec_box()
            
    btn_rc = ttk.Frame(right_p)
    btn_rc.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(btn_rc, text="Add Recipe", command=add_recipe).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_rc, text="Save Selected", command=save_recipe).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_rc, text="Delete selected", command=delete_recipe).pack(side=tk.LEFT, padx=2)
    
    # Save All
    def save_all():
        settings['resources_and_materials'] = resources
        settings['production_recipes'] = recipes
        if save_all_settings(settings):
            viewer.world_settings = settings
            viewer.reload_in_memory_constants()
            viewer.sync_data()
            root.destroy()
            
    ttk.Button(root, text="Save & Apply All Settings", command=save_all).pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
    root.mainloop()

# ==========================================================
# 7. CULTS & PRISONS EDITOR
# ==========================================================
def edit_cults_dialog(viewer):
    settings = load_all_settings()
    
    cults = list(settings.setdefault('cult_names', [
        "Tiraton", "Stagus", "Metrion", "Aurgenas", "Vecelo", "Lophex",
        "Tyrustis", "Opecten", "Carulkem", "Termhill", "Virantor", "Gavusrix"
    ]))
    prisons = list(settings.setdefault('prisons', []))
    
    root = tk.Tk()
    root.title("Cult Organizations & Magistar Prisons Editor")
    root.geometry("800x480")
    root.attributes("-topmost", True)
    
    paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Left: Cult names
    left_p = ttk.LabelFrame(paned, text="12 Cult Organizations")
    paned.add(left_p, weight=2)
    
    cult_box = tk.Listbox(left_p)
    cult_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_cult_box():
        cult_box.delete(0, tk.END)
        for c in cults:
            cult_box.insert(tk.END, c)
    update_cult_box()
    
    def add_cult():
        name = ask_simple_string("Add Cult", "Enter cult name:")
        if name:
            cults.append(name)
            update_cult_box()
            
    def rename_cult():
        sel = cult_box.curselection()
        if sel:
            idx = sel[0]
            new_name = ask_simple_string("Rename Cult", "Enter new name:", cults[idx])
            if new_name:
                cults[idx] = new_name
                update_cult_box()
                
    def delete_cult():
        sel = cult_box.curselection()
        if sel:
            cults.pop(sel[0])
            update_cult_box()
            
    btn_c = ttk.Frame(left_p)
    btn_c.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(btn_c, text="Add", command=add_cult, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_c, text="Rename", command=rename_cult, width=8).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_c, text="Del", command=delete_cult, width=6).pack(side=tk.LEFT, padx=2)
    
    # Right: Magistar Prisons
    right_p = ttk.LabelFrame(paned, text="Magistar (Dragon) Prisons")
    paned.add(right_p, weight=3)
    
    pris_box = tk.Listbox(right_p)
    pris_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_pris_box():
        pris_box.delete(0, tk.END)
        for p in prisons:
            pris_box.insert(tk.END, f"Prison {p.get('id')} at Cell {p.get('cell_id')} (Seal: {p.get('seal_integrity')*100:.0f}%)")
    update_pris_box()
    
    form_p = ttk.Frame(right_p)
    form_p.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(form_p, text="Prison ID:").grid(row=0, column=0, sticky=tk.W)
    p_id_var = tk.StringVar()
    ttk.Entry(form_p, textvariable=p_id_var, width=8).grid(row=0, column=1)
    
    ttk.Label(form_p, text="Cell ID:").grid(row=0, column=2, sticky=tk.W)
    p_cell_var = tk.StringVar()
    ttk.Entry(form_p, textvariable=p_cell_var, width=8).grid(row=0, column=3)
    
    ttk.Label(form_p, text="Seal Integrity:").grid(row=1, column=0, sticky=tk.W)
    p_seal_var = tk.StringVar()
    ttk.Entry(form_p, textvariable=p_seal_var, width=8).grid(row=1, column=1, pady=5)
    
    def load_prison(evt):
        sel = pris_box.curselection()
        if sel:
            p = prisons[sel[0]]
            p_id_var.set(str(p.get('id', 1)))
            p_cell_var.set(str(p.get('cell_id', 1)))
            p_seal_var.set(str(p.get('seal_integrity', 1.0)))
    pris_box.bind("<<ListboxSelect>>", load_prison)
    
    def save_prison():
        sel = pris_box.curselection()
        if sel:
            idx = sel[0]
            try:
                cid = int(p_cell_var.get())
                cell = next((c for c in viewer.cells if c['id'] == cid), None)
                if not cell:
                    messagebox.showerror("Error", f"Cell ID {cid} not found on the map.")
                    return
                prisons[idx] = {
                    "id": int(p_id_var.get()),
                    "cell_id": cid,
                    "x": cell['center'][0],
                    "y": cell['center'][1],
                    "seal_integrity": float(p_seal_var.get())
                }
                update_pris_box()
            except ValueError:
                messagebox.showerror("Error", "Check numeric formats.")
                
    def add_prison():
        new_id = max([p.get('id', 0) for p in prisons]) + 1 if prisons else 1
        prisons.append({"id": new_id, "cell_id": 1, "x": 0.0, "y": 0.0, "seal_integrity": 1.0})
        update_pris_box()
        
    def delete_prison():
        sel = pris_box.curselection()
        if sel:
            prisons.pop(sel[0])
            update_pris_box()
            
    btn_pr = ttk.Frame(right_p)
    btn_pr.pack(fill=tk.X, padx=5, pady=2)
    ttk.Button(btn_pr, text="Add", command=add_prison, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_pr, text="Save", command=save_prison, width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_pr, text="Del", command=delete_prison, width=6).pack(side=tk.LEFT, padx=2)
    
    # Save All
    def save_all():
        settings['cult_names'] = cults
        settings['prisons'] = prisons
        if save_all_settings(settings):
            viewer.world_settings = settings
            viewer.reload_in_memory_constants()
            viewer.sync_data()
            root.destroy()
            
    ttk.Button(root, text="Save & Apply All Settings", command=save_all).pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
    root.mainloop()

# ==========================================================
# 8. FRINGE GROUPS EDITOR
# ==========================================================
def edit_fringe_dialog(viewer):
    settings = load_all_settings()
    ent = settings.setdefault('entities', {})
    fringe = list(ent.setdefault('fringe_groups', []))
    
    root = tk.Tk()
    root.title("Fringe Factions & Specialized Guilds Editor")
    root.geometry("600x400")
    root.attributes("-topmost", True)
    
    left_p = ttk.LabelFrame(root, text="Fringe Factions List")
    left_p.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    fg_box = tk.Listbox(left_p)
    fg_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    def update_fg_box():
        fg_box.delete(0, tk.END)
        for fg in fringe:
            fg_box.insert(tk.END, fg.get('name', 'Group'))
    update_fg_box()
    
    right_p = ttk.LabelFrame(root, text="Specialized Stances")
    right_p.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    ttk.Label(right_p, text="Faction Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    fg_name_var = tk.StringVar()
    ttk.Entry(right_p, textvariable=fg_name_var, width=18).grid(row=0, column=1, padx=5, pady=5)
    
    ttk.Label(right_p, text="Specialty / Role:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    fg_spec_var = tk.StringVar()
    ttk.Entry(right_p, textvariable=fg_spec_var, width=18).grid(row=1, column=1, padx=5, pady=5)
    
    fg_color_var = tk.StringVar(value="#888888")
    color_btn = tk.Button(right_p, text="Guild Banner Color", bg="#888888", width=16)
    color_btn.grid(row=2, column=0, columnspan=2, pady=10)
    
    def select_fg_color():
        c = colorchooser.askcolor(title="Pick Banner Color", initialcolor=fg_color_var.get(), parent=root)
        if c[1]:
            fg_color_var.set(c[1])
            color_btn.config(bg=c[1])
    color_btn.config(command=select_fg_color)
    
    def load_fringe(evt):
        sel = fg_box.curselection()
        if sel:
            fg = fringe[sel[0]]
            fg_name_var.set(fg.get('name', ''))
            fg_spec_var.set(fg.get('specialty', 'Smuggling'))
            fg_color_var.set(fg.get('color', '#888888'))
            color_btn.config(bg=fg.get('color', '#888888'))
    fg_box.bind("<<ListboxSelect>>", load_fringe)
    
    def save_fringe():
        sel = fg_box.curselection()
        if sel:
            idx = sel[0]
            fringe[idx] = {
                "name": fg_name_var.get(),
                "color": fg_color_var.get(),
                "specialty": fg_spec_var.get()
            }
            update_fg_box()
            
    def add_fringe():
        fringe.append({"name": "New Guild", "color": "#888888", "specialty": "Mercenary Operations"})
        update_fg_box()
        
    def delete_fringe():
        sel = fg_box.curselection()
        if sel:
            fringe.pop(sel[0])
            update_fg_box()
            
    btn_fg = ttk.Frame(left_p)
    btn_fg.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(btn_fg, text="Add Guild", command=add_fringe).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_fg, text="Save", command=save_fringe).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_fg, text="Del", command=delete_fringe).pack(side=tk.LEFT, padx=2)
    
    # Save All
    def save_all():
        ent['fringe_groups'] = fringe
        settings['entities'] = ent
        if save_all_settings(settings):
            viewer.world_settings = settings
            viewer.reload_in_memory_constants()
            viewer.sync_data()
            root.destroy()
            
    ttk.Button(root, text="Save & Apply All Settings", command=save_all).pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
    root.mainloop()

# ==========================================================
# INTERNAL TKINTER DIALOG HELPERS
# ==========================================================
def ask_simple_string(title, prompt, initialvalue=""):
    dialog = tk.Toplevel()
    dialog.title(title)
    dialog.geometry("300x120")
    dialog.attributes("-topmost", True)
    dialog.grab_set()
    
    ttk.Label(dialog, text=prompt).pack(anchor=tk.W, padx=10, pady=5)
    var = tk.StringVar(value=initialvalue)
    entry = ttk.Entry(dialog, textvariable=var, width=30)
    entry.pack(padx=10, pady=5)
    entry.focus_set()
    
    result = None
    
    def on_ok():
        nonlocal result
        result = var.get()
        dialog.destroy()
        
    def on_cancel():
        dialog.destroy()
        
    btn_f = ttk.Frame(dialog)
    btn_f.pack(fill=tk.X, padx=10, pady=5)
    ttk.Button(btn_f, text="OK", command=on_ok, width=8).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_f, text="Cancel", command=on_cancel, width=8).pack(side=tk.LEFT, padx=5)
    
    dialog.wait_window()
    return result

def ask_simple_int(title, prompt, initialvalue=0):
    res_str = ask_simple_string(title, prompt, str(initialvalue))
    if res_str is not None:
        try:
            return int(res_str)
        except ValueError:
            messagebox.showerror("Error", "Input must be an integer.")
    return None

def ask_simple_float(title, prompt, initialvalue=0.0):
    res_str = ask_simple_string(title, prompt, str(initialvalue))
    if res_str is not None:
        try:
            return float(res_str)
        except ValueError:
            messagebox.showerror("Error", "Input must be a number.")
    return None
