import tkinter as tk
import customtkinter as ctk
import threading
import speech_recognition as sr  # Para reconhecimento de fala.
import keyboard  # Para capturar eventos de teclado.
import os  # Para executar comandos no sistema operacional.
from ctypes import cast, POINTER  # Para manipular volume no Windows.
from comtypes import CLSCTX_ALL  # Contexto para interação com APIs COM no Windows.
from comtypes import CoUninitialize, CoInitialize
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # Controle de volume com Pycaw.
import webbrowser
import pygame
from gtts import gTTS
from io import BytesIO
from rapidfuzz import process
from datetime import datetime
import pyautogui
import json
from deep_translator import GoogleTranslator
import requests
import geocoder

def liberar_recursos():
    try:
        CoUninitialize()
    except Exception as e:
        print(f"Erro ao liberar contexto COM: {e}")
    finally:
        janela.destroy()

arquivo_json = "config.json"

# Função para salvar as variáveis no arquivo JSON
def salvar_variaveis_json(variaveis):
    with open(arquivo_json, "w") as f:
        json.dump(variaveis, f)

# Função para carregar as variáveis do arquivo JSON
def carregar_variaveis_json():
    if not os.path.exists(arquivo_json): # Verifica se o arquivo existe
        return {"tecla_selecionada": None, "diretorio_padrao_nota": None, "diretorio_padrao_screenshot": None}

    with open(arquivo_json) as f:
        return json.load(f) # Lê o arquivo e retorna como um dicionário

# Carregar variáveis ou definir padrão
variaveis = carregar_variaveis_json()

# Se as variáveis ainda não foram definidas, usar valores padrão e salvar
if variaveis["tecla_selecionada"] is None:
    variaveis["tecla_selecionada"] = "nenhuma"
    variaveis["diretorio_padrao_nota"] = ""
    variaveis["diretorio_padrao_screenshot"] = ""
    salvar_variaveis_json(variaveis)

tecla_selecionada = variaveis["tecla_selecionada"] # Variável global para armazenar a tecla selecionada
diretorio_padrao_nota = variaveis["diretorio_padrao_nota"] # Variável global para armazenar o diretório para notas
diretorio_padrao_screenshot = variaveis["diretorio_padrao_screenshot"] # Variável global para armazenar o diretório para screenshots
# ============== LEITURA E PROCESSAMENTO DE COMANDOS ==============

#Funções de comandos
def falar(mensagem):
    mp3_fp = BytesIO() # Cria o áudio em memória pra não ter que criar um arquivo
    tts = gTTS(text=mensagem, lang='pt-br')
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)

    pygame.mixer.music.load(mp3_fp, "mp3")
    pygame.mixer.music.play()

def mudar_volume(level):
    try:
        CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None
        )
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        # Definir volume como porcentagem
        volume_level = float(level) / 100  # Converte o nível do volume para escala de 0.0 a 1.0
        volume.SetMasterVolumeLevelScalar(volume_level, None)  # Ajusta o volume
        add_historico(f"Volume ajustado para {level}%")
    except Exception as e:
        add_historico(f"Erro ao ajustar o volume: {e}")
        print(e)
    finally:
        CoUninitialize()

def abrir_navegador():
    webbrowser.open("https://", new=0)
    add_historico("Abrindo navegador...")

def play_pause():
    keyboard.send("play/pause")
    add_historico("Mídia pausada ou retomada.")

def desligar():
    liberar_recursos()
    janela.destroy()

def proxima_musica():
    keyboard.send("next track")
    add_historico("Passando para próxima mídia...")

def musica_anterior():
    keyboard.send("previous track")
    add_historico("Passando para mídia anterior...")

def pular_abertura():
    for _ in range(17):
        keyboard.send("right")
    add_historico("Pulando abertura...")

def ativar_zoom():
    keyboard.send("left windows+plus")
    add_historico("Dando zoom na tela...")

def cancelar_zoom():
    keyboard.send("left windows+esc")
    add_historico("Zoom cancelado.")

def abrir_taskmgr():
    os.system("start taskmgr")
    add_historico("Gerenciador de tarefas aberto.")

def escolher_caminho():
    caminho = tk.filedialog.askdirectory(title="Escolha um local para salvar a nota")
    return caminho

def escutar_nota(palavra_chave="terminar"):
    recognizer = sr.Recognizer()
    conteudo = []
    if palavra_chave == None or palavra_chave == "":
        palavra_chave = "terminar"
    add_historico(f"Diga sua nota. Diga '{palavra_chave}' para encerrar.")
    if botao_falas.get() == "on":
        falar("Pode falar.")

    with sr.Microphone() as source:
        while True:
            try:
                audio = recognizer.listen(source, timeout=10)
                frase = recognizer.recognize_google(audio, language="pt-BR")

                if palavra_chave in frase:
                    conteudo.append(frase)
                    add_historico("Nota finalizada.")
                    janela.update()
                    break

                conteudo.append(frase)
            except sr.UnknownValueError:
                add_historico("Não entendi o que você disse.")
                janela.update()
            except sr.RequestError as e:
                add_historico(f"Erro no serviço de reconhecimento: {e}")
                janela.update()
                break
            except sr.WaitTimeoutError:
                add_historico ("Esperando você falar...")
                janela.update()
            except Exception as e:
                add_historico(f"Erro inesperado: {e}")
                janela.update()
                break

    return "\n".join(conteudo) # Junta o conteúdo em um único texto com quebras de linha


def gerar_nota(conteudo):
    nome_arquivo = datetime.now().strftime("nota_%Y%m%d_%H%M%S.txt")

    global diretorio_padrao_nota
    caminho = diretorio_padrao_nota

    if caminho == "":
        caminho = escolher_caminho()

    if caminho == "":  # Se o caminho não for especificado, salva no diretório atual
        caminho = os.getcwd()

    caminho_completo = os.path.join(caminho, nome_arquivo)

    with open(caminho_completo, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)
    add_historico(f"Nota salva em {caminho_completo}")

def criar_nota():
    dialog = ctk.CTkInputDialog(text="Escreva a palavra que você quer usar como sinal de parada. Cuidado para não escrever errado, você tem que dizer exatamente o que escrever!", title="Escolha uma palavra-chave")
    palavra_chave = dialog.get_input()
    conteudo = escutar_nota(palavra_chave)
    gerar_nota(conteudo)

def tirar_screenshot():
    global diretorio_padrao_screenshot
    caminho = diretorio_padrao_screenshot

    if caminho == "":
        caminho = escolher_caminho()

    if caminho == "":
        caminho = os.getcwd()

    nome_arquivo = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
    caminho_completo = os.path.join(caminho, nome_arquivo)

    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(caminho_completo)
        add_historico(f"Print salva em: {caminho_completo}")
    except Exception as e:
        add_historico(f"Erro ao tirar a captura de tela: {e}")

def abrir_steam():
    caminho = r"C:\Program Files (x86)\Steam\Steam.exe"
    if caminho and os.path.exists(caminho):
        os.system(f'start "" "{caminho}"')
        add_historico("Abrindo Steam...")
    else:
        add_historico(r"Não foi possível encontrar o aplicativo. Verifique o caminho C:\Program Files (x86)\Steam\Steam.exe")

def abrir_epic():
    caminho = r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe"
    if caminho and os.path.exists(caminho):
        os.system(f'start "" "{caminho}"')
        add_historico("Abrindo Epic Games...")
    else:
        add_historico(r"Não foi possível encontrar o aplicativo. Verifique o caminho C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe")

def abrir_notas():
    os.system("start notepad")
    add_historico("Abrindo bloco de notas...")

def previsao_tempo():
    API = "a4664ab448fa346b80b7e985e2abe2a2"
    localizacao = geocoder.ip('me')  # 'me' significa o IP da máquina que está executando o código.
    lat = localizacao.latlng[0]
    lon = localizacao.latlng[1]

    link = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API}"
    requisicao = requests.get(link)
    informacoes = requisicao.json()
    descricao = informacoes["weather"][0]["main"]
    temperatura = informacoes["main"]["temp"] - 273.15
    sensacao = informacoes["main"]["feels_like"] - 273.15
    temp_min = informacoes["main"]["temp_min"] - 273.15
    temp_max = informacoes["main"]["temp_max"] - 273.15

    traducao = GoogleTranslator(source="en", target="pt").translate(descricao)

    add_historico(f"""
        Clima: {traducao}
        Temperatura atual: {temperatura:.2f}°C
        Sensação térmica: {sensacao:.2f}°C
        Temperatura máxima: {temp_max:.2f}°C
        Temperatura mínima: {temp_min:.2f}°C
        """)
    if botao_falas.get() == "on":
        falar(f"Clima: {traducao}, Temperatura atual: {temperatura:.0f}°, Sensação térmica: {sensacao:.0f}°, Temperatura máxima: {temp_max:.0f}°, Temperatura mínima: {temp_min:.0f}°")

def pesquisar_google(comando):
    palavras = comando.split(" ")
    frase_remontada = []
    for index, palavra in enumerate(palavras):
        if "pesquis" in palavra:
            for i in range(len(palavras)):
                if i <= index:
                    continue
                frase_remontada.append(palavras[i])
            frase_remontada = " ".join(frase_remontada)

    webbrowser.open(f"https://www.google.com/search?q={frase_remontada}")
    add_historico(f"Pesquisando {frase_remontada}")

def abrir_explorador():
    os.system("start explorer")
    add_historico("Abrindo explorador de arquivos...")

def tocar_rap():
    webbrowser.open("https://music.youtube.com/playlist?list=PLWAtedjL1oPHcnH1uMc_6VBdxd0ABiScF")
    add_historico("Abrindo playlist...")

def tocar_japa():
    webbrowser.open("https://music.youtube.com/playlist?list=PLWAtedjL1oPGlslaBkldhAN3g0A9p7vFa")
    add_historico("Abrindo playlist...")

# Função principal para interpretar comandos
comandos = {
    "abrir navegador": abrir_navegador,
    "volume": mudar_volume,
    "pausar": play_pause,
    "play": play_pause,
    "próxima música": proxima_musica,
    "música anterior": musica_anterior,
    "desligar eco": desligar,
    "pular abertura": pular_abertura,
    "zoom": ativar_zoom,
    "cancela zoom": cancelar_zoom,
    "abrir gerenciador de tarefas": abrir_taskmgr,
    "crie uma nota": criar_nota,
    "anota isso": criar_nota,
    "tira print": tirar_screenshot,
    "tira screenshot": tirar_screenshot,
    "captura tela": tirar_screenshot,
    "abrir steam": abrir_steam,
    "abrir bloco de notas": abrir_notas,
    "abrir epic games": abrir_epic,
    "previsão do tempo": previsao_tempo,
    "pesquisar": pesquisar_google,
    "abrir explorador de arquivos": abrir_explorador,
    "tocar rap de anime": tocar_rap,
    "tocar música japonesa": tocar_japa
}

def processar_comando(comando):
    melhor_correspondencia = process.extractOne(comando, comandos.keys(), score_cutoff=70)
    if melhor_correspondencia:
        if melhor_correspondencia[0] == "volume":
            try:
                level = int("".join(filter(str.isdigit, comando))) # Extrai número do comando
                mudar_volume(level)
            except ValueError:
                add_historico("Não consegui entender o valor do volume.")
        elif melhor_correspondencia[0] == "zoom":
            if "cancel" in comando:
                cancelar_zoom()
            else:
                ativar_zoom()
        elif "abr" in comando:
            if "navega" not in comando and "steam" not in comando and "gerencia" not in comando and "tarefa" not in comando and "bloc" not in comando and "nota" not in comando and "epic" not in comando and "épic" not in comando and "explora" not in comando and "arquivo" not in comando:
                add_historico("Não entendi o que devo abrir...")
                if botao_falas.get() == "on":
                    falar("Não entendi o que devo abrir....")
            elif melhor_correspondencia[0] == "abrir navegador":
                abrir_navegador()
            elif melhor_correspondencia[0] == "abrir steam":
                abrir_steam()
            elif melhor_correspondencia[0] == "abrir gerenciador de tarefas":
                abrir_taskmgr()
            elif melhor_correspondencia[0] == "abrir epic games":
                abrir_epic()
            elif melhor_correspondencia[0] == "abrir explorador de arquivos":
                abrir_explorador()
            else:
                add_historico("Não entendi o que devo abrir...")
                if botao_falas.get() == "on":
                    falar("Não entendi o que devo abrir....")
        elif melhor_correspondencia[0] == "pesquisar":
            pesquisar_google(comando)
        else:
            comandos[melhor_correspondencia[0]]()
    else:
        add_historico(f"Comando não reconhecido: {comando}")

# Funções para reconhecimento de fala
def escutar_comando():
    recognizer = sr.Recognizer()  # Cria um objeto para reconhecimento de fala
    with sr.Microphone() as source:  # Usa o microfone como fonte de áudio
        try:
            audio = recognizer.listen(source, timeout=5)  # Escuta por até 5 segundos
            comando = recognizer.recognize_google(audio, language="pt-BR")
            return comando.lower()
        except sr.UnknownValueError:
            add_historico("Não entendi o que você disse.")  # Erro quando não consegue interpretar
            if botao_falas.get() == "on":
                falar("Não entendi o que você disse.")
        except sr.RequestError as e:
            add_historico(f"Erro no serviço de reconhecimento: {e}")  # Erro ao acessar o Google API
        except sr.WaitTimeoutError:
            add_historico("Você não falou nada.")
            if botao_falas.get() == "on":
                falar("Você não falou nada.")
        except Exception as e:
            add_historico(f"Erro inesperado: {e}")
    return ""

def escutar_comando_thread():
    global reconhecimento_ativo
    try:
        reconhecimento_ativo = True # Indica que o reconhecimento de fala está ativo

        ouvindo = ctk.CTkLabel(
                janela,
                text="Ouvindo...",
                text_color="lightgreen",
                font=("Arial", 20, "bold"),
            )
        ouvindo.place(x=450, y=410)
        janela.update()

        comando = escutar_comando()

        ouvindo.destroy()
        janela.update()

        if comando:
            add_historico(f"Você falou: {comando}")
            processar_comando(comando)
    finally:
        reconhecimento_ativo = False # Libera a flag após o reconhecimento de fala ser concluído

# Loop principal para esperar o botão
reconhecimento_ativo = False
def esperar_tecla():
    global tecla_selecionada, reconhecimento_ativo
    if tecla_selecionada != "nenhuma" and keyboard.is_pressed(tecla_selecionada):
        if not reconhecimento_ativo:  # Só inicia o reconhecimento se não houver outro ativo
            # Cria uma thread para o reconhecimento de voz
            recognition_thread = threading.Thread(target=escutar_comando_thread, daemon=True)
            recognition_thread.start()

    janela.after(100, esperar_tecla)  # Verifica de novo após 100ms

# ============== LEITURA E PROCESSAMENTO DE COMANDOS ==============


# ============== INTERFACE GRÁFICA ==============
# Configs da janela
ctk.set_appearance_mode("dark")
janela = ctk.CTk()
janela.title("Ekko")
janela.geometry("1000x800")
janela.resizable(False, False)
janela.configure(fg_color="#03312c")


# Título
titulo = ctk.CTkButton(
    janela,
    text="Ekko",
    width=300,
    height=60,
    corner_radius=10,
    border_color="lightgreen",
    font=("Arial", 40, "bold"),
    fg_color="#03312c",
    bg_color="#03312c",
    text_color="lightgreen",
    text_color_disabled="lightgreen",
    border_width=0,
    state="disabled",
    hover=False
)
titulo.pack(pady=20)

linha_titulo = ctk.CTkFrame(janela, fg_color="lightgreen", height=2, width=900)
linha_titulo.pack(pady=(0,30))

# Instruções
texto = ctk.CTkButton(
    janela,
    text="Escolha uma tecla que será usada para ativar o reconhecimento de voz. Essa tecla deve ser clicada sempre que você\nquiser falar com o Ekko, e o reconhecimento é ativado mesmo se a janela estiver minimizada.",
    corner_radius=10,
    border_color="lightgreen",
    font=("Arial", 16),
    fg_color="#000222",
    bg_color="#03312c",
    text_color="lightgreen",
    text_color_disabled="lightgreen",
    border_width=2,
    state="disabled",
    hover=False
)
texto.pack(ipady=2)

def janela_tecla():
    janela_nova = ctk.CTkToplevel(janela)
    janela_nova.geometry("400x100")
    janela_nova.title("Pressione uma tecla")
    janela_nova.grab_set()  # Bloqueia interação com a janela principal

    texto = ctk.CTkLabel(janela_nova, text="Pressione a tecla que deve ser selecionada.", font=("Arial", 16))
    texto.pack(fill="both", expand=True)

    def capturar_tecla(event):
        global tecla_selecionada
        tecla_selecionada = event.name
        variaveis["tecla_selecionada"] = tecla_selecionada
        salvar_variaveis_json(variaveis)
        keyboard.unhook(captura)
        tecla_atual.configure(text=f"Tecla atual: {tecla_selecionada}")
        janela_nova.destroy()

    captura = keyboard.on_press(capturar_tecla, suppress=True)

container_tecla = ctk.CTkFrame(janela, bg_color="#03312c", fg_color="#03312c")
botao_tecla = ctk.CTkButton(
    container_tecla,
    text="Escolha uma tecla",
    command=janela_tecla,
    font=("Arial", 16),
    fg_color="lightgreen",
    bg_color="#03312c",
    border_color="#000222",
    text_color="black",
    border_width=3,
    hover_color="#97C397"
)
botao_tecla.grid(column=0, row=0, padx=30)

tecla_atual = ctk.CTkButton(
    container_tecla,
    text=f"Tecla atual: {tecla_selecionada}",
    corner_radius=10,
    border_color="lightgreen",
    font=("Arial", 16),
    fg_color="#000222",
    bg_color="#03312c",
    text_color="lightgreen",
    text_color_disabled="lightgreen",
    border_width=2,
    state="disabled",
    hover=False
)
tecla_atual.grid(column=1, row=0, padx=30)

container_tecla.pack(pady=(30, 0))

# Funcionalidades
texto2 = ctk.CTkLabel(
    janela,
    text="Funcionalidades do Ekko (teclas e pastas que você escolher ficam salvas mesmo depois de fechar o Ekko)",
    text_color="lightgreen",
    font=("Arial", 18),
    anchor="w"
)
texto2.pack(fill="x", padx=60, pady=(30, 3))

container_botoes = ctk.CTkFrame(
    janela,
    fg_color="#03312c",
    bg_color="#03312c"
)
container_botoes.pack(pady=(0, 10))

def escolher_caminho_screenshot():
    global diretorio_padrao_screenshot
    diretorio_padrao_screenshot = tk.filedialog.askdirectory(title="Escolha um local padrão para salvar screenshots")
    screenshot_atual.configure(text=f"Pasta atual: {diretorio_padrao_screenshot.split("/")[-1]}")
    variaveis["diretorio_padrao_screenshot"] = diretorio_padrao_screenshot
    salvar_variaveis_json(variaveis)

botao_screenshot = ctk.CTkButton(
    container_botoes,
    text="Escolha uma pasta\npadrão para screenshots",
    command=escolher_caminho_screenshot,
    font=("Arial", 16),
    fg_color="lightgreen",
    bg_color="#03312c",
    border_color="#000222",
    text_color="black",
    border_width=3,
    hover_color="#97C397",
    width=200
)
botao_screenshot.grid(column=0, row=0, padx=20)

screenshot_atual = ctk.CTkButton(
    container_botoes,
    text=f"Pasta atual: {diretorio_padrao_screenshot.split("/")[-1]}",
    corner_radius=10,
    border_color="lightgreen",
    font=("Arial", 16),
    fg_color="#000222",
    bg_color="#03312c",
    text_color="lightgreen",
    text_color_disabled="lightgreen",
    border_width=2,
    state="disabled",
    hover=False
)
screenshot_atual.grid(column=0, row=1, padx=20)

def escolher_caminho_nota():
    global diretorio_padrao_nota
    diretorio_padrao_nota = tk.filedialog.askdirectory(title="Escolha um local padrão para salvar notas")
    nota_atual.configure(text=f"Pasta atual: {diretorio_padrao_nota.split("/")[-1]}")
    variaveis["diretorio_padrao_nota"] = diretorio_padrao_nota
    salvar_variaveis_json(variaveis)

botao_nota = ctk.CTkButton(
    container_botoes,
    text="Escolha uma pasta\npadrão para notas",
    command= escolher_caminho_nota,
    font=("Arial", 16),
    fg_color="lightgreen",
    bg_color="#03312c",
    border_color="#000222",
    text_color="black",
    border_width=3,
    hover_color="#97C397",
    width=200
)
botao_nota.grid(column=1, row=0, padx=20, pady=5)

nota_atual = ctk.CTkButton(
    container_botoes,
    text=f"Pasta atual: {diretorio_padrao_nota.split("/")[-1]}",
    corner_radius=10,
    border_color="lightgreen",
    font=("Arial", 16),
    fg_color="#000222",
    bg_color="#03312c",
    text_color="lightgreen",
    text_color_disabled="lightgreen",
    border_width=2,
    state="disabled",
    hover=False
)
nota_atual.grid(column=1, row=1, padx=20, pady=5)

botao_falas_var = ctk.StringVar(value="off")
botao_falas = ctk.CTkSwitch(
    container_botoes,
    text="Falas do Ekko",
    font=("Arial", 16),
    text_color="lightgreen",
    button_color="#000222",
    progress_color="lightgreen",
    variable=botao_falas_var,
    onvalue="on",
    offvalue="off"
)
botao_falas.grid(column=2, row=0, padx=20)

def abrir_lista_comandos():
    janela_lista = ctk.CTkToplevel(janela)
    janela_lista.geometry("700x500")
    janela_lista.title("Lista de comandos")
    janela_lista.resizable(False, False)

    janela_lista.transient(janela)  # Define que a nova janela é filha da principal

    container = ctk.CTkScrollableFrame(janela_lista, height=500)
    container.pack(fill="both")

    def add_comando(msg):
        nova_msg = ctk.CTkLabel(container, font=("Arial", 16), text=msg, anchor="w", justify="left", wraplength=655)
        nova_msg.pack(fill="x", padx=10, pady=5)

    comandos_mensagens = [
    '1. Abrir o navegador: Diga "Abre o navegador" para abrir o navegador padrão do seu computador em uma aba vazia.',
    '2. Alterar o volume: Para ajustar o volume do computador, diga algo como "Volume 30", e Ekko irá configurar o volume para o valor especificado.',
    '3. Pausar ou retomar a mídia: Diga "Pause" ou "Play" para pausar ou retomar a mídia atual. Este comando funciona como o botão de pause/play do teclado.',
    '4. Avançar ou voltar na mídia: Diga "Próxima música" para avançar ou "Música anterior" para retornar à faixa anterior.',
    '5. Desligar o Ekko: Para encerrar o assistente, diga algo como "Desligue Ekko" ou "Ekko desligar". Ele será fechado automaticamente.',
    '6. Pular abertura: Diga "Pular abertura" para avançar exatamente 1 minuto e 25 segundos de algum vídeo.',
    '7. Dar zoom na tela: Diga "Zoom" para ativar a lupa do Windows e ampliar a tela.',
    '8. Cancelar o zoom: Diga "Cancelar zoom" para desativar a lupa e voltar ao tamanho normal.',
    '9. Abrir o Gerenciador de Tarefas: Diga "Abre o gerenciador de tarefas" para abrir o Gerenciador de Tarefas do Windows.',
    '10. Criar uma nota: Diga "Crie uma nota" ou "Anota isso" para salvar uma anotação rapidamente.',
    '11. Tirar um print: Diga "Tira print", "Tira screenshot" ou "Captura tela" para capturar uma imagem da tela atual do computador.',
    '12. Abrir Steam: Diga "Abre a Steam" ou "Steam abrir" para abrir a Steam automaticamente.',
    '13. Abrir Epic Games: Diga "Abre a Epic Games" ou "Epic Games abrir" para abrir a Epic Games automaticamente.',
    '14. Abrir bloco de notas: Diga "Abre o bloco de notas" para abrir o bloco de notas.',
    '15. Previsão do tempo: Diga "Previsão do tempo", e Ekko irá te dizer o clima, sensação térmica, temperatura atual, temperatura máxima e mínima da sua localização.',
    '16. Pesquisar: Diga "Pesquise ..." completando com o que você quiser pesquisar, e Ekko vai abrir uma nova aba no seu navegador pesquisando o que você pediu.',
    '17. Abrir Explorador de Arquivos: Diga "Abre o explorador de arquivos", e Ekko irá abrir o explorador de arquivos do Windows.'
    ]

    for m in range(len(comandos_mensagens)):
        add_comando(comandos_mensagens[m])

botao_lista = ctk.CTkButton(
    container_botoes,
    text="Acessar lista de\ncomandos do Ekko",
    command= abrir_lista_comandos,
    font=("Arial", 16),
    fg_color="lightgreen",
    bg_color="#03312c",
    border_color="#000222",
    text_color="black",
    border_width=3,
    hover_color="#97C397",
    width=200
)
botao_lista.grid(column=3, row=0, padx=20, pady=5)

# Caixa de histórico de mensagens
texto3 = ctk.CTkLabel(
    janela,
    text="Mensagens do Ekko",
    text_color="lightgreen",
    font=("Arial", 18),
    anchor="w"
)
texto3.pack(fill="x", padx=60, pady=(5, 3))

frame_com_borda2 = ctk.CTkFrame(
    janela,
    fg_color="#000222",
    bg_color="#03312c",
    border_color="lightgreen",
    border_width=2,
    corner_radius=10
)
frame_com_borda2.pack(fill="both", padx=50, pady=(0, 20), expand=True)

historico = ctk.CTkScrollableFrame(
    frame_com_borda2,
    bg_color="#000222",
    fg_color="#000222",
    border_width=0,
    scrollbar_button_color="lightgreen",
    scrollbar_button_hover_color="#97C397"
)
historico.pack(fill="both", padx=5, pady=5, expand=True)

def add_historico(msg):
    nova_msg = ctk.CTkLabel(historico, font=("Arial", 16), text=msg, anchor="w", text_color="lightgreen", wraplength=870, justify="left")
    nova_msg.pack(fill="x", padx=5)

janela.protocol("WM_DELETE_WINDOW", liberar_recursos)

pygame.mixer.init()
esperar_tecla()

janela.mainloop()
# ============== INTERFACE GRÁFICA ==============