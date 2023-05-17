
import check
from basic import command_input, adding_points, context_open


async def adding_points_manually(client, message) -> str:
    """Adding points to someone. Returns report"""
    if await check.check_specific_command(message, '+add_points'):
        the_input = await command_input(message)
        server_id = message.guild.id
        user_id = int(the_input[3][0])
        points_to_add = int(the_input[2][1])  # type: ignore
        the_reason = ' '.join(the_input[2][2:])  # type: ignore # f-строка видимо не работает с индексами
        returning_message = await adding_points(client, server_id, user_id, points_to_add, the_reason)

    else:
        returning_message = "Wrong command input"

    return returning_message


async def add_new_words(message) -> str:
    """Adds new words to banned words list. Returns report"""
    if await check.check_specific_command(message, '+words('):

        the_input = await command_input(message)
        command = the_input[0]
        word_list = the_input[2]
        server_id = message.guild.id
        price = int(command[7:-1])  # type: ignore

        if price == 0:
            for word in word_list:  # type: ignore
                word = word.lower()
                if await check.check_if_element_exists_on_server('banned_words', server_id, 'word', word):
                    async with context_open(
                            f"DELETE FROM banned_words WHERE word ='{word}' AND server_id = '{server_id}'"):
                        pass
                else:
                    continue
            returning_message = "Слова были удалены или не были добавлены."

        else:
            for word in word_list:  # type: ignore
                word = word.lower()
                if await check.check_if_element_exists_on_server('banned_words', server_id, 'word', word):
                    async with context_open(
                            f"UPDATE banned_words SET price={price} WHERE word='{word}' AND server_id = '{server_id}'"):
                        pass

                else:
                    async with context_open(
                            f"INSERT INTO banned_words(server_id, word, price) "
                            f"VALUES ('{server_id}', '{word}','{price}')"):
                        pass
            len_the_list = len(word_list)  # type: ignore
            returning_message = "Было добавлено " + str(len_the_list) + " слов."

    else:
        returning_message = "Wrong command input"

    return returning_message
