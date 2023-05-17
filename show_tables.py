
from basic import context_open
from check import check_specific_command
import asyncio
from typing import List, Tuple


async def cmd_help(message):
    """Returns help message"""
    await message.channel.send(f"""```
 >Add points to someone: +add_points @mention [points] [reason] (optionally) {chr(10)}
 >Adding words: +words(+/-999) and words separated by spaces {chr(10)}
 >Deleting words: +words(+/-0) and words separated by spaces {chr(10)}
  _____ {chr(10)}
 >See users' points: +users {chr(10)}
 >See banned words: +banneds {chr(10)}
 >See user's avatar: +avatar {chr(10)}
 _____ {chr(10)}
 >Top reacted messages: +top_messages {chr(10)}
 >Top reacted users: +top_users {chr(10)}
 >Top reactions: +top_reactions
 ```""")


async def create_text_table(pairs_list: List[Tuple[str, int]], title: str, column1: str, column2: str) -> list[str]:
    number = 1
    head_line = f"```                      >>> {title}{chr(10)} № | {column1}, {column2}"
    f"{chr(10)}_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _{chr(10)}"
    main_line = ""
    temp_list = []

    for first_or_second in pairs_list:
        first, second = first_or_second
        main_line = f"{main_line} {number}  |  {first}, {second}{chr(10)}"
        number += 1
        if len(main_line) > 1500:
            temp_list.append(f"{head_line}{main_line}```")
            main_line = ""
    if temp_list:
        return temp_list
    else:
        return [f"{head_line}{main_line}```"]


async def show_banned_words(message):
    """Shows banned words table"""
    server_id = message.guild.id

    async with context_open(f"""SELECT word, price FROM banned_words WHERE server_id = {server_id}
            GROUP BY word ORDER BY price DESC""") as items:
        pass
    tables = await create_text_table(items, 'banned_words', 'word', 'price')
    for string in tables:
        await message.channel.send(string)
        await asyncio.sleep(0.3)


async def show_users(message):
    """Shows users' balance"""
    server_id = message.guild.id

    async with context_open(f"""SELECT name, points FROM users WHERE server_id = {server_id}
            GROUP BY name ORDER BY points DESC LIMIT 20""") as items:
        pass
    await message.channel.send(*await create_text_table(items, 'user points', 'name', 'points'))


async def show_stats_messages(client, message):
    """Shows most reacted messages links"""
    server_id = message.guild.id

    async with context_open(
            f"SELECT message_id, channel_id, COUNT(message_id) FROM message_stats "
            f"WHERE server_id = '{server_id}' GROUP BY message_id ORDER BY COUNT(message_id) DESC LIMIT 5") as items:
        pass

    temp_list = []
    main_list = []

    for the_ids in items:
        message_id = int(the_ids[0])
        channel_id = int(the_ids[1])
        reactions_count = int(the_ids[2])

        channel = client.get_channel(channel_id)
        the_message = await channel.fetch_message(message_id)
        message_link = the_message.jump_url

        temp_list.append(message_link)
        temp_list.append(reactions_count)
        main_list.append(temp_list)
        temp_list = []

    await message.channel.send(
        *await create_text_table(main_list, 'top-5 reacted messages', 'message link', 'reacted'))


async def show_stats_users(message):
    """Shows top reacted users"""
    server_id = message.guild.id

    async with context_open(
            f"SELECT message_author_name, COUNT(message_author_name) FROM message_stats "
            f"WHERE server_id = '{server_id}' GROUP BY message_author_name "
            f"ORDER BY COUNT(message_author_name) DESC LIMIT 10") as items:
        pass
    await message.channel.send(*await create_text_table(items, 'top-10 reacted users', 'user', 'reacted'))


async def show_stats_reactions(message):
    """Shows most used reactions"""
    server_id = message.guild.id

    async with context_open(
            f"SELECT reaction, COUNT(reaction) FROM message_stats WHERE server_id = '{server_id}' "
            f"GROUP BY reaction ORDER BY COUNT(reaction) DESC LIMIT 10") as items:
        pass
    await message.channel.send(*await create_text_table(items, 'top-10 reactions', 'reaction', 'used'))


async def show_avatar(message):
    """Shows user's avatar"""
    if await check_specific_command(message, '+avatar'):
        the_avatar = message.mentions[0].avatar
        await message.channel.send(the_avatar)
    else:
        await message.channel.send("Wrong command input")
