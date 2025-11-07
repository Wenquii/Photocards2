# Discord Photocards Bot

## Overview
This is a Discord bot that simulates virtual photocard collection in Discord servers using modern Discord **slash commands** (`/`). Users can collect, view, and manage photocards from various collections. Admins can create collections, add/delete photocards, and manage user collections. The bot was originally created for Korean pop fan communities where photocard collecting is popular.

## Project Status
**Current State**: Bot is successfully running in Replit with slash commands synced. Connected to Discord as STAYNNIES#3081 with 10 active commands.

## Recent Changes (November 7, 2025)
- **MAJOR UPDATE**: Converted entire bot from text-based commands (`tcg!`) to Discord slash commands (`/`)
- Completely rewrote bot.py using discord.ext.commands with app_commands
- Added `/add_collection` command to create new collections via Discord
- Added `/add_photocard` command to upload photocard images directly from Discord
- Added `/delete_photocard` command to remove individual photocards
- Added `/delete_collection` command to remove entire collections
- Improved all existing commands with better formatting and ephemeral error messages
- Fixed critical channel filter bug from previous version
- Fixed Image.ANTIALIAS deprecation warning
- Installed Python 3.11 and dependencies (discord.py, pillow, flask)
- Created .gitignore for Python project
- Configured workflow to run bot as console application

## Architecture

### Core Components
- **bot.py**: Main entry point using discord.ext.commands.Bot with slash commands
- **db/**: SQLite database management
  - schema.sql: User collection data schema
  - db.py: Database handler with CRUD operations
- **a_collections/**: Photocard collection management
  - a_collection.py: Collection class and collection loading
  - files/: Directory for photocard image files (managed via Discord commands)
- **image/**: Image processing for collection displays
  - image.py: Generates composite images of collections with PIL

### Technology Stack
- **Language**: Python 3.11
- **Main Libraries**:
  - discord.py 2.6.4: Discord bot framework with slash commands
  - Pillow 12.0.0: Image processing
  - Flask 3.1.2: (included but not actively used)
- **Database**: SQLite (user_data.db)
- **Environment**: Replit with Nix package management

## Slash Commands

All commands use Discord's native slash command system (`/command`). Simply type `/` in Discord to see all available commands!

### User Commands (Everyone)

#### `/collections`
Lists all available photocard collections with card counts.

#### `/view [collection]`
View your collected cards from a specific collection. Shows a visual grid of your cards.
- **Parameters:**
  - `collection`: Name of the collection to view

### Admin Commands (Admins Only)

#### `/add_collection [collection_name]`
Create a brand new photocard collection.
- **Parameters:**
  - `collection_name`: Name for the new collection (spaces will be converted to underscores)

#### `/add_photocard [collection] [photocard_name] [image]`
Add a new photocard to an existing collection by uploading an image.
- **Parameters:**
  - `collection`: Name of the collection
  - `photocard_name`: Name for the photocard
  - `image`: Upload an image file (PNG, JPG, or JPEG)

#### `/delete_photocard [collection] [photocard_name]`
Delete a specific photocard from a collection.
- **Parameters:**
  - `collection`: Name of the collection
  - `photocard_name`: Name of the photocard to delete

#### `/delete_collection [collection] [confirm]`
Delete an entire collection and all its photocards.
- **Parameters:**
  - `collection`: Name of the collection to delete
  - `confirm`: Type "yes" to confirm deletion

#### `/preview [collection]`
Preview all cards in a collection (useful for seeing the complete set).
- **Parameters:**
  - `collection`: Name of the collection

#### `/unlock [collection] [card_numbers] [user]`
Unlock specific cards for a user. Can unlock multiple cards at once.
- **Parameters:**
  - `collection`: Name of the collection
  - `card_numbers`: Card numbers separated by commas (e.g., "1,2,5,8")
  - `user`: Mention the user to unlock cards for

#### `/lock [collection] [card_numbers] [user]`
Lock/remove specific cards from a user.
- **Parameters:**
  - `collection`: Name of the collection
  - `card_numbers`: Card numbers separated by commas (e.g., "1,2,5")
  - `user`: Mention the user to lock cards for

#### `/debug [user]`
Show detailed debug information about a user's collection across all collections.
- **Parameters:**
  - `user`: Mention the user to debug

## Configuration

### Environment Variables
- `DISCORD_PHOTOCARD_TOKEN`: Discord bot authentication token (required)

### Admin Users
Admin user IDs are defined in constants.py:
- 935057263079600149
- 1351844085547405352
- 1022257383751303209

To add more admins, edit the `ADMINS` list in `constants.py`.

### Allowed Channels
The bot only responds in specific channels. Channel IDs are defined in constants.py:
- 1394358047635280013

To allow the bot in more channels, add channel IDs to the `ALLOWED_CHANNELS` list.

### Database
- Type: SQLite
- File: user_data.db (auto-created, gitignored)
- Schema: Tracks user ID, photo group (collection), and photo ID ownership

### Workflow
- Name: discord-bot
- Command: `python bot.py`
- Output Type: Console
- Status: Running with 10 synced slash commands

## Project Structure
```
.
├── bot.py                 # Main bot with slash commands
├── constants.py          # Configuration constants
├── requirements.txt      # Python dependencies
├── db/                  # Database layer
│   ├── __init__.py
│   ├── db.py
│   └── schema.sql
├── a_collections/       # Collection management
│   ├── __init__.py
│   ├── a_collection.py
│   └── files/          # Photocard images (managed via Discord)
└── image/              # Image processing
    ├── __init__.py
    └── image.py
```

## Usage Guide

### For Regular Users:
1. Use `/collections` to see what collections are available
2. Use `/view [collection_name]` to see your cards
3. Collect cards as admins unlock them for you!

### For Admins:

#### Creating a New Collection:
1. Use `/add_collection my_collection_name`
2. Use `/add_photocard my_collection_name card1 [upload image]` to add cards
3. Repeat step 2 for each card in the collection

#### Managing User Collections:
1. Use `/unlock collection_name 1,2,3 @username` to give cards to users
2. Use `/lock collection_name 2 @username` to remove specific cards
3. Use `/debug @username` to see what cards a user owns

#### Managing Photocards:
- Add: `/add_photocard collection_name new_card [image]`
- Delete: `/delete_photocard collection_name card_name`
- Preview: `/preview collection_name` to see all cards

## Important Notes

### Discord Developer Portal Settings
Make sure these are enabled in your Discord Developer Portal:
1. **Message Content Intent** - Required for the bot to function
2. **Server Members Intent** - Recommended for user management
3. **Slash Commands** - Should be enabled by default

### Image Requirements
- All images in a collection should have **identical dimensions** for best display
- Supported formats: PNG, JPG, JPEG
- Recommended: Square images (e.g., 500x500px)

### Adding a Preview Image
You can add a `preview.jpg` or `preview.png` to any collection folder to show locked cards. This image should match the dimensions of other cards in the collection.

## Troubleshooting

### Slash commands not appearing?
- Make sure the bot has been invited with the `applications.commands` scope
- Wait a few minutes after the bot starts (commands can take time to sync)
- Try restarting Discord

### Bot not responding to commands?
- Check that you're in an allowed channel (see constants.py)
- Verify the bot is online in Discord
- Check the bot logs for errors

### Can't add photocards?
- Ensure the collection exists first (use `/add_collection`)
- Check that your image is in PNG, JPG, or JPEG format
- Make sure you're an admin user

## Development Notes

The bot automatically reloads collections when you add/delete photocards through Discord commands, so changes take effect immediately without needing to restart the bot.

## Future Enhancements
- Trading system between users
- Random card drops/gacha system
- Collection statistics and leaderboards
- Card rarity tiers
- Bulk import/export tools
