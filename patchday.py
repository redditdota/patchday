import json
import time
from dataclasses import dataclass

import praw
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TEST = True
VERSION = "7.32d"

thread_title = f"Patch {VERSION} - Hero Changes Discussion"
thread_header = """Updated heroes are each listed below as a top level comment.
Please discuss changes to a specific hero there!

**All other top level comments are automatically removed.**"""

def main():
    """Creates a new reddit thread and posts a reply for each updated hero with their changes.
    Additionally, makes note of unchanged heroes and creates tables in the OP with comment links.

    Remaining manual actions`:
    - download corresponding ChromeDriver version at https://chromedriver.chromium.org/downloads
    - move it to local path: `mv chromedriver /usr/local/bin/chromedriver`
    - Add outputted thread id to automod config to remove top-level comments (control+f "patchday")
    """
    reddit = login_to_reddit()
    reddit.validate_on_submit = True
    subreddit = reddit.subreddit(SUBREDDIT)
    thread = subreddit.submit(
        title=thread_title,
        selftext=thread_header,
        flair_id=get_flair_id(subreddit),
        send_replies=False,
    )
    print(f"\n\nThread ID for AutoModerator config: {thread.id}\n\n")

    hero_links = []
    patched_heroes = get_all_hero_patches()
    for hero in patched_heroes:
        comment = thread.reply(body=hero.reddit_comment_contents)
        hero_links.append(f"{hero.reddit_image} [{hero.name}]({comment.permalink})")
    hero_table = build_markdown_table(hero_links)
    thread.edit(thread.selftext + f"\n\n----\n\n## Updated Heroes ({len(patched_heroes)})\n\n" + hero_table)

    unmodified = get_all_heroes() - set(hero.name for hero in patched_heroes)
    if unmodified:
        unmodified_hero_cells = []
        for hero_name in sorted(unmodified):
            hero = HeroPatch(hero_name)
            unmodified_hero_cells.append(f"{hero.reddit_image} {hero.name}")
        unmodified_table = build_markdown_table(unmodified_hero_cells)
        thread.edit(thread.selftext + f"\n\n---- \n\n## Unchanged Heroes ({len(unmodified)})\n\n" + unmodified_table)


@dataclass
class HeroPatch:
    """All changes made in a given patch to one hero, with associated properties.
    Also used as a model for heroes that were unmodified in a patch.
    """
    name: str
    basic_changes: list = None
    ability_changes: dict = None
    talent_changes: list = None

    @property
    def basic_lines(self):
        if not self.basic_changes:
            return ""
        return "\n".join(f"- {change}" for change in self.basic_changes)

    @property
    def ability_lines(self):
        if not self.ability_changes:
            return ""
        lines = ""
        for ability_name, changes in self.ability_changes.items():
            change_lines = "\n".join(f"- {change}" for change in changes)
            lines += f"**{ability_name}**\n\n{change_lines}\n\n"
        return lines

    @property
    def talent_lines(self):
        if not self.talent_changes:
            return ""
        lines = f"#### Talents\n\n"
        for change in self.talent_changes:
            lines += f"- {change}\n"
        return lines

    @property
    def reddit_image(self):
        cleaned_name = "".join(char for char in self.name if char not in "'- ").lower()
        return f"[](/hero-{cleaned_name})"

    @property
    def reddit_comment_contents(self):
        header = f"# {self.reddit_image} {self.name}"
        sections = [header, self.basic_lines, self.ability_lines, self.talent_lines]
        return "\n\n".join(sections)


def login_to_reddit():
    with open("creds.json") as f:
        return praw.Reddit(user_agent="patchday script by /u/Decency", **json.load(f))


def get_flair_id(subreddit, flair="Discussion"):
    """Get the id of a given flair, so that preferred styling is applied."""
    choices = list(subreddit.flair.link_templates.user_selectable())
    return next(x for x in choices if x["flair_text"] == flair)["flair_template_id"]


def get_patch_dom():
    """Get the contents of the patch page. This method grabs dynamic content created after page-load."""
    url = f"http://www.dota2.com/patches/{VERSION}"
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)  # Wait to ensure javascript has fully rendered
    return driver.page_source


def get_all_hero_patches():
    """Transform the contents of a Dota patch web page into HeroPatch objects."""
    dom = get_patch_dom()
    soup = BeautifulSoup(dom, "html.parser")
    heroes_changed = soup.find_all("div", class_=generate_filter("hero"))

    output = []
    for hero in heroes_changed:
        hero_name = hero.find("div", class_=generate_filter("hero_name")).text

        first_section = hero.find("div", class_=generate_filter("section"))
        in_talents = first_section.find_parent("div", class_=generate_filter("talent_section"), recursive=False)
        in_abilities = first_section.find_all("div", class_=generate_filter("ability"))
        # if the first section is within the talents or abilities section, there were no basic changes
        if in_talents or in_abilities:
            basic_changes = []
        else:
            basic_divs = first_section.find_all("div", class_=generate_filter("change"))
            basic_changes = [div.text for div in basic_divs]

        ability_sections = hero.find_all("div", class_=generate_filter("ability"))
        ability_changes = {}
        for ability in ability_sections:
            ability_name = ability.find("div", class_=generate_filter("ability_name")).text
            ability_changes_divs = ability.find_all("div", class_=generate_filter("change"))
            ability_changes[ability_name] = [div.text for div in ability_changes_divs]

        talent_section = hero.find("div", class_=generate_filter("talent_section"))
        if talent_section:
            talent_divs = talent_section.find_all("div", class_=generate_filter("change"))
            talent_changes = [div.text for div in talent_divs]
        else:
            talent_changes = []

        output.append(HeroPatch(hero_name, basic_changes, ability_changes, talent_changes))
    return output


def generate_filter(class_type):
    """The patch page applies random characters as suffixes to these classes, which are unpredictable.
    This dynamically creates and returns a filter function based on the input string to locate these.
    :param class_type: a String matching one of the keys in `class_names`
    """
    element = {
        "hero": "patchnotespage_PatchNoteHero_",
        "hero_name": "patchnotespage_HeroName_",
        "section": "patchnotespage_Notes_",
        "change": "patchnotespage_Note_",
        "ability": "patchnotespage_AbilityNote_",
        "ability_name": "patchnotespage_AbilityName_",
        "talent_section": "patchnotespage_TalentNotes_",
    }[class_type]

    def class_filter(css_class):
        return css_class is not None and css_class.startswith(element)

    return class_filter


def get_all_heroes():
    """Returns a set containing the name of each hero.
    """
    with open('heroes.txt') as f:
        return set(hero.strip() for hero in f.readlines())


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


if __name__ == "__main__":
    if TEST:
        SUBREDDIT = "dota2test"
        print("\nTesting...\n")
    else:
        SUBREDDIT = "Dota2"
        print("\nLIVE: preparing to publish...\n")
    main()
    print("Completed.")
