# Kamyroll-GUI

![Kamyroll-GUI](kamyroll-gui.png)

A GUI frontend for the Kamyroll-API using Python and PySide6

## Usage

When starting the application you will be presented with a list and some buttons on the right.
If you are starting it for the first time it will setup some default settings.
You can change them by clicking the `Settings` button and changing the values there.

After you are done with settings, you can add links by clicking the `+ Add` button.
It will open a dialog box where you can paste a link.
If the link is supported it will show a green message.
Click `OK` to add the link to the list.

After adding all your links you can click:
- The `Download Subtitles` to only download subtitles
- The `Download All` button to download

While the download window is actuve you might get prompted for alternative settings
or if a file should be overwritten.

After the download is finished, there will be a popup.
You can now close the download window.

## Settings

Output directory is the base directory into which the files will be written.
Click the `Browse` button to change the parameter.

### Filename format

The settings menu has two fields where a "filename format" is accepted,
`Episode filename format` and `Movie fiename format`
These use python string formatting, everything inside of curly braces (`{}`)
will be replaced with a value, if it is supported.
For example `{series} - {episode}` will become `One Piece - 1`.
Use `{{` and `}}` if you want to use `{` or `}` literally.
For more information read the [Python documentation](https://docs.python.org/3/library/string.html#format-string-syntax).

These values are available for formatting:
- `title`: The title of the media
- `duration`: The duration of the video in milliseconds
- `description`: A description
- `year`: The release year

In addition for an episode these values are available:
- `series`: The series the episode is from
- `season`: The number of the season
- `season_name`: The name of the season
- `episode`: The number of the episode
- `episode_disp`: A string value representing the number
    - For something like specials it might show `Special 1`
- `date`: The release date

### Write separate subtitle files
This option will enable you to write a `.mp4` file and many `.ass` files
instead of a single `.mkv` file.
To help structuring it clearly, there is also a field called `Subtitle prefix`.
If used the file will be prefixed with that name.

If the movie file was `One Piece/One Piece - 01.mp4`
and the subtitle prefix was `subtitles`,
then the output filename for the subtitle would be
`One Piece/subtitles/One Piece - 01.eng.ass`

### Write metadata

This will write metadata like episode title or the cover picture to the file.

### Compress streams

This will make ffmpeg reencode the video.
Use this only if you know what you are doing.
Checking this will slow down the download.

### Use own login credentials

If you dont want to use the bypasses available
you can also provide your own login data.
If this is checked it will prompt you for
your email and password on download.

### Use strict matching

Sometimes some of the subtitles or resolutions might not be available.
If you dont check this box subtitles that are not available will be ignored and
if a resolution is not avaiable it will automatically select a lower resolution.
