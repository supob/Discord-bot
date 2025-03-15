import discord
import os
import time
import asyncio
from discord.ext import commands
from flask import Flask
from threading import Thread

# Configura il prefisso e i permessi del bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Permette di vedere i membri del server
bot = commands.Bot(command_prefix="!", intents=intents)

# Carica il token dal file di Secrets su Replit
TOKEN = os.getenv("TOKEN")
ROLE_NAME = "| Vip"  # Cambia con il nome esatto del ruolo
REDEEM_CHANNEL_NAME = "🔑redeem"  # Il nome del canale
CATEGORY_NAME = "redeem"  # Il nome della categoria
last_used = {}  # Memorizza l'ultima volta che un utente ha usato il comando

# Configura Flask per mantenere il bot attivo
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=3000)

def keep_alive():
    thread = Thread(target=run)
    thread.start()

# Evento quando il bot è pronto
@bot.event
async def on_ready():
    print(f"\U0001F310 Bot is online as {bot.user}")

@bot.command()
async def redeem(ctx):
    # Controlla che il comando sia stato eseguito nel canale giusto
    channel = ctx.channel
    if channel.name != REDEEM_CHANNEL_NAME or channel.category.name != CATEGORY_NAME:
        await ctx.send(f"\U0001F6AB {ctx.author.mention}, please use the command in the {REDEEM_CHANNEL_NAME} channel.")
        return

    # Limita la ripetizione del comando per evitare lo spam
    current_time = time.time()
    if ctx.author.id in last_used and current_time - last_used[ctx.author.id] < 120:
        return

    last_used[ctx.author.id] = current_time

    # Invia un messaggio visibile solo all'utente
    message = await ctx.send(f"\U0001F4E9 {ctx.author.mention}, controlla i tuoi DM per il codice di redeem.")
    await asyncio.sleep(5)  # Aspetta 5 secondi
    await message.delete()  # Cancella il messaggio

    # Invia un DM all'utente per richiedere il codice
    try:
        await ctx.author.send("\U0001F381 **Redeem Request:** Enter your redeem code here. You have 3 attempts and 5 minutes to complete this process.")
    except discord.Forbidden:
        await ctx.send(f"\U0001F6AB {ctx.author.mention}, I couldn't send you a DM. Please enable direct messages.")
        return

    def check(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    attempts = 3
    while attempts > 0:
        try:
            # Attende il codice dall'utente
            code_message = await bot.wait_for('message', check=check, timeout=300)
            code = code_message.content

            # Legge i codici dal file
            with open("codes.txt", "r") as f:
                codes = f.read().splitlines()

            # Verifica se il codice è valido
            if code in codes:
                # Rimuove il codice dalla lista
                codes.remove(code)
                with open("codes.txt", "w") as f:
                    f.write("\n".join(codes))

                # Salva chi ha riscattato il codice
                with open("redeemed_log.txt", "a") as log:
                    log.write(f"{ctx.author.name} redeemed {code} at {time.ctime()}\n")

                # Assegna il ruolo all'utente
                role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)
                if role:
                    await ctx.author.add_roles(role)
                    success_message = (
                        f"\U0001F389 **Redeem Successful!**\n"
                        f"You've successfully redeemed your code and received the **{ROLE_NAME}** role. Enjoy your new privileges!"
                    )
                    await ctx.author.send(success_message)
                else:
                    await ctx.author.send("\U0001F6AB Error: Role not found!")
                return
            else:
                attempts -= 1
                if attempts > 0:
                    await ctx.author.send(f"\U0000274C Invalid code. You have {attempts} attempts left.")
                else:
                    await ctx.author.send("\U0000274C You've used all your attempts. The redeem request has been canceled.")
                    return

        except asyncio.TimeoutError:
            await ctx.author.send("\U000023F3 Your redeem request has been canceled due to inactivity.")
            return
        except Exception as e:
            await ctx.author.send("\U0001F6AB An unexpected error occurred. Please try again later.")
            return

keep_alive()

# Esegui il bot Discord
bot.run(TOKEN)
