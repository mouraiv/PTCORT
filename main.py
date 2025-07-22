import threading
import tkinter as tk
from tkinter import messagebox

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
            command=self.mostrar_coordenadas,
            padx=10,
            pady=5
        ).grid(row=3, column=0, columnspan=2, pady=10)
    
    def atualizar_coordenadas(self, lat, lng):
        self.lat.set(lat)
        self.lon.set(lng)
        print(f"Coordenadas atualizadas: {lat}, {lng}")

    def tratar_selecao_linha(self, dados_linha):
        print(f"Linha selecionada: {dados_linha}")
    
    def abrir_mapa(self):
        try:
            lat = float(self.lat.get() if self.lat.get() else -22.9068)
            lon = float(self.lon.get() if self.lon.get() else -43.1729)
            self.chamada_api(lat, lon)
            self.mapa.criar_mapa(lat, lon, callback_info=self.tratar_selecao_linha)
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira coordenadas válidas!")
    
    def mostrar_coordenadas(self):
        messagebox.showinfo(
            "Coordenadas Atuais",
            f"Latitude: {self.lat.get()}\nLongitude: {self.lon.get()}"
        )
    
    def on_closing(self):
        self.mapa.fechar()
        self.destroy()

if __name__ == "__main__":
    app = Application()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()