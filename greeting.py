import os

from shared import CONFIG_FILE, load_user_name, save_user_name, safe_input


def ensure_and_greet_user():
    existed = os.path.exists(CONFIG_FILE)
    name = load_user_name()
    if name and existed:
        print(f"Hi, {name}! Welcome back!🌞")
        return
    if name:
        print(f"Hi, {name}!")
        return

    while True:
        name_input = safe_input("Welcome to CliFin! What's your name? ").strip()
        if name_input:
            save_user_name(name_input)
            print(f"Hi, {name_input}!")
            break
        print("Name cannot be empty. Please enter your name, or at least what you like to be called😀")
