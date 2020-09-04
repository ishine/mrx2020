import h5py
import numpy as np
import pandas as pd

files_map = pd.read_csv('../tmp/files_map.csv', sep=';;')
tokens_files = open('../tmp/tokens.txt').read().split('\n')
for idx, file in enumerate(tokens_files):
  with h5py.File(file,'r') as f:
    tokens = [x.split('#')[1] for x in f.attrs['tk_43'].split(' ')]
  new_text = ' '.join(tokens)
  file_key = "/%s" % '/'.join(file.split('/')[8:11])
  file_name = files_map.loc[files_map.file==file_key].key.values[0]
  group_name = file_name.split('/')[5]

  file1 = open("tokens/%s.%s.txt" % (group_name, idx), "w")
  file1.write(new_text)
  file1.close()


# Mean Average Precision (MAP)             0.528096
# Mean number of covers in top 1           0.629630
# Mean number of covers in top 10          3.129630
# Mean rank of first correct cover (MR)    4.259259
# Total candidates                        54.000000
# Total cliques                            9.000000
# Total covers in top 10                 169.000000
# Total queries                           54.000000
# cols_idx                                43.000000 <------ tk_43
# ngrams                                   4.000000
# col_chord_type                           1.000000
# col_beat_type                            0.000000
# col_melody_note                          1.000000
# col_bass_note                            0.000000
# col_harm_note                            1.000000
# col_downbeat                             0.000000
# col_strong_beat                          0.000000
# col_weak_beat                            0.000000
