import time
import random
from multiprocessing import Pool
from itertools import chain, combinations, product
from footprint.models import Project
import os
import logging
import numpy as np
import pandas as pd
import db

#features
from features import Feature

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        #logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

print('==============================')
logging.info('Starting builder')
time.sleep(30)

files_map = pd.read_csv('/cache/files_map.csv')
#key = files_map.loc[files_map.file==document.filename].key.values[0]

cache_folder = '/cache'

def feature_extraction(document):
  feat = Feature(document.filename).execute(hop_length=512)
  return feat.df


def grouped_tokens(feat):
  fields = ['beat_type', 'chord_type', 'harm_note', 'melody_note', 'bass_note']
  d = feat.copy()

def tokenize(document):
  #tokens1 = grouped_tokens(document.features['feat'])
  #fields = ['beat_type', 'chord_type', 'harm_note', 'melody_note', 'bass_note']
  fields = ['beat_type', 'chord_type', 'harm_note', 'melody_note', 'bass_note']
  d = document.features['feat'].copy()
  d['res'] = ''
  for c in fields:
      d['res'] += (d[c].map(str) + ':')
  tk1 = d.res.values
  tk2 = [a + '::' + b for a, b in list(zip(tk1, tk1[1:]))]
  tk3 = [a + '::' + b for a, b in list(zip(tk2, tk1[2:]))]
  tokens = ' '.join(tk1) + ' ' +  ' '.join(tk2) + ' ' + ' '.join(tk3)
  #import code; code.interact(local=dict(globals(), **locals()))
  return tokens


def build():
  db_index_name = 'mirex_2020'

  # Initialize project, db instance and evaluator
  project = Project(cache_folder='/cache/project', cache_features=False, cache_tokens=True, cache_signal=True)
  db.connect_to_elasticsearch(project, db_index_name, True)
  project.client.set_scope(db_index_name, 'token', 'tokens_by_spaces')
  #project.tokenize('tracks', session_artists)
  project.process_feature('feat', feature_extraction)
  project.tokenize('token', tokenize)

  #import code; code.interact(local=dict(globals(), **locals()))

  for idx, document in enumerate(files_map.file.values):
    #import code; code.interact(local=dict(globals(), **locals()))
    logging.info('Adding document to database - %s' % document)
    try:
      project.add(document)
    except FileNotFoundError:
      logging.warning("File not found - skipping: filename=%s" % document)
      pass


build()


