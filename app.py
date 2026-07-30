import asyncio
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import edge_tts
import pypdf

# Voces neuronales en español
VOICES = {
    "México - Dalia (Femenino)": "es-MX-DaliaNeural",
    "México - Jorge (Masculino)": "es-MX-JorgeNeural",
    "España - Elvira (Femenino)": "es-ES-ElviraNeural",
    "España - Álvaro (Masculino)": "es-ES-AlvaroNeural",
}


class PDFToAudiobookApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de PDF a Audiolibro")
        self.root.geometry("540x360")
        self.root.resizable(False, False)

        # --- CORRECCIÓN PARA MODO OSCURO EN MACOS ---
        self.root.configure(bg="#2d2d2d")
        self.style = ttk.Style()
        self.style.theme_use("clam")  # Evita la pantalla negra del tema aqua

        # Configuración de estilos visibles para macOS
        self.style.configure(".", background="#2d2d2d", foreground="#ffffff")
        self.style.configure(
            "TLabel", background="#2d2d2d", foreground="#ffffff"
        )
        self.style.configure(
            "TEntry",
            fieldbackground="#3d3d3d",
            foreground="#ffffff",
            insertcolor="#ffffff",
        )
        self.style.configure(
            "TCombobox",
            fieldbackground="#3d3d3d",
            background="#3d3d3d",
            foreground="#ffffff",
        )
        self.style.configure(
            "TButton",
            background="#007ACC",
            foreground="#ffffff",
            borderwidth=0,
        )
        self.style.map(
            "TButton",
            background=[("active", "#005999"), ("disabled", "#444444")],
        )
        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#3d3d3d",
            background="#007ACC",
        )
        # ---------------------------------------------

        self.pdf_path = tk.StringVar()
        self.selected_voice = tk.StringVar(
            value="México - Dalia (Femenino)"
        )

        self._build_gui()

    def _build_gui(self):
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # 1. Selección de PDF
        ttk.Label(
            frame,
            text="1. Selecciona el archivo PDF:",
            font=("Arial", 11, "bold"),
        ).pack(anchor="w", pady=(0, 5))

        pdf_frame = ttk.Frame(frame)
        pdf_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Entry(
            pdf_frame, textvariable=self.pdf_path, state="readonly"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(pdf_frame, text="Buscar...", command=self.browse_pdf).pack(
            side=tk.RIGHT
        )

        # 2. Selección de Voz
        ttk.Label(
            frame, text="2. Selecciona la voz:", font=("Arial", 11, "bold")
        ).pack(anchor="w", pady=(0, 5))

        voice_combo = ttk.Combobox(
            frame,
            textvariable=self.selected_voice,
            values=list(VOICES.keys()),
            state="readonly",
        )
        voice_combo.pack(fill=tk.X, pady=(0, 20))

        # Botón principal
        self.btn_convert = ttk.Button(
            frame,
            text="Convertir a Audiolibro (MP3)",
            command=self.start_conversion,
        )
        self.btn_convert.pack(fill=tk.X, ipady=6)

        # Estado y Progreso
        self.lbl_status = ttk.Label(
            frame, text="Estado: Listo", font=("Arial", 10, "italic")
        )
        self.lbl_status.pack(anchor="w", pady=(15, 5))

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.pack(fill=tk.X)

    def browse_pdf(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar PDF", filetypes=[("Archivos PDF", "*.pdf")]
        )
        if filename:
            self.pdf_path.set(filename)

    def extract_text(self, pdf_file):
        reader = pypdf.PdfReader(pdf_file)
        text_chunks = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                lines = [
                    line.strip()
                    for line in page_text.splitlines()
                    if line.strip() and not line.strip().isdigit()
                ]
                text_chunks.append(" ".join(lines))
        return "\n\n".join(text_chunks)

    async def generate_audio(self, text, voice_code, output_file):
        communicate = edge_tts.Communicate(text, voice_code)
        await communicate.save(output_file)

    def process_conversion(self):
        pdf_file = self.pdf_path.get()
        if not pdf_file:
            messagebox.showwarning(
                "Atención", "Por favor selecciona un archivo PDF."
            )
            self.reset_ui()
            return

        output_file = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("Archivos MP3", "*.mp3")],
            initialfile=os.path.basename(pdf_file).replace(".pdf", ".mp3"),
        )

        if not output_file:
            self.reset_ui()
            return

        try:
            self.lbl_status.config(text="Estado: Leyendo PDF...")
            text = self.extract_text(pdf_file)

            if not text.strip():
                messagebox.showerror(
                    "Error",
                    "No se pudo extraer texto del PDF (puede estar escaneado).",
                )
                self.reset_ui()
                return

            self.lbl_status.config(
                text="Estado: Generando audio (espera un momento)..."
            )

            voice_code = VOICES[self.selected_voice.get()]
            asyncio.run(self.generate_audio(text, voice_code, output_file))

            messagebox.showinfo(
                "Éxito", f"¡Audiolibro generado!\nGuardado en:\n{output_file}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}")
        finally:
            self.reset_ui()

    def start_conversion(self):
        if not self.pdf_path.get():
            messagebox.showwarning(
                "Atención", "Por favor selecciona un archivo PDF primero."
            )
            return

        self.btn_convert.config(state="disabled")
        self.progress.start(10)
        threading.Thread(target=self.process_conversion, daemon=True).start()

    def reset_ui(self):
        self.progress.stop()
        self.btn_convert.config(state="normal")
        self.lbl_status.config(text="Estado: Listo")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFToAudiobookApp(root)
    root.mainloop()