import discord
import os
import asyncio
import ssl
import certifi
import sys
from openai import OpenAI
from dotenv import load_dotenv
import aiohttp

# Carrega variáveis do .env
load_dotenv()

# Solução alternativa para o problema de SSL
# ========================================
class CustomClientSession(aiohttp.ClientSession):
    def __init__(self, *args, **kwargs):
        # Cria um contexto SSL que não verifica certificados
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        super().__init__(*args, connector=aiohttp.TCPConnector(ssl=ssl_context), **kwargs)

# Sobrescreve a sessão HTTP padrão do discord.py
discord.http._session = CustomClientSession()
# ========================================

# Configura o bot do Discord
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Configura o cliente da DeepSeek API
try:
    deepseek_client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    print("✅ Cliente DeepSeek configurado com sucesso")
except Exception as e:
    print(f"❌ Erro ao configurar cliente DeepSeek: {e}")
    sys.exit(1)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')
    try:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="!ai ou @mencione"
            )
        )
        print("✅ Presença do bot atualizada")
    except Exception as e:
        print(f"⚠️ Erro ao definir presença: {e}")

@bot.event
async def on_message(message):
    # Ignora mensagens de bots
    if message.author.bot:
        return

    # Verifica se o bot foi mencionado ou se é um comando !ai
    bot_mentioned = bot.user in message.mentions
    is_command = message.content.startswith('!ai ')
    
    if not (bot_mentioned or is_command):
        return

    try:
        # Limpa o conteúdo da mensagem
        if bot_mentioned:
            query = message.content.replace(f'<@{bot.user.id}>', '').strip()
        else:  # is_command
            query = message.content[4:].strip()

        # Verifica se há texto após a menção/comando
        if not query:
            await message.reply("Olá! Como posso ajudar? Por favor, faça sua pergunta após a menção ou comando.", mention_author=False)
            return

        print(f"📩 Recebida pergunta de {message.author}: {query[:50]}...")
        
        # Envia mensagem de "digitando"
        async with message.channel.typing():
            # Consulta a API da DeepSeek
            try:
                response = await asyncio.to_thread(
                    deepseek_client.chat.completions.create,
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system", 
                            "content": "Você é um assistente de IA em um servidor Discord. Seja conciso e útil."
                        },
                        {"role": "user", "content": query}
                    ],
                    max_tokens=2000,
                    stream=False
                )
                answer = response.choices[0].message.content
                print(f"🤖 Resposta gerada: {answer[:50]}...")
            except Exception as e:
                print(f"⚠️ Erro na API DeepSeek: {e}")
                await message.reply("❌ Ocorreu um erro ao processar sua solicitação com a API.", mention_author=False)
                return
        
        # Envia a resposta formatada
        await send_long_message(message, answer)

    except Exception as e:
        print(f"⚠️ Erro geral: {e}")
        await message.reply(f"❌ Ocorreu um erro inesperado: {str(e)}", mention_author=False)

async def send_long_message(original_message, content):
    """Envia mensagens longas divididas em partes"""
    try:
        if len(content) <= 2000:
            await original_message.reply(content, mention_author=False)
            return
        
        # Divide a mensagem longa
        parts = []
        while content:
            if len(content) > 2000:
                part = content[:2000]
                # Encontra o último espaço para não cortar palavras
                last_space = part.rfind(' ')
                if last_space > 0:
                    part = content[:last_space]
                parts.append(part)
                content = content[len(part):].lstrip()
            else:
                parts.append(content)
                content = ""
        
        # Envia as partes
        for i, part in enumerate(parts):
            if i == 0:
                await original_message.reply(f"**Resposta longa (parte {i+1}/{len(parts)}):**\n{part}", mention_author=False)
            else:
                await original_message.channel.send(f"**Continuação (parte {i+1}/{len(parts)}):**\n{part}")
    except Exception as e:
        print(f"⚠️ Erro ao enviar mensagem longa: {e}")
        await original_message.reply("❌ Ocorreu um erro ao enviar a resposta.", mention_author=False)

if __name__ == "__main__":
    # Verifica se as variáveis de ambiente estão configuradas
    required_vars = ["DISCORD_BOT_TOKEN", "DEEPSEEK_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        print("Certifique-se de ter um arquivo .env com essas variáveis")
        sys.exit(1)
    
    print("🔄 Iniciando bot...")
    print(f"Versão do Python: {sys.version}")
    print(f"Versão discord.py: {discord.__version__}")
    
    try:
        # Inicia o bot
        bot.run(os.getenv("DISCORD_BOT_TOKEN"))
    except Exception as e:
        print(f"❌ Erro fatal ao iniciar bot: {e}")
        print("Soluções possíveis:")
        print("1. Verifique seu token do Discord")
        print("2. Tente novamente mais tarde (servidores Discord podem estar com problemas)")
        print("3. Atualize o Windows e seus certificados raiz")