import pandas as pd
import numpy as np

def normalize_dataframe(df_orig):
  df = df_orig.copy()
  chord_type_values = ['maj', 'min', 'sus', 'aug', 'dim', 'x']
  beat_type_values = ['d', 'u', 'b', 'm']
  df['chord_type'] = df.chord_type.map(lambda x: chord_type_values.index(x))
  df['beat_type'] = df.beat_type.map(lambda x: beat_type_values.index(x))
  df['melody_note'] = df.melody_note+1
  df['bass_note'] = df.bass_note+1
  df['harm_note'] = df.harm_note+1
  df['downbeat'] = df['strong_beat'] = df['weak_beat'] = 0
  df.loc[df.beat_type==0, 'downbeat'] = 1
  df.loc[df.beat_type.isin([0, 1, 2]), 'strong_beat'] = 1
  df.loc[df.beat_type==3, 'weak_beat'] = 1
  return df

def ngrams(arr_tokens, n, tk_idx):
  tk = str(tk_idx)
  ngrams = [tk + '#' + ':'.join(x) for x in zip(*[arr_tokens[i:] for i in range(n)])]
  return ngrams

def compact_token(df, cols):
  arr = np.array(df[cols])
  return [''.join(map(lambda z: format(z, 'x'), x)) for x in arr]

def grouped_tokens(fields, tk_idx, ngrams_size=2):
  flds = fields
  idx = tk_idx
  n = ngrams_size
  def _grouped_tokens(document):
    d = normalize_dataframe(document.features['feat'])
    compacted_tokens = compact_token(d, fields)
    ngrammed_tokens =  ngrams(compacted_tokens, n, idx)
    tk = ' '.join(ngrammed_tokens)
    return tk
  return _grouped_tokens
