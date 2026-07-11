from shared import VERSION, safe_input
from greeting import ensure_and_greet_user
from transactions import data_entry, data_read, manage_transaction
from assets import add_asset, update_asset_value
from financial_status import view_current_financial_status
from help_module import help
from subscriptions import add_subscription, manage_subscriptions, process_due_subscriptions


if __name__ == '__main__':
    ensure_and_greet_user()
    print(f"You are currently running CliFin v{VERSION}")
    process_due_subscriptions()

    while True:
        print("\nMain Menu")
        print("1. Create New Transaction Record 💵")
        print("2. Create New Asset Record 💰")
        print("3. Update Value of Existing Asset 💹")
        print("4. Manage Existing Transactions 📝")
        print("5. Add Subscription 📅")
        print("6. Manage Subscriptions ⚙️")
        print("7. View Historical Data 🕒")
        print("8. View Financial Status 🗽")
        print("9. Explain Me! 😣")
        print("10. Get Me Out of Here! 🚪")

        choice = safe_input("Choose an option (1, 2, 3, 4, 5, 6, 7, 8, 9, or 10): ").strip()

        if choice == '1':
            data_entry()
        elif choice == '2':
            add_asset()
        elif choice == '3':
            update_asset_value()
        elif choice == '4':
            manage_transaction()
        elif choice == '5':
            add_subscription()
        elif choice == '6':
            manage_subscriptions()
        elif choice == '7':
            data_read()
        elif choice == '8':
            view_current_financial_status()
        elif choice == '9':
            help()
        elif choice == '10':
            print("Thank you for using CliFin!😎")
            safe_input("Press [Enter] to exit.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, 5, 6, 7, 8, 9, or 10.")

