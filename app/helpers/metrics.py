import subprocess
import tempfile
import json
import os
import statistics
import logging
# from datetime import datetime

# metrics that we are interested to obtain
REQUIRED_METRICS = [
    'cyclomatic_complexity', 
    'halstead_bugprop', 
    'halstead_difficulty',
    'halstead_volume',
    'maintainability_index'
]

def get(source_file_paths):
    # start = datetime.now()
    # write all source code paths to analyze inside a temporary file
    tf = tempfile.NamedTemporaryFile(mode='w', delete=False)
    # add \n char because .writelines() does not add it ._.
    tf.writelines([x + '\n' for x in source_file_paths])
    tf_name = tf.name
    tf.close()
    
    # run modified multimetric script with a temporary file with target source code paths
    p = subprocess.Popen(
        ['multimetric', tf_name], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    out, err = p.communicate()
    if err:
        logging.warning(f'multimetrics returned with code {p.returncode} and the following error message: {err}')
        # print error but do not raise exceptions, we might wanna skip unknown filetypes
        # raise Exception
    
    # delete temporary file
    os.remove(tf_name)
    
    # load json output into dict
    metrics = json.loads(out.decode('utf-8'))
    
    # use overall metrics for the given repo
    overall_metrics = metrics['overall'].copy()
    
    # cleanup non valuable keys
    for key in metrics['overall'].keys():
        if key not in REQUIRED_METRICS:
            overall_metrics.pop(key)
    
    # print('metrics run took: ')
    # print(datetime.now() - start)
    return overall_metrics

def get_summary(repos_stats):
    # init summary metrics dict
    summary_metrics = dict()
    for key in REQUIRED_METRICS:
        summary_metrics[key] = list()
    
    
    for repo_stats in repos_stats:
        for key in REQUIRED_METRICS:
            # add all keys that we need to one list
            summary_metrics[key].append(repo_stats['metrics'][key])
    
    # get median values for each metric
    for key, val in summary_metrics.items():
        summary_metrics[key] = statistics.median(val)
    
    return summary_metrics