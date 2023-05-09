
import os
import discord
import basic
import change
import show_tables
from dotenv import load_dotenv

# loading variables from virtual environment
load_dotenv()

intents = discord.Intents().all()
intents.members = True
intents.presences = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(await basic.check_and_create_tables())  # maybe have to wait here, but no exceptions seen yet
    print(f"We have logged in as {client.user}")  # connecting message in console


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await basic.quick_word_filter(client, message)  # the very first function, to filter every message

    if message.content.startswith("+"):

        cmd = message.content.split()[0]

        if cmd == "+help":
            await show_tables.cmd_help(message)

        elif cmd == "+banneds":
            await show_tables.show_banned_words(message)

        elif cmd == "+users":
            await show_tables.show_users(message)

        elif cmd == "+top_messages":
            await show_tables.show_stats_messages(client, message)

        elif cmd == "+top_users":
            await show_tables.show_stats_users(message)

        elif cmd == "+top_reactions":
            await show_tables.show_stats_reactions(message)

        elif cmd == "+add_points":
            adding_points = await change.adding_points_manually(client, message)
            await message.channel.send(adding_points)

        elif cmd[:7] == '+words(':
            adding_words = await change.add_new_words(message)
            await message.channel.send(adding_words)

        elif cmd == '+avatar':
            await show_tables.show_avatar(message)

        elif cmd == "+message":
            await message.channel.send(message)



@client.event
async def on_raw_reaction_add(payload):
    message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    reaction = payload.emoji
    user = payload.member
    await basic.reaction_adding_recording(reaction, user, message)


@client.event
async def on_raw_reaction_remove(payload):
    message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    reaction = payload.emoji
    await basic.reaction_removing_recording(reaction, message)


if __name__ == '__main__':
    client.run(os.getenv("TOKEN"))
