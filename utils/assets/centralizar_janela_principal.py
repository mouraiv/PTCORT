# utils/centralizar_janela.py
def centralizar_janela_principal(janela, largura, altura):
    janela.update_idletasks()  # Atualiza informações da janela

    # Tamanho da tela
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()

    # Calcula posição central
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)

    janela.geometry(f"{largura}x{altura}+{x}+{y}")