import cmd
import shlex
import re
from datetime import datetime, timedelta, time as dttime, date as dtdate
from Zudilnik import Zudilnik

"""
:tabe $mp/python/cli.txt
TODO с помощью precmd вывести время перед каждым выводом иной команды (кроме пустой)
TODO#3 начать реально заменять run.py новым кодом
"""

def get_param_number(line):
    (command, *params) = shlex.split(line)
    param_number = len(params)
    if re.search(r'\s$', line):
        param_number+=1
    return param_number

def matching_options(text, options):
    return options if not text else [option for option in options if option.startswith(text)]

def cmd_prompt():
    return f"{datetime.now().strftime('%H:%M')}> "

class ZudilnikCmd(cmd.Cmd):
    prompt = cmd_prompt()

    def postcmd(self, stop, line):
        self.prompt = cmd_prompt()
        return stop

    def emptyline(self):
        pass

    def do_EOF(self, line):
        print()
        return True

    def do_exit(self, line):
        return True

    def complete_hline(self, text, line, begidx, endidx):
        param_number = get_param_number(line)
        if param_number == 1: # подсказываем 1-ый аргумент name
            return matching_options(text, ['Yegor', 'Yulia', 'Eugene', 'Hish'])
        elif param_number == 2: # подсказываем 2-ой аргумент word
            return matching_options(text, ['common', 'heal', 'gore', 'less', 'wisdom', 'welcome', 'goodbye', 'kill'])
        else:
            return []

    def do_comment(self, line):
        """comment <text> | comment <record_id> <text> - comments a given record or the last record if not specified"""
        params = shlex.split(line)
        if len(params) >= 2:
            record_id = params[0]
            comment = params[1]
        else:
            record_id = 'last'
            comment = params[0]

        if record_id == 'last':
            data = zudilnik.comment_last_record(comment)
        else:
            data = zudilnik.comment_record(record_id, comment)

        print(f"Updated comment for record #{data['record_id']} started at {data['record_started_at']}")

deadline=dttime(7, 15) # 07:15 AM
zudilnik = Zudilnik(deadline)
ZudilnikCmd().cmdloop()
