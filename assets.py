from datetime import datetime

from shared import (
    ASSETS_DB,
    db_cursor,
    get_choice,
    get_int_input,
    get_positive_float,
    safe_input,
)


ASSET_TYPES = {
    '1': 'Fixed Deposit',
    '2': 'Investment',
    '3': 'Other Asset',
}


def get_asset_type():
    print("\nAsset Types:")
    for code, asset_type in ASSET_TYPES.items():
        print(f"{code}. {asset_type}")
    asset_choice = get_choice(
        "Enter asset type code (1, 2, or 3): ",
        list(ASSET_TYPES.keys()),
        "Invalid choice. Please enter 1, 2, or 3."
    )
    return ASSET_TYPES[asset_choice]


def add_asset(amount=None):
    asset_type = get_asset_type()

    while True:
        asset_name = safe_input("Enter asset name/description: ").strip()
        if asset_name:
            break
        print("Asset name cannot be empty.")

    if amount is None:
        amount = get_positive_float("Enter amount: ")

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_cursor(ASSETS_DB, commit=True) as c:
        c.execute(
            "INSERT INTO assets (name, asset_type, amount, created_at) VALUES (?, ?, ?, ?)",
            (asset_name, asset_type, amount, created_at)
        )
    print("Asset added successfully.")


def list_assets(db_name=ASSETS_DB):
    with db_cursor(db_name) as c:
        c.execute("SELECT id, name, asset_type, amount FROM assets ORDER BY id")
        return c.fetchall()


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

    if asset_id is None:
        asset_id = get_int_input(
            "Enter asset ID to update: ",
            "Invalid ID. Please enter a valid number.",
            lambda aid: any(existing_id == aid for existing_id, _, _, _ in assets),
            "Asset ID not found. Please enter a valid ID."
        )
    else:
        asset_id = int(asset_id)

    if new_amount is None:
        new_amount = get_positive_float("Enter new amount: ")
    else:
        new_amount = float(new_amount)

    with db_cursor(db_name, commit=True) as c:
        c.execute("UPDATE assets SET amount = ? WHERE id = ?", (new_amount, asset_id))
    print("Asset value updated successfully!")
    return True
