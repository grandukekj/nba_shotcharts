# from. nba_player_stat import nps
# from. plot_shotchart import ps
from nba_shotcharts.nba_player_stat import NBA_player_stat
from nba_shotcharts.plot_shotchart import plot_shotchart

james_harden = NBA_player_stat('james harden', 2019)
jh_RS_shot_df, jh_PO_shot_df = james_harden.shot_chart_to_pandas()
search_shot_fig = plot_shotchart(jh_RS_shot_df, month=3, HW='home')
search_shot_fig.savefig('../shot_test.png')
