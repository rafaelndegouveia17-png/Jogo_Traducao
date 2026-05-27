"""
🌍 LinguaVox — Jogo de Pronúncia e Tradução 🎙️
================================================
Fale palavras no idioma escolhido e veja sua pontuação subir!
Desenvolvido com ❤️ para aprender idiomas de forma divertida.
"""

import os
import sys
import time
import random
import json
import datetime
import tempfile

# ── Dependências externas ─────────────────────────────────────────────────────
try:
    import sounddevice as sd
    import numpy as np
    import scipy.io.wavfile as wav
    import speech_recognition as sr
    from deep_translator import GoogleTranslator
except ImportError as e:
    print(f"\n❌ Biblioteca faltando: {e}")
    print("   Execute: pip install sounddevice numpy scipy SpeechRecognition deep-translator")
    sys.exit(1)


def aplicar_patch_flac_windows() -> None:
    """Evita o WinError 50 do SpeechRecognition no Windows ao criar o subprocess do FLAC."""
    if os.name != "nt":
        return

    try:
        import subprocess
        import speech_recognition.audio as audio_mod

        def safe_get_flac_data(self, convert_rate=None, convert_width=None):
            if self.sample_width > 3 and convert_width is None:
                convert_width = 3

            wav_data = self.get_wav_data(convert_rate, convert_width)
            flac_converter = audio_mod.get_flac_converter()
            kwargs = {"stdin": subprocess.PIPE, "stdout": subprocess.PIPE}
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(
                [flac_converter, "--stdout", "--totally-silent", "--best", "-"],
                **kwargs,
            )
            flac_data, _ = process.communicate(wav_data)
            return flac_data

        audio_mod.AudioData.get_flac_data = safe_get_flac_data
    except Exception:
        pass


aplicar_patch_flac_windows()

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURAÇÕES GLOBAIS
# ══════════════════════════════════════════════════════════════════════════════

DURACAO_GRAVACAO  = 5       # segundos por tentativa
SAMPLE_RATE       = 44100   # Hz
ARQUIVO_WAV       = os.path.join(tempfile.gettempdir(), "linguavox_temp.wav")
ARQUIVO_RANKING   = "linguavox_ranking.json"

IDIOMAS = {
    "en": "🇬🇧 Inglês",
    "es": "🇪🇸 Espanhol",
    "fr": "🇫🇷 Francês",
    "de": "🇩🇪 Alemão",
    "it": "🇮🇹 Italiano",
    "ja": "🇯🇵 Japonês",
    "zh": "🇨🇳 Chinês",
    "pt": "🇧🇷 Português",
}

NIVEIS = {
    "F":  {"nome": "Fácil",        "emoji": "🟢", "pontos": 10,  "tempo": 5,  "mostrar_dica": True},
    "M":  {"nome": "Médio",        "emoji": "🟡", "pontos": 20,  "tempo": 5,  "mostrar_dica": False},
    "D":  {"nome": "Difícil",      "emoji": "🟠", "pontos": 35,  "tempo": 5,  "mostrar_dica": False},
    "MD": {"nome": "Muito Difícil","emoji": "🔴", "pontos": 55,  "tempo": 6,  "mostrar_dica": False},
    "I":  {"nome": "Impossível",   "emoji": "💀", "pontos": 100, "tempo": 7,  "mostrar_dica": False},
}

PALAVRAS = {
    "F": [
        "gato","cachorro","maçã","leite","sol","lua",
        "carro","flor","livro","árvore","água","pão","casa","mão","pé",
        "mesa","cadeira","janela","porta","cidade","praia","noite","manhã","cidadezinha","praça"
    ],
    "M": [
        "escola","amigo","janela","amarelo","azul",
        "vermelho","verde","cinza","preto","branco",
        "música","viagem","cidade","comida","família",
        "computador","telefone","ônibus","trem","avião","mercado","restaurante","trabalho","escritório"
    ],
    "D": [
        "tecnologia","universidade","informação","pronúncia",
        "imaginação","desenvolvimento","conhecimento",
        "criatividade","comunicação","sustentabilidade",
        "responsabilidade","transparência","infraestrutura",
        "inovação","digitalização","automação","privacidade","segurança","eficiência","colaboração"
    ],
    "MD": [
        "o joão foi à fazenda comprar um boi",
        "a menina comeu um bolo de chocolate",
        "o cachorro latiu para o gato na rua",
        "o sol brilha no céu azul todos os dias",
        "a lua ilumina a noite escura e fria",
        "o carro vermelho é muito rápido",
        "a flor amarela é muito bonita",
        "o livro interessante é sobre ciência",
        "a árvore alta tem muitas folhas verdes",
        "o pássaro canta na manhã ensolarada",
        "a família viajou de trem para a serra",
        "o menino desenhou uma casa com jardim",
        "a professora explicou a lição com calma",
        "o mercado abriu cedo e estava movimentado",
        "a festa teve bolo, música e muitos amigos"
    ],
    "I": [
        "anticonstitucionalissimamente",
        "inconstitucionalissimamente",
        "otorrinolaringologista",
        "pneumoultramicroscopicosilicovulcanoconiose",
        "hipopotomonstrosesquipedaliofobia",
        "supercalifragilisticexpialidocious",
        "floccinaucinihilipilification",
        "pseudopseudohypoparathyroidism",
        "psychoneuroendocrinological",
        "thyroparathyroidectomized",
        "electroencephalographically",
        "hepaticocholangiocholecystenterostomies",
        "spectrophotofluorometrically"
    ],
}


# Frases motivacionais por acerto / erro
ACERTOS = [
    "🎉 Incrível! Sua pronúncia está impecável!",
    "🔥 Arrasei! Continua assim!",
    "⭐ Perfeito! Você nasceu poliglota!",
    "🏆 Mandou muito bem! Pontos somados!",
    "💪 Que pronúncia! Orgulho total!",
    "🎯 Na mosca! Sem erros!",
]
ERROS = [
    "😅 Quase lá! Tente de novo!",
    "🙈 Não foi dessa vez… mas não desista!",
    "💭 Hmm, algo escapou. Respira e tenta de novo!",
    "🤔 Sua língua tropeçou, mas o coração quis acertar!",
    "😬 Próxima vez vai! Você consegue!",
]


# ══════════════════════════════════════════════════════════════════════════════
#  FUNÇÕES UTILITÁRIAS
# ══════════════════════════════════════════════════════════════════════════════

def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")


def barra_progresso(atual: int, total: int, largura: int = 20) -> str:
    preenchido = int(largura * atual / total) if total else 0
    barra = "█" * preenchido + "░" * (largura - preenchido)
    return f"[{barra}] {atual}/{total}"


def pausar(msg: str = "Pressione ENTER para continuar..."):
    input(f"\n{msg}")


def linha(char: str = "─", tam: int = 55) -> str:
    return char * tam


def traduzir(texto: str, origem: str, destino: str) -> str:
    try:
        return GoogleTranslator(source=origem, target=destino).translate(texto)
    except Exception:
        return texto


def normalizar(texto: str) -> str:
    """Remove acentos e converte para minúsculas para comparação flexível."""
    import unicodedata
    texto = texto.lower().strip()
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  RANKING / PLACAR
# ══════════════════════════════════════════════════════════════════════════════

def carregar_ranking() -> list:
    if os.path.exists(ARQUIVO_RANKING):
        try:
            with open(ARQUIVO_RANKING, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def salvar_ranking(ranking: list):
    with open(ARQUIVO_RANKING, "w", encoding="utf-8") as f:
        json.dump(ranking, f, ensure_ascii=False, indent=2)


def registrar_pontuacao(nome: str, pontos: int, nivel: str, idioma: str):
    ranking = carregar_ranking()
    ranking.append({
        "nome":   nome,
        "pontos": pontos,
        "nivel":  nivel,
        "idioma": idioma,
        "data":   datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    ranking.sort(key=lambda x: x["pontos"], reverse=True)
    salvar_ranking(ranking[:10])  # top 10


def exibir_ranking():
    ranking = carregar_ranking()
    print("\n" + linha("═"))
    print("🏆  TOP 10 — LINGUAVOX HALL OF FAME  🏆")
    print(linha("═"))
    if not ranking:
        print("   Ainda sem pontuações registradas. Seja o primeiro! 🌟")
    else:
        medalhas = ["🥇", "🥈", "🥉"] + ["🎖️"] * 7
        for i, r in enumerate(ranking):
            nivel_info = NIVEIS.get(r.get("nivel", "F"), {})
            emoji_nivel = nivel_info.get("emoji", "")
            print(
                f"  {medalhas[i]} {r['nome']:<14} "
                f"{r['pontos']:>5} pts  "
                f"{emoji_nivel} {nivel_info.get('nome','?'):<12}  "
                f"🌍 {r.get('idioma','?'):<5}  📅 {r.get('data','')}"
            )
    print(linha("═"))


# ══════════════════════════════════════════════════════════════════════════════
#  GRAVAÇÃO & RECONHECIMENTO
# ══════════════════════════════════════════════════════════════════════════════

def selecionar_dispositivo_entrada():
    """Escolhe um dispositivo de entrada real, com fallback para o padrão do sistema."""
    def canais(info):
        if isinstance(info, dict):
            return info.get("max_input_channels", 0)
        return getattr(info, "max_input_channels", 0)

    try:
        default_device = sd.default.device
        if isinstance(default_device, (list, tuple)) and default_device:
            input_device = default_device[0]
            if input_device is not None:
                info = sd.query_devices(input_device)
                if canais(info) > 0:
                    return input_device
    except Exception:
        pass

    try:
        for idx, info in enumerate(sd.query_devices()):
            if canais(info) > 0:
                return idx
    except Exception:
        return None

    return None


def gravar_audio(duracao: int = DURACAO_GRAVACAO) -> bool:
    """Grava áudio do microfone com fallback de taxa de amostragem para Windows."""
    device = selecionar_dispositivo_entrada()
    taxas = (16000, 22050, 44100)
    ultima_erro = None

    try:
        print(f"\n  🎙️  Gravando por {duracao}s… FALE AGORA!", end="", flush=True)
        for i in range(duracao, 0, -1):
            time.sleep(1)
            print(f" {i}…", end="", flush=True)
        print()

        for taxa in taxas:
            try:
                if os.path.exists(ARQUIVO_WAV):
                    os.remove(ARQUIVO_WAV)

                recording = sd.rec(
                    int(duracao * taxa),
                    samplerate=taxa,
                    channels=1,
                    dtype="int16",
                    device=device,
                )
                sd.wait()
                wav.write(ARQUIVO_WAV, taxa, recording)
                return True
            except Exception as e:
                ultima_erro = e
                try:
                    sd.stop()
                except Exception:
                    pass

        print(f"\n  ❌ Erro ao gravar: {ultima_erro}")
        return False
    except Exception as e:
        print(f"\n  ❌ Erro ao gravar: {e}")
        return False


def reconhecer_fala(idioma_bcp47: str = "pt-BR") -> str | None:
    """Retorna o texto reconhecido ou None."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(ARQUIVO_WAV) as source:
            audio = recognizer.record(source)
        resultado = recognizer.recognize_google(audio, language=idioma_bcp47, show_all=True)
        if not resultado:
            return None
        return resultado["alternative"][0].get("transcript", "")
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"\n  ❌ Erro no serviço de fala: {e}")
        return None


# Mapa de código de idioma → código BCP-47 para reconhecimento
BCP47 = {
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "de": "de-DE",
    "it": "it-IT",
    "ja": "ja-JP",
    "zh": "zh-CN",
    "pt": "pt-BR",
}


# ══════════════════════════════════════════════════════════════════════════════
#  TELAS / MENUS
# ══════════════════════════════════════════════════════════════════════════════

def tela_boas_vindas():
    limpar_tela()
    print("""
╔══════════════════════════════════════════════════════╗
║                                                      ║
║   🌍  L I N G U A V O X  🎙️                         ║
║        Jogo de Pronúncia & Tradução                  ║
║                                                      ║
║   Fale, traduza e conquiste o mundo!                 ║
╚══════════════════════════════════════════════════════╝
""")


def escolher_idioma() -> str:
    print("  🌐  Escolha o idioma alvo:\n")
    codigos = list(IDIOMAS.keys())
    for i, cod in enumerate(codigos, 1):
        print(f"    {i}. {IDIOMAS[cod]}  ({cod})")
    print()
    while True:
        entrada = input("  Digite o número ou o código (ex: en): ").strip().lower()
        if entrada in IDIOMAS:
            return entrada
        if entrada.isdigit() and 1 <= int(entrada) <= len(codigos):
            return codigos[int(entrada) - 1]
        print("  ⚠️  Opção inválida. Tente novamente.")


def escolher_nivel() -> str:
    print("\n  🎮  Escolha o nível de dificuldade:\n")
    for cod, info in NIVEIS.items():
        print(f"    {info['emoji']}  [{cod:>2}]  {info['nome']:<14}  +{info['pontos']} pts/acerto")
    print()
    while True:
        entrada = input("  Nível (F / M / D / MD / I): ").strip().upper()
        if entrada in NIVEIS:
            return entrada
        print("  ⚠️  Opção inválida. Tente novamente.")


def menu_principal() -> str:
    tela_boas_vindas()
    print("  ╔──────────────────────────────────╗")
    print("  │  1. 🎮  Jogar                    │")
    print("  │  2. 🏆  Ver Ranking              │")
    print("  │  3. 📖  Como Jogar               │")
    print("  │  4. 🚪  Sair                     │")
    print("  ╚──────────────────────────────────╝\n")
    while True:
        op = input("  Escolha uma opção: ").strip()
        if op in ("1", "2", "3", "4"):
            return op
        print("  ⚠️  Opção inválida.")


def tela_como_jogar():
    limpar_tela()
    print(linha("═"))
    print("📖  COMO JOGAR — LINGUAVOX")
    print(linha("═"))
    print("""
  1. Escolha o idioma para o qual vai traduzir/falar.
  2. Escolha o nível de dificuldade.
  3. Uma palavra em Português vai aparecer na tela.
     • No nível Fácil, a tradução já aparece de dica. 😊
     • Nos outros níveis, você precisa saber a tradução!
  4. Quando o cronômetro começar, FALE a tradução
     corretamente no idioma escolhido.
  5. A IA vai reconhecer sua voz e comparar com a resposta.
  6. Acertou? ➕ Pontos! Errou? ➖ Vida!
  7. Você começa com ❤️❤️❤️ 3 vidas.
  8. Perde todas as vidas? Fim de jogo! Salve seu placar.

  💡 DICAS:
    • Fale claramente e próximo ao microfone.
    • Pronuncie devagar no início.
    • Palavras compostas: fale tudo junto, sem pausas.
    • Nível Impossível = palavras que ninguém pronuncia! 💀
""")
    print(linha("═"))
    pausar()


# ══════════════════════════════════════════════════════════════════════════════
#  LÓGICA PRINCIPAL DA RODADA
# ══════════════════════════════════════════════════════════════════════════════

def exibir_hud(
    nome: str, nivel: str, idioma: str,
    pontos: int, vidas: int, streak: int,
    rodada: int, total_rodadas: int
):
    info = NIVEIS[nivel]
    vidas_str = "❤️ " * vidas + "🖤 " * (3 - vidas)
    streak_str = f"🔥×{streak}" if streak >= 2 else ""
    print(f"\n  👤 {nome}  |  {info['emoji']} {info['nome']}  |  🌍 {IDIOMAS[idioma]}")
    print(f"  ⭐ Pontos: {pontos}  |  {vidas_str} |  {streak_str}")
    print(f"  {barra_progresso(rodada, total_rodadas)}  Rodada {rodada}/{total_rodadas}")
    print(linha())


def jogar_rodada(
    palavra_pt: str,
    idioma: str,
    nivel: str,
    mostrar_dica: bool,
) -> tuple[bool, str, str]:
    """
    Executa uma rodada do jogo.
    Retorna (acertou: bool, texto_falado: str, traducao_esperada: str).
    """
    traducao_esperada = traduzir(palavra_pt, "pt", idioma).lower().strip()
    info = NIVEIS[nivel]

    print(f"\n  📝  Palavra em Português:  « {palavra_pt.upper()} »")
    if mostrar_dica:
        print(f"  💡  Tradução ({IDIOMAS[idioma]}):  → {traducao_esperada}")
    else:
        print(f"  🤐  Traduza para {IDIOMAS[idioma]} e pronuncie!")
    print(f"\n  ⏱️  Tempo de gravação: {info['tempo']}s")

    sucesso = gravar_audio(info["tempo"])
    if not sucesso:
        return False, "", traducao_esperada

    print("\n  🔍  Analisando sua pronúncia…", end="", flush=True)
    time.sleep(0.5)
    bcp = BCP47.get(idioma, f"{idioma}-{idioma.upper()}")
    texto_reconhecido = reconhecer_fala(bcp)
    print(" feito!")

    if texto_reconhecido is None:
        print("\n  😶  Não consegui entender. Verifique seu microfone.")
        return False, "", traducao_esperada

    texto_norm    = normalizar(texto_reconhecido)
    esperado_norm = normalizar(traducao_esperada)
    acertou = texto_norm == esperado_norm or esperado_norm in texto_norm

    return acertou, texto_reconhecido, traducao_esperada


# ══════════════════════════════════════════════════════════════════════════════
#  SESSÃO COMPLETA DE JOGO
# ══════════════════════════════════════════════════════════════════════════════

TOTAL_RODADAS = 10

def jogar(nome: str):
    limpar_tela()
    print(f"\n  Olá, {nome}! Vamos começar! 🚀\n")

    idioma = escolher_idioma()
    nivel  = escolher_nivel()

    pontos      = 0
    vidas       = 3
    streak      = 0
    maior_streak = 0
    acertos     = 0
    rodada      = 0
    palavras_usadas = set()

    pool = PALAVRAS[nivel][:]
    random.shuffle(pool)

    while rodada < TOTAL_RODADAS and vidas > 0:
        # Pega próxima palavra sem repetir
        disponiveis = [p for p in pool if p not in palavras_usadas]
        if not disponiveis:
            palavras_usadas.clear()
            disponiveis = pool[:]
        palavra = random.choice(disponiveis)
        palavras_usadas.add(palavra)

        rodada += 1
        limpar_tela()
        info = NIVEIS[nivel]
        exibir_hud(nome, nivel, idioma, pontos, vidas, streak, rodada, TOTAL_RODADAS)

        acertou, falado, esperado = jogar_rodada(
            palavra, idioma, nivel, info["mostrar_dica"]
        )

        print(linha("┄"))

        if acertou:
            bonus = int(info["pontos"] * (1 + streak * 0.1))  # bônus de streak
            pontos  += bonus
            streak  += 1
            acertos += 1
            maior_streak = max(maior_streak, streak)
            print(f"\n  {random.choice(ACERTOS)}")
            print(f"  ✅  Você disse:   « {falado} »")
            print(f"  🎯  Esperado:     « {esperado} »")
            if streak >= 2:
                print(f"  🔥  STREAK ×{streak}! Bônus aplicado → +{bonus} pts")
            else:
                print(f"  ➕  +{bonus} pontos!")
        else:
            vidas  -= 1
            streak  = 0
            print(f"\n  {random.choice(ERROS)}")
            if falado:
                print(f"  ❌  Você disse:   « {falado} »")
            print(f"  ✅  Esperado:     « {esperado} »")
            if vidas > 0:
                print(f"  {'❤️ ' * vidas}{'🖤 ' * (3-vidas)}  Restam {vidas} vida(s).")
            else:
                print("  💔  Sem vidas! Fim de jogo!")

        pausar("  ⏎  Pressione ENTER para a próxima rodada…")

    # ── Fim de Sessão ─────────────────────────────────────────────────────────
    limpar_tela()
    print("\n" + linha("═"))
    print("🏁  FIM DE JOGO — RESULTADO FINAL")
    print(linha("═"))
    print(f"\n  👤  Jogador:       {nome}")
    print(f"  🌍  Idioma:        {IDIOMAS[idioma]}")
    print(f"  🎮  Nível:         {info['emoji']} {info['nome']}")
    print(f"  ⭐  Pontuação:     {pontos} pts")
    print(f"  ✅  Acertos:       {acertos}/{TOTAL_RODADAS}")
    print(f"  🔥  Maior Streak:  ×{maior_streak}")
    taxa = int(acertos / TOTAL_RODADAS * 100)
    print(f"  📊  Aproveitamento:{taxa}%")

    if taxa == 100:
        print("\n  🏆  PERFEITO! Você é um gênio dos idiomas!")
    elif taxa >= 70:
        print("\n  🎉  Ótimo desempenho! Continue praticando!")
    elif taxa >= 40:
        print("\n  💪  Bom esforço! Você está melhorando!")
    else:
        print("\n  📚  Pratique mais! Cada erro é um aprendizado!")

    print(linha("═"))

    registrar_pontuacao(nome, pontos, nivel, idioma)
    print(f"\n  💾  Pontuação salva no ranking!")
    pausar()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    limpar_tela()
    tela_boas_vindas()
    nome = input("  🙋  Digite seu nome de jogador: ").strip() or "Anônimo"

    while True:
        op = menu_principal()

        if op == "1":
            jogar(nome)

        elif op == "2":
            limpar_tela()
            exibir_ranking()
            pausar()

        elif op == "3":
            tela_como_jogar()

        elif op == "4":
            limpar_tela()
            print("\n  👋  Até logo! Continue praticando seus idiomas! 🌍✨\n")
            # Limpa arquivo temporário
            if os.path.exists(ARQUIVO_WAV):
                os.remove(ARQUIVO_WAV)
            break


if __name__ == "__main__":
    main()
