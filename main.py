import psycopg2
import atexit


def get_int(string: str):
    expected_integer = input(string)
    try:
        return int(expected_integer)
    except ValueError:
        print('Введённая строка не является целым числом')
        raise RuntimeError


def get_bool(string: str):
    expected_bool = input(string + ' (Да/Нет)   ').lower()
    if expected_bool == 'да':
        return True
    elif expected_bool == 'нет':
        return False
    else:
        print('Введена неверная строка/n')
        get_bool(string)


def client_exists(cur, client_id):
    cur.execute("SELECT id FROM clients WHERE id = %s", (client_id,))
    result = cur.fetchone()
    if result is None:
        print(f"Клиент с указанным id {client_id} не существует")
        raise RuntimeError()
    else:
        return True


def phone_exists(cur, client_id, phone_number):
    cur.execute("SELECT id FROM clients WHERE id = %s AND %s = ANY (phone)", (client_id, phone_number))
    result = cur.fetchone()
    if result is None:
        print(f"Введённый номер телефона не был найден у клиента id {client_id}")
        raise RuntimeError()
    else:
        return True


def create_db(cur):
    cur.execute('''CREATE TABLE clients
                       (id SERIAL PRIMARY KEY,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        phone TEXT[])''')


def add_client(cur):
    first_name = input("Введите фамилию клиента: ")
    last_name = input("Введите имя клиента: ")
    email = input("Введите адрес электронной почты клиента: ")
    phone_question_string = "Хотите добавить номер телефона?"
    phone = []
    while get_bool(phone_question_string):
        phone_question_string = "Хотите добавить ещё один номер?"
        phone.append(input("Введите номер телефона клиента: "))

    cur.execute("INSERT INTO clients (first_name, last_name, email, phone) VALUES (%s, %s, %s, %s)",
                (first_name, last_name, email, phone))


def add_phone(cur):
    client_id = get_int("Введите ID клиента: ")
    if client_exists(cur, client_id):
        phone = input("Введите номер телефона клиента: ")
        cur.execute("UPDATE clients SET phone = array_append(phone, %s) WHERE id = %s", (phone, client_id))


def change_client(cur):
    client_id = get_int("Введите ID клиента: ")
    if client_exists(cur, client_id):
        first_name = input("Введите фамилию клиента: ")
        last_name = input("Введите имя клиента: ")
        email = input("Введите адрес электронной почты клиента: ")
        phone_question_string = "Хотите добавить номер телефона?"
        phone = []
        while get_bool(phone_question_string):
            phone_question_string = "Хотите добавить ещё один номер?"
            phone.append(input("Введите номер телефона клиента: "))

        cur.execute("UPDATE clients SET first_name = %s, last_name = %s, email = %s, phone = %s WHERE id = %s",
                    (first_name, last_name, email, phone, client_id))


def delete_phone(cur):
    client_id = get_int("Введите ID клиента: ")
    if client_exists(cur, client_id):
        phone = input("Введите номер телефона клиента: ")
        if phone_exists(cur, client_id, phone):
            cur.execute("UPDATE clients SET phone = array_remove(phone, %s) WHERE id = %s", (phone, client_id))


def delete_client(cur):
    client_id = get_int("Введите ID клиента: ")
    if client_exists(cur, client_id):
        cur.execute("DELETE FROM clients WHERE id = %s", (client_id,))


def find_client(cur):
    query = input("Введите данные для поиска: ")
    cur.execute(
        "SELECT * FROM clients WHERE first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s OR %s = ANY(phone)",
        (f"%{query}%", f"%{query}%", f"%{query}%", query))
    rows = cur.fetchall()
    if len(rows) == 0:
        print("Клиент не был найден")
        raise RuntimeError()
    for row in rows:
        print(row)


def program(conn):
    cur = conn.cursor()
    try:
        command_number = get_command()
        execute_command(command_number, cur)
        conn.commit()
        print('\nКоманда выполнена успешно')
        print('\n')
    except Exception as e:
        print('\nОшибка при выполнении команды')
        print(e)
        print("\n")


def execute_command(command_number, cur):
    match command_number:
        case "1":
            add_client(cur)
        case "2":
            add_phone(cur)
        case "3":
            change_client(cur)
        case "4":
            delete_phone(cur)
        case "5":
            delete_client(cur)
        case "6":
            find_client(cur)
        case _:
            print("Неправильный номер команды")
            raise RuntimeError()


def get_command():
    command_number = input("""Выберите команду:
1.Добавить нового клиента
2.Добавить телефон для существующего клиента
3.Изменить данные о клиенте
4.Удалить телефон для существующего клиента
5.Удалить существующего клиента
6.Найти клиента по его данным: имени, фамилии, email или телефону.\n""").strip()
    return command_number


with psycopg2.connect(database="clients_db", user="postgres", password="postgres") as connection:
    cur = connection.cursor()

    def exit_handler():
        cur.execute("DROP TABLE IF EXISTS clients CASCADE")
        connection.commit()
        connection.close()
    atexit.register(exit_handler)

    create_db(cur)
    connection.commit()
    while True:
        program(connection)
