import csv

from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import re
from datetime import datetime

def parse_expansion_map(driver, timeout):
    base_url = 'https://www.cardmarket.com/en/FleshAndBlood/Products/Singles'
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
            if expansion_name_raw == "Monarch - Prism Blitz Deck":
                expansion_map['Monarch Blitz Decks'] = expansion_id
            elif expansion_name_raw == "Welcome to Rathe - Bravo, Showstopper Hero Deck":
                expansion_map['Hero Decks Welcome to Rathe'] = expansion_id
            else:
                expansion_map[expansion_name_raw] = expansion_id
        return expansion_map
    except TimeoutException:
        print(f"ERROR: Timed out waiting for {base_url} to load while gathering expansion map!")

def print_input_request(expansion_map):
    print(f"Found {len(expansion_map)} expansion please choose from the following:")
    opt_counter = 0
    for expansion_name_raw in expansion_map.keys():
        print(f"{opt_counter}) {expansion_name_raw}")
        opt_counter += 1

    value = int(input("Expansion: "))
    expansion = list(expansion_map)[value]
    return expansion

def get_num_pages(driver, timeout, expansion_slug, expansion_id):
    expansion_url= f"https://www.cardmarket.com/en/FleshAndBlood/Products/Singles/{expansion_slug}?idCategory=1601&idExpansion={expansion_id}&idRarity=0&sortBy=collectorsnumber_asc&perSite=20"
    driver.get(expansion_url)
    expansion_url_forward_loaded = False
    while not expansion_url_forward_loaded:
        try:
            element_present3 = EC.presence_of_element_located((By.ID, 'pagination'))
            WebDriverWait(driver, timeout).until(element_present3)
            # this should only happen if webdriver eait fails and throws us into the except block straight away
            expansion_url_forward_loaded = True
        except TimeoutException:
            print("WARNING: Attempt of expansion_url load failed!")
            driver.get(expansion_url)
            pass

    pagination = driver.find_element(By.ID, 'pagination')
    pages = int(re.findall(r'\d+', pagination.find_element(By.CLASS_NAME, 'mx-1').text)[-1])
    print(f"Found {pages} pages!")
    return pages


def parse_expansion_page(driver, timeout, expansion_slug, sort_by, page, slugs, super_expansion, edition):
    page_url = f"https://www.cardmarket.com/en/FleshAndBlood/Products/Singles/{expansion_slug}?idRarity=0&sortBy={sort_by}&site={page}"
    driver.get(page_url)
    page_url_loaded = False
    while not page_url_loaded:
        try:
            element_present2 = EC.presence_of_element_located((By.CLASS_NAME, 'table-body'))
            WebDriverWait(driver, timeout).until(element_present2)
            page_url_loaded = True
        except TimeoutException:
            print("WARNING: Attempt of page load failed!")
            driver.get(page_url)
            pass

    table_body = driver.find_element(By.CLASS_NAME, 'table-body')
    # may need a . separator
    rows = table_body.find_elements(By.XPATH, ("//*[starts-with(@id, 'productRow')]"))
    rows_to_write=[]
    for row in rows:
        image_column_div = row.find_element(By.CLASS_NAME, 'col-icon')
        image_column_div_span = image_column_div.find_element(By.TAG_NAME, 'span')
        raw_image_url = image_column_div_span.get_attribute('data-original-title')
        image_url = 'https://' + re.search(r'static(.*?)jpg', raw_image_url).group(0)
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
        price_euros = raw_price.split(' ')[0].replace('.', '').replace(',', '.')
        row_to_write = [image_url,expansion_code, name, variant, url, collector_number, rarity, number_available, price_euros, super_expansion, edition]
        rows_to_write.append(row_to_write)
        slugs.append(f"{expansion_code}_{name}_{collector_number}_{variant}")
        print(f"    {expansion_code}-{collector_number}-{variant}")
    return rows_to_write

def parse_card_market(csv_file):
    # set the driver
    service = Service(executable_path="C:/Users/chad0/PycharmProjects/chromedriver")
    driver = webdriver.Chrome(service=service)
    timeout = 10
    expansion_map = parse_expansion_map(driver, timeout)
    expansion = print_input_request(expansion_map)
    expansion_slug = re.sub(r'(\-)\1+', '\\1', expansion.replace(' ', '-').replace(':', '').replace(',', ''))
    expansion_id = expansion_map[expansion]
    print(f"INFO: Processing {expansion}...")
    expansion_elems = expansion.split(' - ')
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
        super_expansion = expansion

    pages = get_num_pages(driver, timeout, expansion_slug, expansion_id)
    slugs = []
    with open(csv_file, 'a') as f:
        for page in range(1, pages + 1):
            print(f"INFO: Page {page}...")
            if page < 15:
                sort_by = 'collectorsnumber_asc'
                rows_to_write = parse_expansion_page(driver, timeout, expansion_slug, sort_by, page, slugs, super_expansion, edition)
                for row in rows_to_write:
                    f.write('\t'.join(row) + '\n')
            else:
                sort_by = 'collectorsnumber_desc'
                rows_to_write = parse_expansion_page(driver, timeout, expansion_slug, sort_by, page, slugs, super_expansion,edition)
                for row in rows_to_write:
                    f.write('\t'.join(row) + '\n')
    driver.quit()

# make runable
if __name__ == '__main__':
    csv_file = 'LGSPromos.txt'
    parse_card_market(csv_file)
