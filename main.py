import os
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image


WINDOW_WIDTH = 520
WINDOW_HEIGHT = 640
LOGO_RELATIVE_PATH = os.path.join("assets", "dupe_logo.png")


class ImagePipeline:
    """Processing layer isolated from Tkinter UI for easier scaling and testing."""

    def __init__(self, cwebp_path=None, logo_path=None):
        self.cwebp_path = cwebp_path or shutil.which("cwebp")
        self.logo_path = logo_path or os.path.join(os.path.dirname(__file__), LOGO_RELATIVE_PATH)

    def set_cwebp_path(self, cwebp_path):
        self.cwebp_path = cwebp_path

    def _load_logo(self):
        if not os.path.exists(self.logo_path):
            return None, self.logo_path
        try:
            return Image.open(self.logo_path).convert("RGBA"), None
        except Exception:
            return None, self.logo_path

    def _apply_logo(self, img):
        logo, err = self._load_logo()
        if logo is None:
            return None, err

        base = img.convert("RGBA")
        target_w = max(24, int(base.width * 0.15))
        scale = target_w / logo.width
        new_size = (max(1, int(logo.width * scale)), max(1, int(logo.height * scale)))
        logo_resized = logo.resize(new_size, Image.LANCZOS)

        margin = max(10, int(base.width * 0.02))
        pos = (base.width - logo_resized.width - margin, base.height - logo_resized.height - margin)
        base.paste(logo_resized, pos, logo_resized)
        return base, None

    def _save_webp_pillow(self, src_path, out_path):
        img = Image.open(src_path)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        img.save(out_path, "WEBP", lossless=True, quality=100, method=6)

    def _save_webp_cwebp(self, src_path, out_path):
        subprocess.run([self.cwebp_path, "-lossless", "-m", "6", src_path, "-o", out_path], check=True)

    def _make_temp_png_with_logo(self, src_path):
        img = Image.open(src_path)
        with_logo, err = self._apply_logo(img)
        if with_logo is None:
            return None, err

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        with_logo.save(tmp.name, "PNG")
        tmp.close()
        return tmp.name, None

    def process_file(self, src_path, out_path, apply_watermark=False):
        """
        Returns warning string (or None).
        Raises on hard processing failures.
        """
        warning = None
        temp_source = None

        try:
            source = src_path
            if apply_watermark:
                temp_source, warning = self._make_temp_png_with_logo(src_path)
                if temp_source:
                    source = temp_source

            if self.cwebp_path:
                self._save_webp_cwebp(source, out_path)
            else:
                self._save_webp_pillow(source, out_path)
        finally:
            if temp_source and os.path.exists(temp_source):
                try:
                    os.remove(temp_source)
                except Exception:
                    pass

        return warning


class WebPConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PNG → WebP (lossless)")

        self.input_path = None
        self.webp_path = None
        self.apply_watermark_var = tk.BooleanVar(value=False)
        self.pipeline = ImagePipeline()

        self._build_ui()

    # ---------- UI setup ----------
    def _build_ui(self):
        frm = tk.Frame(self.root, padx=10, pady=10)
        frm.pack(fill=tk.BOTH, expand=True)

        self.lbl_selected = tk.Label(frm, text="Ningún archivo seleccionado", anchor="w")
        self.lbl_selected.pack(fill=tk.X)

        tk.Button(frm, text="Seleccionar PNG", command=self.select_png).pack(fill=tk.X, pady=(8, 0))
        tk.Button(frm, text="Convertir a WebP (lossless)", command=self.convert_to_webp).pack(fill=tk.X, pady=(6, 0))

        tk.Label(frm, text="--- o ---", pady=6).pack()

        tk.Button(frm, text="Seleccionar WebP", command=self.select_webp).pack(fill=tk.X)
        tk.Button(frm, text="Comprimir WebP (lossless)", command=self.compress_webp).pack(fill=tk.X, pady=(6, 0))

        tk.Label(frm, text="", pady=6).pack()
        cwebp_text = f"cwebp: {self.pipeline.cwebp_path}" if self.pipeline.cwebp_path else "cwebp: no detectado"
        self.cwebp_label = tk.Label(frm, text=cwebp_text, anchor="w")
        self.cwebp_label.pack(fill=tk.X)
        tk.Button(frm, text="Seleccionar cwebp.exe...", command=self.select_cwebp).pack(fill=tk.X, pady=(2, 0))

        tk.Checkbutton(
            frm,
            text="Imprimir marca de agua (assets\\dupe_logo.png)",
            variable=self.apply_watermark_var,
        ).pack(fill=tk.X, pady=(4, 0))

        tk.Label(frm, text="Procesamiento por lotes", pady=6).pack()
        tk.Button(frm, text="Procesar carpeta: PNG → WebP (batch)", command=self.batch_convert_folder).pack(fill=tk.X)
        tk.Button(frm, text="Comprimir carpeta: WebP (batch)", command=self.batch_compress_webp_folder).pack(fill=tk.X, pady=(6, 0))

        self.status = tk.Label(frm, text="Listo", anchor="w")
        self.status.pack(fill=tk.X, pady=(8, 0))

    # ---------- UI helpers ----------
    def _set_status(self, msg):
        self.status.config(text=msg)
        self.root.update_idletasks()

    def _set_status_async(self, msg):
        self.root.after(0, lambda: self._set_status(msg))

    def _show_info_async(self, title, msg):
        self.root.after(0, lambda: messagebox.showinfo(title, msg))

    def _show_warning(self, msg):
        messagebox.showwarning("Logo", msg)

    # ---------- Input selection ----------
    def select_png(self):
        path = filedialog.askopenfilename(title="Seleccionar PNG", filetypes=[("PNG files", "*.png"), ("All files", "*")])
        if path:
            self.input_path = path
            self.lbl_selected.config(text=path)
            self._set_status("PNG seleccionado")

    def select_webp(self):
        path = filedialog.askopenfilename(title="Seleccionar WebP", filetypes=[("WebP files", "*.webp"), ("All files", "*")])
        if path:
            self.webp_path = path
            self.lbl_selected.config(text=path)
            self._set_status("WebP seleccionado")

    def select_cwebp(self):
        path = filedialog.askopenfilename(title="Seleccionar cwebp.exe", filetypes=[("Executables", "*.exe;*"), ("All files", "*")])
        if path:
            self.pipeline.set_cwebp_path(path)
            self.cwebp_label.config(text=f"cwebp: {path}")
            self._set_status("cwebp seleccionado")

    # ---------- Single file operations ----------
    def _save_target_path(self, source_path, suffix=""):
        default_name = os.path.splitext(os.path.basename(source_path))[0] + suffix + ".webp"
        return filedialog.asksaveasfilename(
            defaultextension=".webp",
            initialfile=default_name,
            filetypes=[("WebP", "*.webp")],
        )

    def _process_single(self, source_path, output_path, status_text, success_title, success_msg):
        try:
            self._set_status(status_text)
            warning = self.pipeline.process_file(
                source_path,
                output_path,
                apply_watermark=self.apply_watermark_var.get(),
            )
            if warning:
                self._show_warning(f"No se aplicó el logo: {warning}")

            self._set_status(f"Guardado: {output_path}")
            messagebox.showinfo(success_title, f"{success_msg}\n{output_path}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error cwebp", f"cwebp falló:\n{e}")
            self._set_status("Error")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo procesar: {e}")
            self._set_status("Error")

    def convert_to_webp(self):
        if not self.input_path:
            messagebox.showwarning("Advertencia", "Selecciona primero un archivo PNG.")
            return

        out_path = self._save_target_path(self.input_path)
        if not out_path:
            return

        self._process_single(
            self.input_path,
            out_path,
            status_text="Convirtiendo…",
            success_title="Éxito",
            success_msg="Convertido a WebP (lossless)",
        )

    def compress_webp(self):
        src = self.webp_path
        if not src:
            if self.input_path and messagebox.askyesno("Confirmar", "No seleccionaste un WebP. ¿Convertir el PNG seleccionado a WebP y re-comprimirlo?"):
                src = self.input_path
            else:
                messagebox.showwarning("Advertencia", "Selecciona primero un archivo WebP o PNG.")
                return

        out_path = self._save_target_path(src, suffix="_compressed")
        if not out_path:
            return

        self._process_single(
            src,
            out_path,
            status_text="Comprimiendo (lossless)…",
            success_title="Éxito",
            success_msg="WebP comprimido (lossless)",
        )

    # ---------- Batch operations ----------
    def _ask_batch_folders(self, source_title):
        source_folder = filedialog.askdirectory(title=source_title)
        if not source_folder:
            return None, None

        output_folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if not output_folder:
            return None, None

        return source_folder, output_folder

    def _run_batch(self, source_folder, output_folder, extension, out_name_builder, status_prefix, done_label):
        self._set_status_async(status_prefix)
        files = [
            os.path.join(source_folder, f)
            for f in os.listdir(source_folder)
            if f.lower().endswith(extension)
        ]

        ok = 0
        fail = 0
        for src_path in files:
            out_path = os.path.join(output_folder, out_name_builder(src_path))
            try:
                self.pipeline.process_file(
                    src_path,
                    out_path,
                    apply_watermark=self.apply_watermark_var.get(),
                )
                ok += 1
            except Exception:
                fail += 1

        self._set_status_async(f"Hecho: {ok} {done_label}, {fail} fallidos")
        self._show_info_async("Batch terminado", f"{done_label.capitalize()}: {ok}\nFallidos: {fail}")

    def batch_convert_folder(self):
        source_folder, output_folder = self._ask_batch_folders("Seleccionar carpeta con PNGs")
        if not source_folder:
            return

        thread = threading.Thread(
            target=self._run_batch,
            args=(
                source_folder,
                output_folder,
                ".png",
                lambda p: os.path.splitext(os.path.basename(p))[0] + ".webp",
                "Procesando carpeta (PNG→WebP)...",
                "convertidos",
            ),
            daemon=True,
        )
        thread.start()

    def batch_compress_webp_folder(self):
        source_folder, output_folder = self._ask_batch_folders("Seleccionar carpeta con WebPs")
        if not source_folder:
            return

        thread = threading.Thread(
            target=self._run_batch,
            args=(
                source_folder,
                output_folder,
                ".webp",
                lambda p: os.path.splitext(os.path.basename(p))[0] + "_compressed.webp",
                "Comprimiendo carpeta (WebP)...",
                "comprimidos",
            ),
            daemon=True,
        )
        thread.start()


def main():
    root = tk.Tk()
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    root.resizable(False, False)
    WebPConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
