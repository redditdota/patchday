import json
from dataclasses import dataclass

import requests
import praw
from bs4 import BeautifulSoup

VERSION = "7.28"
SUBREDDIT = "Dota2"

thread_title = f"Patch {VERSION} - Hero Changes Discussion"
thread_body = """Updated heroes are each listed below as a top level comment. 
Please discuss changes to a specific hero there!

**All other top level comments are automatically removed.**"""


def main():
    """ Remaining manual actions:
    - set suggested sort to "old"
    - add thread id to automod config to remove top-level comments (control+f "patchday")
    - make note of unchanged heroes?
    - disable inbox replies?
    - set flair
    - aggregate direct links to each hero in the OP, for ease of access
    """
    reddit = login_to_reddit()
    reddit.validate_on_submit = True
    thread = reddit.subreddit(SUBREDDIT).submit(title=thread_title, selftext=thread_body)
    print(thread.id)
    for hero in get_all_hero_patches(VERSION):
        thread.reply(body=hero.reddit_comment_contents)

@dataclass
class HeroPatch:
    name: str
    changes: list

    @property
    def reddit_image(self):
        cleaned_name = "".join(char for char in self.name if char not in "'- ").lower()
        return f"[{self.name}](/hero-{cleaned_name})"

    @property
    def reddit_comment_contents(self):
        change_lines = "\n".join(f"- {change}" for change in self.changes)
        return f"{self.reddit_image} **{self.name}**\n\n" + change_lines


def login_to_reddit():
    with open("creds.json") as f:
        return praw.Reddit(user_agent="patchday script by /u/Decency", **json.load(f))

def get_all_hero_patches(version):
    r = requests.get(f"http://www.dota2.com/patches/{version}")
    soup = BeautifulSoup(r.text, 'html.parser')
    heroes_changed = soup.findAll("div", {"class": "HeroNotes"})
    output = []
    for hero in heroes_changed:
        name = hero.find("div", {"class": "HeroName"}).text
        changes = [change.text.strip() for change in
                   hero.findAll("li", {"class": "PatchNote"})]
        output.append(HeroPatch(name, changes))
    return output


if __name__ == "__main__":
    debug = True
    if debug:
        for hero_patch in get_all_hero_patches(VERSION):
            print("\n" + hero_patch.reddit_comment_contents)
    else:
        main()
