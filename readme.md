# Patchday bot for /r/Dota2

This bot provides support for scraping, parsing, collating, and outputting all changes to heroes that were made in a given Dota2 patch. It does so by rendering the javascript from a specific https://www.dota2.com/patches/ page with a headless browser before grabbing that page's DOM. After collection of this patch data, a new post is created on /r/Dota2. For each updated hero, a new reply is made to this post containing that hero's changes. When this completes after a few minutes, the main thread is updated with links to each of these comments, as well as with a list of heroes that received no changes in the patch.

This bot has enabled us to create patch evaluation threads in a fantastic format within minutes of a new patch, leading to a variety of great community discussions with thousands of comments. Some examples: [7.27b](https://old.reddit.com/r/DotA2/comments/hs5iwf/patch_727b_hero_changes_discussion/), [7.30](https://old.reddit.com/r/DotA2/comments/p77wx7/patch_730_hero_changes_discussion/), [7.32](https://old.reddit.com/r/DotA2/comments/wwbw0s/patch_732_hero_changes_discussion/).

## Execution Steps

1. If chrome has updated since last run, download the matching version of chromedriver (eg: `chromedriver_mac64.zip` on my OSX) from http://chromedriver.storage.googleapis.com/index.html.
2. Extract chromedriver from that zipped file and move it to your path: `mv ~/Downloads/chromedriver /usr/local/bin/chromedriver` or the equivalent.
3. Ensure that the `TEST` and `VERSION` constants are set correctly, near the top of the file.
4. `python patchday.py` to execute the file.
5. Copy the post ID (the 6 characters within the url after /comments/), search for `patchday` in the [automoderator config](https://old.reddit.com/r/DotA2/wiki/config/automoderator), and add this ID to this list.

## Potential Improvements

As chrome updates, there is a need to update the webdriver which is utilized for the rendering of the webpage, or a version mismatch will take place. Locking this version with some sort of configuration management would minimize the updates to chromedriver to only when breaking changes occur.

Providing the version and test variables as parameters when executed instead of as declared constants would remove the need to modify the file for each version.

We use an automoderator filter on these threads in order to prevent discussions outside of the changes to specific heroes. There's probably a way to automatically detect threads from the patchdayDota2 user and handle them appropriately, but currently the filter requires the postID from the created thread.

The initial thread is created before attempting to grab the patch data, so an error there will require the thread to be manual deleted.

## Future Expansibility

This bot can iterate and collect data from all patch threads that utilize this web format- 7.00 and beyond, I believe. This capability provides a lot of power for longterm data analysis projects examining Dota2's balance and metagame.

For example: this could be used to measure changes to a specific spell or hero over time, or to measure power creep in terms of quantified buffs versus nerfs. In conjunction with patch analysis reports, such as those produced at https://stats.spectral.gg/lrg2/?cat=ranked, it should also  be possible to measure the effects of a specific type of change on hero winrate (eg: +5 movespeed or +1 armor) by examining dozens of these occurences over the game's history.

Since the program is written modularly, it will be straightforward to adapt it for use on subreddits dedicated to different competitive games. Any game which publishes patch notes in a predictable format that uses asymmetric characters or factions would be a great candidate. After writing the parser for that game's patch notes, only minor tweaks would be required to begin posting threads on patchday.
