import discord
import os
import time
import asyncio
from discord.ext import commands
from flask import Flask
from threading import Thread

# Set up bot prefix and permissions
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Allows bot to view server members
bot = commands.Bot(command_prefix="!", intents=intents)

# Load token from Secrets file on Replit
TOKEN = os.getenv("TOKEN")
ROLE_NAME = "| Vip"  # Change with the exact role name
REDEEM_CHANNEL_NAME = "🔑redeem"  # Channel name
CATEGORY_NAME = "redeem"  # Category name
last_used = {}  # Stores last time a user used the command
cooldown_time = 25  # Time in seconds before user can use !redeem again

# Set up Flask to keep the bot alive
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=3000)

def keep_alive():
    thread = Thread(target=run)
    thread.start()

# Event when the bot is ready
@bot.event
async def on_ready():
    print(f"\U0001F310 Bot is online as {bot.user}")

@bot.command()
async def redeem(ctx):
    # Check that the command is used in the correct channel
    channel = ctx.channel
    if channel.name != REDEEM_CHANNEL_NAME or channel.category.name != CATEGORY_NAME:
        await ctx.send(f"\U0001F6AB {ctx.author.mention}, please use the command in the {REDEEM_CHANNEL_NAME} channel.")
        return

    # Limit command usage to avoid spam (25-second cooldown)
    current_time = time.time()
    if ctx.author.id in last_used and current_time - last_used[ctx.author.id] < cooldown_time:
        time_left = cooldown_time - (current_time - last_used[ctx.author.id])
        await ctx.send(f"\U000023F3 {ctx.author.mention}, you must wait {int(time_left)} more seconds before using !redeem again.")
        return

    last_used[ctx.author.id] = current_time

    # Send a visible message only to the user
    message = await ctx.send(f"\U0001F4E9 {ctx.author.mention}, check your DMs for the redeem code.")
    await asyncio.sleep(5)  # Wait 5 seconds
    await message.delete()  # Delete the message

    # Send a DM to the user asking for the category
    try:
        await ctx.author.send("\U0001F381 **Redeem Request:** Please select a category from the following options: \n1. **Cheat** \n2. **Streaming** \n3. **Role** \n4. **Accounts**")
    except discord.Forbidden:
        await ctx.send(f"\U0001F6AB {ctx.author.mention}, I couldn't send you a DM. Please make sure you have direct messages enabled.")
        return

    def check(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    attempts = 2
    while attempts > 0:
        try:
            # Wait for the category selection from the user
            category_message = await bot.wait_for('message', check=check, timeout=300)
            category = category_message.content.lower()

            if category not in ['cheat', 'streaming', 'role', 'accounts']:
                attempts -= 1
                if attempts > 0:
                    await ctx.author.send(f"\U0000274C Invalid category. You have {attempts} attempts remaining.")
                else:
                    await ctx.author.send("\U0000274C You've used all your attempts. The redemption process has been canceled.")
                    return

                continue  # Ask again

            # Category selection valid, proceed with the product list
            if category == 'cheat':
                await ctx.author.send("**Cheat Products:**\n- Empty\n\nPlease enter your key for this category.")

            elif category == 'streaming':
                await ctx.author.send("**Streaming Products:**\n- Crunchyroll\n\nPlease enter your key for this category (start with `crly-`).")

            elif category == 'role':
                await ctx.author.send("**Role Products:**\n- VIP\n\nPlease enter your key for this category.")

            elif category == 'accounts':
                await ctx.author.send("**Accounts Products:**\n- Rockstar Key\n\nPlease enter your key for this category.")

            # Wait for the key from the user
            key_message = await bot.wait_for('message', check=check, timeout=300)
            key = key_message.content

            # Handle Crunchyroll keys (crly-)
            if category == 'streaming' and key.startswith('crly-'):
                # Check the key
                with open('streaming.txt', 'r') as f:
                    valid_keys = f.read().splitlines()

                if key in valid_keys:
                    valid_keys.remove(key)
                    with open('streaming.txt', 'w') as f:
                        f.write("\n".join(valid_keys))

                    # Log the redemption
                    with open("redeemed_log.txt", "a") as log:
                        log.write(f"{ctx.author.name} redeemed {key} from {category} at {time.ctime()}\n")

                    # Send confirmation and further instructions
                    await ctx.author.send(f"\U0001F389 **Success!** You've redeemed your Crunchyroll key `{key}`. Please do the following:\n\n"
                                           f"1. Contact @orpoby or open a ticket.\n"
                                           f"2. Send a screenshot of the redemption, including the code `{key}` and your Discord username.")

                else:
                    await ctx.author.send(f"\U0000274C Invalid key for Crunchyroll. Please try again with a valid key.")

            # Handle other categories
            elif category == 'role' and key in ['vip']:
                await ctx.author.send(f"\U0001F389 **Success!** You've redeemed the `{key}` role.")
            elif category == 'accounts' and key in ['rockstarkey']:
                await ctx.author.send(f"\U0001F389 **Success!** You've redeemed your Rockstar key `{key}`.")
            else:
                await ctx.author.send(f"\U0000274C Invalid key for {category} category. Please try again.")
                return

        except asyncio.TimeoutError:
            await ctx.author.send("\U000023F3 Timeout: The redemption process was canceled due to inactivity.")
            return
        except Exception as e:
            await ctx.author.send(f"\U0001F6AB Something went wrong: {e}")
            return

keep_alive()

# Run the Discord bot
bot.run(TOKEN)
