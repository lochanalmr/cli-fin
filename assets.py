from datetime import datetime

from shared import ASSETS_DB, init_assets_db, safe_input


def add_asset_entry():
    print("\nAsset Types:")
    print("1. Fixed Deposit")
    print("2. Investment")
    print("3. Other Asset")

    while True:
        asset_choice = safe_input("Enter asset type code (1, 2, or 3): ").strip()
        if asset_choice == '1':
            asset_type = 'Fixed Deposit'
            break
        if asset_choice == '2':
            asset_type = 'Investment'
            break
        if asset_choice == '3':
            asset_type = 'Other Asset'
            break
        print("Invalid choice. Please enter 1, 2, or 3.")

    while True:
        asset_name = safe_input("Enter asset name/description: ").strip()
        if asset_name:
            break
        print("Asset name cannot be empty.")

    while True:
        amount_input = safe_input("Enter amount: ").strip()
        try:
            amount = float(amount_input)
        except ValueError:
            print("Invalid amount. Please enter a valid number.")
            continue

        if amount <= 0:
            print("Amount must be greater than 0.")
            continue

        break

    print("Connecting to database...")
    conn = init_assets_db()
    c = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("Writing to database...")
    c.execute(
        "INSERT INTO assets (name, asset_type, amount, created_at) VALUES (?, ?, ?, ?)",
        (asset_name, asset_type, amount, created_at)
    )
    conn.commit()
    conn.close()
    print("Asset added successfully.")


def list_assets(db_name=ASSETS_DB):
    conn = init_assets_db(db_name)
    c = conn.cursor()
    c.execute("SELECT id, name, asset_type, amount FROM assets ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows


def update_asset_value(asset_id=None, new_amount=None, db_name=ASSETS_DB):
    print("\nUpdate Asset Value")
    assets = list_assets(db_name)

    if not assets:
        print("No assets available to update.")
        return False

    print("Available assets:")
    print(f"{'ID':<3} | {'Name':<20} | {'Type':<15} | {'Amount':>10}")
    print("-" * 60)
    for record_id, name, asset_type, amount in assets:
        print(f"{record_id:<3} | {name:<20} | {asset_type:<15} | {amount:>10.2f}")

    while True:
        if asset_id is None:
            asset_id_input = safe_input("Enter asset ID to update: ").strip()
            try:
                asset_id = int(asset_id_input)
            except ValueError:
                print("Invalid ID. Please enter a valid number.")
                continue
        else:
            asset_id = int(asset_id)

        if any(existing_id == asset_id for existing_id, _, _, _ in assets):
            break
        print("Asset ID not found. Please enter a valid ID.")

    while True:
        if new_amount is None:
            amount_input = safe_input("Enter new amount: ").strip()
            try:
                new_amount = float(amount_input)
            except ValueError:
                print("Invalid amount. Please enter a valid number.")
                continue
        else:
            new_amount = float(new_amount)

        if new_amount <= 0:
            print("Amount must be greater than 0.")
            continue
        break

    conn = init_assets_db(db_name)
    c = conn.cursor()
    c.execute("UPDATE assets SET amount = ? WHERE id = ?", (new_amount, asset_id))
    conn.commit()
    conn.close()
    print("Asset value updated successfully.")
    return True
