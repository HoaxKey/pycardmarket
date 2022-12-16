import csv

from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import re
from datetime import datetime

def parse_card_market(csv_file):
    # set the driver
    service = Service(executable_path="/Users/jfoster/Documents/programs/gecko/geckodriver")
    driver = webdriver.Firefox(service=service)
    timeout = 10
    category_id = 1601
    # load this article
    base_url = 'https://www.cardmarket.com/en/FleshAndBlood/Products/Singles'
     #ALL
    expansions_to_ignore = ['All', 'Arcane Rising - First',
                            'Arcane Rising - Unlimited', 'Classic Battles: Rhinar vs Dorinthea',
                            'Crucible of War - First', 'Crucible of War - Unlimited', 'Dynasty', 'Everfest - First', 'FAB Promos',
                            'Hero Promos', 'History Pack 1', 'History Pack 1 - Black Label', 'Ira Welcome Deck', 'Judge Promos',
                            'LGS Promos', 'Monarch - Boltyn Blitz Deck', 'Monarch - Chane Blitz Deck', 'Monarch - First',
                            'Monarch - Levia Blitz Deck', 'Monarch - Prism Blitz Deck', 'Monarch - Unlimited',
                            'OP Promos', 'Promos', 'Slingshot Underground', 'Tales of Aria - Briar Blitz Deck',
                            'Tales of Aria - First', 'Tales of Aria - Lexi Blitz Deck',
                            'Tales of Aria - Oldhim Blitz Deck', 'Tales of Aria - Unlimited', 'Uprising',
                            'Uprising - Dromai Blitz Deck', 'Uprising - Fai Blitz Deck', 'Welcome to Rathe - Alpha',
                            'Welcome to Rathe - Bravo, Showstopper Hero Deck',
                            'Welcome to Rathe - Dorinthea Ironsong Hero Deck',
                            'Welcome to Rathe - Katsu, the Wanderer Hero Deck',
                            'Welcome to Rathe - Rhinar, Reckless Rampage Hero Deck',
                            'Welcome to Rathe - Unlimited']
    expansions_to_ignore = ['All', 'Arcane Rising - First',
                            'Arcane Rising - Unlimited', 'Classic Battles: Rhinar vs Dorinthea',
                            'Crucible of War - First', 'Crucible of War - Unlimited', 'Dynasty', 'Everfest - First', 'FAB Promos',
                            'Hero Promos', 'History Pack 1', 'History Pack 1 - Black Label', 'Ira Welcome Deck', 'Judge Promos',
                            'LGS Promos', 'Monarch - Boltyn Blitz Deck', 'Monarch - Chane Blitz Deck', 'Monarch - First',
                            'Monarch - Levia Blitz Deck', 'Monarch - Unlimited',
                            'OP Promos', 'Promos', 'Slingshot Underground', 'Tales of Aria - Briar Blitz Deck',
                            'Tales of Aria - First', 'Tales of Aria - Lexi Blitz Deck',
                            'Tales of Aria - Oldhim Blitz Deck', 'Tales of Aria - Unlimited', 'Uprising',
                            'Uprising - Dromai Blitz Deck', 'Uprising - Fai Blitz Deck', 'Welcome to Rathe - Alpha',
                            'Welcome to Rathe - Dorinthea Ironsong Hero Deck',
                            'Welcome to Rathe - Katsu, the Wanderer Hero Deck',
                            'Welcome to Rathe - Rhinar, Reckless Rampage Hero Deck',
                            'Welcome to Rathe - Unlimited']

    with open(csv_file, 'a') as f:
        driver.get(base_url)
        try:
            element_present = EC.presence_of_element_located((By.NAME, 'idExpansion'))
            WebDriverWait(driver, timeout).until(element_present)
            expansion_div = driver.find_element(By.NAME, 'idExpansion')
            expansion_options = expansion_div.find_elements(By.TAG_NAME, 'option')
            expansion_map = {}
            for expansion_option in expansion_options:
                expansion_name_raw = expansion_option.text
                expansion_id = expansion_option.get_attribute('value')
                if expansion_name_raw not in expansions_to_ignore:
                    if expansion_name_raw == "Monarch - Prism Blitz Deck":
                        expansion_map['Monarch Blitz Decks'] = expansion_id
                    elif expansion_name_raw == "Welcome to Rathe - Bravo, Showstopper Hero Deck":
                        expansion_map['Hero Decks Welcome to Rathe'] = expansion_id
                    else:
                        expansion_map[expansion_name_raw] = expansion_id

            for expansion_name_raw, expansion_id in expansion_map.items():
                print(f"INFO: Processing {expansion_name_raw}...")
                expansion_slug = re.sub(r'(\-)\1+', '\\1', expansion_name_raw.replace(' ', '-').replace(':', '').replace(',', ''))
                expansion_url_forward = f"https://www.cardmarket.com/en/FleshAndBlood/Products/Singles/{expansion_slug}?idCategory=1601&idExpansion={expansion_id}&idRarity=0&sortBy=collectorsnumber_asc&perSite=20"
                expansion_elems = expansion_name_raw.split(' - ')
                super_expansion = expansion_elems[0]
                edition = "First"
                if len(expansion_elems) > 1:
                    if expansion_elems[1] == "Unlimited":
                        edition = "Unlimited"
                    elif expansion_elems[1] == "Black Label":
                        edition = "Black Label"
                    elif expansion_elems[1] == "Alpha":
                        edition = "First"
                else:
                    super_expansion = expansion_name_raw
                driver.get(expansion_url_forward)
                expansion_url_forward_loaded = False
                while not expansion_url_forward_loaded:
                    try:
                        element_present3 = EC.presence_of_element_located((By.ID, 'pagination'))
                        WebDriverWait(driver, timeout).until(element_present3)
                        #this should only happen if webdriver eait fails and throws us into the except block straight away
                        expansion_url_forward_loaded = True
                    except TimeoutException:
                        print("WARNING: Attempt of expansion_url load failed!")
                        driver.get(expansion_url_forward)
                        pass

                pagination = driver.find_element(By.ID, 'pagination')
                pages = int(re.findall(r'\d+', pagination.find_element(By.CLASS_NAME, 'mx-1').text)[-1])
                last_slug = ''
                slugs = []
                for page in range(1, pages + 1):
                    print(f"INFO: Page {page}...")
                    forward_page_url = f"https://www.cardmarket.com/en/FleshAndBlood/Products/Singles/{expansion_slug}?idRarity=0&sortBy=collectorsnumber_asc&site={page}"
                    driver.get(forward_page_url)
                    forward_page_url_loaded = False
                    while not forward_page_url_loaded:
                        try:
                            element_present2 = EC.presence_of_element_located((By.CLASS_NAME, 'table-body'))
                            WebDriverWait(driver, timeout).until(element_present2)
                            forward_page_url_loaded = True
                        except TimeoutException:
                            print("WARNING: Attempt of page load failed!")
                            driver.get(forward_page_url)
                            pass

                    table_body = driver.find_element(By.CLASS_NAME, 'table-body')
                    #may need a . separator
                    rows = table_body.find_elements(By.XPATH, ("//*[starts-with(@id, 'productRow')]"))
                    for row in rows:
                        image_column_div = row.find_element(By.CLASS_NAME, 'col-icon')
                        image_column_div_span = image_column_div.find_element(By.TAG_NAME, 'span')
                        raw_image_url = image_column_div_span.get_attribute('data-original-title')
                        image_url = 'https://' + re.search(r'static(.*?)jpg',raw_image_url).group(0)
                        expansion_code_column_div = row.find_element(By.CLASS_NAME, 'col-icon.small')
                        expansion_code = expansion_code_column_div.find_element(By.TAG_NAME, 'span').text
                        name_number_rarity_div = row.find_element(By.CLASS_NAME, 'row.no-gutters')
                        name_number_rarity_sub_div = name_number_rarity_div.find_elements(By.TAG_NAME, 'div')
                        name_div = name_number_rarity_sub_div[0]
                        name_div_a = name_div.find_element(By.TAG_NAME, 'a')
                        raw_name = name_div_a.text
                        try:
                            variant = re.findall(r'\((.*?)\)', raw_name)[-1]
                            if variant in ['Red' , 'Yellow', 'Blue']:
                                variant = 'Regular'
                        except IndexError:
                            variant = 'Regular'
                            pass
                        name = raw_name.replace(f" ({variant})", '')
                        url = name_div_a.get_attribute('href')
                        raw_number = name_number_rarity_sub_div[1].text
                        collector_number = raw_number.split('-')[0]
                        rarity_div = name_number_rarity_sub_div[2]
                        rarity_div_span = rarity_div.find_element(By.CLASS_NAME, 'icon')
                        rarity = rarity_div_span.get_attribute('data-original-title')
                        #this sint the full class name which is 'col-availability px-2' will it work?
                        available_column_div = row.find_element(By.CLASS_NAME, 'col-availability')
                        number_available = available_column_div.find_element(By.TAG_NAME, 'span').text
                        price_column_div = row.find_element(By.CLASS_NAME, 'col-price')
                        raw_price = price_column_div.text
                        price_euros = raw_price.split(' ')[0].replace('.','').replace(',', '.')
                        row_to_write = f"{image_url}\t{expansion_code}\t{name}\t{variant}\t{url}\t{collector_number}\t{rarity}\t{number_available}\t{price_euros}\t{super_expansion}\t{edition}\n"
                        f.write(row_to_write)
                        slugs.append(f"{expansion_code}_{name}_{collector_number}_{variant}")
                        print(f"    {expansion_code}-{collector_number}-{variant}")
                if pages >= 15:
                    for page in range(1, pages + 1):
                        print(f"INFO: Page {page + 15}...")
                        reverse_page_url = f"https://www.cardmarket.com/en/FleshAndBlood/Products/Singles/{expansion_slug}?idRarity=0&sortBy=collectorsnumber_desc&site={page}"
                        driver.get(reverse_page_url)
                        reverse_page_url_loaded = False
                        while not reverse_page_url_loaded:
                            try:
                                element_present2 = EC.presence_of_element_located((By.CLASS_NAME, 'table-body'))
                                WebDriverWait(driver, timeout).until(element_present2)
                                reverse_page_url_loaded = True
                            except TimeoutException:
                                print("WARNING: Attempt of page load failed!")
                                driver.get(reverse_page_url)
                                pass

                        table_body = driver.find_element(By.CLASS_NAME, 'table-body')
                        # may need a . separator
                        rows = table_body.find_elements(By.XPATH, ("//*[starts-with(@id, 'productRow')]"))
                        for row in rows:
                            image_column_div = row.find_element(By.CLASS_NAME, 'col-icon')
                            image_column_div_span = image_column_div.find_element(By.TAG_NAME, 'span')
                            raw_image_url = image_column_div_span.get_attribute('data-original-title')
                            image_url = 'https://' + re.search(r'static(.*?)jpg',raw_image_url).group(0)
                            expansion_code_column_div = row.find_element(By.CLASS_NAME, 'col-icon.small')
                            expansion_code = expansion_code_column_div.find_element(By.TAG_NAME, 'span').text
                            name_number_rarity_div = row.find_element(By.CLASS_NAME, 'row.no-gutters')
                            name_number_rarity_sub_div = name_number_rarity_div.find_elements(By.TAG_NAME, 'div')
                            name_div = name_number_rarity_sub_div[0]
                            name_div_a = name_div.find_element(By.TAG_NAME, 'a')
                            raw_name = name_div_a.text
                            try:
                                variant = re.findall(r'\((.*?)\)', raw_name)[-1]
                                if variant in ['Red', 'Yellow', 'Blue']:
                                    variant = 'Regular'
                            except IndexError:
                                variant = 'Regular'
                                pass

                            name = raw_name.replace(f" ({variant})", '')
                            url = name_div_a.get_attribute('href')
                            raw_number = name_number_rarity_sub_div[1].text
                            collector_number = raw_number.split('-')[0]
                            rarity_div = name_number_rarity_sub_div[2]
                            rarity_div_span = rarity_div.find_element(By.CLASS_NAME, 'icon')
                            rarity = rarity_div_span.get_attribute('data-original-title')
                            # this sint the full class name which is 'col-availability px-2' will it work?
                            available_column_div = row.find_element(By.CLASS_NAME, 'col-availability')
                            number_available = available_column_div.find_element(By.TAG_NAME, 'span').text
                            price_column_div = row.find_element(By.CLASS_NAME, 'col-price')
                            raw_price = price_column_div.text
                            price_euros = raw_price.split(' ')[0].replace('.','').replace(',', '.')
                            print(f"    {expansion_code}-{collector_number}-{variant}")
                            if f"{expansion_code}_{name}_{collector_number}_{variant}" in slugs:
                                break
                            else:
                                slugs.append(f"{expansion_code}_{name}_{collector_number}_{rarity}")
                                row_to_write = f"{image_url}\t{expansion_code}\t{name}\t{variant}\t{url}\t{collector_number}\t{rarity}\t{number_available}\t{price_euros}\t{super_expansion}\t{edition}\n"
                                f.write(row_to_write)
                        else:
                            continue
                        break
        except TimeoutException:
            print(f"ERROR: Timed out waiting for {base_url} to load!")

    driver.quit()


# make runable 
if __name__ == '__main__':
    csv_file = 'promos_161222.txt'
    parse_card_market(csv_file)
