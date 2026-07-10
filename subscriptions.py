from datetime import date, datetime, timedelta
import re

from shared import init_db, init_subscriptions_db, safe_input


def _get_expense_categories():
    return {
        '1': 'Entertainment',
        '2': 'Food',
        '3': 'Asset Purchase',
        '4': 'Travel',
        '5': 'Other'
    }


def parse_subscription_date(value):
    try:
        if not isinstance(value, str):
            return None
        if not re.fullmatch(r"\d{2}-\d{2}-\d{4}", value):
            return None
        day_str, month_str, year_str = value.split('-')
        day = int(day_str)
        month = int(month_str)
        year = int(year_str)
        return date(year, month, day)
    except ValueError:
        return None


def _format_date(value):
    if isinstance(value, date):
        return value.strftime('%d-%m-%Y')
    return value


def calculate_next_due_date(current_due_date, frequency):
    if not isinstance(current_due_date, date):
        return None

    freq = (frequency or '').strip().lower()
    if freq == 'yearly':
        year = current_due_date.year + 1
        try:
            return date(year, current_due_date.month, current_due_date.day)
        except ValueError:
            return date(year, 3, 1)

    if freq == 'monthly':
        month = current_due_date.month + 1
        year = current_due_date.year
        while month > 12:
            month -= 12
            year += 1
        try:
            return date(year, month, current_due_date.day)
        except ValueError:
            return date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)

    if freq == 'weekly':
        return current_due_date + timedelta(days=7)

    if freq == 'daily':
        return current_due_date + timedelta(days=1)

    return None


def _insert_subscription_record(name, amount, frequency, start_date, category, status='active'):
    print("Connecting to subscriptions database...")
    conn = init_subscriptions_db()
    print("Successfully connected to subscriptions database!")
    c = conn.cursor()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("Subscription record is being updated...")
    c.execute(
        """
        INSERT INTO subscriptions (name, amount, frequency, start_date, next_due_date, last_processed_at, category, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, amount, frequency, start_date, start_date, None, category, status, created_at)
    )
    conn.commit()
    print("Subscription record was successfully updated!")
    conn.close()


def add_subscription():
    print('\nAdd Subscription')
    while True:
        name = safe_input('Enter subscription name: ').strip()
        if name:
            break
        print('Subscription name cannot be empty.')

    while True:
        amount_input = safe_input('Enter subscription amount: ').strip()
        try:
            amount = float(amount_input)
        except ValueError:
            print('Invalid amount. Please enter a valid number.')
            continue
        if amount <= 0:
            print('Amount must be greater than 0.')
            continue
        break

    while True:
        print('Select frequency:')
        print('1. Yearly')
        print('2. Monthly')
        print('3. Weekly')
        print('4. Daily')
        frequency_choice = safe_input('Enter frequency code: ').strip()
        if frequency_choice == '1':
            frequency = 'yearly'
            break
        if frequency_choice == '2':
            frequency = 'monthly'
            break
        if frequency_choice == '3':
            frequency = 'weekly'
            break
        if frequency_choice == '4':
            frequency = 'daily'
            break
        print('Invalid choice. Please enter 1, 2, 3, or 4.')

    while True:
        start_date_input = safe_input('Enter start date (DD-MM-YYYY): ').strip()
        parsed_date = parse_subscription_date(start_date_input)
        if parsed_date is not None:
            start_date = parsed_date
            break
        print('Invalid date. Please use DD-MM-YYYY with a valid day, month, and year.')

    categories = _get_expense_categories()
    print('Select a subscription type:')
    for code, category_name in categories.items():
        print(f'{code}. {category_name}')

    while True:
        category_choice = safe_input('Enter category code: ').strip()
        if category_choice in categories:
            category = categories[category_choice]
            break
        print('Invalid category code. Please enter one of the listed options.')

    _insert_subscription_record(name, amount, frequency, start_date.strftime('%d-%m-%Y'), category)
    print('Subscription added successfully.')


def _fetch_subscriptions():
    print("Connecting to subscriptions database...")
    conn = init_subscriptions_db()
    print("Successfully connected to subscriptions database...")
    c = conn.cursor()
    c.execute(
        "SELECT id, name, amount, frequency, start_date, next_due_date, last_processed_at, category, status, created_at FROM subscriptions ORDER BY next_due_date"
    )
    rows = c.fetchall()
    conn.close()
    print("All subscriptions were sucessfully fetched from the database!")
    return rows


def _display_subscriptions(rows):
    if not rows:
        print('No subscriptions found.')
        return False

    print('\nAvailable subscriptions')
    print(f"{'ID':<3} | {'Name':<20} | {'Amount':>10} | {'Frequency':<8} | {'Next Due':<10} | {'Category':<12}")
    print('-' * 88)
    for record_id, name, amount, frequency, start_date, next_due_date, last_processed_at, category, status, created_at in rows:
        print(f"{record_id:<3} | {name:<20} | {amount:>10.2f} | {frequency:<8} | {next_due_date:<10} | {category:<12}")
    return True


def update_subscription():
    print('\nUpdate Subscription')
    rows = _fetch_subscriptions()
    if not _display_subscriptions(rows):
        return

    while True:
        subscription_id_input = safe_input('Enter subscription ID to select: ').strip()
        try:
            subscription_id = int(subscription_id_input)
        except ValueError:
            print('Invalid ID. Please enter a valid number.')
            continue
        selected_subscription = next((row for row in rows if row[0] == subscription_id), None)
        if selected_subscription is None:
            print('No subscription found with that ID.')
            continue
        break

    record_id, existing_name, existing_amount, existing_frequency, existing_start_date, existing_next_due_date, existing_last_processed_at, existing_category, existing_status, existing_created_at = selected_subscription

    while True:
        print('\nLeave a field blank to keep the current value.')

        name_input = safe_input(f'Edit name [{existing_name}]: ').strip()
        new_name = name_input if name_input else existing_name

        amount_input = safe_input(f'Edit amount [{existing_amount:.2f}]: ').strip()
        if amount_input:
            try:
                new_amount = float(amount_input)
            except ValueError:
                print('Invalid amount. Please enter a valid number.')
                continue
            if new_amount <= 0:
                print('Amount must be greater than 0.')
                continue
        else:
            new_amount = existing_amount

        while True:
            frequency_input = safe_input(f'Edit frequency [{existing_frequency}]: ').strip().lower()
            if not frequency_input:
                new_frequency = existing_frequency
                break
            if frequency_input in {'1', 'yearly'}:
                new_frequency = 'yearly'
                break
            if frequency_input in {'2', 'monthly'}:
                new_frequency = 'monthly'
                break
            if frequency_input in {'3', 'weekly'}:
                new_frequency = 'weekly'
                break
            if frequency_input in {'4', 'daily'}:
                new_frequency = 'daily'
                break
            print('Invalid frequency. Please enter yearly, monthly, weekly, daily, or the corresponding number.')

        while True:
            start_date_input = safe_input(f'Edit start date [{existing_start_date}] (DD-MM-YYYY): ').strip()
            if not start_date_input:
                new_start_date = existing_start_date
                break
            parsed_date = parse_subscription_date(start_date_input)
            if parsed_date is not None:
                new_start_date = parsed_date.strftime('%d-%m-%Y')
                break
            print('Invalid date. Please use DD-MM-YYYY with a valid day, month, and year.')

        categories = _get_expense_categories()
        print('Select a category:')
        for code, name in categories.items():
            print(f'{code}. {name}')
        category_input = safe_input(f'Edit category [{existing_category}]: ').strip()
        if category_input:
            if category_input in categories:
                new_category = categories[category_input]
            else:
                print('Invalid category code. Please enter one of the listed options.')
                continue
        else:
            new_category = existing_category

        confirmation = safe_input('Confirm this edit? (y/n): ').strip().lower()
        if confirmation in {'y', 'yes'}:
            conn = init_subscriptions_db()
            c = conn.cursor()
            c.execute(
                "UPDATE subscriptions SET name=?, amount=?, frequency=?, start_date=?, next_due_date=?, category=? WHERE id=?",
                (new_name, new_amount, new_frequency, new_start_date, new_start_date, new_category, record_id)
            )
            conn.commit()
            conn.close()
            print('Subscription updated successfully.')
            return
        if confirmation in {'n', 'no'}:
            print('Edit cancelled. You can modify the subscription again.')
            continue
        print('Invalid choice. Please enter y or n.')


def discontinue_subscription():
    print('\nDiscontinue Subscription')
    rows = _fetch_subscriptions()
    if not _display_subscriptions(rows):
        return

    while True:
        subscription_id_input = safe_input('Enter subscription ID to discontinue: ').strip()
        try:
            subscription_id = int(subscription_id_input)
        except ValueError:
            print('Invalid ID. Please enter a valid number.')
            continue
        selected_subscription = next((row for row in rows if row[0] == subscription_id), None)
        if selected_subscription is None:
            print('No subscription found with that ID.')
            continue
        break

    confirmation = safe_input('Type y to confirm discontinuation: ').strip().lower()
    if confirmation in {'y', 'yes'}:
        conn = init_subscriptions_db()
        c = conn.cursor()
        c.execute("UPDATE subscriptions SET status='discontinued' WHERE id=?", (subscription_id,))
        conn.commit()
        conn.close()
        print('Subscription discontinued successfully.')
    else:
        print('Discontinuation cancelled.')


def manage_subscriptions():
    while True:
        print('\nManage Subscriptions')
        print('1. Add New Subscription')
        print('2. Update Existing Subscription')
        print('3. Discontinue Subscription')
        print('4. Back to Main Menu')
        choice = safe_input('Choose an option (1, 2, 3, or 4): ').strip()
        if choice == '1':
            add_subscription()
        elif choice == '2':
            update_subscription()
        elif choice == '3':
            discontinue_subscription()
        elif choice == '4':
            return
        else:
            print('Invalid choice. Please enter 1, 2, 3, or 4.')


def should_prompt_for_due_subscription(due_date, created_at, today=None, pending_due_dates=None):
    if today is None:
        today = date.today()

    if pending_due_dates is None:
        pending_due_dates = [due_date]

    if len(pending_due_dates) > 1:
        return True

    try:
        created_dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        return False

    if due_date.year != today.year or due_date.month != today.month:
        return False

    if due_date < created_dt.date():
        return True

    return False


def collect_pending_due_dates(current_due_date, today, frequency):
    if not isinstance(current_due_date, date) or not isinstance(today, date):
        return []

    if current_due_date > today:
        return []

    pending = []
    cursor = current_due_date
    while cursor <= today:
        pending.append(cursor)
        cursor = calculate_next_due_date(cursor, frequency)
    return pending


def process_due_subscriptions():
    print('\nConnecting to subscriptions database...')
    conn = init_subscriptions_db()
    print("Subscriptions database successfully connected!")
    c = conn.cursor()
    c.execute(
        "SELECT id, name, amount, frequency, start_date, next_due_date, category, created_at FROM subscriptions WHERE status = 'active'"
    )
    rows = c.fetchall()
    conn.close()

    today = date.today()
    processed_any = False
    for record_id, name, amount, frequency, start_date, next_due_date, category, created_at_value in rows:
        try:
            due_date = date.fromisoformat(next_due_date)
        except (TypeError, ValueError):
            try:
                due_date = datetime.strptime(next_due_date, '%d-%m-%Y').date()
            except ValueError:
                continue

        if due_date > today:
            continue

        processed_any = True
        pending_due_dates = collect_pending_due_dates(due_date, today, frequency)
        if pending_due_dates:
            prompt_for_transaction = should_prompt_for_due_subscription(
                due_date,
                created_at_value,
                today=today,
                pending_due_dates=pending_due_dates
            )
            if prompt_for_transaction:
                should_add = safe_input(f"Subscription '{name}' has {len(pending_due_dates)} pending debit(s). Add all pending expenses at once? (y/n): ").strip().lower()
                should_add_expense = should_add in {'y', 'yes'}
            else:
                should_add_expense = True

            processing_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if should_add_expense:
                for pending_due in pending_due_dates:
                    print(f"Due subscription found. Subscription was added as an expense for {pending_due.strftime('%d-%m-%Y')}.")
                    conn = init_db()
                    expense_cursor = conn.cursor()
                    expense_cursor.execute(
                        "INSERT INTO storage (amount, category, type, created_at) VALUES (?, ?, ?, ?)",
                        (-abs(amount), category, 'expense', processing_time)
                    )
                    conn.commit()
                    conn.close()

                next_due_date_obj = pending_due_dates[-1]
                if next_due_date_obj < today:
                    next_due_date_obj = calculate_next_due_date(next_due_date_obj, frequency)
                if next_due_date_obj is None:
                    continue

                conn = init_subscriptions_db()
                schedule_cursor = conn.cursor()
                schedule_cursor.execute(
                    "UPDATE subscriptions SET status='processed', last_processed_at=? WHERE id=?",
                    (processing_time, record_id)
                )
                schedule_cursor.execute(
                    """
                    INSERT INTO subscriptions (name, amount, frequency, start_date, next_due_date, last_processed_at, category, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (name, amount, frequency, start_date, next_due_date_obj.strftime('%Y-%m-%d'), None, category, 'active', processing_time)
                )
                conn.commit()
                conn.close()

                if prompt_for_transaction and not should_add_expense:
                    print('Subscription skipped. No expense was added.')
            else:
                conn = init_subscriptions_db()
                schedule_cursor = conn.cursor()
                schedule_cursor.execute(
                    "UPDATE subscriptions SET status='processed', last_processed_at=? WHERE id=?",
                    (processing_time, record_id)
                )
                conn.commit()
                conn.close()
                print('Subscription skipped. No expense was added.')

    if not processed_any:
        print('No new subscription debits found.')
