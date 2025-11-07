import os
import pathlib
import re
import shutil
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from constants import ADMINS, ALLOWED_CHANNELS
from db.db import get_database_handler
from a_collections.a_collection import get_collections, get_collection, collections
from image.image import get_collection_picture

token = os.getenv("DISCORD_PHOTOCARD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
db_handler = get_database_handler()


def is_admin(interaction: discord.Interaction) -> bool:
    return interaction.user.id in ADMINS


def is_allowed_channel(interaction: discord.Interaction) -> bool:
    return interaction.channel_id in ALLOWED_CHANNELS


def sanitize_name(name: str) -> Optional[str]:
    """Sanitize collection/photocard names to prevent path traversal attacks."""
    name = name.strip().replace(" ", "_")
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return None
    if name.startswith(".") or name.startswith("_"):
        return None
    return name


def reload_collections():
    """Safely reload the collection registry."""
    collections._collection_registry.clear()
    collections.__init__()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.tree.command(name="collections", description="List all available photocard collections")
async def collections_command(interaction: discord.Interaction):
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in specific channels.", ephemeral=True)
        return
    
    collection_list = get_collections()
    if not collection_list:
        await interaction.response.send_message("No collections available yet.")
        return
    
    msg = ["**Available Collections:**"]
    for collection in collection_list:
        col = get_collection(collection)
        if col:
            msg.append(f"• **{collection}** ({col.num_items} cards)")
    
    await interaction.response.send_message("\n".join(msg))


@bot.tree.command(name="view", description="View your collected cards from a collection")
async def view_command(interaction: discord.Interaction, collection: str):
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in specific channels.", ephemeral=True)
        return
    
    col = get_collection(collection)
    if not col:
        await interaction.response.send_message(f"Collection '{collection}' does not exist.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    owned_images = db_handler.get_owned_images(interaction.user.id, collection)
    img_bytes = get_collection_picture(col, owned_images)
    
    file = discord.File(img_bytes, filename="collection.jpg")
    await interaction.followup.send(
        f"You have collected {len(owned_images)}/{col.num_items} cards in '{col.name}'",
        file=file
    )


@bot.tree.command(name="preview", description="[Admin] Preview all cards in a collection")
async def preview_command(interaction: discord.Interaction, collection: str):
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in specific channels.", ephemeral=True)
        return
    
    if not is_admin(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    col = get_collection(collection)
    if not col:
        await interaction.response.send_message(f"Collection '{collection}' does not exist.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    owned_images = list(range(1, col.num_items + 1))
    img_bytes = get_collection_picture(col, owned_images)
    
    file = discord.File(img_bytes, filename="collection.jpg")
    await interaction.followup.send(f"Preview of '{col.name}' collection", file=file)


@bot.tree.command(name="unlock", description="[Admin] Unlock cards for a user")
async def unlock_command(interaction: discord.Interaction, collection: str, card_numbers: str, user: discord.Member):
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in specific channels.", ephemeral=True)
        return
    
    if not is_admin(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    col = get_collection(collection)
    if not col:
        await interaction.response.send_message(f"Collection '{collection}' does not exist.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    card_ids = card_numbers.split(",")
    messages = []
    
    for card_id in card_ids:
        try:
            card_num = int(card_id.strip())
            if card_num < 1 or card_num > col.num_items:
                messages.append(f"Card {card_num} is out of range (1-{col.num_items})")
                continue
            db_handler.unlock_image(user.id, collection, card_num)
            messages.append(f"Unlocked card {card_num}")
        except ValueError:
            messages.append(f"'{card_id}' is not a valid number")
    
    owned_images = db_handler.get_owned_images(user.id, collection)
    img_bytes = get_collection_picture(col, owned_images)
    
    file = discord.File(img_bytes, filename="collection.jpg")
    await interaction.followup.send(
        f"**Updated {user.display_name}'s collection:**\n" + "\n".join(messages),
        file=file
    )


@bot.tree.command(name="lock", description="[Admin] Lock/remove cards from a user")
async def lock_command(interaction: discord.Interaction, collection: str, card_numbers: str, user: discord.Member):
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in specific channels.", ephemeral=True)
        return
    
    if not is_admin(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    col = get_collection(collection)
    if not col:
        await interaction.response.send_message(f"Collection '{collection}' does not exist.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    card_ids = card_numbers.split(",")
    messages = []
    
    for card_id in card_ids:
        try:
            card_num = int(card_id.strip())
            db_handler.lock_image(user.id, collection, card_num)
            messages.append(f"Locked card {card_num}")
        except ValueError:
            messages.append(f"'{card_id}' is not a valid number")
    
    owned_images = db_handler.get_owned_images(user.id, collection)
    img_bytes = get_collection_picture(col, owned_images)
    
    file = discord.File(img_bytes, filename="collection.jpg")
    await interaction.followup.send(
        f"**Updated {user.display_name}'s collection:**\n" + "\n".join(messages),
        file=file
    )


@bot.tree.command(name="add_collection", description="[Admin] Create a new photocard collection")
async def add_collection_command(interaction: discord.Interaction, collection_name: str):
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in specific channels.", ephemeral=True)
        return
    
    if not is_admin(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    sanitized_name = sanitize_name(collection_name)
    if not sanitized_name:
        await interaction.response.send_message(
            "Invalid collection name. Use only letters, numbers, hyphens, and underscores.",
            ephemeral=True
        )
        return
    
    if get_collection(sanitized_name):
        await interaction.response.send_message(f"Collection '{sanitized_name}' already exists!", ephemeral=True)
        return
    
    files_dir = pathlib.Path(__file__).resolve().parent / "a_collections" / "files"
    new_collection_dir = files_dir / sanitized_name
    
    try:
        new_collection_dir.mkdir(parents=True, exist_ok=False)
        
        preview_path = new_collection_dir / "preview.jpg"
        with open(preview_path, 'w') as f:
            pass
        
        reload_collections()
        
        await interaction.response.send_message(
            f"✅ Created collection '{sanitized_name}'!\n"
            f"Now use `/add_photocard` to add cards to this collection."
        )
    except FileExistsError:
        await interaction.response.send_message(f"Collection directory already exists!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error creating collection: {e}", ephemeral=True)


@bot.tree.command(name="add_photocard", description="[Admin] Add a photocard to a collection")
async def add_photocard_command(
    interaction: discord.Interaction,
    collection: str,
    photocard_name: str,
    image: discord.Attachment
):
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in specific channels.", ephemeral=True)
        return
    
    if not is_admin(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    if not image.content_type or not image.content_type.startswith("image/"):
        await interaction.response.send_message("Please upload a valid image file (PNG, JPG, JPEG).", ephemeral=True)
        return
    
    file_extension = image.filename.split(".")[-1].lower()
    if file_extension not in ["png", "jpg", "jpeg"]:
        await interaction.response.send_message("Image must be PNG, JPG, or JPEG format.", ephemeral=True)
        return
    
    sanitized_collection = sanitize_name(collection)
    if not sanitized_collection:
        await interaction.response.send_message("Invalid collection name.", ephemeral=True)
        return
    
    sanitized_photocard = sanitize_name(photocard_name)
    if not sanitized_photocard:
        await interaction.response.send_message(
            "Invalid photocard name. Use only letters, numbers, hyphens, and underscores.",
            ephemeral=True
        )
        return
    
    await interaction.response.defer(ephemeral=True)
    
    files_dir = pathlib.Path(__file__).resolve().parent / "a_collections" / "files"
    collection_dir = files_dir / sanitized_collection
    
    if not collection_dir.exists():
        await interaction.followup.send(
            f"Collection '{sanitized_collection}' does not exist. Create it first with `/add_collection`.",
            ephemeral=True
        )
        return
    
    save_path = collection_dir / f"{sanitized_photocard}.{file_extension}"
    
    if save_path.exists():
        await interaction.followup.send(
            f"A photocard with name '{sanitized_photocard}' already exists in this collection!",
            ephemeral=True
        )
        return
    
    try:
        await image.save(save_path)
        reload_collections()
        
        col = get_collection(sanitized_collection)
        if col:
            await interaction.followup.send(
                f"✅ Added photocard '{sanitized_photocard}' to collection '{sanitized_collection}'!\n"
                f"Collection now has {col.num_items} cards."
            )
        else:
            await interaction.followup.send(
                f"✅ Photocard added! Collection may need manual reload.",
                ephemeral=True
            )
    except Exception as e:
        await interaction.followup.send(f"Error saving photocard: {e}", ephemeral=True)


@bot.tree.command(name="delete_photocard", description="[Admin] Delete a photocard from a collection")
async def delete_photocard_command(interaction: discord.Interaction, collection: str, photocard_name: str):
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in specific channels.", ephemeral=True)
        return
    
    if not is_admin(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    sanitized_collection = sanitize_name(collection)
    if not sanitized_collection:
        await interaction.response.send_message("Invalid collection name.", ephemeral=True)
        return
    
    sanitized_photocard = sanitize_name(photocard_name)
    if not sanitized_photocard:
        await interaction.response.send_message("Invalid photocard name.", ephemeral=True)
        return
    
    col = get_collection(sanitized_collection)
    if not col:
        await interaction.response.send_message(f"Collection '{sanitized_collection}' does not exist.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    found = False
    
    for image_path in col.image_paths:
        if image_path.stem == sanitized_photocard:
            try:
                image_path.unlink()
                found = True
                reload_collections()
                
                await interaction.followup.send(
                    f"✅ Deleted photocard '{sanitized_photocard}' from collection '{sanitized_collection}'."
                )
                break
            except Exception as e:
                await interaction.followup.send(f"Error deleting photocard: {e}", ephemeral=True)
                return
    
    if not found:
        await interaction.followup.send(
            f"Photocard '{sanitized_photocard}' not found in collection '{sanitized_collection}'.",
            ephemeral=True
        )


@bot.tree.command(name="delete_collection", description="[Admin] Delete an entire collection")
async def delete_collection_command(interaction: discord.Interaction, collection: str, confirm: str):
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in specific channels.", ephemeral=True)
        return
    
    if not is_admin(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    if confirm.lower() != "yes":
        await interaction.response.send_message(
            f"⚠️ To delete collection '{collection}', use: `/delete_collection {collection} yes`",
            ephemeral=True
        )
        return
    
    sanitized_collection = sanitize_name(collection)
    if not sanitized_collection:
        await interaction.response.send_message("Invalid collection name.", ephemeral=True)
        return
    
    col = get_collection(sanitized_collection)
    if not col:
        await interaction.response.send_message(f"Collection '{sanitized_collection}' does not exist.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    files_dir = pathlib.Path(__file__).resolve().parent / "a_collections" / "files"
    collection_dir = files_dir / sanitized_collection
    
    if not collection_dir.exists() or not collection_dir.is_relative_to(files_dir):
        await interaction.followup.send("Invalid collection path.", ephemeral=True)
        return
    
    try:
        shutil.rmtree(collection_dir)
        reload_collections()
        
        await interaction.followup.send(f"✅ Deleted collection '{sanitized_collection}' and all its photocards.")
    except Exception as e:
        await interaction.followup.send(f"Error deleting collection: {e}", ephemeral=True)


@bot.tree.command(name="debug", description="[Admin] Show debug info for a user")
async def debug_command(interaction: discord.Interaction, user: discord.Member):
    if not is_allowed_channel(interaction):
        await interaction.response.send_message("This command can only be used in specific channels.", ephemeral=True)
        return
    
    if not is_admin(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    message = []
    user_id = user.id
    user_name = user.display_name
    
    for collection in get_collections():
        owned = db_handler.get_owned_images(user_id, collection)
        message.append(f"{user_name} ({user_id}) [{collection}]: {owned}")
    
    if message:
        await interaction.response.send_message("\n".join(message))
    else:
        await interaction.response.send_message(f"{user_name} has no cards in any collection.")


bot.run(token)
