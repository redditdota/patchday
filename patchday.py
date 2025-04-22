import json
import time

import praw
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from hero_patch import HeroPatch

TEST = True
VERSION = "7.38c"

thread_title = f"Patch {VERSION} - Hero Changes Discussion"
thread_header = """Updated heroes are each listed below as a top level comment.
Please discuss changes to a specific hero there!

**All other top level comments are automatically removed.**"""

def main(subreddit):
    """Creates a new reddit thread and posts a reply for each updated hero with their changes.
    Additionally, makes note of unchanged heroes and creates tables in the OP with comment links.

    Manual actions:
    - download a version of Chrome at https://google-chrome.en.uptodown.com/mac/versions
    - and ChromeDriver: https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json
    - move chromedriver to the local path: `mv chromedriver /usr/local/bin/chromedriver`
    - add outputted thread id to automod config to remove top-level comments (control+f "patchday")
    """
    patched_heroes = get_all_hero_patches(VERSION)

    thread = create_thread(subreddit)
    print(f"\n{VERSION} patchday thread posted; ID for AutoModerator config: `{thread.id}`")
    print(f"    <https://old.reddit.com/{thread.id}>\n")

    hero_links = []
    for hero in patched_heroes:
        comment = thread.reply(body=hero.reddit_comment_contents)
        hero_links.append(f"{hero.reddit_image} [{hero.name}]({comment.permalink})")
    hero_table = build_markdown_table(hero_links)
    thread.edit(thread.selftext + f"\n\n----\n\n## Updated Heroes ({len(patched_heroes)})\n\n" + hero_table)

    unmodified = get_all_hero_names() - set(hero.name for hero in patched_heroes)
    if unmodified:
        unmodified_hero_cells = []
        for hero_name in sorted(unmodified):
            hero = HeroPatch(hero_name)
            unmodified_hero_cells.append(f"{hero.reddit_image} {hero.name}")
        unmodified_table = build_markdown_table(unmodified_hero_cells)
        thread.edit(thread.selftext + f"\n\n----\n\n## Unchanged Heroes ({len(unmodified)})\n\n" + unmodified_table)

def get_all_hero_patches(version):
    """Transform the contents of a Dota patch web page into a list of HeroPatch objects."""
    dom = get_patch_dom(version)
    soup = BeautifulSoup(dom, "html.parser")
    hero_start = next(div for div in soup.find_all("div") if div.text == "Hero Updates")
    hero_updates_section = hero_start.parent
    modified_heroes_section = list(hero_updates_section.children)[1] # skip header
    modified_heroes = list(modified_heroes_section.children)
    return [HeroPatch.create_from_patch_data(hero) for hero in modified_heroes]

def create_thread(subreddit):
    with open("creds.json") as f:
        reddit = praw.Reddit(user_agent="patchday script by /u/Decency", **json.load(f))
    reddit.validate_on_submit = True
    sub = reddit.subreddit(subreddit)
    choices = list(sub.flair.link_templates.user_selectable())
    discussion_flair_id = next(x for x in choices if x["flair_text"] == "Discussion")["flair_template_id"]
    return sub.submit(
        title=thread_title,
        selftext=thread_header,
        flair_id=discussion_flair_id,
        send_replies=False,
    )

def get_patch_dom(version):
    """Get the contents of the patch page. This method grabs dynamic content created after page-load."""
    url = f"http://www.dota2.com/patches/{version}"
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)  # Wait to ensure javascript content has fully rendered
    return driver.page_source

def build_markdown_table(sequence, columns=4):
    """Construct and return a markdown formatted table given a sequence of elements.
    Table will be built left to right, top to bottom.
    """
    table = "|||||\n" + ":--|" * columns
    for index, element in enumerate(sequence):
        if index % columns == 0:
            table += f"\n| {element} | "  # start a new row
        else:
            table += f"{element} | "
    table += "|"
    return table

def get_all_hero_names():
    """Returns a set containing the name of each hero."""
    with open('heroes.txt') as f:
        return set(hero.strip() for hero in f.readlines())

if __name__ == "__main__":
    if TEST:
        location = "dota2test"
        print("\nTesting...\n")
    else:
        location = "dota2"
        print("\nLIVE: preparing to publish...\n")
    location = "dota2test" if TEST else "dota2"
    main(location)
    print("Completed.")
