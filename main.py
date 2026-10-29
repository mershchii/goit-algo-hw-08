import pickle
import sys
from collections import UserDict
from datetime import datetime, timedelta


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Name cannot be empty.")
        super().__init__(str(value).strip())


class Phone(Field):
    def __init__(self, value: str):
        val = str(value).strip()
        if not (len(val) == 10 and val.isdigit()):
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(val)


class Birthday(Field):
    def __init__(self, value: str):
        try:
            date_obj = datetime.strptime(str(value).strip(), "%d.%m.%Y")
            super().__init__(date_obj.strftime("%d.%m.%Y"))
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone: str) -> None:
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> None:
        phone_obj = self.find_phone(phone)
        if phone_obj:
            self.phones.remove(phone_obj)
        else:
            raise ValueError(f"Phone {phone} not found in contact {self.name.value}.")

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        phone_obj = self.find_phone(old_phone)
        if not phone_obj:
            raise ValueError(f"Phone {old_phone} not found in contact {self.name.value}.")
        new_phone_obj = Phone(new_phone)
        phone_obj.value = new_phone_obj.value

    def find_phone(self, phone: str):
        search_val = str(phone).strip()
        for p in self.phones:
            if p.value == search_val:
                return p
        return None

    def add_birthday(self, birthday: str) -> None:
        self.birthday = Birthday(birthday)

    def __str__(self) -> str:
        phones_str = "; ".join(p.value for p in self.phones)
        birthday_str = f", birthday: {self.birthday.value}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones_str}{birthday_str}"


class AddressBook(UserDict):
    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str):
        return self.data.get(name)

    def delete(self, name: str) -> None:
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self) -> list[dict[str, str]]:
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            bday_val = record.birthday.value
            if isinstance(bday_val, str):
                bday_date = datetime.strptime(bday_val, "%d.%m.%Y").date()
            elif isinstance(bday_val, datetime):
                bday_date = bday_val.date()
            else:
                bday_date = bday_val

            try:
                birthday_this_year = bday_date.replace(year=today.year)
            except ValueError:
                birthday_this_year = bday_date.replace(year=today.year, month=3, day=1)

            if birthday_this_year < today:
                try:
                    birthday_this_year = bday_date.replace(year=today.year + 1)
                except ValueError:
                    birthday_this_year = bday_date.replace(year=today.year + 1, month=3, day=1)

            days_until = (birthday_this_year - today).days
            if 0 <= days_until <= 7:
                congratulation_date = birthday_this_year
                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)

                upcoming_birthdays.append({
                    "name": record.name.value,
                    "birthday": congratulation_date.strftime("%d.%m.%Y"),
                })

        return upcoming_birthdays

    def __str__(self) -> str:
        if not self.data:
            return "Address book is empty."
        return "\n".join(str(record) for record in self.data.values())


def save_data(book: AddressBook, filename: str = "addressbook.pkl") -> None:
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename: str = "addressbook.pkl") -> AddressBook:
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return f"Error: {e}"
        except KeyError:
            return "Error: Contact not found."
        except IndexError:
            return "Error: Enter user name."
    return inner


def parse_input(user_input: str):
    parts = user_input.split()
    if not parts:
        return "", *[]
    cmd, *args = parts
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook) -> str:
    if len(args) < 2:
        raise ValueError("Give me name and phone please.")
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        if phone:
            record.add_phone(phone)
        book.add_record(record)
        message = "Contact added."
    else:
        if phone:
            record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook) -> str:
    if len(args) < 3:
        raise ValueError("Give me name, old phone and new phone please.")
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book: AddressBook) -> str:
    if not args:
        raise IndexError
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    if not record.phones:
        return f"{record.name.value} has no phones saved."
    return f"{record.name.value}: {'; '.join(p.value for p in record.phones)}"


@input_error
def show_all(book: AddressBook) -> str:
    if not book.data:
        return "No contacts saved yet."
    return str(book)


@input_error
def add_birthday(args, book: AddressBook) -> str:
    if len(args) < 2:
        raise ValueError("Give me name and birthday (DD.MM.YYYY) please.")
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook) -> str:
    if not args:
        raise IndexError
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    if record.birthday is None:
        return f"No birthday set for {record.name.value}."
    return f"{record.name.value}'s birthday: {record.birthday.value}"


@input_error
def birthdays(args, book: AddressBook) -> str:
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays in the next 7 days."
    return "\n".join(f"{item['name']}: {item['birthday']}" for item in upcoming)


def run_demo():
    import os
    import tempfile

    print("--- Running demonstration (HW-08 with pickle) ---")
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
        temp_pkl = tmp.name
    os.remove(temp_pkl)

    book = load_data(temp_pkl)
    print(add_contact(["John", "1234567890"], book))
    upcoming_bday = (datetime.today().date() + timedelta(days=2)).strftime("%d.%m.%Y")
    print(add_birthday(["John", upcoming_bday], book))
    save_data(book, temp_pkl)

    restored_book = load_data(temp_pkl)
    print("Restored from pickle:")
    print(show_all(restored_book))
    os.remove(temp_pkl)
    print("--- Demonstration finished successfully ---")


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["--demo", "-d", "demo", "test"]:
        run_demo()
        return

    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        try:
            user_input = input("Enter a command: ").strip()
        except (EOFError, KeyboardInterrupt):
            save_data(book)
            print("\nGood bye!")
            break

        if not user_input:
            continue

        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        elif command == "demo":
            run_demo()

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
