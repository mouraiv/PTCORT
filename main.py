import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import requests

from utils.mapa.main import MapaCEF
from utils.mapa.server.index import server_api

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aplicação com Mapa Interativo")
        self.geometry("400x300")
        self.CHAVE = "d40efb650d1963b7546a6df9ebde4943"
        
        self.lat = tk.DoubleVar(value=-22.9068)
        self.lon = tk.DoubleVar(value=-43.1729)
        self.mapa = MapaCEF()
        
        self.criar_interface()

        # Inicia o servidor Flask em uma thread separada
        threading.Thread(target=self.iniciar_servidor, daemon=True).start()

    def chamada_api(self, lat=None, lon=None):
        try:
            response = requests.post("http://localhost:5000/enderecos", json={"lat": lat, "lon": lon})
            response.raise_for_status()
            print("Resposta da API:", response.json())

        except requests.exceptions.RequestException as e:
            print("Erro ao chamar a API:", e)

    def iniciar_servidor(self):
        server_api.run(host="0.0.0.0", port=5000)
        
    def criar_interface(self):
        frame = tk.Frame(self)
        frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Latitude:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(frame, textvariable=self.lat).grid(row=0, column=1, pady=5, padx=5)
        
        tk.Label(frame, text="Longitude:").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(frame, textvariable=self.lon).grid(row=1, column=1, pady=5, padx=5)
        
        tk.Button(
            frame, 
            text="Abrir Mapa", 
            command=self.abrir_mapa,
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10
        ).grid(row=2, column=0, columnspan=2, pady=20)
        
        tk.Button(
            frame,
            text="Mostrar Coordenadas",
            command=self.atualizar_coordenadas,
            padx=10,
            pady=5
        ).grid(row=3, column=0, columnspan=2, pady=10)

    def abrir_modal_loading(self, texto):
        # Cria a janela de loading
        self.janela_loading = tk.Toplevel(self)
        self.janela_loading.title("Carregando")
        self.janela_loading.geometry("200x80")
        self.janela_loading.resizable(False, False)
        
        # Remove a barra de título
        self.janela_loading.overrideredirect(True)
        
        # Centraliza a janela
        self.janela_loading.update_idletasks()
        width = self.janela_loading.winfo_width()
        height = self.janela_loading.winfo_height()
        x = (self.janela_loading.winfo_screenwidth() // 2) - (width // 2)
        y = (self.janela_loading.winfo_screenheight() // 2) - (height // 2)
        self.janela_loading.geometry(f'+{x}+{y}')
        
        # Impede interação com a janela principal
        self.janela_loading.grab_set()
        
        # Adiciona o texto
        label = ttk.Label(self.janela_loading, text=texto, font=('Arial', 7, "bold italic"))
        label.pack(pady=10)
        
        # Adiciona um spinner
        style = ttk.Style()
        style.configure("Custom.Horizontal.TProgressbar", thickness=2)

        self.progress = ttk.Progressbar(self.janela_loading, mode='indeterminate',
                                        style="Custom.Horizontal.TProgressbar", length=200)
        self.progress.pack(pady=0, padx=20)
        self.progress.start(10)

    def fechar_modal_loading(self):
        if hasattr(self, 'janela_loading'):
            self.janela_loading.destroy()
            del self.janela_loading

    def loading_thread_mapa(self, flag):        
        # Executa na thread principal
        if not flag:
            # Abre o modal (executando na thread principal)
            if not hasattr(self, 'janela_loading') or not self.janela_loading.winfo_exists():
                self.abrir_modal_loading("CARREGANDO MAPA...")
        else:
            # Fecha o modal (executando na thread principal)
            self._fechar_modal_loading()

    def _fechar_modal_loading(self):
        """Fecha o modal de loading de forma segura"""
        if hasattr(self, 'janela_loading') and self.janela_loading.winfo_exists():
            try:
                self.janela_loading.grab_release()
                self.janela_loading.destroy()
            except:
                pass
        # Limpa a referência
        if hasattr(self, 'janela_loading'):
            del self.janela_loading

    def tratar_selecao_linha(self, dados_linha):
        print(f"Linha selecionada: {dados_linha}")

    def abrir_mapa(self):
        try:
            lat = float(self.lat.get() if self.lat.get() else -22.9068)
            lon = float(self.lon.get() if self.lon.get() else -43.1729)
            
            # Inicia o loading
            self.loading_thread_mapa(False)
            
            # Executa o mapa em uma thread separada
            threading.Thread(
                target=self.executar_criacao_mapa,
                args=(lat, lon),
                daemon=True
            ).start()
            
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira coordenadas válidas!")
            self.loading_thread_mapa(True)  # Fecha o loading se houver erro

    def executar_criacao_mapa(self, lat, lon):
        try:
            # Faz a chamada API
            self.chamada_api(lat, lon)
            
            # Cria o mapa (isso deve ser executado na thread principal)
            self.after(0, lambda: self.mapa.criar_mapa(
                lat, 
                lon, 
                callback_info=self.tratar_selecao_linha,
                callback_loading=self.loading_thread_mapa
            ))
            
        except Exception as e:
            print(f"Erro ao criar mapa: {e}")
            self.after(0, lambda: self.loading_thread_mapa(True))  # Fecha o loading em caso de erro

    def atualizar_coordenadas(self):
        try:
            lat = float(self.lat.get() if self.lat.get() else -22.9068)
            lng = float(self.lon.get() if self.lon.get() else -43.1729)
            print(f"Coordenadas atualizadas: {lat}, {lng}")

            # Inicia o loading
            self.loading_thread_mapa(False)
            
            # Executa o mapa em uma thread separada
            threading.Thread(
                target=self.executar_atualização_mapa,
                args=(lat, lng),
                daemon=True
            ).start()

        except ValueError as e:
            print(f"Erro nas coordenadas: {e}")
        except Exception as e:
            print(f"Erro inesperado: {e}")

    def executar_atualização_mapa(self, lat, lng):
        try:
            # 1. Faz a chamada API (POST)
            self.chamada_api(lat, lng)

        except Exception as e:
            print(f"Erro ao atualizar o mapa: {e}")
            self.after(0, lambda: self.loading_thread_mapa(True))  # Fecha o loading em caso de erro

        finally:
            self.after(0, lambda: self.loading_thread_mapa(True))
        
    def on_closing(self):
        self.mapa.fechar()
        self.destroy()

if __name__ == "__main__":
    app = Application()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()