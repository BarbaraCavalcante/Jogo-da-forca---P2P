# -*- coding: utf-8 -*-
import argparse
import threading
import tkinter as tk
from tkinter import messagebox
import winsound  # Sons no Windows
import sys
from p2p import P2PServer, P2PClient, TCP, UDP
from jogo import Forca

def upper_tcp_udp(s: str) -> str:
    v = s.strip().upper()
    if v not in (TCP, UDP):
        raise argparse.ArgumentTypeError("Protocolo deve ser TCP ou UDP")
    return v

# ---------- Sons ----------
def som_vitoria():
    winsound.Beep(880, 200)
    winsound.Beep(988, 200)
    winsound.Beep(1047, 300)

def som_derrota():
    winsound.Beep(440, 400)
    winsound.Beep(349, 400)

# ---------- Funções para interpretar e montar estado do jogo ----------
def montar_state(jogo: Forca) -> str:
    status = "CONT"
    if jogo.venceu():
        status = "WIN"
    elif jogo.perdeu():
        status = "LOSE"
    return f"STATE|{jogo.estado_palavra().replace(' ', '')}|{','.join(sorted(jogo.erradas))}|{jogo.tentativas}|{jogo.dica}|{status}"

def parse_state(msg: str):
    _, palavra_mask, erradas, tentativas, dica, status = msg.split("|", 5)
    err_set = set([e for e in erradas.split(",") if e])
    return palavra_mask, err_set, int(tentativas), dica, status

# ---------- Tela inicial para selecionar protocolo e dados ----------
def tela_inicial_config():
    temp_root = tk.Tk()
    import socket
    temp_root.title("Configuração do Jogo P2P")

    config = {"modo": "servidor", "ip": "", "porta": 5555, "protocolo": TCP}

    tk.Label(temp_root, text="Modo:").grid(row=0, column=0, sticky="w")
    modo_var = tk.StringVar(value="servidor")
    tk.Radiobutton(temp_root, text="Servidor", variable=modo_var, value="servidor").grid(row=0, column=1)
    tk.Radiobutton(temp_root, text="Cliente", variable=modo_var, value="cliente").grid(row=0, column=2)

    tk.Label(temp_root, text="IP:").grid(row=1, column=0, sticky="w")
    ip_entry = tk.Entry(temp_root)
    # Já preenche com o IP real da máquina para facilitar
    ip_entry.insert(0, socket.gethostbyname(socket.gethostname()))
    ip_entry.grid(row=1, column=1, columnspan=2)

    tk.Label(temp_root, text="Porta:").grid(row=2, column=0, sticky="w")
    porta_entry = tk.Entry(temp_root)
    porta_entry.insert(0, "5555")
    porta_entry.grid(row=2, column=1, columnspan=2)

    tk.Label(temp_root, text="Protocolo:").grid(row=3, column=0, sticky="w")
    protocolo_var = tk.StringVar(value=TCP)
    tk.Radiobutton(temp_root, text="TCP", variable=protocolo_var, value=TCP).grid(row=3, column=1)
    tk.Radiobutton(temp_root, text="UDP", variable=protocolo_var, value=UDP).grid(row=3, column=2)

    def confirmar():
        config["modo"] = modo_var.get()
        config["ip"] = ip_entry.get().strip()
        config["porta"] = int(porta_entry.get())
        config["protocolo"] = protocolo_var.get()
        temp_root.destroy()

    tk.Button(temp_root, text="Iniciar", command=confirmar).grid(row=4, column=0, columnspan=3, pady=10)
    temp_root.mainloop()
    return config

# ---------- Interface Tkinter ----------
class ForcaGUI:
    def __init__(self, root, modo, ip, porta, protocolo):
        self.root = root
        self.root.title("Jogo da Forca P2P")
        self.modo = modo
        self.ip = ip
        self.porta = porta
        self.protocolo = protocolo
        self.jogo = None
        self.conexao = None

        if self.modo == "servidor":
            self.tela_configuracao_servidor()
        else:
            self.tela_jogo()
            threading.Thread(target=self.iniciar_cliente, daemon=True).start()

    def tela_configuracao_servidor(self):
        self.frame_config = tk.Frame(self.root)
        self.frame_config.pack(pady=20)

        tk.Label(self.frame_config, text="Digite a palavra secreta:").pack()
        self.entry_palavra = tk.Entry(self.frame_config, font=("Helvetica", 14))
        self.entry_palavra.pack()

        tk.Label(self.frame_config, text="Digite a dica (opcional):").pack()
        self.entry_dica = tk.Entry(self.frame_config, font=("Helvetica", 14))
        self.entry_dica.pack()

        btn_iniciar = tk.Button(self.frame_config, text="Iniciar Jogo", command=self.iniciar_servidor_gui)
        btn_iniciar.pack(pady=10)

    def iniciar_servidor_gui(self):
        palavra = self.entry_palavra.get().strip()
        dica = self.entry_dica.get().strip()
        if not palavra.isalpha() or len(palavra) < 3:
            messagebox.showerror("Erro", "A palavra deve ter pelo menos 3 letras e apenas caracteres A-Z.")
            return
        self.frame_config.destroy()
        self.tela_jogo()
        threading.Thread(target=self.iniciar_servidor, args=(palavra, dica), daemon=True).start()

    def tela_jogo(self):
        self.lbl_boneco = tk.Label(self.root, font=("Courier", 12), justify="left")
        self.lbl_boneco.pack()

        self.lbl_palavra = tk.Label(self.root, text="", font=("Helvetica", 18))
        self.lbl_palavra.pack()

        self.lbl_dica = tk.Label(self.root, text="", font=("Helvetica", 12, "italic"))
        self.lbl_dica.pack()

        self.lbl_erradas = tk.Label(self.root, text="", font=("Helvetica", 12))
        self.lbl_erradas.pack()

        self.lbl_tentativas = tk.Label(self.root, text="", font=("Helvetica", 12))
        self.lbl_tentativas.pack()

        self.entry_letra = tk.Entry(self.root, width=5, font=("Helvetica", 14))
        self.entry_letra.pack()
        self.entry_letra.bind("<Return>", self.enviar_jogada)

        self.btn_enviar = tk.Button(self.root, text="Enviar", command=self.enviar_jogada)
        self.btn_enviar.pack()

        self.txt_chat = tk.Text(self.root, height=8, state="disabled")
        self.txt_chat.pack()

        self.entry_chat = tk.Entry(self.root, width=30)
        self.entry_chat.pack()
        self.entry_chat.bind("<Return>", self.enviar_chat)

        self.btn_sair = tk.Button(self.root, text="Sair", command=self.sair)
        self.btn_sair.pack()

    def atualizar_tela(self):
        if self.jogo:
            self.lbl_boneco.config(text=self.jogo.boneco())
            self.lbl_palavra.config(text=self.jogo.estado_palavra())
            self.lbl_dica.config(text=f"Dica: {self.jogo.dica or '-'}")
            self.lbl_erradas.config(text=f"Erradas: {', '.join(sorted(self.jogo.erradas)) or '-'}")
            self.lbl_tentativas.config(text=f"Tentativas restantes: {self.jogo.tentativas}")

    def mostrar_trofeu(self):
        trofeu = r"""
       ___________
      '._==_==_=_.'        
      .-\:      /-.
     | (|:.     |) |
      '-|:.     |-'
        \::.    /
         '::. .'
           ) (
         _.' '._
        `"""""""`
        """
        win_win = tk.Toplevel(self.root)
        win_win.title("🏆 Parabéns!")
        tk.Label(win_win, text="VOCÊ VENCEU!", font=("Helvetica", 18, "bold")).pack(pady=10)
        tk.Label(win_win, text=trofeu, font=("Courier", 10), justify="center").pack(padx=20, pady=10)
        tk.Button(win_win, text="Fechar", command=win_win.destroy).pack(pady=10)

    def mostrar_derrota(self):
        boneco_triste = r"""
   _____
  /     \
 |  x x  |
 |   ^   |
 |  '-'  |
  \_____/
        """
        lose_win = tk.Toplevel(self.root)
        lose_win.title("😢 Fim de Jogo")
        tk.Label(lose_win, text="VOCÊ PERDEU!", font=("Helvetica", 18, "bold"), fg="red").pack(pady=10)
        tk.Label(lose_win, text=boneco_triste, font=("Courier", 10), justify="center").pack(padx=20, pady=10)
        tk.Button(lose_win, text="Fechar", command=lose_win.destroy).pack(pady=10)

    def enviar_jogada(self, event=None):
        letra = self.entry_letra.get().strip()
        self.entry_letra.delete(0, tk.END)
        if not letra:
            return
        if self.modo == "servidor":
            self.jogo.tentar(letra)
            self.atualizar_tela()
            self.conexao.send(montar_state(self.jogo))
            if self.jogo.terminou():
                if self.jogo.venceu():
                    som_vitoria()
                    self.mostrar_trofeu()
                else:
                    som_derrota()
                    self.mostrar_derrota()
                messagebox.showinfo("Fim de jogo", f"Palavra: {self.jogo.palavra}")
        else:
            self.conexao.send(f"JOGADA|{letra}")

    def enviar_chat(self, event=None):
        msg = self.entry_chat.get().strip()
        self.entry_chat.delete(0, tk.END)
        if not msg:
            return
        self.conexao.send(f"CHAT|{msg}")
        remetente = "Servidor" if self.modo == "servidor" else "Cliente"
        self.add_chat(remetente, msg)

    def add_chat(self, remetente, texto):
        self.txt_chat.config(state="normal")
        self.txt_chat.insert(tk.END, f"[{remetente}]: {texto}\n")
        self.txt_chat.config(state="disabled")
        self.txt_chat.see(tk.END)

    def sair(self):
        try:
            self.conexao.send("QUIT|")
        except:
            pass
        self.root.destroy()

    def iniciar_servidor(self, palavra, dica):
        srv = P2PServer(self.ip, self.porta, self.protocolo, timeout=120.0)
        self.conexao = srv
        srv.start()

        if self.protocolo == UDP:
            while True:
                msg = srv.recv()
                if msg and msg.startswith("HELLO|"):
                    break

        self.jogo = Forca(palavra, dica)
        srv.send(f"INICIAR_JOGO|{self.jogo.palavra}|{self.jogo.dica}")
        self.atualizar_tela()

        while True:
            msg = srv.recv()
            if not msg:
                break
            if msg.startswith("JOGADA|"):
                _, letra = msg.split("|", 1)
                self.jogo.tentar(letra)
                self.atualizar_tela()
                srv.send(montar_state(self.jogo))
                if self.jogo.terminou():
                    if self.jogo.venceu():
                        som_vitoria()
                        self.mostrar_trofeu()
                    else:
                        som_derrota()
                        self.mostrar_derrota()
                    messagebox.showinfo("Fim de jogo", f"Palavra: {self.jogo.palavra}")
                    break
            elif msg.startswith("CHAT|"):
                _, texto = msg.split("|", 1)
                self.add_chat("Cliente", texto)
            elif msg.startswith("QUIT|"):
                break

    def iniciar_cliente(self):
        cli = P2PClient(self.ip, self.porta, self.protocolo, timeout=120.0)
        self.conexao = cli
        cli.connect()

        if self.protocolo == UDP:
            cli.send("HELLO|")

        while True:
            msg = cli.recv()
            if not msg:
                return
            if msg.startswith("INICIAR_JOGO|"):
                _, palavra, dica = msg.split("|", 2)
                self.jogo = Forca(palavra, dica)
                self.atualizar_tela()
                break

        while True:
            msg = cli.recv()
            if not msg:
                break
            if msg.startswith("STATE|"):
                mask, erradas, tent, dica, status = parse_state(msg)
                self.jogo.erradas = erradas
                self.jogo.certas = set([c for c in set(self.jogo.palavra) if c in mask])
                self.jogo.dica = dica
                self.atualizar_tela()
                if status in ("WIN", "LOSE"):
                    if status == "WIN":
                        som_vitoria()
                        self.mostrar_trofeu()
                    else:
                        som_derrota()
                        self.mostrar_derrota()
                    messagebox.showinfo("Fim de jogo", f"Palavra: {self.jogo.palavra}")
                    break
            elif msg.startswith("CHAT|"):
                _, texto = msg.split("|", 1)
                self.add_chat("Servidor", texto)
            elif msg.startswith("QUIT|"):
                break

# ---------- Parser e execução ----------
def build_parser():
    p = argparse.ArgumentParser()
    p.add_argument("--modo", required=True, choices=["servidor", "cliente"])
    p.add_argument("--ip", required=False)
    p.add_argument("--porta", required=True, type=int)
    p.add_argument("--protocolo", required=True, type=upper_tcp_udp)
    return p

def main():
    import socket
    args = build_parser().parse_args()

    if args.modo == "servidor" and not args.ip:
        ip_detectado = socket.gethostbyname(socket.gethostname())
        ip_user = input(f"Digite o IP do servidor [{ip_detectado}]: ").strip()
        args.ip = ip_user if ip_user else ip_detectado

    if args.modo == "cliente" and not args.ip:
        ip_user = input("Digite o IP do servidor: ").strip()
        args.ip = ip_user

    root = tk.Tk()
    ForcaGUI(root, args.modo, args.ip, args.porta, args.protocolo)
    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        cfg = tela_inicial_config()
        root = tk.Tk()
        ForcaGUI(root, cfg["modo"], cfg["ip"], cfg["porta"], cfg["protocolo"])
        root.mainloop()
