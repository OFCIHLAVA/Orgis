# Use BeautifulSoup to transform stuff returned from Wiki
from bs4 import BeautifulSoup
# Use requests to get response from Wiki
import requests
# library for working with search history database
import sqlite3

import sys
import os
import datetime

##############
### README ###
##############

# ↓↓↓ PROGRAM LOGIC ↓↓↓
###############################
# 1. Program asks for imput from user, what topic should be searched on cs wikipedia.
#
# 2. Program takes the input and first checks it against the search history, if that topic was already searched for in the past.
# • If was already searched:
#       → shows the previous result and ask, if should search again anyway.
#       • If user does not want to search the topic again:
#            → Restart and ask for new search topic.
#       • Else if user wants to search that topic again anyway:
#            → Searches for the topic.             
# • Else if was not searched before
#       → Searches for the topic. 
#
# 3. Program searches for given topic on cz wikipedia, gets HTML text using REQUESTS library and extracts relevant infomation from it using BEAUTIFULLSOUP4 library.
# There are 3 resUlt cases:
# [A] CASE - page with name exactly matching searched topic exists on wiki → soup will be article page for searched topic.
#       A1. check, if exact page exists by searchig for div tags with class"mw-parser-output" in result page.
#           • IF exists: 
#               A2. → extractS content paragraphs from result page.
#                   → saves FOUND result in search history with todays date.                      
#                   → END CASE [A]
#
#           • IF not exists:
#                   → saves NONE result in search history with todays date.
#                   → jump to [B] CASE.
#                   → END CASE [A]
# [B] CASE - page with name exactly matching searched topic does not exist on wiki, but some related articles exist (articles with searched string in them).
#       B1. try to get href to related aricles search ("Hledat „XXX“ v jiných článcích.")
#           • IF href found:
#               B2. → get request response from URL from found href.
#               B3. → try to get list of related articles on page.
#                   • IF exist:
#                       B4. → try to get list of titles of related articles.
#                           → END CASE [B]   
#                   • IF not exists:
#                           → jump to [C] CASE
#                           → END CASE [B]
# [C] CASE - page with name exactly matching searched topic does not exist on wiki, and also no related articles exist.
#    → saves NONE result in search history with todays date.

# ↑↑↑ PROGRAM LOGIC ↑↑↑
###############################
# ↓↓↓ FUNCTIONS ↓↓↓

# Wiki search functions:
def search_again(command=str): # Determines if should be topic searched again. Return True / False.
    # Check if A - search again OR N - do not search again.
    while command.strip().lower() not in ['a','n']:
        command = input(f'Chceš znovu hledat? [A]no / [N]e:\n')
    if command.strip().lower() == "a":
        return True          
    return False

def find_page_header(soup_page=str): # Takes soup object from wiki HTML page text and returns 1st Header of that page as text string. Header tag identified as span tag with 'class = "mw-page-title-main"'. 
    header = soup_page.find("span", class_ = "mw-page-title-main").text
    return header    

def find_paragraphs_div(soup_page=str): # Takes soup object from wiki HTML page text and returns list of div tags containing article content paragraphs of that page. Divs indentified as 'class = "mw-parser-output"'.
    content_div_tags = soup_page.find_all("div", class_ = "mw-parser-output")
    return content_div_tags

def find_direct_child_paragraphs(soup_div=str): # Takes soup object div tag and tries to find all the direct child (div tag is direct parent of these p tags) p tags in it. This checks, if given div tag is the one to extract paragraphs from.
    child_paragraphs = soup_div.find_all("p", recursive = False)
    return child_paragraphs

def get_first_paragraph(soup_div=str, div_paragraphs=list): # Takes list of p tags and tries to get first relevant article paragraph from them. Also checks, if result text is not empty text / or very short text - in such case returns whole div tag as text as result.   
    result_text = ""
    for i, paragraph in enumerate(div_paragraphs):
        if is_valid_paragraph(paragraph):        
            result_text += paragraph.text
        if result_text and len(result_text.split(" ")) > 20:
            break
    else:
        result_text = soup_div.text
    return result_text

def is_valid_paragraph(paragraph_tag=str): # Checks if paragraph contain some words. Paragraphs with zero characters after replacing blanks, tabs and new lines are considered non valid.
    paragraphs_characters = paragraph_tag.text.replace(" ", "").replace("\t", "").replace("\n", "").replace(" ", "")    
    return True if len(paragraphs_characters) != 0 else False

def is_non_existing_article(soup_page=str): # Takes soup object from wiki HTML page text and searches for b tag containing text : "Ve Wikipedii dosud neexistuje stránka se jménem XXX.", where XXX is searhed topic. Returns True, if b tag found → non existing article, else returns False.
    b_tags = soup_page.find_all("b")    
    if b_tags:    
        for b_tag in b_tags:
            if "Ve Wikipedii dosud neexistuje stránka" in b_tag.text:
                # print(f'Such article - {searched_topic} - does not exist in Wikipedia yet.')
                return True
    return False    

def find_related_articles_page(soup_page=str): # Takes soup object from wiki HTML page text and searches for a tag leading to page with related articles.    
    # One of hrefs on this page should lead to page with related articles    
    search_in_other_articles_href = soup_page.find_all("a")
    # If found href tag with text matching "Hledat „{searched_topic}“ v jiných článcích." → get response from that href to see realted articles
    if search_in_other_articles_href:
        for href in search_in_other_articles_href:
            if href.text.lower() == f'Hledat „{searched_topic}“ v jiných článcích.'.lower():
                href_to_related_articles = f'https://cs.wikipedia.org{href["href"]}'
                # print(href_to_related_articles)
                return href_to_related_articles
    return 

def related_articles_exist(soup_page=str): # Takes soup object from HTML page text and tries to find p tag with class="mw-search-nonefound" → no result found.
    if soup_page.find("p", class_ = "mw-search-nonefound"):
        return False
    return True

def find_related_articles_titles(soup_page=str): # Takes soup object from HTML page text and tries to find div tags with class="mw-search-result-heading" → these should be all titles of found related articles. If none found, it should mean, that href to related resul leads to one specific article instead.
    # Try to find div tag with list of related articles
    related_articles_div_tags = soup_page.find_all("div", class_="mw-search-result-heading")
    # If found → extract list of related articles titles
    if related_articles_div_tags:
        related_articles_titles = [article.a['title'] for article in related_articles_div_tags]
        return related_articles_titles
    # Else there is only 1 related article → get its title
    related_articles_titles = [soup_page.find("span", class_="mw-page-title-main").text]
    return related_articles_titles

# Search history functions ↓↓↓
def check_if_topic_already_searched(database=str, table_name=str, topic_column=list, topic_values=list): # queries history db, if searched string was already searched for in the past.
        # Function to get specific record/records from database based on criteria passed to function.
        # Provide list of columns and list of values for these columns.
        # Returns list of tuples, tuiples being found records.
    
    # Connect to the database
    conn = sqlite3.connect(database)

    # Create a cursor
    cursor = conn.cursor()

    # Execute a SELECT statement for record based on criteria provided  
    
    # Create the WHERE clause of the SQL statement to select columns from table in database to compare with criteria provided.
    columns_to_select_str = "=? AND ".join([f'"{name}"' for name in topic_column])

    # Create the SELECT statement
    #print(f'SELECT rowid, * FROM "{table_name}" WHERE {columns_to_select_str}=?', tuple(topic_values))
    cursor.execute(f'SELECT rowid, * FROM "{table_name}" WHERE {columns_to_select_str}=?', tuple(topic_values))    

    # Fetch result of the query
    result = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return result

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
    #print(f'INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})', tuple(item_values))
    cursor.execute(f'INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})', tuple(item_values))

    # print(f'Record succesfully inserted into database:')
    # Check the newly added record
    
    # Last added record rowid
    last_added_row_id = cursor.lastrowid
    # print(f'posledni pridane id: {last_added_row_id}')

    cursor.execute(f'SELECT rowid, * FROM {table_name} WHERE rowid={last_added_row_id}')
    result = cursor.fetchone()
    #print(f'Kontrola posleniho pridaneho zaznamu:')
    #print(result)

    # Save the changes
    conn.commit()

    # Close the connection
    conn.close()

    return result

def update_record(database=str, table_name=str, item_column_name=str, item=str, table_column_names=list, item_values=list): # Updates values of records for existing item in database - Function to update values of item already found in table, if same item with different values is beeing added to table
    #print(f'Updating record...')
    # Connect to the database
    conn = sqlite3.connect(database)

    # Create a cursor
    cursor = conn.cursor()

    # Update item with new values provided

    # Create the SET SQL str statement (what columns we want to update in format x=?, y=? ...)    
    set_columns_str = "=?, ".join(f'"{t_c}"' for t_c in table_column_names)

    # Add the item variable for the WHERE clause of SQL statement at the end of the list of new values, so that list matches the order of columns being updated.
    item_values.append(item)

    #print(f'UPDATE "{table_name}" SET {set_columns_str}=? WHERE "{item_column_name}"=?', tuple(item_values))   
    cursor.execute(f'UPDATE "{table_name}" SET {set_columns_str}=? WHERE "{item_column_name}"=?', tuple(item_values))
    # Commit the transaction
    conn.commit()

    # Check the records afer update
    #str_row_ids = ",".join(row_ids_od_records_to_be_changed)
    #cursor.execute(f'SELECT rowid, * FROM "{table_name}" WHERE rowid IN ({str_row_ids})')
    #result = cursor.fetchall()
    #print(f'Updated records: {result}')

    # Close the cursor and connection
    cursor.close()
    conn.close()

    # return updated records
    #return result

def save_search_result_into_history(searched_topic=str, first_relevant_content_article=str, past_result=tuple): # Checks if topic 
    # If this topic not searched before → save result to search history database.
    if not past_result:
        today = datetime.date.today()
        insert_record(search_history_database_path, "history", ["searched_topic", "search_result", "last_search_date"], [str(searched_topic).lower(), first_relevant_content_article, str(today)])
    # else if searched before, update last search date to today, then → check if result is same as last time → if not → update result for that topic in history.
    else:
        # update last search date to today
        today = datetime.date.today()
        update_record(search_history_database_path, "history", "searched_topic", str(searched_topic).lower(), ["last_search_date"], [str(today)])

        # If result different from last search (mby article was updated) → update past result to new result.
        last_search_result = past_result[0][2]
        if first_relevant_content_article != last_search_result:
            update_record(search_history_database_path, "history", "searched_topic", str(searched_topic).lower(), ["search_result"], [first_relevant_content_article]) 
# ↑↑↑ FUNCTIONS ↑↑↑
###############################
# ↓↓↓ CODE ↓↓↓
current_folder = os.path.abspath(os.path.dirname(__file__))
search_history_database_path = f'{current_folder}\search_history.db'

print(f'Input what you want to search for\nOR')
print(f'To EXIT program, type: "exitprogram" into search for input.\n')

# Keep program running until terminated to allow multiple search instances
while True:
    # What user searches for?
    print("\nO čem chceš najít článek na české Wikipedii? (OR exit program by typing: 'exitprogram'): ")
    searched_topic = str(input(f'> ').strip()).lower()
    
    # Check wheter to end program run.
    if searched_topic.lower() == "exitprogram":
        print(f'Terminating program . . .\n')
        sys.exit()      

    # Check, if given topic was already searched for in the past.
    past_result = check_if_topic_already_searched(search_history_database_path, "history", ["searched_topic"], [(str(searched_topic)).lower()])
    # If yes → ask user if want to search that topic again anyway.
    if past_result:
        print(f'Tento výraz - {searched_topic} - už byl hledán {past_result[0][3]}.\nPoslední výsledeK byl:\n\n{past_result[0][2]}')
        print(f'\nChceš znovu hledat výraz - {searched_topic} - na české Wikipedii? [A]no/[N]e')
        command = input(">")
        # if not → restart to search for something different
        if not search_again(command):
            continue    
        else:
            print(f'Jdu znovu hledat článek - {searched_topic} ...\n')
    # If not past result → proceed to search for this topic
    else:    
        print(f'Tento výraz - {searched_topic} - ještě nebyl hledán.')
        print(f'Jdu hledat článek - {searched_topic}\n')

    # Wiki search statement url
    search_url = f'https://cs.wikipedia.org/wiki/{searched_topic}'

    # Get HTML text of wiki page for searched topic
    html_text = requests.get(search_url).text

    # Create soup instance from HTML text
    soup1 = BeautifulSoup(html_text,"html.parser")

    # Try to find all paragraph with content about searched topic
    paragraphs_containers = find_paragraphs_div(soup1)

    ### [A] CASE ###

    # A1. If some found, check if some paragrafs under this parent div iF yes → try to get content from 1st releveant paragraph
    if paragraphs_containers:
        # Try to find some article content in given paragraph container. If some found → extract first relevant paragraph from it.
        for div_tag in paragraphs_containers:
            child_paragraphs = find_direct_child_paragraphs(div_tag)
            # If any found → this div tag is the one, we eant to extract text from
            if child_paragraphs:
                article_div_tag = div_tag
                article_paragraphs = child_paragraphs
                break

        # A2. Extract first relevant paragraph from article
        first_relevant_content_article = get_first_paragraph(article_div_tag, article_paragraphs)

        # Print result message for user           
        print(f'Hurray! I found article with name same as searched topic - {searched_topic} - on czech Wikipedia!')
        print(f'Here is first paragraph of that article:\n')
        print(first_relevant_content_article)
        
        # update search history
        save_search_result_into_history(searched_topic, first_relevant_content_article, past_result)       

    ### [B] CASE ###

    # Else if none content paragraphs found → Given article does not exist → Try to find related articles.
    else:
        # Insert record in search history database with NULL value → indicating such article does not exist.
        first_relevant_content_article = None

        # update search history
        save_search_result_into_history(searched_topic, first_relevant_content_article, past_result)

        # Try to find info about non existing article to be sure whats happening.
        if is_non_existing_article(soup1):
            print(f'Article with searched name does not exist on czech Wikipedia yet.\nSearching for articles with searched string in them now ...')

            # B1. Try to get related articles (wiki search topic in other articles)
            related_articles_href = find_related_articles_page(soup1)
            if not related_articles_href:
                print(f'WARNING! - Error in step B1 → href to related articles search not found. Check why ...')
                input(f'Press ENTER to exit program ...')
                sys.exit()

            # B2. If found → get response from that page → make soup from it and extract related articles from it.
            related_articles_page_text = requests.get(related_articles_href).text
            if not related_articles_page_text:
                print(f'WARNING! - Error in step B2 → could not get response from related articles page. Check why ...')
                # input(f'\nPress ENTER to exit program ...')
                sys.exit()

            # Create soup instance from related arcitles HTML text
            soup2 = BeautifulSoup(related_articles_page_text,"html.parser")

            # B3 Check if any related articles found
            if related_articles_exist(soup2):
                # B4 If any found → extract list of article titles from it
                related_articles_titles = find_related_articles_titles(soup2)
                if not related_articles_titles:
                    print(f'WARNING! - Error in step B3 → related articles found, but could not get their titles. Check why ...')
                    input(f'Press ENTER to exit program ...')
                    sys.exit()                

                # Print result message for user           
                print(f'Too bad, no such article with searched topic - {searched_topic} - exist on czech Wikipedia.')
                print(f'But at least, I found these articles with searched topic - {searched_topic} - in them on czech Wikipedia:\n')
                for title in related_articles_titles:
                    print(title)
                # input(f'\nPress ENTER to exit program ...')
                # sys.exit()
            else:

    ### [C] CASE ###
                # Print result message for user 
                print(f'Too bad, No such article with searched topic - {searched_topic} - exist on czech Wikipedia.')
                print(f'Also, no articles with searched topic - {searched_topic} - in them exist on czech Wikipedia.')
                # input(f'\nPress ENTER to exit program ...')
                # sys.exit()

# ↑↑↑ CODE ↑↑↑
###############################