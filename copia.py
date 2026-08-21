#!/usr/bin/env python3
"""
⚛️ ESPELHO QUANTUM PRO - TELEGRAM
📡 Copia sinais de um canal para outro
🔄 Placar automático + zeramento diário
✅ Placar aparece APENAS nos resultados
✅ Resultado: apenas status + placar (sem ativo)
"""

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from datetime import datetime, timedelta
import re
import asyncio

# ==============================
# CONFIGURAÇÕES
# ==============================
api_id = 22453120
api_hash = "89826a4104518e9ed650cdb451ad8b53"

# String de sessão (autenticação sem interação)
SESSAO_STRING = "1AZWarzwBu7qTbV-h6_Xb7VoLwNt92OWiEq9HJH_3RW3RZbo4t7tQCJ48vt5HFdxwDh1tyrtpF7VMqnDLRRIz7Xt5g2rnyQWqZT2_H56BBHaaZITU39xJN3-bCLocsXDCs91TA8uzsvSV5U8QyRlIc5IaUcUuejXRdL5YyZJj3FPq9ojGyokhmgsnnH2D6LH_P03sucoAuCm4vOOEuvwxtX7E4iYSd62pcr5fADuxzErkJZ4uQHKTXZs0I9ytba43MSL27FUOfu7vRCfdFbBAZyHhdlGtSrgZ3TxtsDQERFbz8z46RJMVzq948QtWRIowyhNU9glZk5VUoUV5-VTUu6ZO2c_uebI="

origem = -1001824915491
destino = -1004483690234

client = TelegramClient(StringSession(SESSAO_STRING), api_id, api_hash)

# ==============================
# VARIÁVEIS DE ESTATÍSTICAS
# ==============================
stats = {
    'win': 0,
    'gale1': 0,
    'gale2': 0,
    'loss': 0
}

# ==============================
# FUNÇÕES
# ==============================

def horario():
    return datetime.now().strftime("%H:%M:%S")

def eh_sinal(texto):
    """Verifica se a mensagem é um sinal de entrada"""
    texto_lower = texto.lower()
    padroes = [
        r"par:", r"direção:", r"direcao:",
        r"horário da entrada:", r"horario da entrada:",
        r"expiração:", r"expiracao:",
        r"proteção", r"protecao",
        r"compra", r"venda", r"🟢", r"🔴"
    ]
    match = 0
    for padrao in padroes:
        if re.search(padrao, texto_lower):
            match += 1
    return match >= 3

def identificar_resultado(texto):
    """Identifica o tipo de resultado"""
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
    """Extrai os dados do sinal do formato específico do canal"""
    dados = {
        'ativo': 'STA/CKS',
        'direcao': 'CALL',
        'horario': '',
        'expiracao': 'M1',
        'protecao1': '',
        'protecao2': ''
    }
    linhas = texto.split('\n')
    for linha in linhas:
        linha_limpa = linha.replace('*', '').replace('_', '').strip()
        
        if 'par:' in linha_limpa.lower():
            match = re.search(r'[Pp]ar:\s*([^\s\n]+)', linha_limpa)
            if match:
                dados['ativo'] = match.group(1).strip()
                
        if 'direção:' in linha_limpa.lower() or 'direcao:' in linha_limpa.lower():
            if 'compra' in linha_limpa.lower() or '🟢' in linha_limpa:
                dados['direcao'] = 'CALL'
            elif 'venda' in linha_limpa.lower() or '🔴' in linha_limpa:
                dados['direcao'] = 'PUT'
                
        if 'horário da entrada:' in linha_limpa.lower() or 'horario da entrada:' in linha_limpa.lower():
            match = re.search(r'(\d{2}:\d{2})', linha_limpa)
            if match:
                dados['horario'] = match.group(1)
                
        if 'expiração:' in linha_limpa.lower() or 'expiracao:' in linha_limpa.lower():
            match = re.search(r'(\d+)[Mm]in', linha_limpa)
            if match:
                dados['expiracao'] = f"M{match.group(1)}"
                
        if 'proteção 1º:' in linha_limpa.lower() or 'protecao 1º:' in linha_limpa.lower():
            match = re.search(r'(\d{2}:\d{2})', linha_limpa)
            if match:
                dados['protecao1'] = match.group(1)
                
        if 'proteção 2º:' in linha_limpa.lower() or 'protecao 2º:' in linha_limpa.lower():
            match = re.search(r'(\d{2}:\d{2})', linha_limpa)
            if match:
                dados['protecao2'] = match.group(1)
                
    if not dados['horario']:
        dados['horario'] = datetime.now().strftime("%H:%M")
    return dados

def calcular_assertividade():
    """Calcula a assertividade"""
    total = stats['win'] + stats['gale1'] + stats['gale2'] + stats['loss']
    if total == 0:
        return 0.0
    return round(((stats['win'] + stats['gale1'] + stats['gale2']) / total) * 100, 1)

def formatar_sinal_quantum(dados):
    """Formata o sinal no padrão Quantum Pro (SEM PLACAR)"""
    emoji_direcao = '🟢' if dados['direcao'] == 'CALL' else '🔴'
    protecoes = ""
    if dados['protecao1']:
        protecoes = f"\n🛡️ Proteção 1: {dados['protecao1']}"
    if dados['protecao2']:
        protecoes += f"\n🛡️ Proteção 2: {dados['protecao2']}"
    
    mensagem = f"""⚛️ SINAL QUANTUM PRO ⚛️

⏰ Horário: {dados['horario']}
💰 Ativo: {dados['ativo']}
📈 Direção: {dados['direcao']} {emoji_direcao}
⌛️ Expiração: {dados['expiracao']}{protecoes}

⚠️ Entrar somente no horário marcado.
🔄 2 recuperação (Gale 2)!"""
    return mensagem

def formatar_resultado_quantum(texto):
    """Formata o resultado no padrão Quantum Pro (APENAS resultado + placar)"""
    resultado = identificar_resultado(texto)
    
    if resultado == 'win':
        stats['win'] += 1
        emoji = '✅'
        status = 'WIN'
    elif resultado == 'gale1':
        stats['gale1'] += 1
        emoji = '✅'
        status = 'WIN (Gale 1)'
    elif resultado == 'gale2':
        stats['gale2'] += 1
        emoji = '✅'
        status = 'WIN (Gale 2)'
    elif resultado == 'loss':
        stats['loss'] += 1
        emoji = '❌'
        status = 'LOSS'
    else:
        return texto
    
    mensagem = f"""{emoji} {status}
📊 Placar: 🟢{stats['win']}W 🟡{stats['gale1']}G1 🟠{stats['gale2']}G2 🔴{stats['loss']}L
🎯 Assertividade: {calcular_assertividade()}%"""
    return mensagem

async def zerar_placar():
    """Zera as estatísticas e envia mensagem de aviso"""
    global stats
    stats = {'win': 0, 'gale1': 0, 'gale2': 0, 'loss': 0}
    print(f"[{horario()}] 🔄 PLACAR ZERADO - NOVO DIA!")
    try:
        mensagem = """🔄 PLACAR ZERADO - NOVO DIA!
📊 Estatísticas reiniciadas à meia-noite.

⚛️ QUANTUM PRO PRONTO PARA OPERAR! ⚛️"""
        await client.send_message(destino, mensagem)
        print(f"[{horario()}] ✅ Mensagem de zeramento enviada!")
    except Exception as e:
        print(f"[{horario()}] ❌ Erro ao enviar mensagem de zeramento: {e}")

async def agendar_zeramento():
    """Agenda o zeramento do placar para meia-noite"""
    while True:
        agora = datetime.now()
        meia_noite = agora.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        tempo_ate_meia_noite = (meia_noite - agora).total_seconds()
        await asyncio.sleep(tempo_ate_meia_noite)
        await zerar_placar()

@client.on(events.NewMessage(chats=origem))
async def processar_mensagem(event):
    texto = event.message.text
    if not texto:
        return
    
    print(f"[{horario()}] 🔔 Nova mensagem detectada!")
    
    # ===== VERIFICA SE É SINAL =====
    if eh_sinal(texto):
        print(f"[{horario()}] 📊 SINAL identificado!")
        dados = extrair_dados_sinal(texto)
        mensagem_enviar = formatar_sinal_quantum(dados)
        print(f"[{horario()}] 📤 Ativo: {dados['ativo']} | Direção: {dados['direcao']} | Horário: {dados['horario']}")
        try:
            await client.send_message(destino, mensagem_enviar)
            print(f"[{horario()}] ✅ Mensagem enviada com sucesso!")
        except Exception as erro:
            print(f"[{horario()}] ❌ Erro ao enviar mensagem: {erro}")
        print("=" * 40)
        return
    
    # ===== VERIFICA SE É RESULTADO =====
    resultado = identificar_resultado(texto)
    if resultado:
        print(f"[{horario()}] 📊 RESULTADO identificado: {resultado.upper()}")
        mensagem_enviar = formatar_resultado_quantum(texto)
        print(f"[{horario()}] 📤 Resultado: {resultado.upper()}")
        print(f"[{horario()}] 📊 Placar: 🟢{stats['win']}W 🟡{stats['gale1']}G1 🟠{stats['gale2']}G2 🔴{stats['loss']}L")
        try:
            await client.send_message(destino, mensagem_enviar)
            print(f"[{horario()}] ✅ Mensagem enviada com sucesso!")
        except Exception as erro:
            print(f"[{horario()}] ❌ Erro ao enviar mensagem: {erro}")
        print("=" * 40)
        return
    
    # ===== SE NÃO É SINAL NEM RESULTADO, IGNORA =====
    print(f"[{horario()}] 📝 Mensagem ignorada (não é sinal nem resultado)")
    print("=" * 40)

async def main():
    print("=" * 50)
    print("     ⚛️ ESPELHO QUANTUM PRO ⚛️")
    print("=" * 50)
    
    await client.start()
    print("✅ Conectado ao Telegram")
    print(f"📡 Origem: {origem}")
    print(f"📡 Destino: {destino}")
    print("⏳ Aguardando novas mensagens...")
    print("=" * 50)
    
    # Inicia a tarefa de zeramento
    asyncio.create_task(agendar_zeramento())
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("📊 RESUMO FINAL")
        print("=" * 50)
        print(f"✅ WIN (sem gale): {stats['win']}")
        print(f"🟡 GALE 1:         {stats['gale1']}")
        print(f"🟠 GALE 2:         {stats['gale2']}")
        print(f"❌ LOSS:           {stats['loss']}")
        print(f"📊 Total:          {stats['win'] + stats['gale1'] + stats['gale2'] + stats['loss']}")
        print(f"🎯 Assertividade:  {calcular_assertividade()}%")
        print("=" * 50)
        print("👋 Bot encerrado!")
