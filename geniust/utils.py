import logging
import re
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, TypeVar, Union

import Levenshtein
from bs4 import BeautifulSoup, Comment, NavigableString
from bs4.element import Tag
from lyricsgenius.utils import clean_str
from telegram.utils.helpers import create_deep_linked_url

import geniust
from geniust.constants import TELEGRAM_HTML_TAGS

# (\[[^\]\n]+\]|\\n|!--![\S\s]*?!__!)|.*[^\x00-\x7F].*
regex = (
    r"(\[[^\]\n]+\]"  # ignore headers like [Chorus]
    r"|\\n"  # ignore newlines in English lines
    r"|!--![\S\s]*?!__!"  # ignore annotations inside !--! and !__!
    r"|<.*?>)"  # ignore HTML tags
    r"|.*"  # capture the beginning of a sentence that
    r"[^\x00-\x7F]"  # is followed by a non-ASCII character
    r".*"  # get the rest of the sentence
)
remove_non_english: Pattern[str] = re.compile(regex, re.MULTILINE)

# The two expressions are fairly like
# the one below captures lines in English.
# The only noticeable difference is
# ignoring \u2005 or \u200c characters usually used in Persian.
remove_english: Pattern[str] = re.compile(
    r"(\[[^\]\n]+\]|\\n|\\u200[5c]|!--![\S\s]*?!__!|<.*?>)|^.*[a-zA-Z]+.*", re.MULTILINE
)

# remove extra newlines except the ones before headers.
# Removes instances of two or more newlines (either \n or <br>)
newline_pattern: Pattern[str] = re.compile(r"(\n|<br\s*[/]*>){2,}(?!\[)")

# remove links from annotations
links_pattern: Pattern[str] = re.compile(r"\nhttp[s]*.*")

# Range of Arabic/Persian characters
PERSIAN_CHARACTERS = re.compile(r"[\u0600-\u06FF]")
# Translation phrase added to the end of the song title (more info at where it's used)
TRANSLATION_PARENTHESES = re.compile(r"\([\u0600-\u06FF]\)")

# Lyrics section headers e.e. \n[Chorus]\n
SECTION_HEADERS = re.compile(r"\n{0,1}\[.*?\]\n{0,1}")
FIX_SECTION_HEADERS = re.compile(r"(?<!\n)\n\[")

# The keys are Telethon message entity types and the values PTB ones.
MESSAGE_ENTITY_TYPES = {
    "MessageEntityBold": "bold",
    "MessageEntityBotCommand": "bot_command",
    "MessageEntityCashtag": "cashtag",
    "MessageEntityCode": "code",
    "MessageEntityEmail": "email",
    "MessageEntityHashtag": "hashtag",
    "MessageEntityItalic": "italic",
    "MessageEntityMention": "mention",
    "MessageEntityMentionName": "text_mention",
    "MessageEntityPhone": "phone_number",
    "MessageEntityPre": "pre",
    "MessageEntityStrike": "strikethrough",
    "MessageEntityTextUrl": "text_link",
    "MessageEntityUnderline": "underline",
    "MessageEntityUrl": "url",
}


def deep_link(
    name: str,
    id: str,
    type: str,
    platform: str = "genius",
    download: bool = False,
) -> str:
    """Deep links given entity using an <a> tag.

    This functions will wrap the entity's name
    or title in an <a> where its href attribute
    will be a deep linked URL allowing the URL
    to get information for the entity.

    Args:
        name (str): Text of the tag.
        id (str): ID of the entity.
        type (str): Type of the entity.
        platform (str, optional): Platform which the entity is from.
        download (bool, optional): Whether user wants to download something or not.

    Raises:
        ValueError: If it comes accross an unknown
            entity (an entiy with an unfimilar API path).

    Returns:
        str: Deep linked entity
            (e.g. <a href="link">song name</name>)
    """
    url = create_deep_linked_url(
        geniust.username, f"{type}_{id}_{platform}{'_download' if download else ''}"
    )
    return f"""<a href="{url}">{name}</a>"""


def remove_unsupported_tags(
    soup: BeautifulSoup, supported: List[str] = TELEGRAM_HTML_TAGS
) -> BeautifulSoup:
    """Removes unsupported tag from BeautifulSoup object.

    Args:
        soup (BeautifulSoup): BeautifulSoup object.
        supported (Optional[List[str]], optional): List of supported tags to keep.
        Defaults to TELEGRAM_HTML_TAGS.

    Returns:
        BeautifulSoup
    """
    restart = True
    while restart:
        restart = False
        for tag in soup:
            name = tag.name
            if name is not None and name not in supported:
                if tag.text:
                    tag.unwrap()
                tag.decompose()
                restart = True
                break

    return soup


def remove_extra_newlines(s: str) -> str:
    """Removes extra newlines.

    Replaces where there are two or more
    newlines with a single newline except
    for the beginning of a lyrics section (e.g. \n\n[Chorus])

    Args:
        s (str): string.

    Returns:
        str: formattted string.
    """
    return newline_pattern.sub("\n", s)


def remove_links(s: str) -> str:
    """Removes links from string.
    Meant to remove links from Genius annotations
    that have a "plain" text format.

    Args:
        s (str): string.

    Returns:
        str: formatted string.
    """
    return links_pattern.sub("", s)


def extract_lyrics_for_card(html_lyrics: str) -> str:
    """Extracts lyrics from HTML and cleans them

    Cleans the extracted lyrics to be searched later.

    Args:
        lyrics (str): Song lyrics in HTML format.

    Returns:
        str: Lyrics with removed section headers.
    """
    lyrics = BeautifulSoup(html_lyrics, "html.parser").get_text().strip()
    lyrics = fix_section_headers(lyrics)
    return SECTION_HEADERS.sub("", lyrics)


def find_matching_lyrics(lines: List[str], lyrics: str) -> Optional[str]:
    """Finds matching lines in lyrics

    Args:
        lines (List[str]): List of lines to search for.
        lyrics (str): Song lyrics.

    Returns:
        Optional[str]: Matching lyrics if there are any. Otherwise None.
    """
    matching_lyrics = []
    for line in lyrics.split("\n"):
        for found_line in lines:
            # We'd expect the match between the lines in the snippet (found_lyrics)
            # and the corresponding lines in the full lyrics to be 100%, but since
            # Genius implements some methods to detect plagiarism and
            # these methods modify the lyrics, a 100% similarity ratio might not happen.
            if Levenshtein.ratio(found_line, line) > 0.75 or clean_str(
                found_line
            ) in clean_str(line):
                matching_lyrics.append(line)
                break
        if len(matching_lyrics) == len(lines):
            break
    return "\n".join(matching_lyrics) if matching_lyrics else None


def fix_section_headers(string: str) -> str:
    """Makes sure section headers have two newline characters before them

    Args:
        string (str): string.

    Returns:
        str: formatted string.
    """
    return FIX_SECTION_HEADERS.sub("\n\n[", string)


def format_language(
    lyrics: Union[BeautifulSoup, str],
    lyrics_language: str,
) -> BeautifulSoup:
    """Removes (non-)ASCII characters

    Removes ASCII or non-ASCII or keeps both based
    on supplied lyrics_language.

    Args:
        lyrics (Union[BeautifulSoup, str]): lyrics.
        lyrics_language (str): User preferred language.

    Raises:
        TypeError: If the type of lyrics isn't recognized.

    Returns:
        BeautifulSoup: formatted lyrics.
    """

    def string_formatter(s: str) -> str:
        if lyrics_language == "English":
            s = remove_non_english.sub("\\1", s, 0)
        elif lyrics_language == "Non-English":
            s = remove_english.sub("\\1", s, 0)
        s = remove_extra_newlines(s)
        return s

    if isinstance(lyrics, (Tag, BeautifulSoup)):
        strings = [
            x
            for x in lyrics.descendants
            if (
                isinstance(x, NavigableString)
                and len(x.strip()) != 0
                and not isinstance(x, Comment)
            )
        ]

        for string in strings:
            formatted = string_formatter(str(string))
            string.replace_with(formatted)
    elif isinstance(lyrics, str):
        lyrics = BeautifulSoup(string_formatter(lyrics), "html.parser")
    else:
        raise TypeError(f"Unknown lyrics type: {type(lyrics)}")

    return lyrics


def format_annotations(
    lyrics: str,
    annotations: List[Dict[int, str]],
    include_annotations: bool,
    identifiers: Tuple[str, str] = ("!--!", "!__!"),
    format_type: str = "zip",
) -> BeautifulSoup:
    """Formats annotations in BeautifulSoup object

    Includes the annotations by inspecting <a> tags and
    then remove the unnecessary HTML tags
    in the end.

    Args:
        lyrics (str): song lyrics.
        annotations (List[Tuple[int, str]]): Song annotations.
            Keys are annotation IDs that point to the annotation text.
            The annotations are found by the href attribute of <a> tags
            in the lyrics.
        include_annotations (bool): Add annotations to lyrics.
        identifiers (Tuple[str, str], optional): Identifiers to wrap annotations in
            when using the zip format. Defaults to ('!--!', '!__!').
        format_type (str, optional): pdf, tgf or zip. Defaults to 'zip'.

    Returns:
        BeautifulSoup: BeautifulSoup object.
    """
    soup: BeautifulSoup = BeautifulSoup(lyrics, "html.parser")
    if include_annotations and annotations:
        used = []
        for a in soup.find_all("a"):
            annotation_id = a.attrs["href"]
            if annotation_id in used:
                continue

            if format_type == "zip":
                annotation_content = (
                    f"<annotation>"
                    f"\n{identifiers[0]}\n"
                    f"{annotations[annotation_id]}"
                    f"\n{identifiers[1]}\n"
                    f"</annotation>"
                )
            else:
                annotation_content = (
                    f"<annotation>" f"{annotations[annotation_id]}" f"</annotation>"
                )
            annotation = BeautifulSoup(annotation_content, "html.parser")
            # annotation = newline_pattern.sub('\n', annotation)
            # annotation = links_pattern.sub('', annotation)

            for tag in annotation.descendants:
                if hasattr(tag, "attrs"):
                    for attribute, _ in list(tag.attrs.items()):
                        if attribute != "href":
                            tag.attrs.pop(attribute)
                if tag.name in ("div", "script", "iframe"):
                    tag.decompose()
                elif tag.name == "blockquote":
                    tag.unwrap()

            a.attrs.clear()
            a.insert_after(annotation)
            used.append(annotation_id)

    return soup


def format_title(artist: str, title: str) -> str:
    """Removes artist name if "Genius" is in the artist name

    Args:
        artist (str): item artist.
        title (str): item title/name.

    Returns:
        str: formatted title.
    """
    if "Genius" in artist:
        final_title = title
    else:
        final_title = f"{artist} - {title}"
    return final_title


def format_filename(string: str) -> str:
    """Removes invalid characters in file name

    Args:
        string (str): filename.

    Returns:
        str: formatted filename.
    """
    return re.sub(r"[\\/:*?\"<>|]", "", string)


def get_description(entity: Dict[str, Any]) -> str:
    """Gets description of entity.

    Gets description of entity from its description annotations,
    removes links and extra newlines in it and returns it.

    Args:
        entity (Dict[str, Any]): Entity data.

    Returns:
        str: Description.
    """
    if not entity.get("description_annotation"):
        return ""

    description = entity["description_annotation"]["annotations"][0]["body"]["plain"]

    if not description:
        return ""

    description = remove_links(description)
    description = remove_extra_newlines(description)

    return description.strip()


def get_song_metadata(song: dict) -> Tuple[str, List[str], List[str]]:
    """Gets song metadata from song data

    Takes Genius translation artists into account.

    Args:
        song (dict): Song data.

    Returns:
        Tuple[str, List[str], List[str]]: Song's title,
            primary artists and featured artists.
    """
    title = song["title"]
    primary_artists = song["primary_artist"]["name"].split(" & ")
    featured_artists = [x["name"] for x in song["featured_artists"]]
    # If True, it means that this song is actually a translation.
    # So we should edit the song title and primary artist.
    # This is meant for translated songs.
    if primary_artists[0].startswith("Genius") and featured_artists == []:
        # This regex expression removes parentheses at the end of title
        # that indicates the song is a translation
        # e.g. song - title (English Translation)
        # but it only does so for Persian. It's tricky to do this for all
        # languages since the actual title itself may have parentheses and
        # it may get removed.
        title = TRANSLATION_PARENTHESES.sub("", title).strip()
        artists, title = [x.strip() for x in title.split("-")]
        primary_artists.clear()
        primary_artists.extend(artists.split(" & "))
    return title, primary_artists, featured_artists


def has_sentence(sentences: List[str], sentence: str) -> bool:
    """Checks for sentence in the list of sentences

    Used to check if a lyric sentence is in the lyric snippet.

    Args:
        sentences (List[str]): List of sentences of the lyrics snippet.
        sentence (str): Sentence from user input to check if it is in the lyrics.

    Returns:
        bool: True means the sentence is in the lyrics and False means it's not.
    """
    for x in sentences:
        if x in sentence:
            return True
    return False


def human_format(num: int) -> str:
    """Returns num in human-redabale format

    from https://stackoverflow.com/a/579376

    Args:
        num (int): number.

    Returns:
        str: Human-readable number.
    """
    # f

    if num < 10000:
        return str(num)

    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0  # type: ignore

    if num == int(num):
        formatter = "%.1d%s"
    else:
        formatter = "%.1f%s"

    return formatter % (num, ["", "K", "M", "G", "T", "P"][magnitude])


RT = TypeVar("RT")


def log(func: Callable[..., RT]) -> Callable[..., RT]:
    """logs entering and exiting functions for debugging."""
    logger = logging.getLogger(func.__module__)

    @wraps(func)
    def wrapper(*args, **kwargs) -> RT:
        logger.debug("Entering: %s", func.__name__)
        result = func(*args, **kwargs)
        # logger.debug(repr(result))
        logger.debug("Exiting: %s", func.__name__)
        return result

    return wrapper
