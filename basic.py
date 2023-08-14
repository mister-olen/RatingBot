import aiosqlite
import datetime
import json
import aiofiles  # type: ignore
from contextlib import asynccontextmanager
from typing import Tuple, List, Optional, Union


# todo should start using type annotations


async def command_input(message) -> Union[Tuple[str, str, List[str], List[str]], Tuple[None, None, None, List]]:
    # todo maybe best is to make four distinct functions
    # todo or make flags that will set variables that the function need
    """
    Converts message text into groups: command, the rest text, separate words after the command, list of id's
    0 - command, 1 - raw_string(without command), 2 - word_list(without command), 3 - id_list
    or None, None, None, [] -if single command without arguments
    """

    command = None  # the first word in the message text
    raw_string = None  # the rest message text (without command)
    word_list = None  # list of separate words (without command)
    id_list = []  # list of user id's (if there were any member mentions)

    stripped_msg = message.content.strip()

    if ' ' in stripped_msg:  # if no spaces - no any words after the command, which returns None, None, None, []
        temp_list = []
        split_message = stripped_msg.split(' ')  # todo edit to .split()
        command = split_message[0]
        raw_string = stripped_msg.split(command, 1)[1].strip()  # second strip if multiple spaces in the message
        word_list = raw_string.split(' ')  # this is a tuple now
        for word in word_list:
            if len(word) > 0:
                temp_list.append(word)
        word_list = temp_list  # now its a list

        for if_mention in word_list:  # checking if mentions in the message  # todo maybe check with discord mentions?
            if if_mention.startswith('<@') and if_mention.endswith('>'):  #todo maybe only check beginning symbols
                id_list.append(if_mention.strip('<!&@>'))  # id number without any symbols. String

    return command, raw_string, word_list, id_list


async def quick_word_filter(client, message) -> Optional[Tuple[List[str], int]]:  # type: ignore
    """Checks if any banned words in the message. Returns word list and the price, or None"""
    server_id = message.guild.id
    user_id = message.author.id
    msg_text = message.content.lower()
    if_banned = False

    async with context_open(f"SELECT word, price FROM banned_words WHERE server_id = {server_id} ") as banned_words:
        pass

    if msg_text.startswith('+words('):  # todo check this - probably a vulnerability
        pass

    else:
        for banned in banned_words:  # fast check on first banned word in the whole message text
            if banned[0] in msg_text:
                if_banned = True
                break

        if if_banned:
            word_list = msg_text.split()  # splitting to distinct 'words' - maybe another vulnerability ("arC AT" - cat)
            found_words = []
            points_sum = 0
            for word in word_list:
                for banned in banned_words:
                    if banned[0] in word:
                        if word in found_words:  # чтобы учитывалось только первое совпадение со списком из базы
                            # но если в одном "слове" сразу несколько вхождений, то учтется первое слово и его цена
                            # catdogbear = cat
                            continue

                        else:
                            found_words.append(word)
                            points_sum += banned[1]
            the_reason = ' '.join(found_words)
            await adding_points(client, server_id, user_id, points_sum, the_reason)
            return found_words, points_sum

        else:
            return None


async def reaction_adding_recording(reaction, user, message):
    """Records any reaction adding to db"""
    server_id = message.guild.id
    message_id = message.id
    channel_id = message.channel.id
    message_author_id = message.author.id
    message_author_name = message.author.name
    reaction_author_id = user.id
    reaction_author_name = user.name
    reaction = reaction
    message_length = len(message.content)  # for sorting?
    time = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

    async with context_open(f"""
            INSERT INTO message_stats (server_id, message_id, channel_id, message_author_id, message_author_name, 
            reaction_author_id, reaction_author_name, reaction, message_length, time) 
            VALUES ('{server_id}', '{message_id}','{channel_id}', '{message_author_id}', '{message_author_name}', 
            '{reaction_author_id}', '{reaction_author_name}', '{reaction}', '{message_length}', '{time}' )
            """):
        pass  # может как-то можно по-другому, без pass?


async def reaction_removing_recording(reaction, message):
    """Deletes the record from db about the reaction, when it was removed"""
    message_id = message.id
    server_id = message.guild.id

    async with context_open(
            f"DELETE FROM message_stats WHERE (reaction = '{reaction}' AND message_id = '{message_id}' "
            f"AND server_id = '{server_id}')"):
        pass


async def adding_points(client, server_id, user_id, points_to_add, the_reason) -> str:
    """Adds points to the user. Returns report"""
    person_name = client.get_user(user_id).name  # not necessary maybe

    async with context_open(
            f"SELECT EXISTS(SELECT 1 FROM users WHERE server_id = '{server_id}' AND user_id = '{user_id}')") as f:
        items = f[0][0]

    if items:  # if both True - the person and the table
        async with context_open(
                f"SELECT points, points_log FROM users "
                f"WHERE (server_id = '{server_id}' AND user_id = '{user_id}')") as f:
            old_points = f[0][0]
            the_dict = json.loads(f[0][1])  # todo maybe make a function that does all the convertations
            the_log_list = the_dict['the_log']
        new_points = old_points + points_to_add

        # adding new string
        new_log_line = f'{points_to_add} {the_reason}'
        the_log_list.append(new_log_line)
        the_dict['the_log'] = the_log_list  # - проверить нужно ли, или словарь автоматически изменяется
        # converting back to json
        if len(the_log_list) > 1:  # deleting first (oldest) string
            the_log_list.pop(0)
        new_json_str = json.dumps(the_dict)


        # modifying old values in db
        async with context_open(
                f"UPDATE users SET name = '{person_name}', points = '{new_points}', points_log = '{new_json_str}' "
                f"WHERE (server_id = '{server_id}' AND user_id = '{user_id}')"):
            returning_message = 'Points added'

    else:
        very_first_log_str = f"{points_to_add} {the_reason}"
        very_first_dict = {'the_log': [very_first_log_str]}
        new_json_str = json.dumps(very_first_dict)
        # just inserting new line to db - but first create the dict
        async with context_open(
                f"INSERT INTO users (server_id, user_id, name, points, points_log) "
                f"VALUES ('{server_id}', '{user_id}', '{person_name}', '{points_to_add}', '{new_json_str}' )"):
            returning_message = 'Points added to new user'

    return returning_message


@asynccontextmanager
async def context_open(query, path="rating_bot_base.db"):
    """Context manager for db queries. Catching exceptions and writing them to log-file"""
    db = None
    cursor = None

    try:
        db = await aiosqlite.connect(path)
        cursor = await db.execute(query)
        items = await cursor.fetchall()
        await db.commit()
        yield items

    except Exception as exc:
        await log_write(exc)
        yield exc  # to prevent "generator didn't yield" Error

    finally:
        if cursor:
            await cursor.close()
        await db.close()


async def log_write(log_text, path='logs.txt'):
    """Writing log message to log-file"""
    time = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
    async with aiofiles.open(path, 'a', encoding='utf-8') as f:
        await f.write(f"> {log_text}, {time}{chr(10)}{chr(10)}")


async def check_and_create_tables() -> str:
    if_were_created = ""
    table_create = {
        "banned_words": "CREATE TABLE IF NOT EXISTS banned_words (server_id INTEGER, word TEXT, price INTEGER)",

        "users": "CREATE TABLE IF NOT EXISTS "
        "users(server_id INTEGER, user_id INTEGER, name TEXT, points INTEGER, points_log TEXT)",

        "message_stats": "CREATE TABLE IF NOT EXISTS message_stats (server_id INTEGER, message_id INTEGER, "
        "message_author_id INTEGER, reaction TEXT, message_length INTEGER, reaction_author_id INTEGER, time TEXT)",
    }
    # todo разобраться со строками и переносами
    for table in table_create:
        async with context_open(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'") as items:
            if items:
                pass
            else:
                async with context_open(table_create[table]):
                    await log_write(f"New table was created: {table}")
                    if_were_created = f"{if_were_created}{table}, "

    if if_were_created:
        return f"Some tables were created: {if_were_created}"
    else:
        return "No new tables were created."


