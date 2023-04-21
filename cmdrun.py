#!/usr/bin/env python3
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from config import Config
from app_registry import AppRegistry
from cli.main import ZudilnikCmd


def runcmd_uninterrupted(cmdobj):
    try:
        cmdobj.cmdloop()
    except BaseException as e:
        error_msg = str(e)
        if not error_msg:
            error_msg = type(e).__name__
        print(f"Error: {error_msg}")
        runcmd_uninterrupted(cmdobj)


if __name__ == '__main__':
    config = Config()

    engine = create_engine(config.database_uri, future=True)
    session = Session(engine)
    now = lambda: datetime.now()

    app = AppRegistry(config, session, now)

    zudcmd = ZudilnikCmd(app)

    if len(sys.argv) >= 2:
        (script_name, *params) = sys.argv
        zudcmd.onecmd(" ".join(params))
    else:
        runcmd_uninterrupted(zudcmd)
