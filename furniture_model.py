import plotly.graph_objects as go
import numpy as np
from collections import defaultdict
import json
import os

# =========================================================
# 🎨 ตั้งค่าสีและฟังก์ชันส่วนกลาง
# =========================================================
BASE_COLOR = '#F8E6B7'
EDGE_COLOR = '#222222'

def get_btype(dx, dy, dz):
    """ฟังก์ชันจัดระเบียบชื่อบล็อกมาตรฐาน"""
    dims = sorted([int(dx), int(dy), int(dz)])
    return f"brick_{dims[0]}x{dims[1]}x{dims[2]}"

# =========================================================
# 🪑 1. โต๊ะ / ชั้นวางของอเนกประสงค์ (Table)
# =========================================================
def generate_table(w=32, l=20, h=16):
    blocks_used = []
    real_w = max(8, int(w))
    real_l = max(8, int(l))
    real_h = max(4, int(h))

    real_w += real_w % 2
    real_l += real_l % 2
    real_h += real_h % 2

    thickness = 2
    bottom_z = max(2, int(real_h / 4))
    bottom_z -= bottom_z % 2
    top_z = real_h - thickness

    if real_h <= 8:
        num_shelves = 1
        z_levels = [top_z]
    else:
        num_shelves = max(2, int(real_h / 16) + 1)
        if num_shelves == 2:
            z_levels = [bottom_z, top_z]
        else:
            raw_levels = np.linspace(bottom_z, top_z, num_shelves)
            z_levels = [int(round(z / 2.0)) * 2 for z in raw_levels]

    x_legs = [0]
    num_x_spans = max(1, int(real_w / 32))
    step_x = (real_w - 2) / num_x_spans

    for i in range(1, num_x_spans):
        pos = int(round(i * step_x / 2.0)) * 2
        x_legs.append(pos)
    x_legs.append(real_w - 2)
    x_legs = sorted(list(set(x_legs)))

    y_legs = [0, real_l - 2]
    leg_positions = [(x, y) for x in x_legs for y in y_legs]

    def pack_legs(start_z, target_h):
        for cx, cy in leg_positions:
            current_z = start_z
            rem_h = target_h
            while rem_h > 0:
                bh = int(min(8, rem_h))
                if bh % 2 != 0: bh += 1
                if bh > rem_h: bh = int(rem_h)

                blocks_used.append({
                    'type': get_btype(2, 2, bh), 'color': BASE_COLOR,
                    'x': cx, 'y': cy, 'z': current_z,
                    'dx': 2, 'dy': 2, 'dz': bh
                })
                current_z += bh
                rem_h -= bh

    pack_legs(0, z_levels[0])
    for i in range(len(z_levels) - 1):
        pack_legs(z_levels[i] + thickness, z_levels[i+1] - (z_levels[i] + thickness))

    def pack_shelf(z_level):
        for cx, cy in leg_positions:
            blocks_used.append({
                'type': get_btype(2, 2, thickness), 'color': BASE_COLOR,
                'x': cx, 'y': cy, 'z': z_level, 'dx': 2, 'dy': 2, 'dz': thickness
            })

        for y in range(2, real_l - 2, 8):
            dy = min(8, real_l - 2 - y)
            if dy > 0:
                blocks_used.append({'type': get_btype(2, dy, thickness), 'color': BASE_COLOR, 'x': 0, 'y': y, 'z': z_level, 'dx': 2, 'dy': dy, 'dz': thickness})
                blocks_used.append({'type': get_btype(2, dy, thickness), 'color': BASE_COLOR, 'x': real_w - 2, 'y': y, 'z': z_level, 'dx': 2, 'dy': dy, 'dz': thickness})

        for x in range(2, real_w - 2, 8):
            dx = min(8, real_w - 2 - x)
            if dx > 0:
                blocks_used.append({'type': get_btype(dx, 2, thickness), 'color': BASE_COLOR, 'x': x, 'y': 0, 'z': z_level, 'dx': dx, 'dy': 2, 'dz': thickness})
                blocks_used.append({'type': get_btype(dx, 2, thickness), 'color': BASE_COLOR, 'x': x, 'y': real_l - 2, 'z': z_level, 'dx': dx, 'dy': 2, 'dz': thickness})

                for y in range(2, real_l - 2, 8):
                    dy = min(8, real_l - 2 - y)
                    if dy > 0:
                        blocks_used.append({'type': get_btype(dx, dy, thickness), 'color': BASE_COLOR, 'x': x, 'y': y, 'z': z_level, 'dx': dx, 'dy': dy, 'dz': thickness})

    for zl in z_levels:
        pack_shelf(zl)

    return blocks_used, real_w, real_l, real_h

# =========================================================
# ชั้นวางรองเท้า (Shoe Rack)
# =========================================================
def generate_shoe_rack(w, l, h, has_walls=False):
    blocks_used = []
    real_w = max(16, int(w)); real_w += real_w % 2
    real_l = max(16, int(l)); real_l += real_l % 2
    real_h = max(16, int(h)); real_h += real_h % 2
    thickness = 2; bottom_z = 8; top_z = real_h - thickness

    num_shelves = max(2, int((real_h - bottom_z) / 18) + 1)
    raw_levels = np.linspace(bottom_z, top_z, num_shelves)
    z_levels = [int(round(z / 2.0)) * 2 for z in raw_levels]

    leg_size = 4
    if has_walls:
        x_legs = [0, real_w - leg_size]
        y_legs = [0, real_l - leg_size]
    else:
        x_legs = [2, real_w - leg_size - 2]
        y_legs = [2, real_l - leg_size - 2]

    if real_w >= 100:
        x_legs.insert(1, (real_w // 2) - ((real_w // 2) % 2))

    def pack_block(start_x, end_x, start_y, end_y, start_z, target_h):
        if target_h <= 0 or start_x >= end_x or start_y >= end_y: return
        for z in range(0, target_h, 8):
            dz = min(8, target_h - z)
            if dz % 2 != 0: dz += 1
            if dz > target_h - z: dz = int(target_h - z)
            for x in range(start_x, end_x, 8):
                dx = min(8, end_x - x)
                for y in range(start_y, end_y, 8):
                    dy = min(8, end_y - y)
                    blocks_used.append({'type': get_btype(dx, dy, dz), 'color': BASE_COLOR, 'x': x, 'y': y, 'z': start_z + z, 'dx': dx, 'dy': dy, 'dz': dz})

    for cx in x_legs:
        for cy in y_legs:
            pack_block(cx, cx + leg_size, cy, cy + leg_size, 0, z_levels[0])
            for i in range(len(z_levels) - 1):
                start_z = z_levels[i] + thickness
                target_h = z_levels[i+1] - start_z
                pack_block(cx, cx + leg_size, cy, cy + leg_size, start_z, target_h)

    if has_walls:
        pack_block(0, thickness, 0, real_l, z_levels[0], real_h - z_levels[0])
        pack_block(real_w - thickness, real_w, 0, real_l, z_levels[0], real_h - z_levels[0])
        pack_block(thickness, real_w - thickness, real_l - thickness, real_l, z_levels[0], real_h - z_levels[0])
        for zl in z_levels:
            pack_block(thickness, real_w - thickness, 0, real_l - thickness, zl, thickness)
        pack_block(0, real_w, 0, real_l, real_h, thickness)
        final_h = real_h + thickness
    else:
        for zl in z_levels:
            pack_block(0, real_w, 0, real_l, zl, thickness)
        final_h = real_h

    return blocks_used, real_w, real_l, final_h

# =========================================================
# 🔌 3. กล่องจัดระเบียบสายไฟ (Cable Box)
# =========================================================
def generate_cable_box(w, l, h):
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
                    blocks_used.append({'type': get_btype(dx, dy, dz), 'color': BASE_COLOR, 'x': x, 'y': y, 'z': start_z + z, 'dx': dx, 'dy': dy, 'dz': dz})

    pack_block(0, real_w, 0, real_l, 0, thick)
    wall_h = real_h - (thick * 2)
    pack_block(0, real_w, 0, thick, thick, wall_h)
    pack_block(0, real_w, real_l - thick, real_l, thick, wall_h)

    mid_y = real_l // 2
    mid_y -= mid_y % 2
    slit_w = 4
    slit_start = mid_y - (slit_w // 2)
    slit_end = mid_y + (slit_w // 2)

    pack_block(0, thick, thick, slit_start, thick, wall_h)
    pack_block(0, thick, slit_end, real_l - thick, thick, wall_h)
    pack_block(real_w - thick, real_w, thick, slit_start, thick, wall_h)
    pack_block(real_w - thick, real_w, slit_end, real_l - thick, thick, wall_h)

    gap_size = 2
    lid_end_y = real_l - thick - gap_size
    pack_block(0, real_w, 0, lid_end_y, real_h - thick, thick)
    pack_block(0, thick, lid_end_y, real_l - thick, real_h - thick, thick)
    pack_block(real_w - thick, real_w, lid_end_y, real_l - thick, real_h - thick, thick)

    return blocks_used, real_w, real_l, real_h

# =========================================================
# 📱 4. แท่นวางโทรศัพท์/แท็บเล็ต (Device Stand)
# =========================================================
def generate_device_stand(w, l, h):
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
                    blocks_used.append({'type': get_btype(dx, dy, dz), 'color': BASE_COLOR, 'x': x, 'y': y, 'z': start_z + z, 'dx': dx, 'dy': dy, 'dz': dz})

    side_width = (real_w - 4) // 2
    side_width -= side_width % 2
    if side_width < 2: side_width = 2
    hole_start = side_width
    hole_end = real_w - side_width
    gap_y = 4

    pack_block(0, hole_start, 0, gap_y, 0, thick)
    pack_block(hole_end, real_w, 0, gap_y, 0, thick)
    pack_block(0, real_w, gap_y, real_l, 0, thick)

    pack_block(0, hole_start, 0, 2, thick, 2)
    pack_block(hole_end, real_w, 0, 2, thick, 2)

    steps = (real_l - gap_y) // 2
    if steps < 1: steps = 1
    available_h = real_h - thick
    step_h = available_h // steps
    step_h -= step_h % 2
    if step_h <= 0: step_h = 2

    current_z = thick
    for i in range(steps):
        y_start = gap_y + (i * 2)
        y_end = real_l
        h_step = step_h
        if i == steps - 1:
            h_step = real_h - current_z
            h_step -= h_step % 2
        if h_step > 0 and y_start < y_end:
            pack_block(0, real_w, y_start, y_end, current_z, h_step)
            current_z += h_step

    return blocks_used, real_w, real_l, real_h

# =========================================================
# ✏️ 5. ที่จัดระเบียบเครื่องเขียน (Stationery Organizer)
# =========================================================
def generate_stationery_organizer(w, l, h):
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
                    blocks_used.append({'type': get_btype(dx, dy, dz), 'color': BASE_COLOR, 'x': x, 'y': y, 'z': start_z + z, 'dx': dx, 'dy': dy, 'dz': dz})

    pack_block(0, real_w, 0, real_l, 0, thick)

    div_y = (real_l // 2) - ((real_l // 2) % 2)
    div_x = (real_w // 2) - ((real_w // 2) % 2)

    back_h = real_h - thick
    front_h = (real_h // 2) - ((real_h // 2) % 2)
    if front_h < 4: front_h = 4

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
# 🎨 ฟังก์ชัน Render 3D อเนกประสงค์
# =========================================================
def render_3d_model(blocks_used, title, width, length, height, color_hex="#F8E6B7"):
    fig = go.Figure()

    def add_mesh_box(x0, y0, z0, dx, dy, dz, color):
        x = [x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0]
        y = [y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy]
        z = [z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz]
        i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
        j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
        k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
        fig.add_trace(go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=1.0, flatshading=True))

        edges_x, edges_y, edges_z = [], [], []
        for start, end in [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)]:
            edges_x.extend([x[start], x[end], None])
            edges_y.extend([y[start], y[end], None])
            edges_z.extend([z[start], z[end], None])
        fig.add_trace(go.Scatter3d(x=edges_x, y=edges_y, z=edges_z, mode='lines', line=dict(color=EDGE_COLOR, width=2), hoverinfo='none', showlegend=False))

    type_counter = defaultdict(int)
    for b in blocks_used:
        add_mesh_box(b['x'], b['y'], b['z'], b['dx'], b['dy'], b['dz'], color_hex)
        type_counter[b['type']] += 1

    fig.update_layout(
        title=f"{title} | Size: {width}W x {length}D x {height}H (cm)",
        scene=dict(
            aspectmode='data',
            xaxis=dict(showbackground=False, visible=True, title='Width (X)'),
            yaxis=dict(showbackground=False, visible=True, title='Depth (Y)'),
            zaxis=dict(showbackground=False, visible=True, title='Height (Z)')
        ),
        paper_bgcolor='white', plot_bgcolor='white', showlegend=False
    )

    total_pieces = 0
    bom = []
    for btype, count in sorted(type_counter.items(), reverse=True):
        bom.append({"type": btype, "count": count})
        total_pieces += count

    return fig, bom, total_pieces

# =========================================================
# 🎮 ตัวควบคุมหลัก (Master Controller)
# =========================================================
def build_furniture(item_type, **kwargs):
    item_type = item_type.lower()

    if item_type == 'table':
        w = kwargs.get('w', 32); l = kwargs.get('l', 20); h = kwargs.get('h', 16)
        blocks_data, w, l, h = generate_table(w, l, h)
        title = "Smart Table"

    elif item_type == 'shoe_rack':
        w = kwargs.get('w', 80); l = kwargs.get('l', 32); h = kwargs.get('h', 96)
        has_walls = kwargs.get('has_walls', False)
        blocks_data, w, l, h = generate_shoe_rack(w, l, h, has_walls)
        wall_text = "Cabinet (with Walls)" if has_walls else "Open Rack"
        title = f"{wall_text} Shoe Rack"

    elif item_type == 'cable_box':
        w = kwargs.get('w', 32); l = kwargs.get('l', 14); h = kwargs.get('h', 14)
        blocks_data, w, l, h = generate_cable_box(w, l, h)
        title = "Cable Organizer Box"

    elif item_type == 'device_stand':
        w = kwargs.get('w', 10); l = kwargs.get('l', 12); h = kwargs.get('h', 14)
        blocks_data, w, l, h = generate_device_stand(w, l, h)
        title = "Phone/Tablet Stand"

    elif item_type == 'stationery':
        w = kwargs.get('w', 20); l = kwargs.get('l', 16); h = kwargs.get('h', 14)
        blocks_data, w, l, h = generate_stationery_organizer(w, l, h)
        title = "Stationery Organizer"

    elif item_type in ['shelf', 'shelves', 'ชั้น', 'ชั้นวาง', 'ชั้นวางหนังสือ', 'bookshelf']:
        w = kwargs.get('w', 80); l = kwargs.get('l', 32); h = kwargs.get('h', 96)
        has_walls = kwargs.get('has_walls', False)
        blocks_data, w, l, h = generate_shoe_rack(w, l, h, has_walls)  
        title = "Storage Shelf"

    elif item_type in ['chair', 'เก้าอี้']:
        w = kwargs.get('w', 40); l = kwargs.get('l', 40); h = kwargs.get('h', 80)
        blocks_data, w, l, h = generate_table(w, l, h)  
        title = "Chair"

    elif item_type in ['cabinet', 'ตู้', 'locker']:
        w = kwargs.get('w', 80); l = kwargs.get('l', 40); h = kwargs.get('h', 120)
        has_walls = kwargs.get('has_walls', True)
        blocks_data, w, l, h = generate_shoe_rack(w, l, h, has_walls)
        title = "Storage Cabinet"

    elif item_type in ['desk', 'โต๊ะทำงาน', 'workspace']:
        w = kwargs.get('w', 120); l = kwargs.get('l', 60); h = kwargs.get('h', 80)
        blocks_data, w, l, h = generate_table(w, l, h)
        title = "Desk"

    else:
        return None, None, None, None

    color_hex = kwargs.get('color', BASE_COLOR)
    fig, bom, total_pieces = render_3d_model(blocks_data, title, w, l, h, color_hex)
    
    return fig, bom, total_pieces, (w, l, h)

# =========================================================
# 🌐 API Function for Web Integration
# =========================================================
def generate_model_from_requirements(requirements):
    try:
        product_type = requirements.get('product_type', 'table')
        width = requirements.get('width', 80)
        length = requirements.get('length', 32)
        height = requirements.get('height', 96)
        color = requirements.get('color', BASE_COLOR)
        special_features = requirements.get('special_features', [])
        has_walls = requirements.get('has_walls', 'walls' in special_features)
        
        # Debug: Print wall detection
        print(f"🔍 Debug: special_features = {special_features}")
        print(f"🔍 Debug: has_walls = {has_walls}")
        
        product_mapping = {
            'ชั้นวางรองเท้า': 'shoe_rack',
            'โต๊ะ': 'table',
            'กล่องจัดระเบียบสาย': 'cable_box',
            'แท่นวางโทรศัพท์': 'device_stand',
            'ที่จัดระเบียบเครื่องเขียน': 'stationery',
            'ชั้น': 'shelf',
            'ชั้นวาง': 'shelf',
            'ชั้นวางหนังสือ': 'shelf',
            'bookshelf': 'shelf',
            'shelves': 'shelf',
            'เก้าอี้': 'chair',
            'ตู้': 'cabinet',
            'locker': 'cabinet',
            'โต๊ะทำงาน': 'desk',
            'desk': 'desk',
            'workspace': 'desk'
        }
        
        if product_type in product_mapping:
            product_type = product_mapping[product_type]
        
        fig, bom, total_pieces, dimensions = build_furniture(
            product_type,
            w=width,
            l=length, 
            h=height,
            color=color,
            has_walls=has_walls # ส่งค่า has_walls ลงไปตอน build
        )
        
        if fig is None:
            return None
            
        plotly_json = fig.to_json()
        
        return {
            "status": "success",
            "plotly_json": json.loads(plotly_json),
            "bom": bom,
            "total_pieces": total_pieces,
            "dimensions": {
                "width": dimensions[0],
                "length": dimensions[1], 
                "height": dimensions[2]
            },
            "product_type": product_type,
            "color": color
        }
        
    except Exception as e:
        print(f"Error generating model: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    fig, bom, pieces, dims = build_furniture('shoe_rack', w=80, l=32, h=96, color="#0000FF")
    if fig:
        print(f"Generated model with {pieces} pieces")
        fig.show()
    else:
        print("Failed to generate model")