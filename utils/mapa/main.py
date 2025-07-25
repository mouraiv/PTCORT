import folium
import os
import tempfile
import threading
from cefpython3 import cefpython as cef
import sys
import queue

class MapaCEF:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.map_file_path = "map.html"
        self.browser = None
        self.cef_initialized = False
        self.command_queue = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._cef_thread, daemon=True)
        self.thread.start()

    def _cef_thread(self):
        sys.excepthook = cef.ExceptHook
        cef.Initialize(settings={
            "windowless_rendering_enabled": False,
            "context_menu": {"enabled": False},
        })
        self.cef_initialized = True
        
        while self.running:
            try:
                # Processar comandos da fila
                callback = self.command_queue.get(timeout=0.1)
                if callback:
                    callback()
            except queue.Empty:
                pass
            
            cef.MessageLoopWork()
        
        cef.Shutdown()

    def criar_mapa(self, lat, lon, callback_info=None, callback_loading=None):
        # Criar o mapa HTML
        mapa = folium.Map(location=[lat, lon], zoom_start=15)
        folium.Marker(
            [lat, lon],
            popup="Arraste para mover",
            draggable=True
        ).add_to(mapa)
        
        # Enviar comando para a thread do CEF
        def _abrir_janela():
            if self.browser:
                self.browser.CloseBrowser()
                self.browser = None

            window_info = cef.WindowInfo()
            window_info.SetAsPopup(0, "Mapa Interativo")
            
            # Suponha que o arquivo esteja em um subdiretório do diretório atual
            base_dir = os.path.dirname(os.path.abspath(__file__))  # Caminho do script atual
            map_file_path = os.path.join(base_dir, "html", self.map_file_path)

            # Converte o caminho para o formato de URL de arquivo
            map_file_url = f"file:///{map_file_path.replace(os.sep, '/')}"
            
            self.browser = cef.CreateBrowserSync(
                window_info=window_info,
                url=map_file_url,
                settings={
                    "file_access_from_file_urls_allowed": True,
                    "universal_access_from_file_urls_allowed": True,
                    "web_security_disabled": False,
                }
            )

            bindings = cef.JavascriptBindings()
            bindings.SetFunction("updateInfo", callback_info)
            bindings.SetFunction("loadingMap", callback_loading)
            self.browser.SetJavascriptBindings(bindings)

            # Abre DevTools para depuração
            self.browser.ShowDevTools()
            
        self.command_queue.put(_abrir_janela)

    def fechar(self):
        self.running = False
        self.thread.join()