import pandas as pd

df = pd.read_csv('./tmp/results.txt', sep='\t', names=['q', 'f'])
ct0 = ct1 = 0
for idx, line in df.iterrows():
  q = df['q'][0].split('/')[-1].split('-')[0]
  f = df['f'][0].split('/')[-1].split('-')[0].replace('.au', '')
  if q==f:
    ct0+=1
  else:
    ct1+=1
print(ct0, ct1)

