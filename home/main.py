import time
import random
from itertools import chain, combinations, product
from footprint.models import Project
import footprint.evaluators as evaluators
from itertools import combinations
import os
import logging
import numpy as np
import pandas as pd
import db
import csv

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
files_map = pd.read_csv('/cache/files_map.csv', sep=';;')
queries_map = pd.read_csv('/cache/queries_map.csv', sep=';;')

results_file = '/cache/results.txt'
db_index_name = 'mirex_2020'


valid_cols = ['chord_type', 'beat_type', 'melody_note', 'bass_note', 'harm_note', 'downbeat', 'strong_beat', 'weak_beat']
candidate_cols = [[x] for x in valid_cols]
candidate_cols += [list(x) for x in list(combinations(valid_cols, 2))]
candidate_cols += [list(x) for x in list(combinations(valid_cols, 3))]
candidate_cols += [list(x) for x in list(combinations(valid_cols, 4))]

def read_clique_map(filename):
  f = open(filename, 'r', encoding='utf-8')
  s = list(csv.reader(f, delimiter='\t'))
  f.close()
  return dict([[x[1], x[0]] for x in s])



#import code; code.interact(local=dict(globals(), **locals()))
results_df = None

for idx, tk_cols in enumerate(candidate_cols):
  for ngrams in [1, 2, 3, 4]:

    # create new project with the default CSI evaluator
    project = Project(cache_folder='/cache/project', cache_features=True, cache_tokens=False, cache_signal=True)

    evaluator = evaluators.CSI(project)

    # Initialize project's db client
    db.connect_to_elasticsearch(project, db_index_name, True)
    #project.client.set_scope(db_index_name, ['tk_b'], 'tokens_by_spaces')

    token_code = 'tk_%s' % idx
    project.client.set_scope(db_index_name, token_code, 'tokens_by_spaces')

    # Declare methods used to extract features
    project.process_feature('feat', features.complete_extraction)

    # Declare tokenization strategies to be used
    project.tokenize(token_code, tokenization.grouped_tokens(tk_cols, idx, ngrams_size=ngrams))

    evaluator.build(files_map.file.values, max_processors=max_processors)

    evaluator.match(queries_map.file.values, amnt_results_per_query=10)

    ev = evaluator.evaluate()




    clique_file = '/cache/clique_file.csv'
    df_clique = files_map.append(queries_map)
    df_clique['clique'] = df_clique.key.map(lambda x: x.split('/')[5])
    df_clique[['clique', 'file']].to_csv(clique_file, index=False, header=False, sep='\t')
    r = evaluator.results(read_clique_map(clique_file), ranking_size=10)[0]
    r['cols_idx'] = idx
    r['ngrams'] = ngrams
    for col in valid_cols:
      r['col_%s' % col] = 0
    for col in tk_cols:
      r['col_%s' % col] = 1
    if results_df is None:
      results_df = r
    else:
      results_df = results_df.append(r)
    print(r.T)
    #import code; code.interact(local=dict(globals(), **locals()))
    results_df.to_csv('/cache/tokens_results.csv', index=False, header=True, sep='\t')


