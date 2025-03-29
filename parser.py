import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from hero_patch import HeroPatch

def get_all_hero_patches(version):
    """Transform the contents of a Dota patch web page into a list of HeroPatch objects."""
    dom = get_patch_dom(version)
    soup = BeautifulSoup(dom, "html.parser")
    hero_start = next(div for div in soup.find_all("div") if div.text == "Hero Updates")
    hero_updates_section = hero_start.parent
    modified_heroes_section = list(hero_updates_section.children)[1] # skip header
    modified_heroes = list(modified_heroes_section.children)
    return [HeroPatch.create_from_patch_data(hero) for hero in modified_heroes]

def get_patch_dom(version):
    """Get the contents of the patch page. This method grabs dynamic content created after page-load."""
    url = f"http://www.dota2.com/patches/{version}"
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)  # Wait to ensure javascript has fully rendered
    return driver.page_source


def get_all_hero_names():
    """Returns a set containing the name of each hero."""
    with open('heroes.txt') as f:
        return set(hero.strip() for hero in f.readlines())