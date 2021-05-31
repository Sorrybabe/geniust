<h1>
  <img src="logo.png" alt="GeniusT logo" width="200" align="center"/>
  Genius T
</h1>


![status](https://img.shields.io/uptimerobot/status/m786636302-b2fa3edeb9237ae327f70d06)
![GitHub release (latest by
date)](https://img.shields.io/github/v/release/allerter/geniust)
![build](https://github.com/allerter/geniust/workflows/build/badge.svg)
[![Test
Coverage](https://api.codeclimate.com/v1/badges/74d5611d77cb26f4ed16/test_coverage)](https://codeclimate.com/github/Allerter/geniust/test_coverage)
[![Code style:
black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Telegram
Link](https://img.shields.io/static/v1?label=Telegram&message=Click%20Here&color=blue&logo=telegram)](https://t.me/genius_the_bot)

A Telegram bot that provides music info and lyrics from Genius.

## Features

> -   [Genius/Music Info](#geniusmusic-info)
> -   [Genius Account](#genius-account)
> -   [GeniusT Shuffle](#geniust-shuffle)
> -   [Song Lyrics](#song-lyrics)
> -   [Album Lyrics](#album-lyrics)
> -   [Telegram features](#telegram-features)

### Genius/Music Info

GeniusT allows searching for songs, albums, artists, users, and song
lyrics. Furthermore, users can access tracks in albums, information
about those tracks, view the artist info of those tracks, and about any
information that one could want! All entities (albums, artists, and
songs) are deep-linked; for example, users can view the artist of a song
just by clicking on the artist\'s name, and from there they can go on to
viewing that artist\'s songs, albums, the features on those songs and
all that can be discovered!

### Genius Account

Using Genius\'s OAuth2, users can easily log into Genius in the bot and
view their account\'s details (including unread messages), and even vote
on album/song descriptions when viewing them.

### GeniusT Shuffle
<img src="geniust/data/shuffle.jpg" alt="GeniusT Shuffle logo" width="480"/>
GeniusT offers a basic genre-based music recommendation system that
offers users song recommendations from about 20K songs based on their
favorite genres and artists. Users can get their preferences from their
Genius or Spotify account or enter them manually. By logging into their
account through OAuth2, GeniusT will try to generate user's preferences
based on their account activity. If the user chooses to go the manual route,
they either input their age (and let the bot guess
the genres) or select them manually. Afterward, users can also add their
favorite artists from the available ones or finish without any favorite
artists (each user must have at least one favorite genre). Available
genres:

Fore more information about the recommender itself refer to the
[GeniusT Recommender](https://github.com/allerter/geniust-recommender)
repository.

Users can start using shuffle by sending the /shuffle command. After
submitting their genres and adding their favorite artists, their
preferences are saved. From then on, sending /shuffle will return 5
recommended songs based on their preferences. For any of the 5 songs, if
they can be found on Genius, they\'ll be deep-linked to be viewed. There
also be deep-links for preview and download URLs if the song has a
preview URL for song previews or a download URL or ISRC ID for
downloads. The bot will send the full song if the song has a direct
download URL, but if it has an ISRC ID, users will be directed to
another bot.

### Song Lyrics

The bot provides song lyrics using Telegram messages. The annotated
fragments of songs are linked to their annotations which are uploaded by
the bot in a separate channel meant for annotations. Meaning when users
view lyrics for a song, they can click on highlighted lyrics that will
lead them to the annotations right there in Telegram.

Currently **annotated** lyrics are only open to the developers.

### Album Lyrics

As for the albums, users can either view the tracks and their lyrics
one-by-one (as they normally would) or they could have the lyrics of all
the tracks all in one place in three formats:

-   PDF: A PDF containing the album description, a table of contents
    containing song titles linked to the page of the song lyrics, and
    the lyrics of all the songs in the album.
-   ZIP: A ZIP file containing TXT files of each song\'s lyrics.
-   TELEGRA.PH: Returns a link to a *telegra.ph* page which in turn has
    the album\'s description and links to other *telegra.ph* pages that
    each has the description and the lyrics of a song. This feature
    isn't maintained, so some things might look off.

Currently this feature is only open to the developers.

### Lyrics Customizations

The bot allows users to choose between including and excluding the
annotations from the lyrics. Users can also choose not to include ASCII
or non-ASCII characters in the lyrics. One of the uses of this could be
to remove English lines from songs that have been translated into Arabic
or Persian so that only the translated lines remain.

### Telegram Features

Users can search Genius navigating the inline menu which can be accessed
using the `/start` command. Alternatively, you could directly reach to
the desired feature using commands:

-   **/start** start the bot
-   **/album**: search for an album
-   **/artist**: search for an artist
-   **/song**: search for a song
-   **/song_by_lyrics**: search for a song by lyrics
-   **/user**: search for a user
-   **/lyric_card**: get a lyric card by providing lyrics
-   **/lyric_card_custom**: build a custom lyric card
-   **/shuffle**: Get music recommendation
-   **/bot_language**: set bot language
-   **/login**: log into Genius/Spotify
-   **/cancel**: cancel the current task
-   **/donate**: donate to the developers
-   **/help**: more info about the bot
-   **/contact_us**: send us a message

Users can also perform searches by using the inline search feature. For
example:

-   searching songs: `@genius_the_bot .song we will rock you`
-   searching albums: `@genius_the_bot .album hotel diablo`
-   searching artists: `@genius_the_bot .artist Queen`
-   searching users: `@genius_the_bot .user lemonade`
-   getting lyric cards: `genius_the_bot .lyric_card we will rock you`
