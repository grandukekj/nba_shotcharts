import nba_player_stat as nps
import plot_shotchart as ps

james_harden = nps.NBA_player_stat('james harden', 2019)
jh_RS_shot_df, jh_PO_shot_df = james_harden.shot_chart_to_pandas()
search_shot_fig = ps.plot_shotchart(jh_RS_shot_df, month=3, HW='home')
search_shot_fig.savefig('../shot_test.png')
