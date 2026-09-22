#!/usr/bin/env python3
"""
⚛️ ESPELHO TRADER MAGO - TELEGRAM
📡 Copia sinais + classifica resultado pelo TEMPO desde o sinal
✅ Opção D: WIN e WIN NA PROTEÇÃO contam como WIN geral
✅ Zeramento automático à meia-noite (horário de Brasília)
❌ SEM OCR — classificação 100% por tempo
❌ SEM campo Suporte no sinal enviado
"""

# ==============================
# FUSO HORÁRIO BRASÍLIA (UTC-3)
# ==============================
import os
os.environ['TZ'] = 'America/Sao_Paulo'
try:
    import time
    time.tzset()
except Exception:
    pass

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from datetime import datetime, timedelta
import re
import asyncio
import sys
import unicodedata

# ==============================
# CONFIGURAÇÕES
# ==============================
api_id = int(os.environ.get('API_ID', '22453120'))
api_hash = os.environ.get('API_HASH', '89826a4104518e9ed650cdb451ad8b53')
SESSAO_STRING = os.environ.get('SESSAO_STRING', '')

origem = int(os.environ.get('CANAL_ORIGEM', '-1001245695047'))
destino = int(os.environ.get('CANAL_DESTINO', '-1004483690234'))

if not SESSAO_STRING:
    print("❌ ERRO: Variável SESSAO_STRING não definida!")
    print("   Configure a string de sessão no Railway.")
    sys.exit(1)

client = TelegramClient(StringSession(SESSAO_STRING), api_id, api_hash)

# ==============================
# ESTATÍSTICAS
# ==============================
stats = {'win': 0, 'loss': 0}

ultimo_sinal_horario = None      # datetime do último sinal
ultimo_sinal_expiracao_min = 1   # expiração em minutos (M1 = 1)

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
    """Versão simplificada — só exige 'ativo:' e 'horário:'/'horario:'."""
    t = texto.lower()
    tem_ativo = 'ativo:' in t
    tem_horario = 'horário:' in t or 'horario:' in t
    return tem_ativo and tem_horario

def extrair_dados_sinal(texto):
    dados = {
        'ativo': 'EUR/JPY (OTC)',
        'direcao': 'CALL',
        'horario': '',
        'expiracao': 'M1'
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
    if not dados['horario']:
        dados['horario'] = datetime.now().strftime("%H:%M")
    return dados

def calcular_assertividade():
    total = stats['win'] + stats['loss']
    if total == 0:
        return 0.0
    return round((stats['win'] / total) * 100, 1)

def formatar_sinal_quantum(dados):
    """SEM campo Suporte."""
    emoji_direcao = '🟢' if dados['direcao'] == 'CALL' else '🔴'
    return f"""⚛️ SINAL TRADER MAGO ⚛️

⏰ Horário: {dados['horario']}
💵 Ativo: {dados['ativo']}
📉 Direção: {dados['direcao']} {emoji_direcao}
⏳ Expiração: {dados['expiracao']}

⚠️ Entrar somente no horário marcado.
🔄 2 recuperação (Gale 2)!"""

def classificar_por_tempo():
    """
    Classifica o resultado pelo tempo desde o último sinal.
    Regra (M1): <= 2 velas -> WIN | > 2 velas -> LOSS
    Retorna (resultado, minutos_decorridos)
    """
    global ultimo_sinal_horario, ultimo_sinal_expiracao_min

    if ultimo_sinal_horario is None:
        return None, None

    delta_min = (datetime.now() - ultimo_sinal_horario).total_seconds() / 60
    limite = ultimo_sinal_expiracao_min * 2

    resultado = 'win' if delta_min <= limite else 'loss'
    return resultado, delta_min

def formatar_resultado_quantum(resultado, minutos=None):
    if resultado == 'win':
        stats['win'] += 1
        emoji, status = '✅', 'WIN'
    elif resultado == 'loss':
        stats['loss'] += 1
        emoji, status = '❌', 'LOSS'
    else:
        return None

    detalhe = f" _(em {minutos:.1f} min)_" if minutos is not None else ""

    return f"""{emoji} {status}{detalhe}
📊 Placar: 🟢{stats['win']}W 🔴{stats['loss']}L
🎯 Assertividade: {calcular_assertividade()}%"""

async def zerar_placar():
    global stats
    stats = {'win': 0, 'loss': 0}
    print(f"[{horario()}] 🔄 PLACAR ZERADO - NOVO DIA! (horário Brasília)")
    try:
        msg = """🔄 PLACAR ZERADO - NOVO DIA!
📊 Estatísticas reiniciadas à meia-noite.

⚛️ TRADER MAGO PRONTO PARA OPERAR! ⚛️"""
        await client.send_message(destino, msg)
        print(f"[{horario()}] ✅ Mensagem de zeramento enviada!")
    except Exception as e:
        print(f"[{horario()}] ❌ Erro ao enviar zeramento: {e}")

async def agendar_zeramento():
    """Agenda o zeramento pra meia-noite EXATA do horário de Brasília."""
    while True:
        agora = datetime.now()
        meia_noite = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        if agora >= meia_noite:
            meia_noite = meia_noite + timedelta(days=1)

        espera = (meia_noite - agora).total_seconds()
        print(f"[{horario()}] ⏰ Próximo zeramento em {espera/3600:.2f}h (às 00:00 Brasília)")

        await asyncio.sleep(espera)
        await zerar_placar()

@client.on(events.NewMessage(chats=origem))
async def processar_mensagem(event):
    global ultimo_sinal_horario, ultimo_sinal_expiracao_min

    texto = obter_texto(event)
    tem_foto = event.message.photo is not None

    print(f"[{horario()}] 🔔 Nova mensagem (foto={tem_foto})")
    print(f"[{horario()}] 📝 Texto: {repr(texto[:200])}")

    # ---- PRIMEIRO: verifica se é SINAL (com ou sem foto) ----
    if texto and eh_sinal(texto):
        dados = extrair_dados_sinal(texto)
        msg = formatar_sinal_quantum(dados)

        ultimo_sinal_horario = datetime.now()
        m = re.search(r'M(\d+)', dados['expiracao'])
        ultimo_sinal_expiracao_min = int(m.group(1)) if m else 1

        print(f"[{horario()}] 📊 SINAL | {dados['ativo']} | {dados['direcao']} | {dados['horario']} | exp={dados['expiracao']}")
        try:
            await client.send_message(destino, msg)
            print(f"[{horario()}] ✅ Enviado!")
        except Exception as e:
            print(f"[{horario()}] ❌ Erro: {e}")
        print("=" * 40)
        return

    # ---- DEPOIS: se for foto SEM sinal, trata como resultado ----
    if tem_foto:
        resultado, minutos = classificar_por_tempo()
        if resultado:
            msg = formatar_resultado_quantum(resultado, minutos)
            try:
                await client.send_message(destino, msg)
                print(f"[{horario()}] ✅ Resultado: {resultado.upper()} (em {minutos:.1f} min)")
                print(f"[{horario()}] 📊 Placar: 🟢{stats['win']}W 🔴{stats['loss']}L")
            except Exception as e:
                print(f"[{horario()}] ❌ Erro: {e}")
        else:
            print(f"[{horario()}] ⚠️ Sem sinal anterior — ignorando")
        print("=" * 40)
        return

    # ---- RESULTADO POR TEXTO ----
    if texto:
        t = normalizar(texto)
        if 'LOSS' in t or '❎' in texto:
            resultado = 'loss'
        elif 'WIN' in t:
            resultado = 'win'
        else:
            resultado = None

        if resultado:
            msg = formatar_resultado_quantum(resultado, None)
            if msg:
                await client.send_message(destino, msg)
                print(f"[{horario()}] ✅ Resultado (texto): {resultado.upper()}")
            print("=" * 40)
            return

    print(f"[{horario()}] 📝 Ignorada")
    print("=" * 40)

async def main():
    print("=" * 50)
    print("     ⚛️ ESPELHO TRADER MAGO ⚛️")
    print("=" * 50)
    print(f"🕐 Fuso horário: {time.tzname}")
    print(f"🕐 Agora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} (Brasília)")
    await client.start()
    print("✅ Conectado")
    print(f"📡 Origem: {origem}")
    print(f"📡 Destino: {destino}")
    print("🛡️ WIN NA PROTEÇÃO conta como WIN geral")
    print("⏱️ Classificação 100% por tempo (sem OCR)")
    print("🔄 Zeramento automático à meia-noite (Brasília)")
    print("⏳ Aguardando...")
    asyncio.create_task(agendar_zeramento())
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Encerrado!")
