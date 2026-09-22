#!/usr/bin/env python3
"""
⚛️ ESPELHO QUANTUM PRO - TELEGRAM
📡 Copia sinais + lê resultados por OCR (fotos sem legenda)
✅ Usa horário da mensagem como fallback quando OCR falha
✅ Opção D: WIN NA PROTEÇÃO conta como WIN geral
"""

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from datetime import datetime, timedelta
import re
import asyncio
import os
import sys
import io
import unicodedata

# ==============================
# CONFIGURAÇÕES
# ==============================
api_id = int(os.environ.get('API_ID', '22453120'))
api_hash = os.environ.get('API_HASH', '89826a4104518e9ed650cdb451ad8b53')
SESSAO_STRING = os.environ.get('SESSAO_STRING', '')

origem = int(os.environ.get('CANAL_ORIGEM', '-1001824915491'))
destino = int(os.environ.get('CANAL_DESTINO', '-1004483690234'))

if not SESSAO_STRING:
    print("❌ ERRO: Variável SESSAO_STRING não definida!")
    sys.exit(1)

client = TelegramClient(StringSession(SESSAO_STRING), api_id, api_hash)

# ==============================
# OCR
# ==============================
try:
    import easyocr
    import numpy as np
    from PIL import Image
    print("⏳ Carregando OCR (pode demorar na 1ª vez)...")
    _reader = easyocr.Reader(['pt', 'en'], gpu=False, verbose=False)
    OCR_OK = True
    print("✅ OCR carregado")
except Exception as e:
    print(f"⚠️ OCR indisponível: {e}")
    OCR_OK = False

# ==============================
# ESTATÍSTICAS
# ==============================
stats = {'win': 0, 'loss': 0}

# Guarda o horário do último sinal enviado, pra estimar o resultado
ultimo_sinal_horario = None  # datetime
ultimo_sinal_expiracao_min = 1  # M1 por padrão

# ==============================
# FUNÇÕES
# ==============================

def horario():
    return datetime.now().strftime("%H:%M:%S")

def obter_texto(event):
    msg = event.message
    return msg.message or msg.text or ""

def normalizar(txt):
    txt = txt.upper()
    txt = unicodedata.normalize('NFKD', txt)
    txt = ''.join(c for c in txt if not unicodedata.combining(c))
    txt = txt.replace('0', 'O').replace('1', 'I').replace('5', 'S')
    txt = re.sub(r'[^A-Z ]+', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt

def eh_sinal(texto):
    t = texto.lower()
    return (
        'ativo:' in t and
        ('horário:' in t or 'horario:' in t) and
        ('expiração:' in t or 'expiracao:' in t) and
        ('direção:' in t or 'direcao:' in t)
    )

def extrair_dados_sinal(texto):
    dados = {
        'ativo': 'EUR/JPY (OTC)',
        'direcao': 'CALL',
        'horario': '',
        'expiracao': 'M1',
        'suporte': ''
    }
    m = re.search(r'Ativo:\s*([^\n]+)', texto, re.IGNORECASE)
    if m: dados['ativo'] = m.group(1).strip()
    m = re.search(r'Hor[áa]rio:\s*(\d{1,2}:\d{2})', texto, re.IGNORECASE)
    if m: dados['horario'] = m.group(1).strip()
    m = re.search(r'Expira[çc][ãa]o:\s*([^\n]+)', texto, re.IGNORECASE)
    if m: dados['expiracao'] = m.group(1).strip()
    m = re.search(r'Dire[çc][ãa]o:\s*([^\n]+)', texto, re.IGNORECASE)
    if m:
        d = m.group(1).strip().upper()
        if 'CALL' in d or '🟢' in d or 'COMPRA' in d:
            dados['direcao'] = 'CALL'
        elif 'PUT' in d or '🔴' in d or 'VENDA' in d:
            dados['direcao'] = 'PUT'
        else:
            dados['direcao'] = d
    m = re.search(r'Suporte:\s*([^\n]+)', texto, re.IGNORECASE)
    if m: dados['suporte'] = m.group(1).strip()
    if not dados['horario']:
        dados['horario'] = datetime.now().strftime("%H:%M")
    return dados

def calcular_assertividade():
    total = stats['win'] + stats['loss']
    if total == 0:
        return 0.0
    return round((stats['win'] / total) * 100, 1)

def formatar_sinal_quantum(dados):
    emoji_direcao = '🟢' if dados['direcao'] == 'CALL' else '🔴'
    suporte_linha = f"\n🥇 Suporte: {dados['suporte']}" if dados['suporte'] else ""
    return f"""⚛️ SINAL QUANTUM PRO ⚛️

⏰ Horário: {dados['horario']}
💵 Ativo: {dados['ativo']}
📉 Direção: {dados['direcao']} {emoji_direcao}
⏳ Expiração: {dados['expiracao']}{suporte_linha}

⚠️ Entrar somente no horário marcado.
🔄 2 recuperação (Gale 2)!"""

def classificar_ocr(texto_ocr):
    """OCR apenas para detectar WIN ou LOSS na imagem."""
    t = normalizar(texto_ocr)
    print(f"[OCR NORMALIZADO] {t}")

    tem_loss = 'LOSS' in t or 'LOS' in t
    tem_win = (
        'WIN' in t or 'VVIN' in t or 'VIN' in t or
        re.search(r'\bW\s*I\s*N\b', t) is not None
    )

    if tem_loss:
        return 'loss'
    if tem_win:
        return 'win'
    return None

def estimar_por_horario():
    """
    Fallback: se o OCR falhou, estima o resultado pelo tempo
    desde o último sinal enviado.
    Regra (M1):
      - até 2 min  -> win (sem gale ou na proteção — opção D conta tudo como win)
      - mais de 2 min -> loss
    """
    global ultimo_sinal_horario, ultimo_sinal_expiracao_min

    if ultimo_sinal_horario is None:
        return None

    delta = (datetime.now() - ultimo_sinal_horario).total_seconds() / 60
    limite = ultimo_sinal_expiracao_min * 2  # 2 velas

    if delta <= limite:
        return 'win'
    return 'loss'

def formatar_resultado_quantum(resultado, origem_deteccao=""):
    if resultado == 'win':
        stats['win'] += 1
        emoji, status = '✅', 'WIN'
    elif resultado == 'loss':
        stats['loss'] += 1
        emoji, status = '❌', 'LOSS'
    else:
        return None

    sufixo = f" _(via {origem_deteccao})_" if origem_deteccao else ""

    return f"""{emoji} {status}{sufixo}
📊 Placar: 🟢{stats['win']}W 🔴{stats['loss']}L
🎯 Assertividade: {calcular_assertividade()}%"""

async def zerar_placar():
    global stats
    stats = {'win': 0, 'loss': 0}
    print(f"[{horario()}] 🔄 PLACAR ZERADO - NOVO DIA!")
    try:
        msg = """🔄 PLACAR ZERADO - NOVO DIA!
📊 Estatísticas reiniciadas à meia-noite.

⚛️ QUANTUM PRO PRONTO PARA OPERAR! ⚛️"""
        await client.send_message(destino, msg)
    except Exception as e:
        print(f"[{horario()}] ❌ Erro ao enviar zeramento: {e}")

async def agendar_zeramento():
    while True:
        agora = datetime.now()
        meia_noite = agora.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        await asyncio.sleep((meia_noite - agora).total_seconds())
        await zerar_placar()

@client.on(events.NewMessage(chats=origem))
async def processar_mensagem(event):
    global ultimo_sinal_horario, ultimo_sinal_expiracao_min

    texto = obter_texto(event)
    tem_foto = event.message.photo is not None

    print(f"[{horario()}] 🔔 Nova mensagem (foto={tem_foto})")

    # ---- SINAL (texto) ----
    if texto and eh_sinal(texto):
        dados = extrair_dados_sinal(texto)
        msg = formatar_sinal_quantum(dados)

        # Guarda o horário do sinal pra estimar resultado depois
        ultimo_sinal_horario = datetime.now()
        m = re.search(r'M(\d+)', dados['expiracao'])
        ultimo_sinal_expiracao_min = int(m.group(1)) if m else 1

        print(f"[{horario()}] 📊 SINAL | {dados['ativo']} | {dados['direcao']} | {dados['horario']}")
        try:
            await client.send_message(destino, msg)
            print(f"[{horario()}] ✅ Enviado!")
        except Exception as e:
            print(f"[{horario()}] ❌ Erro: {e}")
        print("=" * 40)
        return

    # ---- FOTO DE RESULTADO ----
    if tem_foto:
        resultado = None
        via = ""

        # 1) Tenta OCR
        if OCR_OK:
            print(f"[{horario()}] 🖼️ Foto — rodando OCR...")
            try:
                img_bytes = await event.message.download_media(file=bytes)
                img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
                arr = np.array(img)

                resultado_ocr = _reader.readtext(arr, detail=0, paragraph=True)
                texto_ocr = " ".join(resultado_ocr)
                print(f"[{horario()}] 🔎 OCR bruto: {texto_ocr[:200]}")

                resultado = classificar_ocr(texto_ocr)
                via = "OCR"
            except Exception as e:
                print(f"[{horario()}] ❌ Erro OCR: {e}")

        # 2) Fallback: horário
        if resultado is None:
            resultado = estimar_por_horario()
            via = "horário"
            print(f"[{horario()}] ⏱️ Fallback por horário: {resultado}")

        if resultado:
            msg = formatar_resultado_quantum(resultado, via)
            try:
                await client.send_message(destino, msg)
                print(f"[{horario()}] ✅ Resultado enviado: {resultado.upper()} (via {via})")
                print(f"[{horario()}] 📊 Placar: 🟢{stats['win']}W 🔴{stats['loss']}L")
            except Exception as e:
                print(f"[{horario()}] ❌ Erro ao enviar: {e}")
        else:
            print(f"[{horario()}] ⚠️ Não foi possível classificar a foto")
        print("=" * 40)
        return

    # ---- RESULTADO POR TEXTO (fallback) ----
    if texto:
        t = normalizar(texto)
        if 'LOSS' in t or '❎' in texto:
            resultado = 'loss'
        elif 'WIN' in t:
            resultado = 'win'
        else:
            resultado = None

        if resultado:
            msg = formatar_resultado_quantum(resultado, "texto")
            if msg:
                await client.send_message(destino, msg)
                print(f"[{horario()}] ✅ Resultado (texto): {resultado.upper()}")
            print("=" * 40)
            return

    print(f"[{horario()}] 📝 Ignorada")
    print("=" * 40)

async def main():
    print("=" * 50)
    print("     ⚛️ ESPELHO QUANTUM PRO ⚛️")
    print("=" * 50)
    await client.start()
    print("✅ Conectado")
    print(f"📡 Origem: {origem}")
    print(f"📡 Destino: {destino}")
    print("🛡️ WIN NA PROTEÇÃO conta como WIN geral")
    print("⏱️ Fallback por horário ativado")
    print("⏳ Aguardando...")
    asyncio.create_task(agendar_zeramento())
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Encerrado!")
