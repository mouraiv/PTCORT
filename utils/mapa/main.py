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

    def criar_mapa(self, lat, lon, callback):
        # Criar o mapa HTML
        mapa = folium.Map(location=[lat, lon], zoom_start=15)
        folium.Marker(
            [lat, lon],
            popup="Arraste para mover",
            draggable=True
        ).add_to(mapa)
        
        script = f"""
        <script>
        const linhaSelecionada = [];

        function criarRadio() {{
            const radio = document.createElement("input");
            radio.type = "radio";
            radio.name = "grupo-radio";
            radio.dataset.checked = "false";

            radio.addEventListener("click", function () {{
            if (this.dataset.checked === "true") {{
                this.checked = false;
                this.dataset.checked = "false";
                linhaSelecionada.length = 0;
            }} else {{
                document.querySelectorAll("input[name='grupo-radio']").forEach(r => {{
                r.dataset.checked = "false";
                }});

                this.dataset.checked = "true";
                coletarLinhaSelecionada(this);
            }}
            }});

            return radio;
        }}

        function coletarLinhaSelecionada(radio) {{
            const tr = radio.closest("tr");
            const tds = tr.querySelectorAll("td");

            linhaSelecionada.length = 0;
            for (let i = 1; i < tds.length; i++) {{
            linhaSelecionada.push(tds[i].textContent.trim());
            }}

            console.log("Linha selecionada:", linhaSelecionada);
        }}

        fetch("http://localhost:5000/enderecos")
            .then(res => res.json())
            .then(dados => {{
            const tabela = document.getElementById("tabela-enderecos");
            const tipos = ["cep_correios", "opem_street", "dbc_logradouro"];

            tipos.forEach(tipo => {{
                const dadosTipo = dados.find(item => item[tipo])?.[tipo] || [];
                const headerRow = tabela.querySelector(`.header-${{tipo}}`);

                dadosTipo.forEach(linha => {{
                const tr = document.createElement("tr");

                const tdRadio = document.createElement("td");
                const radio = criarRadio();
                tdRadio.appendChild(radio);
                tr.appendChild(tdRadio);

                linha.forEach(valor => {{
                    const td = document.createElement("td");
                    td.textContent = valor;
                    tr.appendChild(td);
                }});

                headerRow.insertAdjacentElement("afterend", tr);
                }});
            }});
            }})
            .catch((erro) => {{
            console.error("Erro ao buscar dados:", erro);
            }});
            document.addEventListener('DOMContentLoaded', function() {{
                var map = {{mapa.get_name()}};
                Object.values(map._layers).forEach(layer => {{
                    if (layer instanceof L.Marker) {{
                        layer.on('dragend', function(e) {{
                            var latlng = e.target.getLatLng();
                            if (window.updateCoords) {{
                                window.updateCoords(latlng.lat, latlng.lng);
                            }}
                        }});
                    }}
                }});
            }});
        </script>
        """
        mapa.get_root().html.add_child(folium.Element(script))
        #mapa.save(self.map_file_path)
        
        # Enviar comando para a thread do CEF
        def _abrir_janela():
            if self.browser:
                self.browser.CloseBrowser()
                self.browser = None
            
            bindings = cef.JavascriptBindings()
            bindings.SetFunction("updateCoords", callback)
            
            window_info = cef.WindowInfo()
            window_info.SetAsPopup(0, "Mapa Interativo")

            import os

            # Suponha que o arquivo esteja em um subdiretório do diretório atual
            base_dir = os.path.dirname(os.path.abspath(__file__))  # Caminho do script atual
            map_file_path = os.path.join(base_dir, "html", self.map_file_path)

            # Converte o caminho para o formato de URL de arquivo
            map_file_url = f"file:///{map_file_path.replace(os.sep, '/')}"

            print(map_file_url)
            
            self.browser = cef.CreateBrowserSync(
                window_info=window_info,
                url=map_file_url,
                settings={
                    "file_access_from_file_urls_allowed": True,
                    "universal_access_from_file_urls_allowed": True,
                }
            )
            self.browser.SetJavascriptBindings(bindings)
        
        self.command_queue.put(_abrir_janela)

    def fechar(self):
        self.running = False
        self.thread.join()