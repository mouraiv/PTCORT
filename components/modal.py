import tkinter as tk

from utils.assets.centralizar_janela_secundaria import centralizar_janela_secundaria

class ModalWindow(tk.Toplevel):
    def __init__(self, master, largura, altura):
        super().__init__(master)
        
        self.geometry(f"{largura}x{altura}")
        centralizar_janela_secundaria(self, master, largura=largura, altura=altura)
        
        self.transient(master)
        self.grab_set()

        self.overrideredirect(True)
        
        self.lift()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))

        # Conteúdo da modal
        tk.Label(self, text="Janela Modal").pack(pady=10)
        self.close_button = tk.Button(self, text="Fechar", command=self.destroy)
        self.close_button.pack(pady=10)

