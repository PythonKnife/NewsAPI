import ast
import atexit
import json
import os
import time
from datetime import datetime, timedelta
from random import randrange

import git
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, redirect
from newsapi import NewsApiClient

COUNTRIES_LANGUAGES = { "ar": [None],
    # "ar": [None], "gr": [None], "nl": [None], "za": [None], "au": [None],
    # "hk": [None], "nz": [None], "kr": [None], "at": [None], "hu": [None],
    # "ng": [None], "se": [None], "be": [None], "in": [None], "no": [None],
    # "ch": [None], "br": [None], "id": [None], "ph": [None], "tw": [None],
    # "bg": [None], "ie": [None], "pl": [None], "th": [None], "ca": [None],
    # "il": [None], "pt": [None], "tr": [None], "cn": [None], "it": [None],
    # "ro": [None], "ae": [None], "co": [None], "jp": [None], "ru": [None],
    # "ua": [None], "cu": [None], "lv": [None], "sa": [None], "gb": [None],
    # "cz": [None], "lt": [None], "rs": [None], "us": [None], "eg": [None],
    # "my": [None], "sg": [None], "ve": [None], "fr": [None], "mx": [None],
    # "sk": [None], "de": [None], "ma": [None], "si": [None],
}
CATEGORIES = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

SOURCES_LANGUAGE = {
    "abc-news": "en", # "bbc-news": "en", "cnn": "en", "fox-news": "en", "google-news": "en",
}

app = Flask(__name__)

load_dotenv()

API_KEYS = ast.literal_eval(os.getenv("API_KEYS"))
LAST_KEY_INDEX = randrange(0, len(API_KEYS))

repo = git.Repo.init(path='.')
BRANCH_MASTER_NAME = "master"
BRANCH_DATA_NAME = "data"
remote_origin = repo.remote()


def get_key():
    global LAST_KEY_INDEX
    LAST_KEY_INDEX = (LAST_KEY_INDEX + 1) % len(API_KEYS)
    return API_KEYS[LAST_KEY_INDEX]


def git_prepare():
    repo.index.checkout(force=True)
    repo.git.checkout(BRANCH_MASTER_NAME)
    remote_origin.pull()
    if repo.git.branch("--list", BRANCH_DATA_NAME):
        git.Head.delete(repo, BRANCH_DATA_NAME, force=True)
    repo.create_head(BRANCH_DATA_NAME).checkout()


def git_done():
    if repo.active_branch.name == BRANCH_DATA_NAME:
        commit_and_push(BRANCH_DATA_NAME, "update data")
    else:
        print("Branch[{0}] wrong while commit the data!".format(repo.active_branch.name))


def commit_and_push(branch: str = 'master', message: str = 'Auto commit'):
    has_changed = False

    for file in repo.untracked_files:
        print(f'Added untracked file: {file}')
        repo.git.add(file)
        if has_changed is False:
            has_changed = True

    if repo.is_dirty() is True:
        for file in repo.git.diff(None, name_only=True).split('\n'):
            if file:
                print(f'Added file: {file}')
                repo.git.add(file)
                if has_changed is False:
                    has_changed = True

    if has_changed is True:
        repo.git.commit('-m', message)
        repo.git.push('origin', branch, force=True)


@app.route('/')
def index():
    return redirect("https://github.com/PythonKnife/NewsAPI/raw/master/README.md")


def write_file(path, file_name, content, mode='a'):
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, file_name), mode) as f:
        f.write(content)


def update_top_headline():
    newsapi = NewsApiClient(api_key=get_key())
    for category in CATEGORIES:
        for (country, language) in COUNTRIES_LANGUAGES.items():
            print("Started category:{0} country:{1} language:{2} at :{3}".format(category, country, language,
                                                                                 time.strftime(
                                                                                     "%A, %d. %B %Y %I:%M:%S %p")))
            for lan in language:
                top_headlines = newsapi.get_top_headlines(category=category, country=country,
                                                          language=lan, page_size=100)
                if lan is None:
                    lan = country
                write_file("top-headlines/category/{0}/{1}/".format(category, country), "{0}.json".format(lan),
                           json.dumps(top_headlines))


def update_everything():
    newsapi = NewsApiClient(api_key=get_key())
    for (source, language) in SOURCES_LANGUAGE.items():
        print("Started source:{0} : {1}".format(source, time.strftime("%A, %d. %B %Y %I:%M:%S %p")))
        all_articles = newsapi.get_everything(sources=source,
                                              from_param=(datetime.now() - timedelta(days=1, hours=5,
                                                                                     minutes=30)).date().isoformat(),
                                              language=language,
                                              sort_by='publishedAt',
                                              page_size=100)
        write_file("everything/", "{0}.json".format(source), json.dumps(all_articles))


def update_data():
    git_prepare()
    update_top_headline()
    update_everything()
    git_done()


# scheduler = BackgroundScheduler()
# INTERVAL = 6 * 60
# scheduler.add_job(func=update_data, trigger="interval", minutes=INTERVAL)
# if not scheduler.running:
#     scheduler.start()
#
# # Shut down the scheduler when exiting the app
# atexit.register(lambda: scheduler.shutdown())

update_data()
