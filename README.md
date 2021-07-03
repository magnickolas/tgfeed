# tgfeed

User-application for [Telegram][tg] to create feeds from the given lists of chats.

**Requirements:** Python 3.9+

## Quickstart

### Prepare your first feed

Create a folder with the name starting with \* (e.g. \*cat_memes) and put there all the channels to collect posts from.

### Install and run the application

```console
pip install tgfeed 
python -m tgfeed
```

The first time you run the app, you'll be prompted to type in your phone number, verification code and cloud password if applicable.

Tgfeed will create a private channel and periodically forward the new posts to it.

## Running from source
1. Install [Poetry][poetry]
2. Install dependencies into a virtual environment:
    ```console
    poetry install
    ```
3. Start the application and let it run:
    ```console
    # Sample app_id and app_hash, you should normally use your own
    export APP_ID=611335 APP_HASH=d524b414d21f4d37f08684c1df41ac9c
    poetry run python -m tgfeed
    ```

## Environment variables

|                       Name | Type | Info                                                             | Required |                Default value                 |
| --------------------------:|:----:| ---------------------------------------------------------------- |:--------:|:--------------------------------------------:|
|                     APP_ID | int  | [Telegram API][tg_api]                                           |    +     |                                              |
|                   APP_HASH | str  | [Telegram API][tg_api]                                           |    +     |                                              |
|         FOLDER_FEED_PREFIX | str  | The prefix of folders for feeds                                  |    -     |                      *                       |
|                     DB_DIR | str  | Location for persistent storage                                  |    -     | [User data dir] (e.g. ~/.local/share/tgfeed) |
| INITIAL_FORWARD_CHAT_LIMIT | int  | Amount of messages to take from new chats the time they're added |    -     |                      10                      |
|              POLL_INTERVAL | int  | How often to update feeds (in seconds)                           |    -     |                      5                       |


[tg]: https://telegram.org/
[tg_api]: https://core.telegram.org/api/obtaining_api_id
[poetry]: https://python-poetry.org/
