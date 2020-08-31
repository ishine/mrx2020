import time
import random
from multiprocessing import Pool
from itertools import chain, combinations, product
from footprint.models import Project
from evaluator import Evaluator
import os
import logging
import numpy as np
import pandas as pd
import db

#features
import features
import tokenization

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("info.log"),
        logging.StreamHandler()
    ]
)
logging.info('Starting builder')

time.sleep(30) # TODO: remove

# file paths, configs and etc.
max_processors = 3
files_map = pd.read_csv('/cache/files_map.csv')
queries_map = pd.read_csv('/cache/queries_map.csv')
results_file = '/cache/results.txt'
db_index_name = 'mirex_2020'

# create new project with the default CSI evaluator
project = Project(cache_folder='/cache/project', cache_features=False, cache_tokens=True, cache_signal=True)
evaluator = evaluators.CSI(project)

# Initialize project's db client
db.connect_to_elasticsearch(project, db_index_name, True)
project.client.set_scope(db_index_name, 'token', 'tokens_by_spaces')

# Declare methods used to extract features
project.process_feature('feat', features.complete_extraction)

# Declare tokenization strategies to be used
project.tokenize('tk_a', tokenization.grouped_tokens(['beat_type', 'chord_type', 'harm_note', 'melody_note', 'bass_note']))
project.tokenize('tk_b', tokenization.grouped_tokens(['chord_type', 'harm_note', 'melody_note', 'bass_note']))

evaluator.build(files_map.file.values)

evaluator.match(queries_map.file.values, amnt_results_per_query=10)

ev = evaluator.evaluate()

import code; code.interact(local=dict(globals(), **locals()))







