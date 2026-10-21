"""Piksel Renk Seçici - fotoğraf yükle, bir piksele tıkla, RGB kodunu gör."""
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk

MIN_ZOOM, MAX_ZOOM = 0.05, 40.0


class RenkSecici(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Piksel Renk Seçici")
        self.geometry("1100x750")
        self.minsize(700, 450)

        self.image = None      # orijinal PIL görüntüsü (RGB)
        self.tk_image = None   # ekranda gösterilen kesit
        self.zoom = 1.0
        self.offset_x = 0.0    # görüntünün tuval üzerindeki sol üst konumu
        self.offset_y = 0.0
        self.drag_start = None
        self.selected = None   # (x, y) seçili piksel

        self._build_ui()
        self.bind("<Control-o>", lambda e: self.open_image())
        self.bind("<Control-c>", lambda e: self.copy_value("rgb"))

    # ---------- Arayüz ----------
    def _build_ui(self):
        toolbar = tk.Frame(self, padx=8, pady=6)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(toolbar, text="📂 Fotoğraf Aç (Ctrl+O)", command=self.open_image).pack(side=tk.LEFT)
        tk.Button(toolbar, text="Sığdır", command=self.fit_to_window).pack(side=tk.LEFT, padx=(8, 0))
        tk.Button(toolbar, text="1:1", command=lambda: self.set_zoom(1.0)).pack(side=tk.LEFT, padx=(4, 0))
        self.zoom_label = tk.Label(toolbar, text="Yakınlaştırma: -")
        self.zoom_label.pack(side=tk.LEFT, padx=12)
        tk.Label(toolbar, text="Sol tık: piksel seç  •  Tekerlek: yakınlaştır  •  Sağ tık sürükle: kaydır",
                 fg="gray40").pack(side=tk.RIGHT)

        body = tk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(body, bg="#2b2b2b", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.create_text(20, 20, anchor="nw", fill="#bbbbbb", font=("Segoe UI", 14),
                                text="Başlamak için bir fotoğraf açın.", tags="hint")

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<ButtonPress-3>", self.on_drag_start)
        self.canvas.bind("<B3-Motion>", self.on_drag)
        self.canvas.bind("<ButtonPress-2>", self.on_drag_start)
        self.canvas.bind("<B2-Motion>", self.on_drag)
        self.canvas.bind("<Configure>", lambda e: self.redraw())

        side = tk.Frame(body, width=260, padx=12, pady=12)
        side.pack(side=tk.RIGHT, fill=tk.Y)
        side.pack_propagate(False)

        tk.Label(side, text="Seçilen Renk", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.swatch = tk.Frame(side, height=110, bg="#dddddd", relief=tk.SUNKEN, bd=1)
        self.swatch.pack(fill=tk.X, pady=(6, 10))

        self.rgb_var = tk.StringVar(value="RGB: -")
        self.hex_var = tk.StringVar(value="HEX: -")
        self.pos_var = tk.StringVar(value="Konum: -")
        tk.Label(side, textvariable=self.rgb_var, font=("Consolas", 14, "bold")).pack(anchor="w")
        tk.Label(side, textvariable=self.hex_var, font=("Consolas", 12)).pack(anchor="w", pady=(2, 0))
        tk.Label(side, textvariable=self.pos_var, font=("Consolas", 10), fg="gray30").pack(anchor="w", pady=(2, 8))

        tk.Button(side, text="RGB kopyala", command=lambda: self.copy_value("rgb")).pack(fill=tk.X)
        tk.Button(side, text="HEX kopyala", command=lambda: self.copy_value("hex")).pack(fill=tk.X, pady=(4, 0))

        tk.Frame(side, height=1, bg="gray70").pack(fill=tk.X, pady=14)
        tk.Label(side, text="İmlecin Altındaki", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        hover_row = tk.Frame(side)
        hover_row.pack(fill=tk.X, pady=(4, 0))
        self.hover_swatch = tk.Frame(hover_row, width=28, height=28, bg="#dddddd", relief=tk.SUNKEN, bd=1)
        self.hover_swatch.pack(side=tk.LEFT)
        self.hover_var = tk.StringVar(value="-")
        tk.Label(hover_row, textvariable=self.hover_var, font=("Consolas", 10), justify=tk.LEFT).pack(side=tk.LEFT, padx=8)

        self.status_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.status_var, anchor="w", padx=8, fg="gray30").pack(side=tk.BOTTOM, fill=tk.X)

    # ---------- Dosya ----------
    def open_image(self, path=None):
        path = path or filedialog.askopenfilename(
            title="Fotoğraf seç",
            filetypes=[("Görüntüler", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tif *.tiff *.ico"),
                       ("Tüm dosyalar", "*.*")])
        if not path:
            return
        try:
            img = Image.open(path)
            img.load()
        except Exception as exc:
            messagebox.showerror("Hata", f"Görüntü açılamadı:\n{exc}")
            return
        # Saydam pikseller için RGBA'yı da destekle, gösterimde RGB'ye çevir.
        self.image = img.convert("RGBA") if img.mode in ("RGBA", "LA", "P") else img.convert("RGB")
        self.selected = None
        self.canvas.delete("hint")
        self.status_var.set(f"{path}  —  {img.width} × {img.height} piksel")
        self.fit_to_window()

    # ---------- Yakınlaştırma / kaydırma ----------
    def fit_to_window(self):
        if not self.image:
            return
        cw, ch = max(self.canvas.winfo_width(), 1), max(self.canvas.winfo_height(), 1)
        z = min(cw / self.image.width, ch / self.image.height, 1.0)
        self.zoom = max(MIN_ZOOM, z)
        self.offset_x = (cw - self.image.width * self.zoom) / 2
        self.offset_y = (ch - self.image.height * self.zoom) / 2
        self.redraw()

    def set_zoom(self, new_zoom, anchor=None):
        if not self.image:
            return
        new_zoom = min(MAX_ZOOM, max(MIN_ZOOM, new_zoom))
        if anchor is None:
            anchor = (self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2)
        ax, ay = anchor
        # Yakınlaştırmayı imlecin bulunduğu noktayı sabit tutarak yap.
        ix, iy = (ax - self.offset_x) / self.zoom, (ay - self.offset_y) / self.zoom
        self.zoom = new_zoom
        self.offset_x = ax - ix * self.zoom
        self.offset_y = ay - iy * self.zoom
        self.redraw()

    def on_wheel(self, event):
        factor = 1.25 if event.delta > 0 else 0.8
        self.set_zoom(self.zoom * factor, (event.x, event.y))

    def on_drag_start(self, event):
        self.drag_start = (event.x, event.y, self.offset_x, self.offset_y)

    def on_drag(self, event):
        if not self.drag_start:
            return
        sx, sy, ox, oy = self.drag_start
        self.offset_x = ox + event.x - sx
        self.offset_y = oy + event.y - sy
        self.redraw()

    # ---------- Çizim ----------
    def redraw(self):
        if not self.image:
            return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        z = self.zoom
        # Sadece görünen bölgeyi kırp ve ölçekle (büyük zoom'da hızlı kalması için).
        left = max(0, int((0 - self.offset_x) / z))
        top = max(0, int((0 - self.offset_y) / z))
        right = min(self.image.width, int((cw - self.offset_x) / z) + 2)
        bottom = min(self.image.height, int((ch - self.offset_y) / z) + 2)

        self.canvas.delete("img", "marker")
        if right > left and bottom > top:
            crop = self.image.crop((left, top, right, bottom))
            w = max(1, round((right - left) * z))
            h = max(1, round((bottom - top) * z))
            resample = Image.NEAREST if z >= 1 else Image.LANCZOS
            shown = crop.resize((w, h), resample)
            self.tk_image = ImageTk.PhotoImage(shown)
            self.canvas.create_image(self.offset_x + left * z, self.offset_y + top * z,
                                     anchor="nw", image=self.tk_image, tags="img")
        self.zoom_label.config(text=f"Yakınlaştırma: %{z * 100:.0f}")
        self.draw_marker()

    def draw_marker(self):
        self.canvas.delete("marker")
        if not self.selected:
            return
        x, y = self.selected
        z = self.zoom
        x0, y0 = self.offset_x + x * z, self.offset_y + y * z
        if z >= 6:  # piksel yeterince büyükse etrafına kare çiz
            self.canvas.create_rectangle(x0, y0, x0 + z, y0 + z, outline="black", width=3, tags="marker")
            self.canvas.create_rectangle(x0, y0, x0 + z, y0 + z, outline="white", width=1, tags="marker")
        else:
            cx, cy, r = x0 + z / 2, y0 + z / 2, 7
            for color, width in (("black", 3), ("white", 1)):
                self.canvas.create_line(cx - r - 4, cy, cx - 2, cy, fill=color, width=width, tags="marker")
                self.canvas.create_line(cx + 2, cy, cx + r + 4, cy, fill=color, width=width, tags="marker")
                self.canvas.create_line(cx, cy - r - 4, cx, cy - 2, fill=color, width=width, tags="marker")
                self.canvas.create_line(cx, cy + 2, cx, cy + r + 4, fill=color, width=width, tags="marker")

    # ---------- Piksel okuma ----------
    def canvas_to_pixel(self, cx, cy):
        if not self.image:
            return None
        x = int((cx - self.offset_x) // self.zoom)
        y = int((cy - self.offset_y) // self.zoom)
        if 0 <= x < self.image.width and 0 <= y < self.image.height:
            return x, y
        return None

    def pixel_info(self, x, y):
        px = self.image.getpixel((x, y))
        r, g, b = px[:3]
        a = px[3] if len(px) == 4 else None
        return r, g, b, a

    def on_click(self, event):
        pos = self.canvas_to_pixel(event.x, event.y)
        if not pos:
            return
        self.selected = pos
        r, g, b, a = self.pixel_info(*pos)
        hex_code = f"#{r:02X}{g:02X}{b:02X}"
        self.rgb_var.set(f"RGB: ({r}, {g}, {b})")
        self.hex_var.set(f"HEX: {hex_code}" + (f"   Alfa: {a}" if a is not None else ""))
        self.pos_var.set(f"Konum: x={pos[0]}, y={pos[1]}")
        self.swatch.config(bg=hex_code)
        self.draw_marker()

    def on_motion(self, event):
        pos = self.canvas_to_pixel(event.x, event.y)
        if not pos:
            self.hover_var.set("-")
            self.hover_swatch.config(bg="#dddddd")
            return
        r, g, b, _ = self.pixel_info(*pos)
        self.hover_swatch.config(bg=f"#{r:02X}{g:02X}{b:02X}")
        self.hover_var.set(f"({r}, {g}, {b})\nx={pos[0]}, y={pos[1]}")

    def copy_value(self, kind):
        if not self.selected:
            return
        r, g, b, _ = self.pixel_info(*self.selected)
        text = f"{r}, {g}, {b}" if kind == "rgb" else f"#{r:02X}{g:02X}{b:02X}"
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_var.set(f"Panoya kopyalandı: {text}")


if __name__ == "__main__":
    app = RenkSecici()
    if len(sys.argv) > 1:
        app.after(100, lambda: app.open_image(sys.argv[1]))
    app.mainloop()
