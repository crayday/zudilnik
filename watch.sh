curdir=$(dirname -- "$0")
watch "python3 $curdir/cmdrun.py gi && echo && python3 $curdir/cmdrun.py tl 40"
