
from basic import command_input, context_open


async def check_specific_command(message, howd_look) -> bool:  # type: ignore
    input_result = await command_input(message)

    command = input_result[0]
    raw_str = input_result[1]
    word_list = input_result[2]
    id_list = input_result[3]

    if command is not None:  # если команда введена без аргументов

        if howd_look == '+words(':
            if (command[7] in ('-', '+')) and (command.endswith(')')) and (command[8:-1].isdigit()):
                return True
            else:
                return False

        elif howd_look == '+add_points':
            if len(word_list) > 1:  # type: ignore
                if len(word_list[1]) > 1:  # type: ignore
                    if (word_list[1][1:].isdigit()) and (  # type: ignore
                            word_list[1][0] in ('+', '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):  # type: ignore
                        return True
                else:
                    if word_list[1].isdigit():  # type: ignore
                        return True
            else:
                return False

        if howd_look == '+avatar':
            if id_list:
                return True


async def check_if_element_exists_on_server(table_name, server_id, column_name, element_name) -> bool:
    # todo 'table name' is always 'banned_words' since this function only used in one case, so 'column_name' argument
    """Checks if certain element is in certain table with given server_id. Returns True or False"""
    # используется только в add_new_words()  # todo maybe just use Try-Except there instead of this function?
    # shows if the item is in the table
    async with context_open(
            f"SELECT EXISTS(SELECT 1 FROM {table_name} "
            f"WHERE server_id = '{server_id}' AND {column_name} = '{element_name}')") as items:
        pass

    if items[0][0]:
        result = True
    else:
        result = False

    return result
