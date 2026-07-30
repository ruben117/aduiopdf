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

        self.lbl_progress = ttk.Label(
            frame, text="", font=("Arial", 9)
        )
        self.lbl_progress.pack(anchor="e", pady=(4, 0))

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
                joined = " ".join(lines)
                if joined:
                    text_chunks.append(joined)
        return text_chunks

    async def generate_audio(self, chunks, voice_code, output_file, on_progress):
        total = len(chunks)
        with open(output_file, "wb") as out:
            for i, chunk_text in enumerate(chunks, start=1):
                communicate = edge_tts.Communicate(chunk_text, voice_code)
                async for tts_chunk in communicate.stream():
                    if tts_chunk["type"] == "audio":
                        out.write(tts_chunk["data"])
                on_progress(i, total)

    def _set_progress(self, current, total):
        self.progress.config(value=current, maximum=total)
        self.lbl_progress.config(text=f"Página {current} de {total}")

    def process_conversion(self, pdf_file, output_file):
        try:
            self.root.after(
                0, self.lbl_status.config, {"text": "Estado: Leyendo PDF..."}
            )
            chunks = self.extract_text(pdf_file)

            if not chunks:
                self.root.after(
                    0,
                    messagebox.showerror,
                    "Error",
                    "No se pudo extraer texto del PDF (puede estar escaneado).",
                )
                return

            self.root.after(
                0,
                self.lbl_status.config,
                {"text": "Estado: Generando audio..."},
            )
            def switch_to_determinate():
                self.progress.stop()
                self.progress.config(
                    mode="determinate", value=0, maximum=len(chunks)
                )

            self.root.after(0, switch_to_determinate)

            def on_progress(current, total):
                self.root.after(0, self._set_progress, current, total)

            voice_code = VOICES[self.selected_voice.get()]
            asyncio.run(
                self.generate_audio(chunks, voice_code, output_file, on_progress)
            )

            self.root.after(
                0,
                messagebox.showinfo,
                "Éxito",
                f"¡Audiolibro generado!\nGuardado en:\n{output_file}",
            )
        except Exception as e:
            self.root.after(
                0, messagebox.showerror, "Error", f"Ocurrió un error:\n{e}"
            )
        finally:
            self.root.after(0, self.reset_ui)

    def start_conversion(self):
        pdf_file = self.pdf_path.get()
        if not pdf_file:
            messagebox.showwarning(
                "Atención", "Por favor selecciona un archivo PDF primero."
            )
            return

        base_name = os.path.splitext(os.path.basename(pdf_file))[0]
        output_file = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("Archivos MP3", "*.mp3")],
            initialfile=f"{base_name}.mp3",
        )
        if not output_file:
            return

        self.btn_convert.config(state="disabled")
        self.lbl_progress.config(text="")
        self.progress.config(mode="indeterminate")
        self.progress.start(10)
        threading.Thread(
            target=self.process_conversion,
            args=(pdf_file, output_file),
            daemon=True,
        ).start()

    def reset_ui(self):
        self.progress.stop()
        self.progress.config(mode="indeterminate", value=0)
        self.btn_convert.config(state="normal")
        self.lbl_status.config(text="Estado: Listo")
        self.lbl_progress.config(text="")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFToAudiobookApp(root)
    root.mainloop()