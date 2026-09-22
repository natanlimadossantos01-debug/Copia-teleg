#!/usr/bin/env python3
"""
⚛️ ESPELHO QUANTUM PRO - TELEGRAM
📡 Copia sinais de um canal para outro
🔄 Placar automático + zeramento diário
✅ Adaptado para o formato: Ativo / Horário / Expiração / Direção / Suporte
"""

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from datetime import datetime, timedelta
import re
import asyncio
import os
import sys

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
# ESTATÍSTICAS
# ==============================
stats = {'win': 0, 'gale1': 0, 'gale2': 0, 'loss': 0}

# ==============================
# FUNÇÕES
# ==============================

def horario():
    return datetime.now().strftime("%H:%M:%S")

def eh_sinal(texto):
    """Detecta o formato novo: Ativo / Horário / Expiração / Direção"""
    texto_lower = texto.lower()
    tem_ativo = 'ativo:' in texto_lower
    tem_horario = 'horário:' in texto_lower or 'horario:' in texto_lower
    tem_expiracao = 'expiração:' in texto_lower or 'expiracao:' in texto_lower
    tem_direcao = 'direção:' in texto_lower or 'direcao:' in texto_lower
    return tem_ativo and tem_horario and tem_expiracao and tem_direcao

def identificar_resultado(texto):
    texto_lower = texto.lower()
    if "❎gestão" in texto or "❎ gestão" in texto:
        return 'loss'
    if "win" in texto_lower and "proteção 2" in texto_lower and "✅" in texto:
        return 'gale2'
    if "win" in texto_lower and "proteção 1" in texto_lower and "✅" in texto:
        return 'gale1'
    if "quem pegou colocou dinheiro no bolso" in texto_lower:
        return 'win'
    if "win" in texto_lower and ("lucro" in texto_lower or "💰" in texto):
        return 'win'
    return None

def extrair_dados_sinal(texto):
    """Extrai dados do formato novo"""
    dados = {
        'ativo': 'EUR/JPY (OTC)',
        'direcao': 'CALL',
        'horario': '',
        'expiracao': 'M1',
        'suporte': ''
    }

    # Ativo
    m = re.search(r'Ativo:\s*([^\n]+)', texto, re.IGNORECASE)
    if m:
        dados['ativo'] = m.group(1).strip()

    # Horário
    m = re.search(r'Hor[áa]rio:\s*(\d{1,2}:\d{2})', texto, re.IGNORECASE)
    if m:
        dados['horario'] = m.group(1).strip()

    # Expiração
    m = re.search(r'Expira[çc][ãa]o:\s*([^\n]+)', texto, re.IGNORECASE)
    if m:
        dados['expiracao'] = m.group(1).strip()

    # Direção
    m = re.search(r'Dire[çc][ãa]o:\s*([^\n]+)', texto, re.IGNORECASE)
    if m:
        dir_txt = m.group(1).strip().upper()
        if 'CALL' in dir_txt or '🟢' in dir_txt or 'COMPRA' in dir_txt:
            dados['direcao'] = 'CALL'
        elif 'PUT' in dir_txt or '🔴' in dir_txt or 'VENDA' in dir_txt:
            dados['direcao'] = 'PUT'
        else:
            dados['direcao'] = dir_txt

    # Suporte
    m = re.search(r'Suporte:\s*([^\n]+)', texto, re.IGNORECASE)
    if m:
        dados['suporte'] = m.group(1).strip()

    if not dados['horario']:
        dados['horario'] = datetime.now().strftime("%H:%M")

    return dados

def calcular_assertividade():
    total = stats['win'] + stats['gale1'] + stats['gale2'] + stats['loss']
    if total == 0:
        return 0.0
    return round(((stats['win'] + stats['gale1'] + stats['gale2']) / total) * 100, 1)

def formatar_sinal_quantum(dados):
    emoji_direcao = '🟢' if dados['direcao'] == 'CALL' else '🔴'
    suporte_linha = f"\n🥇 Suporte: {dados['suporte']}" if dados['suporte'] else ""

    mensagem = f"""⚛️ SINAL QUANTUM PRO ⚛️

⏰ Horário: {dados['horario']}
💵 Ativo: {dados['ativo']}
📉 Direção: {dados['direcao']} {emoji_direcao}
⏳ Expiração: {dados['expiracao']}{suporte_linha}

⚠️ Entrar somente no horário marcado.
🔄 2 recuperação (Gale 2)!"""
    return mensagem

def formatar_resultado_quantum(texto):
    resultado = identificar_resultado(texto)

    if resultado == 'win':
        stats['win'] += 1
        emoji, status = '✅', 'WIN'
    elif resultado == 'gale1':
        stats['gale1'] += 1
        emoji, status = '✅', 'WIN (Gale 1)'
    elif resultado == 'gale2':
        stats['gale2'] += 1
        emoji, status = '✅', 'WIN (Gale 2)'
    elif resultado == 'loss':
        stats['loss'] += 1
        emoji, status = '❌', 'LOSS'
    else:
        return texto

    return f"""{emoji} {status}
📊 Placar: 🟢{stats['win']}W 🟡{stats['gale1']}G1 🟠{stats['gale2']}G2 🔴{stats['loss']}L
🎯 Assertividade: {calcular_assertividade()}%"""

async def zerar_placar():
    global stats
    stats = {'win': 0, 'gale1': 0, 'gale2': 0, 'loss': 0}
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
    texto = event.message.text
    if not texto:
        return

    print(f"[{horario()}] 🔔 Nova mensagem detectada!")

    if eh_sinal(texto):
        dados = extrair_dados_sinal(texto)
        mensagem_enviar = formatar_sinal_quantum(dados)
        print(f"[{horario()}] 📊 SINAL | {dados['ativo']} | {dados['direcao']} | {dados['horario']}")
        try:
            await client.send_message(destino, mensagem_enviar)
            print(f"[{horario()}] ✅ Enviado!")
        except Exception as erro:
            print(f"[{horario()}] ❌ Erro: {erro}")
        print("=" * 40)
        return

    resultado = identificar_resultado(texto)
    if resultado:
        mensagem_enviar = formatar_resultado_quantum(texto)
        print(f"[{horario()}] 📊 RESULTADO: {resultado.upper()}")
        try:
            await client.send_message(destino, mensagem_enviar)
            print(f"[{horario()}] ✅ Enviado!")
        except Exception as erro:
            print(f"[{horario()}] ❌ Erro: {erro}")
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
    print("⏳ Aguardando...")
    asyncio.create_task(agendar_zeramento())
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Encerrado!")
