# tgfeed

Tool for [Telegram][tg] to create feeds from lists of chats.

## Main features

- Collect posts from multiple channels in an RSS manner and publish them to a single one
- Optionally filter out posts that are suspicious of advertisements

## Quickstart

### Prepare your first feed

Create a folder with a name starting with \* (e.g. \*cats_memes)
and put all the channels to collect posts from in it.

### Install the application

The app requires at least Python 3.9

```console
pip install tgfeed
```

### Get API id

One should follow [an instruction][tg_api] to obtain a developer API id.

### Run

```console
# Sample app_id and app_hash, you should normally use your own
export APP_ID=611335 APP_HASH=d524b414d21f4d37f08684c1df41ac9c
python -m tgfeed
```

The first time you run the app, you'll be prompted to type in your phone number,
verification code and cloud password if applicable.

The tool will create a private channel with the folder's name
(it can be changed manually later) and periodically forward new posts to it.

### Daemonizing

As the application needs to be continuously run, it is recommended
to use some tooling in order to create a background daemon,
e.g. a systemd service:

```
[Unit]
Description=tgfeed
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0
StartLimitBurst=10

[Service]
Restart=on-failure
ExecStart=python3 -m tgfeed
# Sample app_id and app_hash, you should normally use your own
Environment="APP_ID=611335"
Environment="APP_HASH=d524b414d21f4d37f08684c1df41ac9c"
# ... other env vars ...

[Install]
WantedBy=default.target
```

## Running from source

1. Install [Poetry][poetry]
2. Install dependencies into a virtual environment:
   ```console
   poetry install
   ```
3. Run the application same as in the previous section

## Environment variables

|                       Name | Type | Info                                                                    | Required |                Default value                 |
| -------------------------: | :--: | ----------------------------------------------------------------------- | :------: | :------------------------------------------: |
|                     APP_ID | int  | [Telegram API][tg_api]                                                  |    +     |                                              |
|                   APP_HASH | str  | [Telegram API][tg_api]                                                  |    +     |                                              |
|         FOLDER_FEED_PREFIX | str  | The prefix of folders for feeds                                         |    -     |                      \*                      |
|                     DB_DIR | str  | Location for persistent storage                                         |    -     | [User data dir] (e.g. ~/.local/share/tgfeed) |
| INITIAL_FORWARD_CHAT_LIMIT | int  | Amount of messages to take from new chats the time they're added        |    -     |                      1                       |
|              POLL_INTERVAL | int  | How often to update feeds (in seconds)                                  |    -     |                      5                       |
|       USE_EXISTING_CHANNEL | bool | Whether to use existing channel with the approptiate name to forward to |    -     |                    False                     |
|     IGNORE_DUPLICATE_POSTS | bool | Ignore duplicate posts from channels                                    |    -     |                     True                     |
|    REMOVE_FORWARDED_HEADER | bool | Remove forwarded header from posts                                      |    -     |                    False                     |
|      MARK_CHANNELS_AS_READ | bool | Mark channels as read after forwarding                                  |    -     |                     True                     |
|       IGNORE_ADVERTISEMENT | bool | Ignore messages containing potential advertisement                      |    -     |                    False                     |
|            IGNORE_NO_MEDIA | bool | Ignore messages without media content (meme mode)                       |    -     |                    False                     |

[tg]: https://telegram.org/
[tg_api]: https://core.telegram.org/api/obtaining_api_id
[poetry]: https://python-poetry.org/
