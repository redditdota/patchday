from dataclasses import dataclass


@dataclass
class HeroPatch:
    """All changes made in a given patch to one hero, with associated properties.
    Also used as a model for heroes that were unmodified in a patch.
    """
    name: str
    general_changes: list = None
    facet_changes: dict = None
    ability_changes: dict = None
    talent_changes: list = None

    def __repr__(self):
        return (
            f'{self.name}:\n'
            f'- General changes: {self.general_changes}\n'
            f'- Facet changes: {self.facet_changes}\n'
            f'- Ability changes: {self.ability_changes}\n'
            f'- Talent changes: {self.talent_changes}\n'
        )

    @property
    def general_lines(self):
        if not self.general_changes:
            return ""
        lines = "#### General\n\n"
        change_lines = "\n".join(f"- {change}" for change in self.general_changes)
        return lines + change_lines

    @property
    def ability_lines(self):
        if not self.ability_changes:
            return ""
        lines = "#### Abilities\n\n"
        for ability_name, changes in self.ability_changes.items():
            change_lines = "\n".join(f"    - {change}" for change in changes)
            lines += f"  - **{ability_name}**\n\n{change_lines}\n\n"
        return lines

    @property
    def talent_lines(self):
        if not self.talent_changes:
            return ""
        lines = "#### Talents\n\n"
        for change in self.talent_changes:
            lines += f"- {change}\n"
        return lines

    @property
    def facet_lines(self):
        if not self.facet_changes:
            return ""
        lines = "#### Facets\n\n"
        for facet_name, changes in self.facet_changes.items():
            change_lines = "\n".join(f"    - {change}" for change in changes)
            lines += f"  - **{facet_name}**\n\n{change_lines}\n\n"
        return lines

    @property
    def reddit_image(self):
        cleaned_name = "".join(char for char in self.name if char not in "'- ").lower()
        return f"[](/hero-{cleaned_name})"

    @property
    def reddit_comment_contents(self):
        header = f"# {self.reddit_image} {self.name}"
        sections = [header, self.general_lines, self.facet_lines, self.ability_lines, self.talent_lines]
        return "\n\n".join(sections)

    @classmethod
    def create_from_patch_data(cls, raw_hero_data):
        """
        A constructor that accounts for heroes with facets and the new model of the hero patch pages.
        The contents of each hero patch are extracted based on the following structure (section omitted if no changes):
        Hero Div (1..126)
            0 General section
                Hero image section
                Name + General
                    Attribute + Hero Name
                    empty div
                    General Container...
                        General Change 1
                        General Change 2
            1 empty section
            2 Facets Container...
                'Facets'
                Facet 1 Section
                Facet 2 Section
            3 'Abilities'
            4 Abilities Container...
                ..
            5 'Talents'
            6 Talents Container...
                ..
        """
        sections = list(section for section in raw_hero_data)
        general_section, empty_section = sections[0:2]  # header and general changes section, blank section
        change_sections = sections[2:] # any changes to facets, abilities, and talents are in here
        hero_name = next(anchor.text.strip() for anchor in general_section.find_all("a") if anchor.text)

        general_changes = extract_general_changes(general_section)
        facet_changes = {}
        ability_changes = {}
        talent_changes = []

        abilities_section_upcoming = False
        talents_section_upcoming = False
        for index, section in enumerate(change_sections):
            if section.text.startswith('Facets'):
                facet_changes = extract_facet_changes(section)
            elif section.text == 'Abilities':
                abilities_section_upcoming = True
            elif abilities_section_upcoming:
                ability_changes = extract_ability_changes(section)
                abilities_section_upcoming = False
            elif section.text == 'Talents':
                talents_section_upcoming = True
            elif talents_section_upcoming:
                talent_changes = extract_talent_changes(section)
                talents_section_upcoming = False
        return cls(hero_name, general_changes, facet_changes, ability_changes, talent_changes)


def extract_general_changes(section):
    try:
        # dig in, attempting to find the relevant section where changes are listed
        general_area = list(child for child in section.children)[1]
        general_container = list(child for child in general_area.children)[2]
        general_changes = [change.text for change in general_container.children]
    except IndexError:
        general_changes = []
    return general_changes


def extract_facet_changes(section):
    facet_changes = {}
    facets_changed = [child for child in section.children][1]  # 0 is the 'Facets' div
    for facet in facets_changed:
        # divs 0-3 are "New"/"Reworked" cruft, 4-5 is facet header, 6 is facet changes (as a tree)
        facet_name = next(p.text for p in [child for child in facet.children][5] if p.text)
        facet_changes[facet_name] = []
        facet_change_container = [child for child in facet.children][6]
        if len(facet_change_container.find_all('img')) > 0:
            # if an image is present, the facet is tied to at least one ability
            for ability_modified in facet_change_container.children:
                change = [child for child in ability_modified.children][1]  # 0 is the image
                notes = [child for child in change.children]
                name_section, notes_sections = notes[0], notes[1:]  # split section
                ability_name = next(child.text for child in name_section if child.text)
                for note in notes_sections:
                    # add each bullet point with its associated ability, but skip the styling and etc.
                    if note.text:
                        facet_changes[facet_name].append(f'{ability_name}: {note.text}')
        else:
            # facet changes don't correspond to an ability, just pass along the change list
            for change in facet_change_container:
                facet_changes[facet_name].append(change.text)
    return facet_changes


def extract_ability_changes(section):
    ability_changes = {}
    abilities_changed = list(child for child in section.children)
    for ability in abilities_changed:
        image, container = ability.children
        ability_change_contents = [child for child in container.children]
        strings = [item.text for item in ability_change_contents if item.text]
        ability_name, note = strings[0], strings[1:]
        ability_changes[ability_name] = note
    return ability_changes


def extract_talent_changes(section):
    talent_notes = list(child for child in section.children)[1]
    return [item.text for item in talent_notes if item.text]