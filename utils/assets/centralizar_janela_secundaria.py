def centralizar_janela_secundaria(janela_secundaria, janela_principal, largura, altura):
    janela_secundaria.update_idletasks()
    x_pai = janela_principal.winfo_rootx()
    y_pai = janela_principal.winfo_rooty()
    largura_pai = janela_principal.winfo_width()
    altura_pai = janela_principal.winfo_height()

    x = x_pai + (largura_pai // 2) - (largura // 2)
    y = y_pai + (altura_pai // 2) - (altura // 2)

    janela_secundaria.geometry(f"{largura}x{altura}+{x}+{y}")
    
