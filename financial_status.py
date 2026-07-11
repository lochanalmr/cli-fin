from shared import ASSETS_DB, STORAGE_DB, db_cursor, format_currency, format_table, print_table


def view_current_financial_status():
    print("\n" + "=" * 60)
    print("View Financial Status")
    print("=" * 60)

    with db_cursor(STORAGE_DB) as c:
        c.execute("SELECT amount, type FROM storage")
        rows = c.fetchall()

    total_income = 0.0
    total_expenses = 0.0
    for amount, transaction_type in rows:
        normalized_type = transaction_type.lower()
        if normalized_type == 'income':
            total_income += abs(amount)
        elif normalized_type == 'expense':
            total_expenses += abs(amount)

    spendable_balance = total_income - total_expenses

    print(f"\nSpendable balance: {format_currency(spendable_balance)}")

    with db_cursor(ASSETS_DB) as asset_cursor:
        asset_cursor.execute("SELECT name, asset_type, amount FROM assets ORDER BY created_at")
        asset_rows = asset_cursor.fetchall()

    asset_totals = {}
    for _, asset_type, amount in asset_rows:
        asset_totals[asset_type] = asset_totals.get(asset_type, 0.0) + abs(amount)

    print("\nOther assets:")
    if asset_rows:
        headers = ['Asset Type', 'Total Amount']
        table_rows = [[asset_type, format_currency(total)] for asset_type, total in sorted(asset_totals.items())]
        print_table(headers, table_rows)
    else:
        print("- None")

    other_assets_total = sum(asset_totals.values())
    net_asset_value = spendable_balance + other_assets_total
    print(f"\nTotal other assets: {format_currency(other_assets_total)}")
    print(f"Estimated net asset value: {format_currency(net_asset_value)}")
    return
