import time
import random
from multiprocessing import Pool
from itertools import chain, combinations, product
from footprint.models import Project
import os
import logging
import numpy as np
import footprint.features.ocmi as ocmi
import pandas as pd
import db

#features
import librosa
from madmom.features.downbeats import RNNDownBeatProcessor
from madmom.features.downbeats import DBNDownBeatTrackingProcessor
from scipy import interpolate
import crema

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
cache_folder = '/cache'

def feat_downbeats(document):
  y, sr = document.signal()
  act = RNNDownBeatProcessor()(y)
  proc = DBNDownBeatTrackingProcessor(beats_per_bar=[4, 3], fps=50)
  beats = proc(act)
  samples = librosa.time_to_samples(beats.T[0], sr=sr)
  downbeats = np.vstack((beats.T, samples.T)).T
  return downbeats

def feat_sync_crema(document):
  hop_length = 512
  model = crema.models.chord.ChordModel()
  y, sr =document.signal()
  data = model.outputs(y=y, sr=sr)
  fac = (float(sr) / 44100.0) * 4096.0 / hop_length
  times_orig = fac * np.arange(len(data['chord_bass']))
  nwins = int(np.floor(float(y.size) / hop_length))
  times_new = np.arange(nwins)
  interp = interpolate.interp1d(times_orig, data['chord_pitch'].T, kind='nearest', fill_value='extrapolate')
  X = interp(times_new)
  downbeats = document.features['downbeats']
  beat_frames = downbeats.T[2].astype(int)
  beat_frames = ((beat_frames / len(y) * X.shape[1])).astype(int)
  ret = librosa.util.sync(X, beat_frames, aggregate=np.median)
  return ret

def feat_sync_crema_ocmi(document):
  num_indexes = 3
  C = document.features['sync_crema']
  return np.round(ocmi.ocmi(C)[:num_indexes], 2)


def tokenize(document):
  import code; code.interact(local=dict(globals(), **locals()))
  return "1"


def build():
  db_index_name = 'mirex_2020'

  # Initialize project, db instance and evaluator
  project = Project(cache_folder='/cache/project', cache_features=False, cache_signal=True)
  db.connect_to_elasticsearch(project, db_index_name, True)
  project.client.set_scope(db_index_name, 'token', 'tokens_by_spaces')
  #project.tokenize('tracks', session_artists)
  project.process_feature('downbeats', feat_downbeats)
  project.process_feature('sync_crema', feat_sync_crema)
  project.process_feature('sync_crema_ocmi', feat_sync_crema_ocmi)
  project.tokenize('token', tokenize)

  #import code; code.interact(local=dict(globals(), **locals()))

  for idx, document in enumerate(files_map.file.values):
    print("aeae")
    #import code; code.interact(local=dict(globals(), **locals()))
    logging.info('Adding document to database - %s' % document)
    project.add(document)


build()


