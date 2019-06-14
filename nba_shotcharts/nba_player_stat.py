import datetime
import time

import bs4
import pandas as pd
import requests
from bs4 import BeautifulSoup


class NBA_player_stat(object):
    baseURL = 'https://www.basketball-reference.com'

    def __init__(self, playerName, year):
        self.playerName = playerName.title()
        self.year = str(year)

    def find_player_page(self):
        FirstLetter_LastName = self.playerName.split(" ")[1][0].lower()
        last_name_page = requests.get('https://www.basketball-reference.com/players/%s' % FirstLetter_LastName)
        LastName_soup = BeautifulSoup(last_name_page.content, 'lxml')
        for link in LastName_soup.find_all('strong'):
            for plink in link.find_all('a'):
                if plink.get_text() == self.playerName:
                    player_page = NBA_player_stat.baseURL + plink.get('href')[:-5] + '/gamelog/' + self.year
                    return player_page

    # def get_info(self):
    #     fullname
    #     position
    #     handedness
    #     height
    #     weight
    #     current_team
    #     birthdate
    #     age
    #     college
    #     draft_year
    #     drafted_by
    #     draft_pick
    #     nba_debut
    #     experience

    @staticmethod
    def str2sec(str_arg):
        # str_arg must be formatted in 'MM:SS' string format
        to_time = time.strptime(str_arg, '%M:%S')
        to_sec = datetime.timedelta(minutes=to_time.tm_min, seconds=to_time.tm_sec).total_seconds()
        return to_sec

    def stats_to_pandas(self):
        player_page = requests.get(self.find_player_page)
        player_soup = BeautifulSoup(player_page.content, 'lxml')
        table = player_soup.find('table', {'class': 'row_summable sortable stats_table'})
        gamelog_df = pd.read_html(str(table))[0]

        gamelog_df = gamelog_df.rename(columns={gamelog_df.columns[5]: 'HomeOrAway'})
        gamelog_df = gamelog_df.rename(columns={gamelog_df.columns[7]: 'ScoreDiff'})

        # extract data only on the days the player played
        player_data = gamelog_df[(gamelog_df.G != 'G') & (gamelog_df.G.notnull())].copy()

        player_data['WinorLose'] = [1 if wl == 'W' else 0 for wl in player_data['ScoreDiff'].str[:1]]
        player_data['ScoreDiff'] = player_data['ScoreDiff'].apply(lambda st: st[st.find("(") + 1:st.find(")")]).astype(
            int)

        int_list = ['Rk', 'G', 'GS', 'FG', 'FGA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK',
                    'TOV', 'PF', 'PTS', '+/-']
        flt_list = ['FG%', '3P%', 'FT%', 'GmSc']

        for col in player_data.columns:
            if col in int_list:
                player_data[col] = pd.to_numeric(player_data[col], downcast='integer')
            elif col in flt_list:
                player_data[col] = pd.to_numeric(player_data[col], downcast='float')

        player_data['Date'] = pd.to_datetime(player_data['Date'], format='%Y-%m-%d')
        player_data['Age'] = [int(age.split('-')[0]) + int(age.split('-')[1]) / 365.0 for age in player_data['Age']]
        player_data['HomeOrAway'] = [1 if where != '@' else 0 for where in player_data['HomeOrAway']]
        player_data['MP'] = pd.to_datetime(player_data['MP'], format='%M:%S').dt.time

        return player_data

    def shot_chart_to_pandas(self):
        global home_road, player_rs_shotchart_url
        player_page = self.find_player_page()
        player_shooting_page_url = player_page.split('/gamelog')[0] + '/shooting/' + self.year
        player_shooting_page = requests.get(player_shooting_page_url)
        player_shooting_soup = BeautifulSoup(player_shooting_page.content, 'html.parser')

        for i in player_shooting_soup.find_all('a'):
            if i.get_text() == 'Regular Season':
                player_rs_shotchart_url = self.baseURL + i.get('href')  # RS stands for Regular Season
            if 'Playoff' in i.get_text() and 'playoffs=1' in i.get('href'):
                player_po_shotchart_url = self.baseURL + i.get('href')

        player_rs_shotchart_df = pd.DataFrame(columns=['Date', 'player_Team', 'Against', 'Home_Road', 'Qtr',
                                                       "TimeLeft", 'Shot_Pts', 'make', 'top_coord', 'left_coord',
                                                       'Team_score', 'Opp_Score'])
        player_po_shotchart_df = player_rs_shotchart_df.copy()

        for player_shotchart_URL in [player_rs_shotchart_url, player_po_shotchart_url]:

            player_shotchart_page = requests.get(player_shotchart_URL)
            player_shotchart_soup = BeautifulSoup(player_shotchart_page.content, 'html.parser')

            for item in player_shotchart_soup.find_all(text=lambda text: isinstance(text, bs4.Comment)):
                if 'overthrow table_container' in item:
                    data = BeautifulSoup(item, "html.parser")
                    for i, shot in enumerate(data.find_all("div", {"class": "tooltip"})):

                        # shot info
                        gameInfo = shot.get('tip').split(',')  # gameInfo[0] = 'April 9' , gameInfo[1] = '2019'
                        ## game dates
                        gamedate = gameInfo[0] + gameInfo[1]
                        gamedate_object = datetime.datetime.strptime(gamedate, '%b %d %Y')
                        gamedate_val = gamedate_object.date()
                        ## the teams played and the quarter the shot was thrown
                        team_Qtr = gameInfo[2].split('<br>')
                        # team_Qtr[1] = '4th Qtr'
                        Qtr = int(''.join(filter(str.isdigit, team_Qtr[1])))
                        # team_Qtr[0] = 'HOU at OKC'
                        playerTeam = [x for x in team_Qtr[0].split(' ') if x.isupper() == 1][0]
                        against = [x for x in team_Qtr[0].split(' ') if x.isupper() == 1][1]
                        if 'vs' in team_Qtr[0]:
                            home_road = 'home'
                        elif 'at' in team_Qtr[0]:
                            home_road = 'road'
                        ### description of the shot taken
                        shot_description = gameInfo[3].split('<br>')
                        # shot_description[0] = '0:00 remaining'
                        shot_min = shot_description[0].strip().split(' ')[0].split(':')[0]
                        shot_sec = shot_description[0].strip().split(' ')[0].split(':')[1]
                        # shot_description[1] = 'Missed 3-pointer from 24 ft'
                        shot_pts = int(''.join(filter(str.isdigit, shot_description[1].split(' ')[1])))
                        # shot_description[2] = 'HOU trails 111-112'
                        team_score = int(shot_description[2].split(' ')[-1].split('-')[0])
                        opp_score = int(shot_description[2].split(' ')[-1].split('-')[1])

                        # shot loc
                        shotloc_text = shot.get('style').split(';')
                        top_coord = int(
                            ''.join(filter(str.isdigit, shotloc_text[0])))  # take only the int val for top coordinate
                        left_coord = int(
                            ''.join(filter(str.isdigit, shotloc_text[1])))  # take only the int val for left coordinate

                        # make or miss
                        make_or_miss = shot.get('class')[1]

                        # enter each shot into dataframe
                        if player_shotchart_URL == player_rs_shotchart_url:
                            player_rs_shotchart_df.loc[i] = [gamedate_val, playerTeam, against, home_road,
                                                             Qtr, datetime.time(0, int(shot_min), int(shot_sec)),
                                                             shot_pts, make_or_miss, top_coord, left_coord,
                                                             team_score, opp_score]

                        elif player_shotchart_URL == player_po_shotchart_url:
                            player_po_shotchart_df.loc[i] = [gamedate_val, playerTeam, against, home_road,
                                                             Qtr, datetime.time(0, int(shot_min), int(shot_sec)),
                                                             shot_pts, make_or_miss, top_coord, left_coord,
                                                             team_score, opp_score]

        return player_rs_shotchart_df, player_po_shotchart_df
