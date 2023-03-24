import os
import sqlite3

##############
### README ###
##############

#### This file serves for managing the search history of wiki search tool ####
# 1. creating the search history table.
# 2. manual inserting of some records.
# 3. showing all the history records in search history.
# 4. deleting whole seach history (if for some reason we would like to reset the search history)

###############################

# ↓↓↓ FUNCTIONS ↓↓↓
def create_table(database=str, table_name=str, columns_statement=str): # Functin to create / conect database with specified table with specified columns.
                                                             # columns_statement parameter needs to be string with SQL statement as when creating table in sql.
                                                             # for example: 'name TEXT NOT NULL, age INTEGER NOT NULL' 
    # Check if the database file exists
    if not os.path.exists(database):
        print(f"Database '{database}' does not exist. Creating database file '{database}' now.")
    else:
        print(f"Database '{database}' already exists. Connecting to the database file.")

    try:
        # Connect to the database
        conn = sqlite3.connect(database)

        # Create a cursor
        cursor = conn.cursor()

        # Check if the table already exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        result = cursor.fetchone()
        if result:
            print(f"Table '{table_name}' already exists in database '{database}', not creating new table.")
        else:
            # Create the table
            cursor.execute(f'CREATE TABLE {table_name} ({columns_statement})')
            print(f'Table {table_name} created in database {database}')

        # Save the changes
        conn.commit()
    except sqlite3.OperationalError as e:
        # The database does not exist
        if "no such table" in str(e):
            print(f"Database '{database}' does not exist")
        else:
            print(f'Error when connectiong to the database: {e}.')
    except Exception as e:
        print(f'Error when connectiong to the database: {e}')
    finally:
        # Close the connection
        conn.close()

def insert_record(database=str, table_name=str, table_columns=list, item_values=list): # Function to insert new item into the table. values order must match the table_columns order.
    # Connect to the database
    conn = sqlite3.connect(database)

    # Create a cursor
    cursor = conn.cursor()

    # Insert the new item into the table
        
    # Destinations columns SQL clause str
    columns_str = ", ".join((f'"{t_c}"' for t_c in table_columns))
    # print(columns_str)

    # Values placeholdesr str
    placeholders = ", ".join(["?" for c in table_columns])
    # print(placeholders)

    # Values to be inserted for record (must be is same order as column order)
    # print(item_values)

    # Insert into table
    print(f'INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})', tuple(item_values))
    cursor.execute(f'INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})', tuple(item_values))

    # print(f'Record succesfully inserted into database:')
    # Check the newly added record
    
    # Last added record rowid
    last_added_row_id = cursor.lastrowid
    # print(f'posledni pridane id: {last_added_row_id}')

    cursor.execute(f'SELECT rowid, * FROM {table_name} WHERE rowid={last_added_row_id}')
    result = cursor.fetchone()
    print(f'Kontrola posleniho pridaneho zaznamu:')
    print(result)

    # Save the changes
    conn.commit()

    # Close the connection
    conn.close()

    return result

def get_table_columns(database=str, table_name=str): # Returns list of columns names.

    # Connect to the database
    conn = sqlite3.connect(database)

    # Create a cursor
    cursor = conn.cursor()

    # Retrieve the column names for the materials table
    cursor.execute(f'PRAGMA table_info({table_name})')

    # Store the column names in a list
    column_names = [row[1] for row in cursor if row[1] != "id"]

    # Close the connection
    conn.close()
    return column_names

def show_all_records_database_in_table(database=str, table_name=str): # Shows all records in given database and table with its headings.
    
    # Connect to the database
    conn = sqlite3.connect(database)

    # Create a cursor
    cursor = conn.cursor()

    # Retrieve the column names for table
    column_names = get_table_columns(database, f'"{table_name}"')

    # Select all rows from the materials table
    cursor.execute(f'SELECT rowid, * FROM "{table_name}"')
    # Print count of records
    rows = cursor.fetchall()
    print(f'{len(rows)} records in database {database}, table {table_name}:\n')

    # Print the records
    print(f'Showing records in database: {database}, in table: {table_name}.\n')    

    # Adding ID colum name to column names (optional)
    # column_names.insert(0, "ID")

    # Print the column headings
    print('\t'.join(column_names))

    # Iterate over the result set and print the rows

    for row in rows:
        print('\t'.join([str(x) for x in row]))

    # Close the connection
    conn.close()

def confirm_deletion(command=str): # Ask user for deletion confirmation. Return True / False.
    # Check if A - Delete  OR N - Abort deletion.
    while command.strip().lower() not in ['c','a']:
        command = input(f'Confirm or Abort deletion [C]onfirm / [A]bort:\n')
    if command.strip().lower() == "c":
        return True          
    return False

def delete_all_records(database=str, table_name=str): # Deletes all record from table (no conditions specified). Return deleted records.
    # Connect to database
    conn = sqlite3.connect(database)

    # Create cursor
    cursor = conn.cursor()

    # get count of records to be deleted
    cursor.execute(f'SELECT rowid, * FROM "{table_name}"')
    records_to_be_deleted = cursor.fetchall()
    count_records_to_be_deleted = len(records_to_be_deleted)

    # Ask user for confirmation of deletion
    if records_to_be_deleted:
        print(f'There are: {count_records_to_be_deleted} search history records about do be deleted.')
        command = input(f'Do you really want to delete all search history? This cannot be undone. [C]onfirm / [A]bort:\n')
        if not confirm_deletion(command):
            print(f'Aborting deletion. Nothing deleted.')
            return

        # Construct the SQL statement
        cursor.execute(f'DELETE FROM "{table_name}"')

        # Commit the transaction
        conn.commit()

        # Close the connection
        conn.close()

        print(f'{count_records_to_be_deleted} search history results succesfully deleted from database: {database}')
        return records_to_be_deleted
    
    return
# ↑↑↑ FUNCTIONS ↑↑↑

###############################

# ↓↓↓ CODE ↓↓↓
current_folder = os.path.abspath(os.path.dirname(__file__))
search_histrory_path = f'{current_folder}\search_history.db'

# 1. Create search history database
#create_table(search_histrory_path, "history", "searched_topic TEXT NOT NULL, search_result TEXT, last_search_date TEXT NOT NULL")

# 2. insert Ondra
#insert_record(search_histrory_path, "history", ["searched_topic", "search_result", "last_search_date"], ["ondra", "zrzavy kluk", "2023-03-23"] )

# Show all revcords in search history
show_all_records_database_in_table(search_histrory_path, "history")

# Clear search history (careful, this cannnot be undone - all non-backuped records will be lost)
#delete_all_records(search_histrory_path, "history")

# ↑↑↑ CODE ↑↑↑

###############################