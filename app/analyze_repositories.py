#!/usr/bin/env python
from urllib.parse import urlparse
import os
import git
from glob import glob
import argparse
from datetime import datetime
from tqdm import tqdm
import helpers
import shutil
import json
import logging
from helpers.logger import get_logger
import prettytable
from multiprocessing.pool import ThreadPool, Pool

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker-count', type=int, help='number of parallel workers, default=5', default=5)
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction, help='enable debug output')

    parser.add_argument('mode', help='parsing mode', choices=('filesystem', 'remote'))

    parser.add_argument('-u', '--git-username', help='git username for remote origin authentication')
    parser.add_argument('-p', '--git-password', help='git password for remote origin authentication. Your access tokens should go here')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--repo-file', help='file, containing URLs of git repositories to scan, separated by new lines')
    group.add_argument('-r', '--repo-url',  help='URL of a git repository to scan')
    
    parser.add_argument('-o', '--output-file', help='path to write the output JSON file to', required=True)

    return parser.parse_args()
    

def init_git_env(username, password):
    # set git auth variables
    os.environ['GIT_TRACE']    = '1'
    os.environ['GIT_ASKPASS']  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'git_askpass.py')
    if args.git_username:
        os.environ['GIT_USERNAME'] = username
    if args.git_password:
        os.environ['GIT_PASSWORD'] = password
    
    logger.debug(f'set environment vars to: {os.environ}')


def get_repo_urls(args):
    if args.repo_file:
        with open(args.repo_file, 'rb') as f:
            return [x.rstrip('/') for x in f.read().decode().strip().splitlines()]
    else:
        return [args.repo_url.rstrip('/')]
    

def open_repo(mode, repo_url):
    if mode == 'remote':
        repo_path = f'./repos/{urlparse(repo_url).path[1:]}'
        git.Repo.clone_from(repo_url, repo_path)
        logger.debug(f'cloning repo {repo_url} to {repo_path}')
        return repo_path
    
    try:
        git.Repo(repo_url)
    except git.exc.NoSuchPathError:
        logger.error(f'failed to open git repo at path: {repo_url}!')
    return repo_url

def get_repo_stats(repo_url, mode, worker_count):
    try:
        # open repo, get repo filepath
        repo_path = open_repo(mode, repo_url)
        # get repo items recursively in all subdirds
        source_wildcard = f'{repo_path}/**/*'
        source_file_paths = glob(source_wildcard, recursive=True)
        # filter off only files
        source_file_paths = [f for f in source_file_paths if os.path.isfile(f)]
        
        logger.debug(f'{repo_path} | got following source file paths from glob: {source_file_paths}')
        
        # execute 3 processing tasks in parallel 
        with ThreadPool(processes=3) as pool:
            async_churn   = pool.apply_async(helpers.churn.get,   (repo_path, worker_count))
            async_loc     = pool.apply_async(helpers.loc.get,     (source_file_paths, worker_count))
            async_metrics = pool.apply_async(helpers.metrics.get, (source_file_paths,))
            # wait for all tasks to complete
            pool.close()
            pool.join()
        
        # get code churn
        churn = async_churn.get()
        logger.debug(f'{repo_path} | churn: {churn}')
        
        # get loc
        loc = async_loc.get()
        logger.debug(f'{repo_path} | loc: {loc}')
        
        # get code quality metrics
        metrics = async_metrics.get()
        logger.debug(f'{repo_path} | metrics: {metrics}')
        
        # remove repo contents
        if mode == 'remote':
            shutil.rmtree(repo_path)
            logger.debug(f'removed {repo_path} directory')
        
        return {
            'url'    : repo_url,
            'churn'  : churn,
            'loc'    : loc,
            'metrics': metrics
        }
    except:
        logger.exception(f'the following error occured during the processing of repository {repo_url}')

def get_stats_summary(repos_stats):
    summary = {
        'summary': {
            'loc'    : helpers.loc.get_summary(repos_stats),
            'churn'  : helpers.churn.get_summary(repos_stats),
            'metrics': helpers.metrics.get_summary(repos_stats)
        },
        'repositories': repos_stats
    }
    
    return summary

def pprint(stats_summary):
    churn_table = prettytable.PrettyTable(
        field_names=['Added', 'Deleted', 'Changed'],
        align='l',
        float_format='0.2'
    )
    
    loc_table = prettytable.PrettyTable(
        field_names=['Language', 'Files', 'Total Lines', 'Lines of Code', 'Percentage of Code'],
        align='l',
        float_format='0.2',
        sortby='Total Lines',
        reversesort = True
    )
    
    metrics_table = prettytable.PrettyTable(
        field_names=['Metric Name', 'Metric Value'], 
        align='l',
        float_format='0.2'
    )
    # add table values
    churn_table.add_row(list(stats_summary['summary']['churn'].values()))
   
    for language, metrics in stats_summary['summary']['loc'].items():
        loc_table.add_row([language, metrics['file_count'], metrics['line_count'], metrics['code_count'], metrics['code_percentage']])
    
    for metric, value in stats_summary['summary']['metrics'].items():
        metrics_table.add_row([metric, value])
    
    print('\n\n[!] Churn stats\n')
    print(churn_table)
    print('\n\n[!] LoC stats\n')
    print(loc_table)
    print('\n\n[!] Code quality metrics stats\n')
    print(metrics_table)



# thread callback that refreshes tqdm pbar & stores results in a common list
def pbar_update(repo_stats):
    repo_name = repo_stats['url'].split('/')[-1]
    # append results
    repos_stats.append(repo_stats)
    # set pbar description
    pbar.set_description(f'Finished processing repo "{repo_name}"')
    # update pbar
    pbar.update()

# parse args
args = parse_args()
# init debug
if args.debug:
    logger = get_logger(logging.DEBUG)
else:
    logger = get_logger(logging.INFO)

if __name__ == '__main__':      
    # init git env vars
    init_git_env(args.git_username, args.git_password)
    # get repo urls to process
    repo_urls = get_repo_urls(args)

    logger.debug(repo_urls)
    print(f'[*] processing {len(repo_urls)} repositories')
    
    # init list for gathering callback results
    repos_stats = list()
    
    # init tqdm pbar with total length matching repos count
    pbar = tqdm(total=len(repo_urls))
    
    # run processing tasks for each repo in parallel
    # use processes to kick off main workers
    # use 3 separate threads inside of each main workers to split up the execution
    with Pool(processes=args.worker_count) as pool:
        try:
            for i in range(pbar.total):
                pool.apply_async(get_repo_stats, args=(repo_urls[i], args.mode, args.worker_count), callback=pbar_update)
            pool.close()
            pool.join()
        except KeyboardInterrupt:
            logger.error('script terminated by user... stopping the processing, outputting intermediate results...')
            pool.terminate()
    
    pbar.close()
    # get summary stats for all repos
    stats_summary = get_stats_summary(repos_stats)
    # pprint stats summary
    pprint(stats_summary)
    
    # results_file = f'./repositories_metrics_{datetime.now().strftime("%Y_%m_%d")}.json'
    with open(args.output_file, 'w') as f:
        json.dump(stats_summary, f)
    
    print(f'\n\n[+] saved repository metrics to file "{os.path.abspath(args.output_file)}"')