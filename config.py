import os


class Config:
    database_uri: str = os.environ.get(
        "ZUD_DATABASE_URI", "sqlite:///db.sqlite3"
    )
    deadline_time: str = os.environ.get("ZUD_DEADLINE_TIME", "06:00:00")
    cli_user_id: int = int(os.environ.get("ZUD_CLI_USER_ID", 1))
