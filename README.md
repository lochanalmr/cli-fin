# CliFin
Clifin is a simple command line tool for tracking finances. All databases are created and stored locally. The local sqlite database files are fully readable by other database management tools, and can be synced between devices with your preferred cloud storage service. Enter sensitive data at your own risk, as the databases are not encrypted.

## Functionality
- Entering transactions (income & expenses with category and amount)
- Viewing summary of transactions of a specified month
- Viewing raw data of transactions of a specified month, as a table
- Exporting raw data of transactions of a specified month, as a labeled .csv file
- Viewing financial status along with other assets other than income, to show net asset value
- Entering other assets such as fixed deposits, investments, and other assets
- Updating value of assets

## Technology stack
- Python 3.14
- sqlite3
- json

## Using the program
Inside the folder with the python script inside your preferred terminal emulator, and run `python clifin_main.py`. 

Upon entering your first transaction, a database called `storage.db` will be created. When you add assets through the main menu, `assets.db` will be created. Do not delete these files, unless you want to completely delete all stored data. Functionality for editing previous transactions is not provided, so if you want to edit previous transactions, you may need to use a database management tool. However, updating asset values stored in `assets.db` is supported within the program. `user_config.json` contains the name entered in the first run, and can be changed if required by editing it.

When data is exported as a .csv file, it will be available within the same folder the program runs from. The database file will be named in this format: `transactions_[year]_[month no.]_[month name]`. The .csv file will include the exact date and time of when the transaction was entered, income/expense, category of income/expense, and amount of the transaction.

## Database structure
`storage.db` contains transaction data. <br>It contains: `id` (automatically incremented), `amount` with sign, `category`, `type`, `created_at`.

`assets.db` contains assets data. <br>It contains: `id` (automatically incremented), `name`, `asset_type`, `amount`, `created_at`.