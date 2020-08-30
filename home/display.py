def plot_dataframe(feature_df, lim=None):
    df_res = feature_df.copy()
    plt.plot(df_res[df_res.melody_note>=0].beat_time, df_res[df_res.melody_note>=0].melody_note, '.', label='melody', color='brown')
    plt.plot(df_res.beat_time, df_res.bass_note, '.', label='bass', color='purple')
    plt.plot(df_res.beat_time, df_res.harm_note, '.', label='harm', color='green')
    #plt.plot(df_res.beat_number, df_res.pitch_ocmi_min, '.-', color='green', alpha=0.3, label='_nolegend_')
    #plt.plot(df_res.beat_number, df_res.pitch_ocmi_max, '.-', color='green', alpha=0.3, label='_nolegend_')


    plt.vlines(df_res[df_res.beat_type=='d'].beat_time, ymin=-1, ymax=13, color='darkblue', alpha=0.4, label='downbeat')
    plt.vlines(df_res[df_res.beat_type=='u'].beat_time, ymin=-1, ymax=13, color='blue', alpha=0.2, label='upbeat')
    plt.vlines(df_res[df_res.beat_type=='b'].beat_time, ymin=-1, ymax=13, color='lightblue', alpha=0.3, label='beat')


    df_res['to'] = df_res.beat_time.shift(-1)
    df_res.fillna(df_res.beat_time.max()+0.001, inplace=True)
    from collections import defaultdict
    colors = defaultdict(lambda: 'gray')
    colors.update({'maj': 'orange', 'min': 'green', 'sus': 'yellow', 'aug': 'fuchsia', 'dim': 'darkorange'})

    for idx, row in df_res.iterrows():
        plt.axvspan(row.beat_time, row.to, color=colors[row.chord_type], alpha=0.1, lw=0)
        plt.xlabel('Beat number ')
        plt.ylabel('Semitonal distance from pitch0 ')
        if lim is not None:
            plt.xlim((0, lim))
    #plt.xticks(np.arange(min(df_res.beat_time), max(df_res.beat_time)+1, 1.0))

# plt.figure(figsize=(16, 6))
# plt.subplot('211')
# plot_dataframe(obj3.df, 60)
# plt.subplot('212')
# plot_dataframe(obj4.df, 60)
# plt.show()
