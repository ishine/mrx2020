import time
import random
from multiprocessing import Pool
from itertools import chain, combinations, product
from footprint.models import Project
import footprint.evaluators as evaluators
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
files_map = pd.read_csv('/cache/files_map.csv', sep=';;')
queries_map = pd.read_csv('/cache/queries_map.csv', sep=';;')

results_file = '/cache/results.txt'
db_index_name = 'mirex_2020'


tks = [['tk_i', 'tk_g' ,'tk_h', 'tk_c'], 'tk_a', 'tk_b', 'tk_c', 'tk_d', 'tk_e', 'tk_f', 'tk_g', 'tk_h']
for tk in tks:

  # create new project with the default CSI evaluator
  project = Project(cache_folder='/cache/project', cache_features=True, cache_tokens=False, cache_signal=True)

  evaluator = evaluators.CSI(project)

  # Initialize project's db client
  db.connect_to_elasticsearch(project, db_index_name, True)
  #project.client.set_scope(db_index_name, ['tk_b'], 'tokens_by_spaces')

  project.client.set_scope(db_index_name, tk, 'tokens_by_spaces')

  # Declare methods used to extract features
  project.process_feature('feat', features.complete_extraction)

  # Declare tokenization strategies to be used
  project.tokenize('tk_a', tokenization.grouped_tokens(['beat_type', 'chord_type', 'harm_note', 'melody_note', 'bass_note']))
  project.tokenize('tk_b', tokenization.grouped_tokens(['chord_type', 'harm_note', 'melody_note', 'bass_note']))
  project.tokenize('tk_c', tokenization.grouped_tokens(['chord_type', 'harm_note', 'melody_note']))
  project.tokenize('tk_d', tokenization.grouped_tokens(['beat_type', 'chord_type', 'harm_note', 'bass_note']))
  project.tokenize('tk_e', tokenization.grouped_tokens(['beat_type', 'chord_type', 'melody_note', 'bass_note']))
  project.tokenize('tk_f', tokenization.grouped_tokens(['beat_type', 'chord_type', 'melody_note']))
  project.tokenize('tk_g', tokenization.grouped_tokens(['beat_type', 'chord_type', 'harm_note']))
  project.tokenize('tk_h', tokenization.grouped_tokens(['beat_type', 'chord_type', 'bass_note']))
  project.tokenize('tk_i', tokenization.grouped_tokens(['beat_type', 'chord_type', 'melody_note']))

  evaluator.build(files_map.file.values)

  evaluator.match(queries_map.file.values, amnt_results_per_query=10)

  ev = evaluator.evaluate()


  import csv
  def read_clique_map(filename):
    f = open(filename, 'r', encoding='utf-8')
    s = list(csv.reader(f, delimiter='\t'))
    f.close()
    return dict([[x[1], x[0]] for x in s])
  clique_file = '/cache/clique_file.csv'
  df_clique = files_map.append(queries_map)
  df_clique['clique'] = df_clique.key.map(lambda x: x.split('/')[5])
  df_clique[['clique', 'file']].to_csv(clique_file, index=False, header=False, sep='\t')
  #import code; code.interact(local=dict(globals(), **locals()))
  print(evaluator.results(read_clique_map(clique_file), ranking_size=10)[0].T)

