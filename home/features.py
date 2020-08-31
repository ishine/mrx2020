import librosa
import vamp
import numpy as np
import pandas as pd
import scipy
import scipy.linalg
import logging
import scipy.stats
import crema
from scipy import interpolate
from sklearn.preprocessing import MinMaxScaler
from madmom.features.downbeats import RNNDownBeatProcessor
from madmom.features.downbeats import DBNDownBeatTrackingProcessor

class Feature():

    def __init__(self, file):
        logging.debug("Loading audio")
        self.df = None
        self.file = file
        self.y, self.sr = librosa.load(file)
        self.notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def execute(self, hop_length=512):
        self.generate_downbeats()
        self.melodia()
        self.generate_crema(hop_length)
        self.bass()
        self.estimate_key()
        self.merge()
        logging.debug("Done!")
        return self

    def generate_downbeats(self):
        logging.debug("Generating downbeats")
        rnn_proc = RNNDownBeatProcessor()
        rnn_obj = rnn_proc(self.file)
        downbeat_proc = DBNDownBeatTrackingProcessor(beats_per_bar=[3, 4], fps=100)
        downbeats = downbeat_proc(rnn_obj)
        df_downbeats = pd.DataFrame(downbeats, columns=['beat_time', 'beat'])
        f = lambda x: (x[1]-x[0])/2
        dif = list(map(f, zip(downbeats.T[0], downbeats.T[0][1:])))
        dif += downbeats.T[0][:-1]
        df_downbeats2 = df_downbeats.set_index('beat_time')
        df_mid = pd.DataFrame(dif, columns=['beat_time'])
        df_mid['beat'] = downbeats.T[1][:-1] + 0.5
        df_mid['beat_type'] =  'm'
        df_mid.set_index('beat_time', inplace=True)
        df_downbeats2['beat_type'] = 'b'
        df_downbeats2.loc[df_downbeats2.beat==1, 'beat_type'] = 'd'
        df_downbeats2.loc[df_downbeats2.beat==df_downbeats2.beat.max(), 'beat_type'] = 'u'
        df_downbeats2 = df_downbeats2.append(df_mid).reset_index(drop=False).sort_values(['beat_time']).reset_index(drop=True)
        self.df_downbeats = df_downbeats2

    def melodia(self):
        logging.debug("Generating melody")
        df = self.df
        melodia = vamp.collect(self.y, self.sr, "mtg-melodia:melodia")
        hop, melody = melodia['vector']
        timestamps = 8 * 128/self.sr + np.arange(len(melody)) * (128/self.sr)
        timestamps /= 2
        melody_pos = melody[:]
        melody_pos[melody<=0] = None
        df_melodia = pd.DataFrame(np.vstack([timestamps, melody]).T)
        #df_melodia.to_csv('/dataset/test/melodia.csv', index=False)
        df_melodia[1] = df_melodia[1].fillna(-1)
        #df_melodia = df_melodia[df_melodia[1]>0]
        #df_melodia[2] = librosa.hz_to_note(df_melodia[1], octave=False)

        #df_melodia[[0, 0, 2]].to_csv('%s.melody_note_all.txt' % self.file, sep='\t', header=False, index=False)
        tmp_df = pd.merge_asof(df_melodia, self.df_downbeats, left_on=0, right_on='beat_time')
        tmp_df = tmp_df[(tmp_df.beat_time>0) & (tmp_df[1] > 0)]
        tmp_df['melody_note'] = tmp_df[1].map(self.write_melody_note)
        tmp_df['melody_note_ori'] = librosa.hz_to_note(tmp_df[1], octave=False)


        tmp_df = tmp_df.groupby(['beat_time']).agg(lambda x: scipy.stats.mode(x)[0]).reset_index(drop=False)
        tmp_df = tmp_df[['beat_time', 'melody_note', 'melody_note_ori']]
        self.df_melodia = tmp_df

    def generate_crema(self, hop_length):
        logging.debug("Generating crema features")
        model = crema.models.chord.ChordModel()
        data = model.outputs(y=self.y, sr=self.sr)
        fac = (float(self.sr) / 44100.0) * 4096.0 / hop_length
        times_orig = fac * np.arange(len(data['chord_bass']))
        nwins = int(np.floor(float(self.y.size) / hop_length))
        times_new = np.arange(nwins)
        interp1 = interpolate.interp1d(times_orig, data['chord_pitch'].T, kind='nearest', fill_value='extrapolate')
        self.crema_pitch = interp1(times_new)
        interp2 = interpolate.interp1d(times_orig, data['chord_bass'].T, kind='nearest', fill_value='extrapolate')
        self.crema_bass = interp2(times_new)[:-1]
        chords = model.predict(y=self.y, sr=self.sr)
        df_chords = pd.DataFrame(list(chords.data))
        chord_arr = df_chords.value.str.split(':', n=1, expand=True)
        df_chords['chord_note'] = chord_arr[0].map(self.write_crema_note)
        df_chords['chord_ori'] = df_chords.value
        try:
            df_chords['chord_type'] = chord_arr[1].str.extract(r'(maj|min|sus|aug|dim)').fillna('x')
        except:
            df_chords['chord_type'] = 'x'
        self.df_chords = df_chords

    def bass(self):
        logging.debug("Processing Bass")
        bass_ocmi = self.ocmi(self.crema_bass, scaled=False)[0]
        ts = librosa.frames_to_time(np.arange(len(bass_ocmi)))
        df_bass = pd.DataFrame(bass_ocmi, index=ts, columns=['bass_note'])
        df_bass.loc[(pd.DataFrame(self.crema_bass).max()<0.3).values, 'bass_note'] = -1
        df_bass.reset_index(inplace=True, drop=False)
        df_bass = pd.merge_asof(df_bass, self.df_downbeats, left_on='index', right_on='beat_time')
        df_bass = df_bass[df_bass.beat_time>0][['beat_time', 'bass_note']]
        df_bass = df_bass.groupby(['beat_time']).agg(lambda x: scipy.stats.mode(x)[0]).reset_index(drop=False)
        self.df_bass = df_bass

    def merge(self):
        logging.debug('Merging')
        df_m1 = pd.merge_asof(self.df_downbeats, self.df_chords, left_on='beat_time', right_on='time')
        df_m1 = df_m1.join(self.df_melodia.set_index('beat_time'), on='beat_time')
        df_m1 = df_m1.join(self.df_bass.set_index('beat_time'), on='beat_time')
        df_m1['beat'] = df_m1['beat'].astype(int)
        def find_note(x):
            try:
                return self.notes[int(x)]
            except:
                return -1

        #self.base_note = df_m1[df_m1.beat==1].bass_note.value_counts().index[0]
        #base_note = self.notes[base_note]
        #logging.debug(base_note)
        #df_m1['base_note'] = base_note
        df_m1['bass_note_ori'] = df_m1['bass_note'].map(find_note)

        df_m1['harm_note'] = (df_m1['chord_note'] - self.base_note) % 12
        df_m1['melody_note'] = (df_m1['melody_note'] - df_m1['chord_note']) % 12
        df_m1['melody_note'] = df_m1['melody_note'].fillna(-1).astype(int)
        df_m1['bass_note'] = (df_m1['bass_note'] - df_m1['chord_note']) % 12


        #df_m1['melody_note'] = df_m1['melody_note'].fillna(-1).astype(int)
        self.df = df_m1[['beat_time', 'beat', 'chord_note', 'chord_ori', 'bass_note_ori', 'melody_note_ori', 'chord_type', 'beat_type', 'harm_note', 'melody_note', 'bass_note']]

    def ocmi(self, feature, scaled=True):
        r = np.argsort(1 - feature.T).T
        return (MinMaxScaler().fit_transform(r) if scaled else r)

    def write_melody_note(self, x):
        try:
            return self.notes.index(librosa.hz_to_note(x, octave=False))
        except:
            return -1

    def gen_labels(self):
        xx = np.array((self.df.beat_time).values)
        xx2 = np.hstack([[0], xx])
        dfx = pd.DataFrame([[f1, f2] for f1, f2 in zip(xx2[:-1], xx)])
        dfx['label'] = np.hstack([[''], np.array((self.df.beat_type).values)])[:-1]
        dfx.to_csv('%s.beats.txt' % self.file, sep='\t', header=False, index=False)
        dfx['label'] = np.hstack([[''], np.array((self.df.chord_ori).values)])[:-1]
        dfx.to_csv('%s.chord.txt' % self.file, sep='\t', header=False, index=False)
        dfx['label'] = np.hstack([[''], np.array((self.df.bass_note_ori).values)])[:-1]
        dfx.to_csv('%s.bass_note_ori.txt' % self.file, sep='\t', header=False, index=False)
        dfx['label'] = np.hstack([[''], np.array((self.df.melody_note_ori).values)])[:-1]
        dfx.to_csv('%s.melody_note_ori.txt' % self.file, sep='\t', header=False, index=False)

    def estimate_key(self):
        dist = pd.DataFrame(self.crema_pitch.T).mean().values
        candidate_keys = self.ks_key(dist)
        maj_min = pd.DataFrame(np.array(candidate_keys).T).max().values.argmax()
        estimated_key = candidate_keys[maj_min].argsort()[-1]
        self.base_note = estimated_key

    def ks_key(self, X):
        X = scipy.stats.zscore(X)

        # Coefficients from Kumhansl and Schmuckler
        # as reported here: http://rnhart.net/articles/key-finding/
        major = np.asarray([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        major = scipy.stats.zscore(major)

        minor = np.asarray([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        minor = scipy.stats.zscore(minor)

        # Generate all rotations of major
        major = scipy.linalg.circulant(major)
        minor = scipy.linalg.circulant(minor)
        return major.T.dot(X), minor.T.dot(X)

    def term_hist(self, columns):
        d = self.df.copy()
        d['res'] = ''
        for c in columns:
            d['res'] += (d[c].map(str) + ':')
        return d[d.down].res.value_counts()

    def write_crema_note(self, x):
        try:
            return self.notes.index(x)
        except:
            return -1
