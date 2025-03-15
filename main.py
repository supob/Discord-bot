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
                await ctx.author.send("**Cheat Products:**\n- Empty")
                await asyncio.sleep(5)  # Wait 5 seconds before closing the ticket
                await ctx.author.send("Closing the ticket now.")
                # Logic for closing the ticket here
                return  # End the function, close ticket

            elif category == 'streaming':
                await ctx.author.send("**Streaming Products:**\n- Crunchyroll")
            elif category == 'role':
                await ctx.author.send("**Role Products:**\n- VIP")
            elif category == 'accounts':
                await ctx.author.send("**Accounts Products:**\n- Rockstar Key")

            # Ask for the key after displaying the products
            await ctx.author.send("Please enter the key for this category.")

            # Wait for the key from the user
            key_message = await bot.wait_for('message', check=check, timeout=300)
            key = key_message.content

            # Check the category-specific text files for the key
            file_name = f"{category}.txt"
            try:
                with open(file_name, "r") as f:
                    keys = f.read().splitlines()

                if key in keys:
                    # Key is valid, remove it from the file and log
                    keys.remove(key)
                    with open(file_name, "w") as f:
                        f.write("\n".join(keys))

                    # Log the redemption
                    with open("redeemed_log.txt", "a") as log:
                        log.write(f"{ctx.author.name} redeemed {key} from {category} at {time.ctime()}\n")

                    # Assign the role to the user (if applicable)
                    role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)
                    if role:
                        await ctx.author.add_roles(role)
                        await ctx.author.send(f"\U0001F389 **Success!** Your code has been successfully redeemed!")
                    else:
                        await ctx.author.send("\U0001F6AB Error: Couldn't find the role.")
                else:
                    await ctx.author.send(f"\U0000274C Invalid key for {category} category. Please try again.")
                    return

            except FileNotFoundError:
                await ctx.author.send(f"\U0001F6AB Error: No valid file for {category}.")
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
