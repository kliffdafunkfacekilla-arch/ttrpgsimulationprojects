import sys
import os
import random
import math
from PyQt6.QtGui import QImage, QPainter, QPen, QBrush, QColor, QFont, QPolygonF
from PyQt6.QtCore import QPointF, QRectF, Qt

def generate_city_map(city_name, seed_str, dest_path):
    # Hash seed string to get an integer seed
    val = 0
    for char in seed_str:
        val = (val * 31 + ord(char)) & 0xFFFFFFFF
    random.seed(val)
    
    img = QImage(800, 800, QImage.Format.Format_ARGB32)
    img.fill(QColor("#EFE5CF")) # Parchment background color
    
    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # 1. Draw River (75% chance)
    has_river = random.random() < 0.75
    river_points = []
    if has_river:
        river_color = QColor("#89b6c4")
        river_pen = QPen(river_color, 45, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(river_pen)
        
        start_y = random.randint(150, 650)
        end_y = random.randint(150, 650)
        for x in range(-50, 851, 100):
            t = (x + 50) / 900.0
            y = (1 - t) * start_y + t * end_y + math.sin(t * math.pi * 3.5) * 70
            river_points.append(QPointF(x, y))
            
        for i in range(len(river_points)-1):
            painter.drawLine(river_points[i], river_points[i+1])
            
    # 2. Generate City Wall (polygon around center (400, 400))
    cx, cy = 400, 400
    radius = random.randint(220, 270)
    num_vertices = random.randint(7, 10)
    wall_points = []
    for i in range(num_vertices):
        angle = (2 * math.pi / num_vertices) * i
        r = radius + random.randint(-35, 35)
        wx = cx + r * math.cos(angle)
        wy = cy + r * math.sin(angle)
        wall_points.append(QPointF(wx, wy))
        
    wall_poly = QPolygonF(wall_points)
    
    # Draw green park areas (gardens/orchards)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor("#D9E3C4"))) # Moss green
    for _ in range(15):
        gx = random.randint(200, 600)
        gy = random.randint(200, 600)
        gr = random.randint(35, 80)
        painter.drawEllipse(QPointF(gx, gy), gr, gr)
        
    # Helper to check if a point is close to the river
    def close_to_river(x, y, threshold=30):
        if not has_river:
            return False
        for pt in river_points:
            if math.hypot(x - pt.x(), y - pt.y()) < threshold:
                return True
        return False

    # 3. Draw Building Blocks & Rooftops
    roof_colors = [
        QColor("#A34C3D"), QColor("#B76652"), QColor("#7F7F7F"), 
        QColor("#8C9675"), QColor("#D38E5F"), QColor("#5A5A66")
    ]
    
    # Draw thousands of houses inside the city walls
    for _ in range(950):
        ang = random.random() * 2 * math.pi
        r = random.random() * (radius - 20)
        hx = cx + r * math.cos(ang)
        hy = cy + r * math.sin(ang)
        
        # Don't place directly on the river path
        if close_to_river(hx, hy, 35):
            continue
            
        painter.save()
        painter.translate(hx, hy)
        painter.rotate(random.randint(0, 360))
        
        w = random.randint(12, 22)
        h = random.randint(8, 14)
        
        # Shadow
        shadow_color = QColor("#2A2A2A")
        shadow_color.setAlpha(60)
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(2, 2, w, h)
        
        # Roof
        painter.setBrush(QBrush(random.choice(roof_colors)))
        painter.setPen(QPen(QColor("#2D2D2D"), 1.0))
        painter.drawRect(0, 0, w, h)
        
        # Ridge line on roof
        ridge_color = QColor("#FFFFFF")
        ridge_color.setAlpha(100)
        painter.setPen(QPen(ridge_color, 0.8))
        painter.drawLine(0, int(h/2), w, int(h/2))
        
        painter.restore()
        
    # 4. Draw Main Roads (connecting center to walls)
    painter.setPen(QPen(QColor("#C2B290"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for pt in wall_points[::2]: # Connect every second wall vertex (gates) to center
        painter.drawLine(QPointF(cx, cy), pt)
        
    # 5. Draw City Walls
    wall_pen = QPen(QColor("#4A4A4A"), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin)
    painter.setPen(wall_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPolygon(wall_poly)
    
    # Towers at wall vertices
    for pt in wall_points:
        # Outer tower shadow
        shadow_color = QColor("#2A2A2A")
        shadow_color.setAlpha(60)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(pt + QPointF(2, 2), 11, 11)
        
        # Tower wall
        painter.setPen(QPen(QColor("#3A3A3A"), 2))
        painter.setBrush(QBrush(QColor("#6A6A6A")))
        painter.drawEllipse(pt, 10, 10)
        
        # Tower roof cone
        painter.setBrush(QBrush(QColor("#A34C3D")))
        painter.drawEllipse(pt, 5, 5)
        
    # 6. Draw Central Castle Keep
    painter.setPen(QPen(QColor("#1F1F1F"), 2.2))
    painter.setBrush(QBrush(QColor("#5A5A6A")))
    # Castle compound shadow
    painter.drawRect(cx - 32, cy - 32, 64, 64)
    # Outer towers
    for tx, ty in [(cx-30, cy-30), (cx+30, cy-30), (cx-30, cy+30), (cx+30, cy+30)]:
        painter.setBrush(QBrush(QColor("#7A7A8A")))
        painter.drawEllipse(QPointF(tx, ty), 13, 13)
        painter.setBrush(QBrush(QColor("#A34C3D")))
        painter.drawEllipse(QPointF(tx, ty), 8, 8)
        
    # 7. Compass Rose & Scale Bar details
    # Scale Bar
    painter.setPen(QPen(QColor("#4A3B2C"), 2))
    painter.drawLine(50, 750, 150, 750)
    painter.drawLine(50, 745, 50, 755)
    painter.drawLine(100, 745, 100, 755)
    painter.drawLine(150, 745, 150, 755)
    
    painter.setPen(QColor("#4A3B2C"))
    painter.setFont(QFont("Georgia", 8))
    painter.drawText(QRectF(40, 725, 120, 20), Qt.AlignmentFlag.AlignCenter, "500 meters")
    
    # 8. Title Frame
    border_pen = QPen(QColor("#4A3B2C"), 3)
    painter.setPen(border_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRect(15, 15, 770, 770)
    painter.drawRect(20, 20, 760, 760)
    
    # Title box
    painter.setBrush(QBrush(QColor("#EFE5CF")))
    painter.setPen(QPen(QColor("#4A3B2C"), 2))
    painter.drawRect(230, 30, 340, 50)
    
    painter.setPen(QColor("#3A2A1A"))
    font = QFont("Georgia", 15, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(QRectF(230, 30, 340, 50), Qt.AlignmentFlag.AlignCenter, city_name.upper())
    
    painter.end()
    img.save(dest_path)
    print(f"[+] City Map generated successfully for '{city_name}' at: {dest_path}")
