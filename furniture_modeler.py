import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict
from scipy.optimize import minimize
from skimage import color
import os
import datetime

# =========================================================
# COLOR MIXING MODULE (Kubelka-Munk)
# =========================================================
CAP_WEIGHT_GRAMS = 2.5
PIGMENT_STRENGTH_FACTOR = 5.0
N_DRAWS = 5000
RANDOM_SEED = 42
INVENTORY_SIZE = 60
BASE_COLOR = '#F8E6B7'
EDGE_COLOR = '#222222'

def hex_to_rgb_norm(hex_str):
    hex_str = str(hex_str).lstrip('#')
    if len(hex_str) != 6: hex_str = "F8E6B7"
    return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)]) / 255.0

def rgb_to_hex(rgb_norm):
    rgb = np.clip(rgb_norm * 255, 0, 255).astype(int)
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def rgb_to_ks(rgb_norm):
    rgb_lin = np.where(rgb_norm > 0.04045, ((rgb_norm + 0.055) / 1.055) ** 2.4, rgb_norm / 12.92)
    R = np.clip(rgb_lin, 0.01, 0.99)
    return (1.0 - R)**2 / (2.0 * R)

def ks_to_rgb(ks):
    R = 1.0 + ks - np.sqrt(ks**2 + 2.0 * ks)
    rgb_norm = np.where(R > 0.0031308, 1.055 * (R ** (1/2.4)) - 0.055, 12.92 * R)
    return np.clip(rgb_norm, 0, 1)

def calculate_delta_e(rgb1, rgb2):
    c1 = color.rgb2lab(rgb1.reshape(1, 1, 3))
    c2 = color.rgb2lab(rgb2.reshape(1, 1, 3))
    return float(color.deltaE_ciede2000(c1[0, 0], c2[0, 0]))

def calculate_color_mix(target_hex, total_mass_grams):
    recipe = {"status": "success", "target_hex": target_hex, "mix_caps": [], "pigments": [], "delta_e": 0}
    try:
        csv_path = "BRICKIT_palette_hex_optionB_full_sorted_rgb.xlsx - palette.csv"
        if not os.path.exists(csv_path):
            recipe["status"] = "fallback"
            recipe["message"] = "CSV not found. Using raw color."
            return recipe

        df = pd.read_csv(csv_path)
        np.random.seed(RANDOM_SEED)
        drawn_indices = np.random.randint(0, len(df), size=N_DRAWS)
        drawn_caps = df.iloc[drawn_indices].copy()
        
        inventory = (drawn_caps.groupby(['color_en', 'color_th', 'hex', 'r', 'g', 'b', 'group'])
                     .size().reset_index(name='stock_caps')
                     .sort_values('stock_caps', ascending=False).reset_index(drop=True))
        inventory['stock_mass'] = inventory['stock_caps'] * CAP_WEIGHT_GRAMS

        target_rgb = hex_to_rgb_norm(target_hex)
        inv_rgb = inventory[['r', 'g', 'b']].values / 255.0
        inv_ks = np.array([rgb_to_ks(c) for c in inv_rgb])

        inv_lab = color.rgb2lab(inv_rgb.reshape(-1, 1, 3)).reshape(-1, 3)
        target_lab = color.rgb2lab(target_rgb.reshape(1, 1, 3)).reshape(1, 3)
        distances = np.linalg.norm(inv_lab - target_lab, axis=1)

        num_candidates = min(INVENTORY_SIZE, len(inventory))
        candidate_indices = np.argsort(distances)[:num_candidates]
        subset_ks = inv_ks[candidate_indices]
        subset_inventory = inventory.iloc[candidate_indices].copy()
        subset_stock_mass = subset_inventory['stock_mass'].values

        def objective_m1(weights):
            if np.sum(weights) == 0: return 100.0
            w_norm = weights / np.sum(weights)
            mix_ks = np.dot(w_norm, subset_ks)
            return calculate_delta_e(ks_to_rgb(mix_ks), target_rgb)

        x0 = np.zeros(num_candidates); x0[0] = 1.0
        bounds = [(0.0, min(1.0, m / total_mass_grams)) for m in subset_stock_mass]
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
        
        res_m1 = minimize(objective_m1, x0, method='SLSQP', bounds=bounds, constraints=constraints, options={'maxiter': 100, 'ftol': 1e-6})
        m1_ratios = res_m1.x

        for idx, ratio in enumerate(m1_ratios):
            if ratio > 0.01:
                row = subset_inventory.iloc[idx]
                grams_needed = float(ratio * total_mass_grams)
                recipe["mix_caps"].append({
                    "color_name": str(row['color_en']), "hex": str(row['hex']),
                    "grams": round(grams_needed, 2), "caps": round(grams_needed / CAP_WEIGHT_GRAMS, 1)
                })

        m1_mix_ks = np.dot(m1_ratios, subset_ks)
        recipe["delta_e"] = round(calculate_delta_e(ks_to_rgb(m1_mix_ks), target_rgb), 2)
        return recipe
    except Exception as e:
        recipe["status"] = "error"
        recipe["message"] = str(e)
        return recipe

# =========================================================
# 🏗️ 3D GENERATOR FUNCTIONS (ALL 5 TYPES)
# =========================================================
def get_btype(dx, dy, dz):
    dims = sorted([int(dx), int(dy), int(dz)])
    return f"brick_{dims[0]}x{dims[1]}x{dims[2]}"

def generate_smart_tiled_shelf(scale, base_color):
    blocks_used = []
    S = float(scale)
    logical_w, logical_l, logical_h = 32, 20, 16
    real_w, real_l, real_h = int(logical_w * S), int(logical_l * S), int(logical_h * S)
    real_w += real_w % 2; real_l += real_l % 2; real_h += real_h % 2
    thickness = 2
    bottom_z = int(4 * S); bottom_z += bottom_z % 2
    top_z = real_h - thickness

    z_levels = [top_z] if S <= 0.5 else [int(round(z / 2.0)) * 2 for z in np.linspace(bottom_z, top_z, max(2, int(S) + 1))]
    x_legs = [0]
    num_x_spans = max(1, int(S))
    step_x = (real_w - 2) / num_x_spans
    for i in range(1, num_x_spans): x_legs.append(int(round(i * step_x / 2.0)) * 2)
    x_legs.append(real_w - 2)
    x_legs = sorted(list(set(x_legs)))
    y_legs = [0, real_l - 2]
    leg_positions = [(x, y) for x in x_legs for y in y_legs]

    def pack_legs(start_z, target_h):
        for cx, cy in leg_positions:
            current_z = start_z; rem_h = target_h
            while rem_h > 0:
                bh = int(min(8, rem_h)); bh += bh % 2
                if bh > rem_h: bh = int(rem_h)
                blocks_used.append({'type': get_btype(2, 2, bh), 'color': base_color, 'x': cx, 'y': cy, 'z': current_z, 'dx': 2, 'dy': 2, 'dz': bh})
                current_z += bh; rem_h -= bh

    pack_legs(0, z_levels[0])
    for i in range(len(z_levels) - 1): pack_legs(z_levels[i] + thickness, z_levels[i+1] - (z_levels[i] + thickness))

    def pack_shelf(z_level):
        for cx, cy in leg_positions:
            blocks_used.append({'type': get_btype(2, 2, thickness), 'color': base_color, 'x': cx, 'y': cy, 'z': z_level, 'dx': 2, 'dy': 2, 'dz': thickness})
        for y in range(2, real_l - 2, 8):
            dy = min(8, real_l - 2 - y)
            if dy > 0:
                blocks_used.append({'type': get_btype(2, dy, thickness), 'color': base_color, 'x': 0, 'y': y, 'z': z_level, 'dx': 2, 'dy': dy, 'dz': thickness})
                blocks_used.append({'type': get_btype(2, dy, thickness), 'color': base_color, 'x': real_w - 2, 'y': y, 'z': z_level, 'dx': 2, 'dy': dy, 'dz': thickness})
        for x in range(2, real_w - 2, 8):
            dx = min(8, real_w - 2 - x)
            if dx > 0:
                blocks_used.append({'type': get_btype(dx, 2, thickness), 'color': base_color, 'x': x, 'y': 0, 'z': z_level, 'dx': dx, 'dy': 2, 'dz': thickness})
                blocks_used.append({'type': get_btype(dx, 2, thickness), 'color': base_color, 'x': x, 'y': real_l - 2, 'z': z_level, 'dx': dx, 'dy': 2, 'dz': thickness})
                for y in range(2, real_l - 2, 8):
                    dy = min(8, real_l - 2 - y)
                    if dy > 0: blocks_used.append({'type': get_btype(dx, dy, thickness), 'color': base_color, 'x': x, 'y': y, 'z': z_level, 'dx': dx, 'dy': dy, 'dz': thickness})

    for zl in z_levels: pack_shelf(zl)
    return blocks_used, real_w, real_l, real_h

def generate_shoe_rack(scale, has_walls, base_color):
    blocks_used = []
    S = float(scale)
    logical_w = 80; real_l = 32; real_h = 96
    real_w = max(40, int(logical_w * S)); real_w += real_w % 2
    thickness = 2; bottom_z = 8
    top_z = real_h - thickness
    num_shelves = max(3, int(real_h / 18))
    z_levels = [int(round(z / 2.0)) * 2 for z in np.linspace(bottom_z, top_z, num_shelves)]
    leg_size = 4
    x_legs = [0, real_w - leg_size] if has_walls else [2, real_w - leg_size - 2]
    y_legs = [0, real_l - leg_size] if has_walls else [2, real_l - leg_size - 2]
    if real_w >= 100: x_legs.insert(1, (real_w // 2) - ((real_w // 2) % 2))

    def pack_block(start_x, end_x, start_y, end_y, start_z, target_h):
        if target_h <= 0 or start_x >= end_x or start_y >= end_y: return
        for z in range(0, target_h, 8):
            dz = min(8, target_h - z); dz += dz % 2; dz = min(dz, int(target_h - z))
            for x in range(start_x, end_x, 8):
                dx = min(8, end_x - x)
                for y in range(start_y, end_y, 8):
                    dy = min(8, end_y - y)
                    blocks_used.append({'type': get_btype(dx, dy, dz), 'color': base_color, 'x': x, 'y': y, 'z': start_z + z, 'dx': dx, 'dy': dy, 'dz': dz})

    for cx in x_legs:
        for cy in y_legs:
            pack_block(cx, cx + leg_size, cy, cy + leg_size, 0, z_levels[0])
            for i in range(len(z_levels) - 1): pack_block(cx, cx + leg_size, cy, cy + leg_size, z_levels[i] + thickness, z_levels[i+1] - (z_levels[i] + thickness))

    if has_walls:
        pack_block(0, thickness, 0, real_l, z_levels[0], real_h - z_levels[0])
        pack_block(real_w - thickness, real_w, 0, real_l, z_levels[0], real_h - z_levels[0])
        pack_block(thickness, real_w - thickness, real_l - thickness, real_l, z_levels[0], real_h - z_levels[0])
        for zl in z_levels: pack_block(thickness, real_w - thickness, 0, real_l - thickness, zl, thickness)
        pack_block(0, real_w, 0, real_l, real_h, thickness)
        final_h = real_h + thickness
    else:
        for zl in z_levels: pack_block(0, real_w, 0, real_l, zl, thickness)
        final_h = real_h

    return blocks_used, real_w, real_l, final_h

def generate_cable_box(w, l, h, base_color):
    blocks_used = []
    real_w, real_l, real_h = max(20, int(w)), max(12, int(l)), max(10, int(h))
    real_w += real_w % 2; real_l += real_l % 2; real_h += real_h % 2
    thick = 2

    def pack_block(start_x, end_x, start_y, end_y, start_z, target_h):
        if target_h <= 0 or start_x >= end_x or start_y >= end_y: return
        for z in range(0, target_h, 8):
            dz = min(8, target_h - z); dz += dz % 2; dz = min(dz, int(target_h - z))
            for x in range(start_x, end_x, 8):
                dx = min(8, end_x - x)
                for y in range(start_y, end_y, 8):
                    dy = min(8, end_y - y)
                    blocks_used.append({'type': get_btype(dx, dy, dz), 'color': base_color, 'x': x, 'y': y, 'z': start_z + z, 'dx': dx, 'dy': dy, 'dz': dz})

    pack_block(0, real_w, 0, real_l, 0, thick)
    wall_h = real_h - (thick * 2)
    pack_block(0, real_w, 0, thick, thick, wall_h)
    pack_block(0, real_w, real_l - thick, real_l, thick, wall_h)

    mid_y = real_l // 2; mid_y -= mid_y % 2
    slit_w = 4; slit_start = mid_y - (slit_w // 2); slit_end = mid_y + (slit_w // 2)

    pack_block(0, thick, thick, slit_start, thick, wall_h)
    pack_block(0, thick, slit_end, real_l - thick, thick, wall_h)
    pack_block(real_w - thick, real_w, thick, slit_start, thick, wall_h)
    pack_block(real_w - thick, real_w, slit_end, real_l - thick, thick, wall_h)

    gap_size = 2; lid_end_y = real_l - thick - gap_size
    pack_block(0, real_w, 0, lid_end_y, real_h - thick, thick)
    pack_block(0, thick, lid_end_y, real_l - thick, real_h - thick, thick)
    pack_block(real_w - thick, real_w, lid_end_y, real_l - thick, real_h - thick, thick)

    return blocks_used, real_w, real_l, real_h

def generate_device_stand(w, l, h, base_color):
    blocks_used = []
    real_w = max(10, int(w)); real_w += real_w % 2
    real_l = max(10, int(l)); real_l += real_l % 2
    real_h = max(10, int(h)); real_h += real_h % 2
    thick = 2

    def pack_block(start_x, end_x, start_y, end_y, start_z, target_h):
        if target_h <= 0 or start_x >= end_x or start_y >= end_y: return
        for z in range(0, target_h, 8):
            dz = min(8, target_h - z); dz += dz % 2; dz = min(dz, int(target_h - z))
            for x in range(start_x, end_x, 8):
                dx = min(8, end_x - x)
                for y in range(start_y, end_y, 8):
                    dy = min(8, end_y - y)
                    blocks_used.append({'type': get_btype(dx, dy, dz), 'color': base_color, 'x': x, 'y': y, 'z': start_z + z, 'dx': dx, 'dy': dy, 'dz': dz})

    side_width = (real_w - 4) // 2; side_width -= side_width % 2
    if side_width < 2: side_width = 2
    hole_start = side_width; hole_end = real_w - side_width; gap_y = 4

    pack_block(0, hole_start, 0, gap_y, 0, thick)
    pack_block(hole_end, real_w, 0, gap_y, 0, thick)
    pack_block(0, real_w, gap_y, real_l, 0, thick)
    pack_block(0, hole_start, 0, 2, thick, 2)
    pack_block(hole_end, real_w, 0, 2, thick, 2)

    steps = max(1, (real_l - gap_y) // 2)
    available_h = real_h - thick
    step_h = available_h // steps; step_h -= step_h % 2
    if step_h <= 0: step_h = 2

    current_z = thick
    for i in range(steps):
        y_start = gap_y + (i * 2); y_end = real_l
        h_step = step_h
        if i == steps - 1:
            h_step = real_h - current_z; h_step -= h_step % 2
        if h_step > 0 and y_start < y_end:
            pack_block(0, real_w, y_start, y_end, current_z, h_step)
            current_z += h_step

    return blocks_used, real_w, real_l, real_h

def generate_stationery_organizer(w, l, h, base_color):
    blocks_used = []
    real_w = max(16, int(w)); real_w += real_w % 2
    real_l = max(12, int(l)); real_l += real_l % 2
    real_h = max(10, int(h)); real_h += real_h % 2
    thick = 2

    def pack_block(start_x, end_x, start_y, end_y, start_z, target_h):
        if target_h <= 0 or start_x >= end_x or start_y >= end_y: return
        for z in range(0, target_h, 8):
            dz = min(8, target_h - z); dz += dz % 2; dz = min(dz, int(target_h - z))
            for x in range(start_x, end_x, 8):
                dx = min(8, end_x - x)
                for y in range(start_y, end_y, 8):
                    dy = min(8, end_y - y)
                    blocks_used.append({'type': get_btype(dx, dy, dz), 'color': base_color, 'x': x, 'y': y, 'z': start_z + z, 'dx': dx, 'dy': dy, 'dz': dz})

    pack_block(0, real_w, 0, real_l, 0, thick)
    div_y = (real_l // 2) - ((real_l // 2) % 2)
    div_x = (real_w // 2) - ((real_w // 2) % 2)
    back_h = real_h - thick
    front_h = max(4, (real_h // 2) - ((real_h // 2) % 2))

    pack_block(0, thick, div_y, real_l, thick, back_h)
    pack_block(real_w - thick, real_w, div_y, real_l, thick, back_h)
    pack_block(thick, real_w - thick, real_l - thick, real_l, thick, back_h)
    pack_block(thick, real_w - thick, div_y, div_y + thick, thick, back_h)
    pack_block(0, thick, 0, div_y, thick, front_h)
    pack_block(real_w - thick, real_w, 0, div_y, thick, front_h)
    pack_block(thick, real_w - thick, 0, thick, thick, front_h)
    pack_block(div_x, div_x + thick, thick, div_y, thick, front_h)

    return blocks_used, real_w, real_l, real_h

# =========================================================
# 🚀 MAIN GENERATOR WRAPPER (Called by API)
# =========================================================
def generate_model_json(item_type, w=32, l=20, h=16, scale=1.0, color_hex="#19e619", has_walls=False, save_to_file=True):
    """รับค่าพารามิเตอร์ สร้าง 3D Model ทั้ง 5 ชนิด และคืนค่าเป็น JSON พร้อมข้อมูลวัสดุ"""
    item_type = str(item_type).lower()
    color_hex = color_hex if str(color_hex).startswith('#') else f"#{color_hex}"

    if 'shoe' in item_type or 'รองเท้า' in item_type or 'cabinet' in item_type:
        blocks_data, final_w, final_l, final_h = generate_shoe_rack(scale, has_walls, color_hex)
        title = "Cabinet Shoe Rack" if has_walls else "Open Shoe Rack"
    elif 'cable' in item_type or 'สายไฟ' in item_type:
        blocks_data, final_w, final_l, final_h = generate_cable_box(w, l, h, color_hex)
        title = "Cable Organizer Box"
    elif 'device' in item_type or 'มือถือ' in item_type or 'แท็บเล็ต' in item_type:
        blocks_data, final_w, final_l, final_h = generate_device_stand(w, l, h, color_hex)
        title = "Phone/Tablet Stand"
    elif 'stationery' in item_type or 'เครื่องเขียน' in item_type or 'ปากกา' in item_type:
        blocks_data, final_w, final_l, final_h = generate_stationery_organizer(w, l, h, color_hex)
        title = "Stationery Organizer"
    else:
        blocks_data, final_w, final_l, final_h = generate_smart_tiled_shelf(scale, color_hex)
        title = "Smart Tiled Shelf"

    # Count Bill of Materials (BOM)
    type_counter = defaultdict(int)
    for b in blocks_data: type_counter[b['type']] += 1
    total_blocks = sum(type_counter.values())

    # Build Plotly Figure
    fig = go.Figure()
    edges_x, edges_y, edges_z = [], [], []

    for b in blocks_data:
        x0, y0, z0 = b['x'], b['y'], b['z']
        dx, dy, dz = b['dx'], b['dy'], b['dz']
        x = [x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0]
        y = [y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy]
        z = [z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz]
        i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]; j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]; k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
        
        fig.add_trace(go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=b['color'], opacity=1.0, flatshading=True))
        
        for start, end in [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)]:
            edges_x.extend([x[start], x[end], None]); edges_y.extend([y[start], y[end], None]); edges_z.extend([z[start], z[end], None])

    fig.add_trace(go.Scatter3d(x=edges_x, y=edges_y, z=edges_z, mode='lines', line=dict(color=EDGE_COLOR, width=2), hoverinfo='none', showlegend=False))

    fig.update_layout(
        title=f"{title} | Setup: {final_w}W x {final_l}D x {final_h}H (cm)",
        scene=dict(
            aspectmode='data',
            xaxis=dict(showbackground=False, visible=True, title='Width (cm)'),
            yaxis=dict(showbackground=False, visible=True, title='Depth (cm)'),
            zaxis=dict(showbackground=False, visible=True, title='Height (cm)')
        ),
        margin=dict(l=0, r=0, t=40, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False
    )

    total_weight = total_blocks * 15.0 # สมมติบล็อกละ 15 กรัม
    color_recipe = calculate_color_mix(color_hex, total_weight)
    eco_impact = round(total_weight / 1000, 2) # กิโลกรัม

    result = {
        "status": "success",
        "dimensions": {"width": final_w, "length": final_l, "height": final_h},
        "bom": dict(type_counter),
        "total_blocks": total_blocks,
        "eco_impact_kg": eco_impact,
        "color_mix": color_recipe,
        "plotly_json": json.loads(fig.to_json()),
        "metadata": {
            "title": title,
            "item_type": item_type,
            "color_hex": color_hex,
            "created_at": datetime.datetime.now().isoformat(),
            "parameters": {
                "w": w, "l": l, "h": h, 
                "scale": scale, 
                "has_walls": has_walls
            }
        }
    }

    # 💾 บันทึก JSON ลงไฟล์
    if save_to_file:
        try:
            # สร้างโฟลเดอร์ models ถ้ายังไม่มี
            models_dir = "models"
            if not os.path.exists(models_dir):
                os.makedirs(models_dir)
            
            # สร้างชื่อไฟล์จาก timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_item_type = item_type.replace(" ", "_").replace("/", "_")
            filename = f"{models_dir}/{safe_item_type}_{timestamp}.json"
            
            # บันทึก JSON ลงไฟล์
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Model saved to: {filename}")
            result["saved_file"] = filename
            
        except Exception as e:
            print(f"❌ Error saving model: {e}")
            result["save_error"] = str(e)

    return result