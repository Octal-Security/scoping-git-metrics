import git
import re
from datetime import datetime, timedelta
from collections import Counter
import pytz
from multiprocessing.pool import ThreadPool

GIT_CHANGE_REGEX = re.compile(r'@@ \-(\d+),?(\d+)? \+(\d+),?(\d+)? @@')

def commit_churn_threadsafe(repo_path, commit_sha, next_commit_sha):
    repo = git.Repo(repo_path)
    commit      = repo.commit(commit_sha)
    next_commit = repo.commit(next_commit_sha)
    return commit_churn(commit, next_commit)

def commit_churn(commit, next_commit):
    added   = 0
    deleted = 0
    
    for diff in commit.diff(next_commit, create_patch=True):
        git_changes = GIT_CHANGE_REGEX.findall(diff.diff.decode('utf-8'))
        for git_change in git_changes:
            _, old_line_count, _, new_line_count = git_change
            # deal with diff lines like @@ -1 +1,2 @@
            # if old / new line count is missing -- 1 line was modified
            if not old_line_count:
                old_line_count = 1
            
            if not new_line_count:
                new_line_count = 1
            
            line_count_diff = int(new_line_count) - int(old_line_count)
            if line_count_diff > 0:
                added   += line_count_diff
            else:
                deleted += abs(line_count_diff)

    return added, deleted

def get(repo_path, worker_count):
    # start = datetime.now()
    repo = git.Repo(repo_path)
    
    yearly_churn = {
        'added'  : 0,
        'deleted': 0,
        'changed': 0
    }

    year_ago = pytz.UTC.localize(datetime.today()) - timedelta(days=365)
    
    yearly_commits = [x for x in repo.iter_commits() if x.committed_datetime > year_ago]
    yearly_commits_sorted = sorted(yearly_commits, key=lambda x: x.committed_datetime)
    
    worker_arguments = list()
    for i, commit in enumerate(yearly_commits_sorted):
        if i + 1 < len(yearly_commits_sorted):
            worker_arguments.append((repo_path, commit.hexsha, yearly_commits_sorted[i + 1].hexsha))
    
    with ThreadPool(processes=worker_count) as pool:
        churn_list = pool.starmap(commit_churn_threadsafe, worker_arguments)
    
    
    # iterate over commits, get current & next commit to get the difference
    # for i, commit in enumerate(yearly_commits_sorted):
    #     if i + 1 < len(yearly_commits_sorted):
    #         next_commit = yearly_commits_sorted[i + 1]
    #         added, deleted = commit_churn(commit, next_commit)
            
    #         yearly_churn['added']   += added
    #         yearly_churn['deleted'] += deleted
    #         yearly_churn['changed'] += added + deleted
    
    for churn in churn_list:
        added, deleted = churn
        yearly_churn['added']   += added
        yearly_churn['deleted'] += deleted
        yearly_churn['changed'] += added + deleted
       
    # print(f'churn run took: {datetime.now() - start}; total commits processed: {len(yearly_commits_sorted)}')
    return yearly_churn

def get_summary(repos_stats):
    summary_churn = Counter()
    
    for repo_stats in repos_stats:
        # add up churn values from multiple dicts
        summary_churn += Counter(repo_stats['churn'])
    
    if len(summary_churn):
        return dict(summary_churn)
    # if churn is 0, return dict of zeros
    return {'added':0, 'deleted':0, 'changed':0}