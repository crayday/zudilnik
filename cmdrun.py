#!/usr/bin/env python3
import os
import sys
from datetime import time as dttime
from Zudilnik import Zudilnik
from ZudilnikCmd import ZudilnikCmd

def runcmd_uninterrupted(cmdobj):
    try:
        cmdobj.cmdloop()
    except Exception as e:
        vprint("Error: "+str(e))
        runcmd_uninterrupted(cmdobj)

deadline = dttime(6, 0) # 06:00 AM
#dbpath = os.path.dirname(os.path.abspath(__file__))+"/db.sqlite3"
dbpath = os.getenv("HOME")+"/Dropbox/zudilnik/db.sqlite3"
zudcmd = ZudilnikCmd(Zudilnik(deadline, dbpath))

if len(sys.argv) >= 2:
    (script_name, *params) = sys.argv
    zudcmd.onecmd(" ".join(params))
else:
    runcmd_uninterrupted(zudcmd)
