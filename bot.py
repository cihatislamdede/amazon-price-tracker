import logging
import os
from datetime import datetime

import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from dotenv import load_dotenv

import db as db

db.create_table()

handler = logging.FileHandler(filename="discord.log", encoding="utf-8")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler, logging.StreamHandler()],
    format="%(asctime)s:%(levelname)s:%(name)s: %(message)s",
)

load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])
CURRENCY = "TL"
headers = {
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0",
    "Cache-Control": "max-age=0",
}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)


def fetch_price_from_amazon(url):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        product_price = soup.find("span", class_="a-price-whole")
        if not product_price:
            return None
        product_price = product_price.get_text().split(",")[0]
        # remove dot from price
        product_price = product_price.replace(".", "")
        return float(product_price)
    except Exception as e:
        logging.error(e)
        return None


@bot.event
async def on_ready():
    await bot.tree.sync()
    logging.info(f"Bot Started --> {bot.user.name}")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="Amazon 💸")
    )
    await check_price.start()


@bot.tree.command(name="products", description="List all products")
async def products(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        products = db.get_all_products()
        embed = discord.Embed(title="Products")
        if not products:
            embed.description = "No products found"
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        for product in products:
            url = product[1]
            title = product[2]
            threshold_price = product[3]
            embed.add_field(
                name=title,
                value=f"URL: {url}\nThreshold Price: {threshold_price} {CURRENCY}",
                inline=False,
            )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        logging.error(e)
        await interaction.followup.send(e)


@bot.tree.command(name="add", description="Add a new product for tracking")
async def add(
    interaction: discord.Interaction, url: str, title: str, threshold_price: float
):
    if threshold_price <= 0:
        await interaction.response.send_message(
            "Threshold price must be greater than 0",
            ephemeral=True,
        )
        return
    await interaction.response.defer()
    try:
        await interaction.followup.send(f"Added `{title}` to the database :sunglasses:")
        db.insert_product(url, title, threshold_price, interaction.user.id)
    except Exception as e:
        logging.error(e)
        await interaction.followup.send(e)


@bot.tree.command(name="remove", description="Remove a product from tracking")
async def remove(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    options = []
    try:
        products = db.get_all_products()
        if not products:
            await interaction.followup.send("No products found", ephemeral=True)
            return
        for product in products:
            options.append(
                discord.SelectOption(
                    value=product[0],
                    description=f"Threshold Price: {product[3]} {CURRENCY}",
                    label=product[2],
                )
            )
        select = discord.ui.Select(
            placeholder="Select an product", max_values=1, min_values=1, options=options
        )

        async def callback(interaction):
            db.delete_product(select.values[0])
            await interaction.response.send_message(
                f"Removed from the database :sunglasses:", ephemeral=True
            )

        select.callback = callback
        view = discord.ui.View(timeout=30)
        view.add_item(select)
        await interaction.followup.send(
            "Select a product to remove", view=view, ephemeral=True
        )
    except Exception as e:
        logging.error(e)
        await interaction.followup.send(e)


@bot.tree.command(name="updateprice", description="Update a product's threshold price")
async def updateprice(interaction: discord.Interaction, new_price: float):
    if new_price <= 0:
        await interaction.response.send_message(
            "Threshold price must be greater than 0", ephemeral=True
        )
        return
    await interaction.response.defer(ephemeral=True)
    options = []
    try:
        products = db.get_all_products()
        if not products:
            await interaction.followup.send("No products found", ephemeral=True)
            return
        for product in products:
            options.append(
                discord.SelectOption(
                    value=product[0],
                    description=f"Threshold Price: {product[3]} {CURRENCY}",
                    label=product[2],
                )
            )
        select = discord.ui.Select(
            placeholder="Select an product", max_values=1, min_values=1, options=options
        )

        async def callback(interaction):
            db.update_threshold(select.values[0], new_price)
            await interaction.response.send_message(
                f"Updated threshold price :sunglasses:", ephemeral=True
            )

        select.callback = callback
        view = discord.ui.View(timeout=30)
        view.add_item(select)
        await interaction.followup.send(
            "Select a product to update", view=view, ephemeral=True
        )
    except Exception as e:
        logging.error(e)
        await interaction.followup.send(e)


@tasks.loop(minutes=20)
async def check_price():
    logging.info("Checking prices...")
    try:
        products = db.get_all_products()
        for product in products:
            product_id = product[0]
            url = product[1]
            title = product[2]
            threshold_price = product[3]
            user_id = product[4]
            price = fetch_price_from_amazon(url=url)
            if price is None:
                continue
            if price <= threshold_price:
                last_notification = db.get_latest_notification(product_id=product_id)
                if last_notification:
                    last_notification_price, last_notification_date = last_notification
                    created_at_datetime = datetime.strptime(
                        last_notification_date, "%Y-%m-%d %H:%M:%S"
                    )
                    time_difference = datetime.now() - created_at_datetime
                    if (
                        price >= last_notification_price
                        and time_difference.seconds < 60 * 60 * 24
                    ):
                        continue
                channel = bot.get_channel(CHANNEL_ID)
                embed = discord.Embed(title=title)
                embed.colour = discord.Colour.green()
                embed.url = url
                embed.description = f"Threshold: {threshold_price} {CURRENCY}\n New Price: {price} {CURRENCY}"
                await channel.send(f"<@{user_id}>", embed=embed)
                db.insert_notification(product_id=product_id, price=price)
                logging.info(f"New price found for {title} --> {price}")
    except Exception as e:
        logging.error(e)


bot.run(BOT_TOKEN, log_handler=handler, log_level=logging.INFO)
