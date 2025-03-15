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

    # Limit command usage to avoid spam
    current_time = time.time()
    if ctx.author.id in last_used and current_time - last_used[ctx.author.id] < 120:
        return

    last_used[ctx.author.id] = current_time

    # Send a visible message only to the user
    message = await ctx.send(f"\U0001F4E9 {ctx.author.mention}, check your DMs for the redeem code.")
    await asyncio.sleep(5)  # Wait 5 seconds
    await message.delete()  # Delete the message

    # Send a DM to the user asking for the category selection
    try:
        await ctx.author.send("🎯 **Category Selection:** Please choose a category.\n\n1. Cheat\n2. Streaming\n3. Role\n4. Accounts")
    except discord.Forbidden:
        await ctx.send(f"\U0001F6AB {ctx.author.mention}, I couldn't send you a DM. Please make sure you have direct messages enabled.")
        return

    def check_category(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    category_choice = None
    while not category_choice:
        try:
            category_message = await bot.wait_for('message', check=check_category, timeout=300)
            category_choice = category_message.content.lower()

            if category_choice not in ['cheat', 'streaming', 'role', 'accounts']:
                await ctx.author.send("❌ Invalid category. Please select from the following: Cheat, Streaming, Role, Accounts.")
                category_choice = None
        except asyncio.TimeoutError:
            await ctx.author.send("\U000023F3 Timeout: The category selection was canceled due to inactivity.")
            return

    # Ask for the key after category selection
    await ctx.author.send(f"🔑 **You chose the {category_choice} category.** Please enter the key associated with this category.")

    attempts = 3
    while attempts > 0:
        try:
            key_message = await bot.wait_for('message', check=check_category, timeout=300)
            key = key_message.content.strip()

            # Check the selected category file for the key
            category_file = f"{category_choice}.txt"
            category_found = False

            # Check if the file exists
            if os.path.exists(category_file):
                with open(category_file, "r") as f:
                    keys = f.read().splitlines()

                # Check if the key is valid
                if key in keys:
                    category_found = True
                    keys.remove(key)
                    with open(category_file, "w") as f:
                        f.write("\n".join(keys))

                    # Log who redeemed the key
                    with open("redeemed_log.txt", "a") as log:
                        log.write(f"{ctx.author.name} redeemed key {key} from {category_choice} at {time.ctime()}\n")

                    # Assign the role to the user
                    role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)
                    if role:
                        await ctx.author.add_roles(role)
                        success_message = (
                            f"\U0001F389 **Success!**\n"
                            f"Your key has been successfully redeemed and you've been granted the **{ROLE_NAME}** role. Enjoy!"
                        )
                        await ctx.author.send(success_message)
                    else:
                        await ctx.author.send("\U0001F6AB Error: Couldn't find the role.")
                    return

            if not category_found:
                # Try to find the key in other categories
                for other_category in ['cheat', 'streaming', 'role', 'accounts']:
                    if other_category != category_choice and os.path.exists(f"{other_category}.txt"):
                        with open(f"{other_category}.txt", "r") as f:
                            other_keys = f.read().splitlines()

                        if key in other_keys:
                            await ctx.author.send(f"❌ Incorrect category. The key you entered belongs to the {other_category} category.")
                            return

                attempts -= 1
                if attempts > 0:
                    await ctx.author.send(f"❌ Invalid key. You have {attempts} attempts remaining.")
                else:
                    await ctx.author.send("❌ You've used all your attempts. The redemption process has been canceled.")
                    return

        except asyncio.TimeoutError:
            await ctx.author.send("\U000023F3 Timeout: The redemption process was canceled due to inactivity.")
            return
        except Exception as e:
            await ctx.author.send("\U0001F6AB Something went wrong. Please try again later.")
            return

keep_alive()

# Run the Discord bot
bot.run(TOKEN)
