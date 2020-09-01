import pandas as pd

def grouped_tokens(fields):
  flds = fields
  def _grouped_tokens(document):
    d = document.features['feat'].copy()
    d['res'] = ''
    for c in flds:
        d['res'] += (d[c].map(str) + ':')
    tk1 = d.res.values
    tk2 = [a + '::' + b for a, b in list(zip(tk1, tk1[1:]))]
    tk3 = [a + '::' + b for a, b in list(zip(tk2, tk1[2:]))]
    tokens = ' '.join(tk1) + ' ' +  ' '.join(tk2) + ' ' + ' '.join(tk3)
    return tokens
  return _grouped_tokens
