from pygount import SourceAnalysis, ProjectSummary
import statistics
import itertools
from multiprocessing.pool import ThreadPool
# from datetime import datetime
import logging

logging.basicConfig(level=logging.ERROR)

# language properties that we are interested to sum up
LANGUAGE_SUM_PROPERTIES = [
    'code_count', 
    'documentation_count', 
    'empty_count', 
    'file_count', 
    'line_count', 
    'source_count', 
    
]

# language properties that we are interested to get median value of
LANGUAGE_MEDIAN_PROPERTIES = [
    'code_percentage', 
    'documentation_percentage',
    'empty_percentage',
    'source_percentage'
]

def get(source_file_paths, worker_count):
    # start = datetime.now()
    project_summary = ProjectSummary()
    
    with ThreadPool(processes=worker_count) as pool:
        worker_arguments = list(zip(source_file_paths, itertools.repeat('pygount')))
        source_analysis_list = pool.starmap(SourceAnalysis.from_file, worker_arguments)
        
    
    for source_analysis in source_analysis_list:
        project_summary.add(source_analysis)
    # print('loc run took: ')
    # print(datetime.now() - start)
    return get_proj_dict(project_summary)

def get_summary(repos_stats):
    # init summary dict
    summary_loc = dict()
    
    # aggregate info from multiple loc dicts into one, group by language and corresponding metrics
    # e.g. {'Python':{'code_count':[1,40,33],...}, 'Markdown':{'code_count':[13, 22],...}}
    for repo_stats in repos_stats:
        for language in repo_stats['loc'].keys():
            # create a common dict with loc info for a given language if it does not exist
            if language not in summary_loc.keys():
                summary_loc.update({language: _create_summary_for_language(language)})
            # append loc info to the corresponding language
            for property in summary_loc[language].keys():
                summary_loc[language][property].append(repo_stats['loc'][language][property])
    
    # compute proper values for summary metrics
    for language in summary_loc.keys():
        # sum properties that need to be summed up
        for property in LANGUAGE_SUM_PROPERTIES:
            summary_loc[language][property] = sum(summary_loc[language][property])
        # get median from properties that need to be medianned :D
        for property in LANGUAGE_MEDIAN_PROPERTIES:
            summary_loc[language][property] = statistics.median(summary_loc[language][property])
    
    return summary_loc
    # ProjectSummary.add()
    # print(repos_stats)

def _create_summary_for_language(language):
    summary_lang_loc = dict()
    for property in LANGUAGE_SUM_PROPERTIES + LANGUAGE_MEDIAN_PROPERTIES:
        summary_lang_loc.update({property: list()})
    
    return summary_lang_loc

def get_lang_dict(language_summary):
    lang_dict = dict()
    
    for property in LANGUAGE_SUM_PROPERTIES + LANGUAGE_MEDIAN_PROPERTIES:
        lang_dict.update({property: getattr(language_summary, property)})
    
    return lang_dict

def get_proj_dict(project_summary):
    proj_dict = dict()
    # iterate over languages
    for language, summary in project_summary.language_to_language_summary_map.items():
        proj_dict.update({language: get_lang_dict(summary)})
    
    # get total stats for all languages
    proj_dict.update({
        'Total': {
            'code_count':               project_summary.total_code_count,
            'documentation_count':      project_summary.total_documentation_count,
            'empty_count':              project_summary.total_empty_count,
            'file_count':               project_summary.total_file_count,
            'line_count':               project_summary.total_line_count,
            'source_count':             project_summary.total_source_count,
            'code_percentage':          project_summary.total_code_percentage,
            'documentation_percentage': project_summary.total_documentation_percentage,
            'empty_percentage':         project_summary.total_empty_percentage,
            'source_percentage':        project_summary.total_source_percentage
        }
    })
    
    return proj_dict