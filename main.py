import os
import time
import argparse
from datetime import timedelta
import datetime
import pytz
import random
from git import Repo # incorrect warning, ignore
import socket

# Set to True while debugging, otherwise False. Disables actively committing.
DEBUG = False
# on any given day, choose a random number of commits to add between:
COMMIT_MIN = 200
COMMIT_MAX = 400
HOSTNAME_MATCH = "boorb" # boorb, birb, crow, starchy

# this script works in a period of 26 weeks, starting from a specific date
# if the following is changed, must be 26 weeks from original, or the name-writing will be off
START_DATE = datetime.date(2021, 5, 9)  # must be SUNDAY
TODAY = datetime.date.today()
TIME = datetime.datetime.now().time()
# the shape of my name to commit
THOR = [
    [0, 0, 0, 0, 0, 0, 0],  # START: 0
    [0, 1, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 0],
    [0, 1, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],  # 6
    [0, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0],  # 12
    [0, 0, 1, 1, 1, 0, 0],
    [0, 1, 0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],  # 18
    [0, 1, 1, 1, 1, 1, 0],
    [0, 1, 0, 1, 0, 0, 0],
    [0, 1, 0, 1, 0, 0, 0],
    [0, 1, 0, 1, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0],  # 24
    [1, 1, 1, 1, 1, 1, 1] # insert a bar
]
THOR_LEN = THOR.__len__() # 26 

def print_name_test(n: list[list[int]]):
    """Print the name. Check that it is correctly formatted."""
    def l(x): return "#" if x == 1 else " "
    output = ["", "", "", "", "", "", ""]
    for week in n:
        for i, day in enumerate(week):
            output[i] += l(day)
    for r in output:
        print(r)
# print_name_test(THOR)

def get_root_directory() -> str:
    """return /home/thor/projects/github_name"""
    return "/home/thor/projects/github_name"
    # """return the root directory of the git repository."""
    # stream = os.popen("/home/thor/projects/github-name")
    # stream = os.popen("git rev-parse --show-toplevel")
    # root = stream.read().strip()
    # stream.close()
    # return root

DUMPFILE = get_root_directory() + "/.dump" # file to dump a billion commits into

def parse_args() -> argparse.Namespace:
    """
    Parses command line arguments.
    Returns argparse.Namespace: The parsed arguments.
    accept arguments to:
    - backdate commits some number of weeks
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backdate", help="flag: number of weeks to backdate commits", default=52, type=int)
    args = parser.parse_args()

    if DEBUG: print("args: %s" % args)
    assert(args.backdate <= 52 and args.backdate >= 1)
    return args

def is_name_day(date) -> bool:
    """return whether the date is a nameday."""
    day = (date.weekday() + 1) % 7 # rotation correction
    weeks_since_start_date = ((date - START_DATE) // 7).days
    week = weeks_since_start_date % THOR_LEN

    if THOR[week][day] == 0:
        return False
    else:
        return True

def preexisting_commits(repo_dir: str, date_string: str):
    import subprocess
    """
    Count the number of Git commits in a given repository on a specific date.
    :param repo_dir: Path to the Git repository directory as a string.
    :param date_string: Date in 'YYYY-MM-DD' format as a string.
    :return: Number of commits on the given date.
    """
    # Convert date_string to datetime object to calculate the next day
    date = datetime.datetime.strptime(date_string, '%Y-%m-%d')
    next_day = date + timedelta(days=1)
    
    # Format dates for git log command
    # since_date = date.strftime('%Y-%m-%d')
    # until_date = next_day.strftime('%Y-%m-%d')
    since_date = f"{date_string} 00:00"
    until_date = f"{date_string} 23:59"
    
    # Run git log command to get commits between since_date and until_date
    cmd = [
        'git', '-C', repo_dir, 'log',
        '--since={}'.format(since_date),
        '--until={}'.format(until_date),
        '--pretty=format:%h'
        # '--pretty=oneline'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Split the output by new lines to count commits. 
        # Filter out empty strings to avoid counting them as commits.
        commit_lines = [line for line in result.stdout.strip().split('\n') if line]
        n = len(commit_lines)
        print(f"{n} preexisting commits")
        return n
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
        return 0

def date_str(date) -> str:
    "return the date in format 'YYYY-MM-DD' with 0-padding"
    if date.day < 10:
        day = "0%s" % date.day
    else:
        day = str(date.day)
    if date.month < 10:
        month = "0%s" % date.month
    else:
        month = str(date.month)

    return "%s-%s-%s" % (date.year, month, day)

def git_commit_n_times_on_date(repo: Repo, n, date):
    """write `n` empty commits on `date`"""
    print(f"{date} writing {n} commits")
    if DEBUG: return

    with open(DUMPFILE, "a") as commit_dump:
        for i in range(n):
            aware_datetime = datetime.datetime(
                date.year, date.month, date.day, 14, i % 60, i % 59, i % 58, tzinfo=pytz.UTC)
            commit_msg = "date: %s, n: %s" % (date, i)
            commit_dump.write(commit_msg+"\n")
            repo.index.add(DUMPFILE)
            # The following is finicky. Non-aware datetimes are disallowed.
            repo.index.commit(
                commit_msg, commit_date=aware_datetime, author_date=aware_datetime)

def git_push(repo: Repo):
    """
    Pushes changes to the remote repository using the GitPython library.
    :param repo: A Repo instance representing the Git repository.
    """
    try:
        # Specify the remote name, assuming it's the default 'origin'
        remote = repo.remote(name='origin')
        push_info = remote.push()
        for info in push_info:
            print(f"Pushed {info.summary}")
    except Exception as e:
        print(f"An error occurred during git push: {e}")

def main():
    print(f"\ndate: {TODAY}, at time: {TIME}") 
    hostname = socket.gethostname()
    if hostname != HOSTNAME_MATCH:
        print(f"Only to be run on {HOSTNAME_MATCH}, not {hostname}, exiting...")
        return

    print(f"hostname matches; continuing on {hostname}")

    args = parse_args()
    repo = Repo(get_root_directory())
    # print(f"repo {repo}; dumpfile is {DUMPFILE}")
    assert(not repo.bare) # check that the repo is not empty

    # backdate a year with commits.
    date = max(START_DATE, TODAY - timedelta(weeks=args.backdate))
    assert(date > START_DATE) 

    while date < TODAY:
        if is_name_day(date):
            print(f"{date} is name day")
            # compute number of commits to add 
            date_string = date_str(date)
            n_preexisting = preexisting_commits(get_root_directory(), date_string)
            if n_preexisting > COMMIT_MIN: # don't duplicate work
                date += timedelta(days=1)
                continue

            n_commits = random.randrange(COMMIT_MIN, COMMIT_MAX) 
            n_diff = max(0, n_commits - n_preexisting)
            git_commit_n_times_on_date(repo, n_diff, date)

            # github defends against DDOS attacks.
            # be polite and wait 200ms before pushing the next day
            git_push(repo)
            time.sleep(0.2)
        else: 
            print(f"{date} is not nameday")
        
        date += timedelta(days=1)

if __name__ == "__main__":
    # dstr = date_str(TODAY)
    # n = preexisting_commits(get_root_directory(),dstr)
    # print(n, get_root_directory(), dstr)
    main()
