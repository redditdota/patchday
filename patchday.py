import json
import requests
from dataclasses import dataclass

import praw
from bs4 import BeautifulSoup

THREAD_ID = "" # "hs5iwf"
VERSION = "7.27d"

def main():
    """ Remaining manual actions:
    - create thread
    - set suggested sort to "old"
    - add thread id to automod config to remove top-level comments (control+f "patchday")
    - make note of unchanged heroes?
    - disable inbox replies?
    """
    reddit = login_to_reddit()
    thread = reddit.submission(THREAD_ID)
    for hero in get_all_hero_patches():
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


def get_all_hero_patches():
    r = requests.get(f"http://www.dota2.com/patches/{VERSION}")
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
        for hero_patch in get_all_hero_patches():
            print("\n" + hero_patch.reddit_comment_contents)
    else:
        main()
