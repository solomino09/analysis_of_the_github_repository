import requests
import time
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
from getpass import getpass


print("\nPlease enter your credentials for GitHub:")
login = input("Login: ") or None
password = getpass("Password: ") or None
authentication = HTTPBasicAuth(login, password)

if not login and not password:
    time_out = 60
    print("\nYou will have to wait a long time, prepare a lot of tea and cookies!\n")
else:
    time_out = 0

url_input = input("Public repository URL at github.com: ") or None
if url_input:
    url_input = url_input.split("github.com")
    url_in_processing = url_input[1].split("/")
    url = "https://api.github.com/repos/{}/{}".format(
        url_in_processing[1], url_in_processing[2]
    )

start_date = (
    input("Analysis start date. If empty, then unlimited (format yyyy-mm-dd) : ")
    or None
)
if start_date:
    start_date = start_date.split("-")
    start_date = datetime(int(start_date[0]), int(start_date[1]), int(start_date[2]))
    date_since = "&since=" + start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
else:
    date_since = ""

end_date = (
    input("Analysis end date. If empty, then unlimited (format yyyy-mm-dd) : ") or None
)
if end_date:
    end_date = end_date.split("-")
    end_date = datetime(int(end_date[0]), int(end_date[1]), int(end_date[2]), 23, 59)
    date_until = "&until=" + end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
else:
    date_until = ""
branch = input("Repository branch. The default is master: ") or "master"


def converting_date_time(pull_request):
    date = pull_request["created_at"].split("T")[0].split("-")
    time = pull_request["created_at"].split("T")[1].split(":")
    date_time = datetime(
        int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1])
    )
    return date_time


def pull_requests_of_repo_filter_by_date(list_pull_requests):
    result = []
    if start_date or end_date:
        for pull_req in list_pull_requests.json():
            pull_req_craated = converting_date_time(pull_req)
            if start_date and end_date:
                if start_date <= pull_req_craated and pull_req_craated <= end_date:
                    result.append(pull_req)
            elif start_date:
                if start_date <= pull_req_craated:
                    result.append(pull_req)
            elif end_date:
                if pull_req_craated <= end_date:
                    result.append(pull_req)
        return result
    else:
        return list_pull_requests.json()


def issues_in_repo_filter_by_date(list_issues):
    result = []
    for issue in list_issues.json():
        if "issues" in issue["html_url"]:
            if start_date or end_date:
                issue_craated = converting_date_time(issue)
                if start_date and end_date:
                    if start_date <= issue_craated and issue_craated <= end_date:
                        result.append(issue)
                elif start_date:
                    if start_date <= issue_craated:
                        result.append(issue)
                elif end_date:
                    if issue_craated <= end_date:
                        result.append(issue)
            else:
                result.append(issue)
    return result


def pull_requests_of_repo_github(repo, state_pulls):
    pull_requests = []
    next = True
    i = 1
    while next == True:
        link = repo + "/pulls?base={}&state={}&page={}&per_page=100".format(
            branch, state_pulls, i
        )
        if login and password:
            pull_requests_pg = requests.get(link, auth=authentication)
        else:
            pull_requests_pg = requests.get(link)
        pull_requests = pull_requests + pull_requests_of_repo_filter_by_date(
            pull_requests_pg
        )
        if "link" in pull_requests_pg.headers:
            if 'rel="next"' not in pull_requests_pg.headers["link"]:
                next = False
        if len(pull_requests_pg.json()) < 100:
            next = False
        else:
            time.sleep(time_out)
        i += 1
    return pull_requests


def commits_of_repo_github(repo):
    commits = []
    next = True
    i = 1
    while next == True:
        link = repo + "/commits?sha={}&page={}&per_page=100{}{}".format(
            branch, i, date_since, date_until
        )
        if login and password:
            commits_pg = requests.get(link, auth=authentication)
        else:
            commits_pg = requests.get(link)
        commits = commits + commits_pg.json()
        if "link" in commits_pg.headers:
            if 'rel="next"' not in commits_pg.headers["link"]:
                next = False
        if len(commits_pg.json()) < 100:
            next = False
        else:
            time.sleep(time_out)
        i += 1
    return commits


def issues_of_repo_github(repo, state_issues):
    issues = []
    next = True
    i = 1
    while next == True:
        link = repo + "/issues?state={}&page={}&per_page=100{}".format(
            state_issues, i, date_since
        )
        if login and password:
            issues_pg = requests.get(link, auth=authentication)
        else:
            issues_pg = requests.get(link)
        issues = issues + issues_in_repo_filter_by_date(issues_pg)
        if "link" in issues_pg.headers:
            if 'rel="next"' not in issues_pg.headers["link"]:
                next = False
        if len(issues_pg.json()) < 100:
            next = False
        else:
            time.sleep(time_out)
        i += 1
    return issues


def quantity_of_old_items(list_items, days):
    result = []
    point_datetime = datetime.now() - timedelta(days)
    for item in list_items:
        item_craated = converting_date_time(item)
        if item_craated <= point_datetime:
            result.append(item)
    return len(result)


def date_print(data_open, data_closed, data_old):
    print("_" * 31)
    print("|" + " " * 29 + "|")
    print("| {}|  {} |".format("Open".ljust(15), str(len(data_open)).ljust(9)))
    print("|", "_" * 29, "|", sep="")

    print("|" + " " * 29 + "|")
    print("| {}|  {} |".format("Closed".ljust(15), str(len(data_closed)).ljust(9)))
    print("|", "_" * 29, "|", sep="")

    print("|" + " " * 29 + "|")
    print("| {}|  {} |".format("Old".ljust(15), str(data_old).ljust(9)))
    print("|", "_" * 29, "|", sep="")


def commit_analysis():
    data_commits = commits_of_repo_github(url)
    commit_counter = []
    for d_c in data_commits:
        if d_c["author"]:
            if d_c["author"]["login"]:
                commit_counter.append(d_c["author"]["login"])
    commit_counter_dict = dict(
        (x, commit_counter.count(x)) for x in set(commit_counter)
    )
    best_commiter = sorted(
        commit_counter_dict.items(), key=lambda value: value[1], reverse=True
    )
    print("\n\tComiter rate")
    print("_" * 31)
    print("|" + " " * 29 + "|")
    for (key, value) in best_commiter[:30]:
        print("| {}|  {} |".format(key.ljust(20), str(value).ljust(4)))
    if not len(best_commiter):
        print("| {}|  {} |".format("Commits".ljust(15), str(0).ljust(9)))
    print("|", "_" * 29, "|", sep="")


def pull_requests_analysis():
    data_open = pull_requests_of_repo_github(url, "open")
    data_closed = pull_requests_of_repo_github(url, "closed")
    quantity_old_pr = quantity_of_old_items(data_open, 30)
    print("\n\tPull requests info")
    date_print(data_open, data_closed, quantity_old_pr)


def issues_analysis():
    data_issues_open = issues_of_repo_github(url, "open")
    data_issues_closed = issues_of_repo_github(url, "closed")
    quantity_old_issues = quantity_of_old_items(data_issues_open, 14)
    print("\n\t Issues info")
    date_print(data_issues_open, data_issues_closed, quantity_old_issues)


if url_input:
    commit_analysis()
    pull_requests_analysis()
    issues_analysis()
