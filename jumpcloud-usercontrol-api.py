import requests
from tqdm import tqdm
from prettytable import PrettyTable
import sys
from termcolor import colored
import os

# Set color variables
green_check = colored("✔", "green")
red_cross = colored("✘", "red")

# Define the global headers variable

headers = {"x-api-key": os.environ.get("jc_token")}

def list_all_users():
    url = "https://console.jumpcloud.com/api/systemusers/"
    querystring = {
        "fields": "email sudo passwordless_sudo _id",
        "filter": "",
        "limit": "99",
        "skip": "0",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    user_list = response.json().get("results")

    # Create a new PrettyTable instance
    table = PrettyTable()
    table.field_names = ["#", "ID", "Email", "Sudo"]

    # Add rows to the table
    for i, user in enumerate(user_list, start=1):
        user_id = user['_id']
        email = user['email']
        sudo = green_check if user['passwordless_sudo'] else red_cross
        table.add_row([i, user_id, email, sudo])

    # Set column alignments
    table.align = "l"
    table.align["Sudo"] = "c"  # Align the "Sudo" column to the center

    # Print the table
    print(table)

def search_user(input_text):
    url = "https://console.jumpcloud.com/api/search/systemusers"
    payload = {
        "fields": "",
        "filter": {},
        "searchFilter": {"fields": ["username"], "searchTerm": [input_text]},
    }

    response = requests.request("POST", url, headers=headers, json=payload)

    user_list = response.json().get("results")

    if user_list:
        # Create a new PrettyTable instance
        table = PrettyTable()
        table.field_names = ["#", "ID", "Email", "Sudo"]

        # Add rows to the table
        for i, user in enumerate(user_list, start=1):
            user_id = user['_id']
            email = user['email']
            sudo = green_check if user['passwordless_sudo'] else red_cross
            table.add_row([i, user_id, email, sudo])

        # Set column alignments
        table.align = "l"
        table.align["Sudo"] = "c"  # Align the "Sudo" column to the center
        
        # Print the table
        print(table)

        # Get user input for the selected user
        user_index = int(input("Enter the number of the user: ")) - 1

        if 0 <= user_index < len(user_list):
            selected_user = user_list[user_index]
            user_id = selected_user["_id"]
            sudo_status = selected_user.get("passwordless_sudo", False)

            if sudo_status:
                choice = input("The selected user already has sudo privileges. Do you want to revoke them? (y/n): ")
                if choice.lower() == "y":
                    # Revoke sudo privileges for the selected user
                    payload = {
                        "sudo": False,
                        "passwordless_sudo": False,
                    }
                    update_url = f"https://console.jumpcloud.com/api/systemusers/{user_id}"
                    response_update = requests.put(update_url, json=payload, headers=headers)

                    if response_update.status_code == 200:
                        print("Sudo privileges revoked successfully.")
                    else:
                        print("Failed to revoke sudo privileges.")
                else:
                    print("Revoke operation cancelled.")
            else:
                choice = input("The selected user does not have sudo privileges. Do you want to grant them? (y/n): ")
                if choice.lower() == "y":
                    # Grant sudo privileges for the selected user
                    payload = {
                        "sudo": True,
                        "passwordless_sudo": True,
                    }
                    update_url = f"https://console.jumpcloud.com/api/systemusers/{user_id}"
                    response_update = requests.put(update_url, json=payload, headers=headers)

                    if response_update.status_code == 200:
                        print("Sudo privileges granted successfully.")
                    else:
                        print("Failed to grant sudo privileges.")
                else:
                    print("Grant operation cancelled.")
        else:
            print("Invalid user number.")
    else:
        print("No users found matching the search criteria.")

def grant_all_sudos():
    url = "https://console.jumpcloud.com/api/systemusers/"
    querystring = {
        "fields": "email sudo passwordless_sudo _id username",
        "filter": "",
        "limit": "99",
        "skip": "0",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    user_list = response.json().get("results")

    if not user_list:
        print("No users found.")
        return

    # Create a new PrettyTable instance
    table = PrettyTable()
    table.field_names = ["#", "ID", "Username", "Sudo", "Passwordless Sudo"]

    # Add rows to the table
    for i, user in enumerate(user_list, start=1):
        user_id = user["_id"]
        username = user.get("username", "")
        sudo = user.get("sudo", False)
        passwordless_sudo = user.get("passwordless_sudo", False)
        table.add_row([i, user_id, username, green_check if sudo else red_cross, green_check if passwordless_sudo else red_cross])

    # Set column alignments
    table.align = "l"
    table.align["Sudo"] = "c"  # Align the "Sudo" column to the center
    table.align["Passwordless Sudo"] = "c"  # Align the "Sudo" column to the center

    # Print the table
    print(table)

    # Get user input to confirm the action
    choice = input("Are you sure you want to grant sudo privileges to these users? (y/n): ")
    if choice.lower() != "y":
        return

    # Apply sudo privileges with progress bar
    applied_users = []
    with tqdm(total=len(user_list), desc="Progress", unit="user") as pbar:
        for user in user_list:
            user_id = user["_id"]
            sudo = user.get("sudo", False)
            passwordless_sudo = user.get("passwordless_sudo", False)
            if not sudo or not passwordless_sudo:
                payload = {
                    "sudo": True,
                    "passwordless_sudo": True,
                }
                update_url = f"https://console.jumpcloud.com/api/systemusers/{user_id}"
                response_update = requests.put(update_url, json=payload, headers=headers)
                if response_update.status_code == 200:
                    applied_users.append(user)
                pbar.update(1)

    # Create a new PrettyTable instance for applied users
    applied_table = PrettyTable()
    applied_table.field_names = ["#", "ID", "Username", "Sudo", "Passwordless Sudo"]

    # Add rows to the table
    for i, user in enumerate(applied_users, start=1):
        user_id = user["_id"]
        username = user.get("username", "")
        sudo = user.get("sudo", False)
        passwordless_sudo = user.get("passwordless_sudo", False)
        applied_table.add_row([i, user_id, username, red_cross if sudo else green_check, red_cross if passwordless_sudo else green_check])

    # Set column alignments
    applied_table.align = "l"
    applied_table.align["Sudo"] = "c"  # Align the "Sudo" column to the center
    applied_table.align["Passwordless Sudo"] = "c"  # Align the "Sudo" column to the center

    # Print the table of applied users
    print("\nApplied Sudo Privileges:")
    print(applied_table)

def revoke_all_sudos():
    url = "https://console.jumpcloud.com/api/systemusers/"
    querystring = {
        "fields": "email sudo passwordless_sudo _id username",
        "filter": "",
        "limit": "99",
        "skip": "0",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    user_list = response.json().get("results")

    if not user_list:
        print("No users found.")
        return

    # Create a new PrettyTable instance
    table = PrettyTable()
    table.field_names = ["#", "ID", "Username", "Sudo", "Passwordless Sudo"]

    # Add rows to the table
    for i, user in enumerate(user_list, start=1):
        user_id = user["_id"]
        username = user.get("username", "")
        sudo = user.get("sudo", False)
        passwordless_sudo = user.get("passwordless_sudo", False)
        table.add_row([i, user_id, username, green_check if sudo else red_cross, green_check if passwordless_sudo else red_cross])

    # Set column alignments
    table.align = "l"
    table.align["Sudo"] = "c"  # Align the "Sudo" column to the center
    table.align["Passwordless Sudo"] = "c"  # Align the "Sudo" column to the center

    # Print the table
    print(table)

    # Get user input to confirm the action
    choice = input("Are you sure you want to revoke sudo privileges from these users? (y/n): ")
    if choice.lower() != "y":
        return

    # Revoke sudo privileges with progress bar
    revoked_users = []
    with tqdm(total=len(user_list), desc="Progress", unit="user") as pbar:
        for user in user_list:
            user_id = user["_id"]
            sudo = user.get("sudo", False)
            passwordless_sudo = user.get("passwordless_sudo", False)
            if sudo or passwordless_sudo:
                payload = {
                    "sudo": False,
                    "passwordless_sudo": False,
                }
                update_url = f"https://console.jumpcloud.com/api/systemusers/{user_id}"
                response_update = requests.put(update_url, json=payload, headers=headers)
                if response_update.status_code == 200:
                    user["sudo"] = False
                    user["passwordless_sudo"] = False
                    revoked_users.append(user)
                pbar.update(1)

    # Create a new PrettyTable instance for revoked users
    revoked_table = PrettyTable()
    revoked_table.field_names = ["#", "ID", "Username", "Sudo", "Passwordless Sudo"]

    # Add rows to the table
    for i, user in enumerate(revoked_users, start=1):
        user_id = user["_id"]
        username = user.get("username", "")
        sudo = user.get("sudo", False)
        passwordless_sudo = user.get("passwordless_sudo", False)
        revoked_table.add_row([i, user_id, username, green_check if sudo else red_cross, green_check if passwordless_sudo else red_cross])

    # Set column alignments
    revoked_table.align = "l"
    table.align["Sudo"] = "c"  # Align the "Sudo" column to the center
    table.align["Passwordless Sudo"] = "c"  # Align the "Sudo" column to the center

    # Print the table of revoked users
    print("\nRevoked Sudo Privileges:")
    print(revoked_table)

# Main menu loop
while True:
    try:
        # Display menu options
        print("\nMenu Options:")
        print("(1) List all users")
        print("(2) Search for a user")
        print("(3) Sudo Control")
        print("(0) Exit")

        # Get user input
        choice = input("Enter your choice: ")

        if choice == "1":
            list_all_users()
        elif choice == "2":
            input_text = input("Enter the username (or partial username) to search for: ")
            search_user(input_text)
        elif choice == "3":
            # Sudo Control sub-menu
            while True:
                print("\nSudo Control Options:")
                print("(1) Grant all Sudo's")
                print("(2) Revoke all Sudo's")
                print("(0) Back to Main Menu")

                sub_choice = input("Enter your choice: ")
                if sub_choice == "1":
                    grant_all_sudos()
                elif sub_choice == "2":
                    revoke_all_sudos()
                elif sub_choice == "0":
                    break
                else:
                    print("Invalid choice. Please try again.")

        elif choice == "0":
            print("Exiting the program...")
            sys.exit()
        else:
            print("Invalid choice. Please try again.")
    except KeyboardInterrupt:
        # Handle Ctrl+C interruption
        print("\nCommand interrupted. Returning to Main Menu...")