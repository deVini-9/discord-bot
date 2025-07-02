import discord
from discord.ext import commands
import sqlite3
import random

# --- Configurações do Bot ---
# Substitua 'SEU_TOKEN_DO_BOT_AQUI' pelo token do seu bot Discord.
# Você pode obter o token na página de desenvolvedor do Discord (Discord Developer Portal).
TOKEN = 'SEU_TOKEN_DO_BOT_AQUI'

# Define as intenções (intents) que o bot usará.
# É importante habilitar as intenções necessárias no Discord Developer Portal.
# Para comandos de barra (/), você geralmente precisa de 'message_content' se for ler o conteúdo de mensagens.
# Para este exemplo, 'default' é suficiente para comandos de barra.
intents = discord.Intents.default()
# Se você for usar comandos que leem o conteúdo das mensagens (ex: !roll 1d20),
# descomente a linha abaixo e habilite no portal do desenvolvedor.
# intents.message_content = True

# Cria uma instância do bot com as intenções definidas.
# command_prefix é usado para comandos prefixados (ex: !roll), mas não é estritamente necessário para comandos de barra.
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Configuração do Banco de Dados SQLite ---
# Conecta-se ao banco de dados SQLite. Se o arquivo não existir, ele será criado.
conn = sqlite3.connect('foundry_lite.db')
cursor = conn.cursor()

# Cria uma tabela de exemplo para fichas de personagem (apenas para demonstração de estrutura).
# Esta tabela não é usada diretamente nos comandos atuais, mas serve como base.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        character_name TEXT NOT NULL,
        hp INTEGER,
        strength INTEGER,
        dexterity INTEGER,
        constitution INTEGER,
        intelligence INTEGER,
        wisdom INTEGER,
        charisma INTEGER
    )
''')
conn.commit()  # Salva as mudanças no banco de dados

# --- Eventos do Bot ---


@bot.event
async def on_ready():
    """
    Este evento é disparado quando o bot está pronto e conectado ao Discord.
    """
    print(f'Bot conectado como {bot.user.name} ({bot.user.id})')
    print('Pronto para rolar os dados e gerenciar a aventura!')


@bot.event
async def on_command_error(ctx, error):
    """
    Tratamento de erros para comandos.
    """
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Comando não encontrado. Tente `/roll` para rolar dados.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Erro: Argumento faltando. Uso correto: `{ctx.command.usage}`")
    else:
        print(f"Ocorreu um erro: {error}")
        await ctx.send("Ocorreu um erro ao executar o comando. Por favor, tente novamente mais tarde.")

# --- Comandos do Bot ---


@bot.tree.command(name="roll", description="Rola dados no formato XdY (+/- Z). Ex: /roll 1d20+5")
async def roll(interaction: discord.Interaction, formula: str):
    """
    Comando para rolar dados.
    Suporta formatos como '1d20', '2d6+3', '1d10-2'.
    """
    await interaction.response.defer()  # Defer a resposta para que o bot tenha mais tempo para processar

    try:
        # Remove espaços em branco da fórmula
        formula = formula.replace(" ", "").lower()

        # Separa a parte dos dados da parte do modificador
        modificador = 0
        if '+' in formula:
            partes = formula.split('+')
            formula_dados = partes[0]
            modificador = int(partes[1])
        elif '-' in formula:
            partes = formula.split('-')
            formula_dados = partes[0]
            modificador = -int(partes[1])
        else:
            formula_dados = formula

        # Separa o número de dados e o tipo de dado (ex: 1d20 -> num_dados=1, tipo_dado=20)
        if 'd' not in formula_dados:
            await interaction.followup.send("Formato inválido. Use XdY (ex: 1d20, 2d6+3).")
            return

        num_dados_str, tipo_dado_str = formula_dados.split('d')
        # Se não especificar, assume 1 dado
        num_dados = int(num_dados_str) if num_dados_str else 1
        tipo_dado = int(tipo_dado_str)

        if num_dados <= 0 or tipo_dado <= 0:
            await interaction.followup.send("O número de dados e o tipo de dado devem ser maiores que zero.")
            return

        resultados_individuais = []
        soma_dados = 0
        for _ in range(num_dados):
            resultado = random.randint(1, tipo_dado)
            resultados_individuais.append(resultado)
            soma_dados += resultado

        resultado_final = soma_dados + modificador

        # Cria a mensagem de resposta
        mensagem = (
            f"**{interaction.user.display_name}** rolou `{formula}`:\n"
            f"Resultados: {', '.join(map(str, resultados_individuais))}\n"
            f"Soma dos dados: {soma_dados}"
        )
        if modificador != 0:
            mensagem += f" {'+' if modificador > 0 else '-'} {abs(modificador)}"
        mensagem += f"\n**Resultado Final: {resultado_final}**"

        await interaction.followup.send(mensagem)

    except ValueError:
        await interaction.followup.send("Formato de rolagem inválido. Use XdY (+/- Z). Ex: `/roll 1d20+5`")
    except Exception as e:
        print(f"Erro ao rolar dados: {e}")
        await interaction.followup.send("Ocorreu um erro ao processar sua rolagem. Verifique a fórmula e tente novamente.")

# --- Sincronização de Comandos de Barra ---


@bot.command()
async def sync(ctx):
    """
    Comando para sincronizar os comandos de barra (/), útil durante o desenvolvimento.
    Apenas para o dono do bot.
    """
    if ctx.author.id == bot.owner_id:  # Substitua bot.owner_id pelo seu ID de usuário Discord para maior segurança
        await bot.tree.sync()
        await ctx.send("Comandos de barra sincronizados!")
    else:
        await ctx.send("Você não tem permissão para usar este comando.")

# --- Execução do Bot ---
# Certifique-se de que o token do bot está definido antes de rodar.
if TOKEN == 'SEU_TOKEN_DO_BOT_AQUI':
    print("ERRO: Por favor, substitua 'SEU_TOKEN_DO_BOT_AQUI' pelo token real do seu bot Discord.")
else:
    bot.run(TOKEN)
