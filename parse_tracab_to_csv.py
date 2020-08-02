
import pandas as pd
import numpy as np
import sys
import xml.etree.ElementTree as ET

tracab_file = sys.argv[1]
meta_file = sys.argv[2]
f7_file = sys.argv[3]

def parse_f7(file_name):

    # parse the xml and convert to a tree and root
    tree = ET.parse(file_name)
    root = tree.getroot()

    match_id = int(root.find('SoccerDocument').get('uID')[1:])

    # ## get the main game info from the single 'Game' node
    gameinfo = root.findall('SoccerDocument')
    gameinfo = gameinfo[0]
    # # gameinfo.get('Country')
    # gameinfo = gameinfo.iter('MatchData')
    # gameinfo = gameinfo[0]



    # gameinfo.iter('MatchInfo')
    # root.iter('MatchData').iter('MatchInfo').get('Period')

    formation_place = []
    player_id = []
    position = []
    jersey_no = []
    status = []

    for neighbor in gameinfo.iter('MatchPlayer'):
        formation_place.append(neighbor.get('Formation_Place'))
        player_id.append(neighbor.get('PlayerRef'))
        position.append(neighbor.get('Position'))
        jersey_no.append(neighbor.get('ShirtNumber'))
        status.append(neighbor.get('Status'))


    players1 = pd.DataFrame(
        {'formation_place': formation_place,
         'player_id': player_id,
         'position': position,
         'jersey_no': jersey_no,
         'status': status})


    p_id = []
    first_name = []
    last_name = []

    for neighbor in gameinfo.iter('Player'):
        p_id.append(neighbor.get('uID'))
        first_name.append(neighbor.find('PersonName').find('First').text)
        last_name.append(neighbor.find('PersonName').find('Last').text)


    players2 = pd.DataFrame(
        {'first_name': first_name,
         'player_id': p_id,
         'last_name': last_name})


    players1['player_id'] = players1['player_id'].str[1:]
    players2['player_id'] = players2['player_id'].str[1:]

    playersDB = players1.merge(players2, on='player_id', how='inner')
    playersDB["player_name"] = playersDB["first_name"].map(str) + " " + playersDB["last_name"]


    minute = []
    period_id = []
    player_off = []
    player_on = []


    for neighbor in gameinfo.iter('Substitution'):
        minute.append(neighbor.get('Time'))
        period_id.append(neighbor.get('Period'))
        player_off.append(neighbor.get('SubOff'))
        player_on.append(neighbor.get('SubOn'))


    subs = pd.DataFrame(
        {'minute': minute,
         'period_id': period_id,
         'player_off': player_off,
         'player_on': player_on
        })


    subs['player_off'] = subs['player_off'].str[1:]
    subs['player_on'] = subs['player_on'].str[1:]

    playersDB['start_min'] = 0
    playersDB['end_min'] = 0

    match_length = 90
    for neighbor in gameinfo.iter('Stat'):
        if neighbor.get('Type') == "match_time":
            match_length = int(neighbor.text)

    for i in range(0,len(playersDB)):

        player_2_test = playersDB.iloc[i]

        if player_2_test['status'] == "Start":

            if player_2_test['player_id'] in subs.player_off.get_values():
                playersDB.at[i, 'end_min'] = subs.loc[subs['player_off'] == player_2_test['player_id']]['minute'].get_values()[0]

            else:
                playersDB.at[i, 'end_min'] = match_length

        if player_2_test['status'] == "Sub":

            if player_2_test['player_id'] in subs.player_on.get_values():
                playersDB.at[i, 'start_min'] = subs.loc[subs['player_on'] == player_2_test['player_id']]['minute'].get_values()[0]
                playersDB.at[i, 'end_min'] = match_length
            else:
                playersDB.at[i, 'end_min'] = player_2_test['end_min']

            if player_2_test['player_id'] in subs.player_off.get_values():
                playersDB.at[i, 'end_min'] = subs.loc[subs['player_off'] == player_2_test['player_id']]['minute'].get_values()[0]

    playersDB['mins_played'] = playersDB["end_min"] - playersDB["start_min"]

    playersDB['match_id'] = match_id

    teams = []
    for team in gameinfo.findall('Team'):
        teams.append(team.get('uID')[1:])

    playersDB['team_id'] = ""
    playersDB['team'] = ""


    for i in range(0,36):
        if i <= 17:
            playersDB.at[i, 'team_id'] = teams[0]
            playersDB.at[i, 'team'] = 1
        else:
            playersDB.at[i, 'team_id'] = teams[1]
            playersDB.at[i, 'team'] = 0

    return(playersDB)


def parse_tracking_metadata(filename):

    tree = ET.parse(filename)
    root = tree.getroot()

    period_startframe = []
    period_endframe = []

    gamexml = root.findall('match')[0]
    # gamexml.findall('period').get('iStartFrame')

    info_raw = []

    for i in gamexml.iter('period'):
            # get the info from the ball node main chunk
    #         print(int(i.get('iId')))
            info_raw.append( i.get('iStartFrame') )
            info_raw.append( i.get('iEndFrame') )

    # # Create empty dict Capitals
    game_info = dict()

    # # Fill it with some values
    game_info['period1_start'] = int(info_raw[0])
    game_info['period1_end'] = int(info_raw[1])
    game_info['period2_start'] = int(info_raw[2])
    game_info['period2_end'] = int(info_raw[3])
    game_info['period3_start'] = int(info_raw[4])
    game_info['period3_end'] = int(info_raw[5])
    game_info['period4_start'] = int(info_raw[6])
    game_info['period4_end'] = int(info_raw[7])


    for detail in root.iter('match'):
        game_info['pitch_x'] = int(float(detail.get('fPitchXSizeMeters')))
        game_info['pitch_y'] = int(float(detail.get('fPitchYSizeMeters')))

    return(game_info)

def parse_tracab(tracking_filename,
                   metadata_filename,
                   game_info,
                   remove_officials = True,
                   trim_dead_time = True):

    # remove_officials = True
    # trim_dead_time = True

    # parsing tracking data

    with open(tracking_filename) as fn:
        content = fn.readlines()

    tdat_raw = [x.strip() for x in content]

    frameID = []
    team = []
    target_id = []
    jersey_no = []
    x = []
    y = []
    z = []
    speed = []
    ball_owning_team = []
    ball_status = []
    ball_contact = []

    for f in range(0,len(tdat_raw)):

        string_items = tdat_raw[f].split(":",2)

        ## frameID
        frameID_temp = int(string_items[0])

        # ball
        ball_raw = string_items[2].split(";")[0]
        ball_raw = ball_raw.split(",")

        frameID.append(frameID_temp)
        team.append(10)
        target_id.append(100)
        jersey_no.append(999)
        x.append(ball_raw[0])
        y.append(ball_raw[1])
        z.append(ball_raw[2])
        speed.append(ball_raw[3])
        ball_owning_team.append(ball_raw[4])
        ball_status.append(ball_raw[5])

        if len(ball_raw) == 7:
            ball_contact.append(ball_raw[6])
        else:
            ball_contact.append("NA")

        ## humans
        humans_raw = string_items[1].split(";")
        humans_raw = list(filter(None, humans_raw)) # fastest

        for i in range(0,len(humans_raw)):

            human_pieces = humans_raw[i].split(",")

            frameID.append(frameID_temp)
            team.append(human_pieces[0])
            target_id.append(human_pieces[1])
            jersey_no.append(human_pieces[2])
            x.append(human_pieces[3])
            y.append(human_pieces[4])
            speed.append(human_pieces[5])
            ball_contact.append("NA")
            z.append(0)
            ball_owning_team.append(ball_raw[4])
            ball_status.append(ball_raw[5])

    tdat = pd.DataFrame(
    {'frameID': frameID,
     'team': team,
     'target_id': target_id,
     'jersey_no': jersey_no,
     'x': x,
     'y': y,
     'z': z,
     'speed': speed,
     'ball_owning_team': ball_owning_team,
     'ball_status': ball_status,
     'ball_contact': ball_contact})

    tdat["frameID"] = pd.to_numeric(tdat["frameID"])
    tdat["team"] = pd.to_numeric(tdat["team"])
    tdat["target_id"] = pd.to_numeric(tdat["target_id"])
    tdat["jersey_no"] = pd.to_numeric(tdat["jersey_no"])
    tdat["x"] = pd.to_numeric(tdat["x"])
    tdat["y"] = pd.to_numeric(tdat["y"])
    tdat["z"] = pd.to_numeric(tdat["z"])

    if remove_officials == True:
        tdat = tdat[tdat['team'] != 4]
        tdat = tdat[tdat['team'] != -1]

    if trim_dead_time == True:

        tree = ET.parse(metadata_filename)
        root = tree.getroot()

        period_startframe = []
        period_endframe = []

        gamexml = root.findall('match')[0]
        # gamexml.findall('period').get('iStartFrame')

        info_raw = []

        for i in gamexml.iter('period'):
                # get the info from the ball node main chunk
        #         print(int(i.get('iId')))
                info_raw.append( i.get('iStartFrame') )
                info_raw.append( i.get('iEndFrame') )

    #     return(game_info)

        frames_to_include = []

        frames_to_include.append(list(range(game_info['period1_start'], game_info['period1_end']+1)))
        frames_to_include.append(list(range(game_info['period2_start'], game_info['period2_end']+1)))


        if game_info['period3_start'] != 0:
            frames_to_include.append(list(range(game_info['period3_start'], game_info['period3_end']+1)))
            frames_to_include.append(list(range(game_info['period4_start'], game_info['period4_end']+1)))

        flat_list = []

        for sublist in frames_to_include:
            for item in sublist:
                flat_list.append(item)

        tdat = tdat[tdat['frameID'].isin(flat_list)]

        tdat = tdat.reset_index(drop=True)

    return(tdat)

def add_team_in_possession(trackingdata):

    trackingdata['team_in_possession'] = [(x == 1 and y == "H") or
                                     (x == 0 and y == "A")
                                     for x,y in zip(trackingdata.team,
                                     trackingdata.ball_owning_team )]
    return( trackingdata )

def add_ball_xy(trackingdata):

    ball_df = trackingdata[trackingdata['team'] == 10].reset_index(drop=True)[['frameID', 'x', 'y']]
    ball_df.columns = ['frameID', 'ball_x', 'ball_y']

    trackingdata = trackingdata.merge(ball_df, on = "frameID")

    return(trackingdata)

def add_distance_to_ball(trackingdata):

    if 'ball_x' in trackingdata.columns:
        trackingdata['distance_to_ball'] = trackingdata[['x', 'y']].sub(np.array( trackingdata[['ball_x', 'ball_y']] )).pow(2).sum(1).pow(0.5)
        trackingdata.distance_to_ball = trackingdata.distance_to_ball.round(2)
        return(trackingdata)

    else:
        print("x||----------------")
        print("Ball x and y coordinates missing - 'add_distance_to_ball' function failed")
        print("Use 'add_ball_xy' to add the missing coordinates")
        print("----------------||x")

def add_distance_to_goals(trackingdata, x = 5250):

    trackingdata['distance_to_goal1'] = trackingdata[['x', 'y']].sub(np.array( [-x, 0] )).pow(2).sum(1).pow(0.5)
    trackingdata['distance_to_goal2'] = trackingdata[['x', 'y']].sub(np.array( [x, 0] )).pow(2).sum(1).pow(0.5)

    # trackingdata.distance_to_goal1 = trackingdata.distance_to_goal1.round(2)
    # trackingdata.distance_to_goal2 = trackingdata.distance_to_goal2.round(2)

    return(trackingdata)

def add_GKs(list_of_ids, list_of_gks):
    res = []
    for i in list_of_ids:
        if i in list_of_gks:
            res.append(1)
        else:
            res.append(0)
    return(res)


def calc_distance(x,y):
    return np.sqrt(np.sum((x-y)**2))


def add_attacking_direction(trackingdata, metadata):

    period1_start_frame = trackingdata[trackingdata['frameID'] == metadata['period1_start']].reset_index(drop=True)
    avg_starting_x_team1 = period1_start_frame[period1_start_frame['team'] == 1]['x'].mean()
    avg_starting_x_team0 = period1_start_frame[period1_start_frame['team'] == 0]['x'].mean()

    ## lists of attacking direction
    periods_list = []
    direction_list = []

    if avg_starting_x_team0 < avg_starting_x_team1:
        periods_list.append(1)
        periods_list.append(1)
        periods_list.append(1)
        periods_list.append(2)
        periods_list.append(2)
        periods_list.append(2)
        direction_list.append(1)
        direction_list.append(-1)
        direction_list.append(0)
        direction_list.append(-1)
        direction_list.append(1)
        direction_list.append(0)

    else:
        periods_list.append(1)
        periods_list.append(1)
        periods_list.append(1)
        periods_list.append(2)
        periods_list.append(2)
        periods_list.append(2)
        direction_list.append(-1)
        direction_list.append(1)
        direction_list.append(0)
        direction_list.append(1)
        direction_list.append(-1)
        direction_list.append(0)

    attacking_direction_ref = pd.DataFrame(
    {'period_id': periods_list,
    'attacking_direction': direction_list,
    'team': [0,1,10,0,1,10]})

    trackingdata = pd.merge(trackingdata, attacking_direction_ref, on = ["team", "period_id"])

    return(trackingdata)

def add_player_id(f7_filename, tracking_data):

    playerDB_ = parse_f7(f7_filename)[['jersey_no','player_id', 'team', 'player_name']]

    ballDB = pd.Series(['999.0', '000000', '10.0', 'ball'], index=['jersey_no','player_id', 'team', 'player_name'])
    playerDB_ = playerDB_.append(ballDB, ignore_index=True)

    playerDB_['jersey_no'] = playerDB_['jersey_no'].transform(float)
    playerDB_['team'] = playerDB_['team'].transform(float)

    tracking_data = tracking_data.merge(playerDB_, on = ['jersey_no', 'team'])

    return(tracking_data)

def period_id_calc(frameID, tracking_meta):

    if (frameID >= int(tracking_meta['period1_start']) and frameID <= int(tracking_meta['period1_end'])):
        return(1)
    elif (frameID >= int(tracking_meta['period2_start']) and frameID <= int(tracking_meta['period2_end'])):
        return(2)
    elif (frameID >= int(tracking_meta['period3_start']) and frameID <= int(tracking_meta['period3_end'])):
        return(3)
    elif (frameID >= int(tracking_meta['period4_start']) and frameID <= int(tracking_meta['period4_end'])):
        return(4)
    else:
        return(5)


# def add_keepers(tracking_data, tracking_data):
    # playerDB_ = parse_f7(f7_filename)[['jersey_no','player_id', 'team', 'player_name']]
    # list_of_gks = list(playerDB_[playerDB_['position'] == "Goalkeeper"]['player_id'])

def calc_bounding_boxes(tracking_data):
    res = []
    for frame__ in list(set(tracking_data['frameID'])):

        frame_seg = tracking_data[tracking_data['frameID'] == frame__].reset_index(drop=True)

        for team in [0,1]:

            team_seg = frame_seg[frame_seg['team'] == team].reset_index(drop=True)

            x_list = list(team_seg['x'])
            y_list = list(team_seg['y'])

            if team_seg.iloc[0]['attacking_direction'] == 1:
                x_list.remove(min(x_list))
            else:
                x_list.remove(max(x_list))



            output = dict({
                "frameID": frame__,
                "team": team,
                "min_bb_x": min(x_list),
                "min_bb_y": min(y_list),
                "max_bb_x": max(x_list),
                "max_bb_y": max(y_list)})

            res.append(output)

    df = pd.DataFrame(res)
    return(df)


def main():

    if '.dat' not in tracab_file:
        print("** Warning: Tracab file not a .dat data type! " + str(tracab_file) + " supplied")

    if '.xml' not in meta_file:
        print("** Warning: Meta file not a .xml data type! " + str(meta_file) + " supplied")

    if tracab_file.replace(".dat", "") not in meta_file:
        print("** Warning: Files from two different games supplied")

    # load and parse initial data
    game_meta = parse_tracking_metadata(meta_file)

    print(".... parsing tracab raw")
    tdat = parse_tracab(tracab_file, meta_file, game_meta)

    ## AUGMENT DATA
    print(".... adding team in possession")
    tdat = add_team_in_possession(tdat)
    print(".... adding ball xy")
    tdat = add_ball_xy(tdat)
    print(".... adding distance to the ball")
    tdat = add_distance_to_ball(tdat)
    print(".... adding distance to the goals")
    tdat = add_distance_to_goals(tdat)
    print(".... adding periods")
    tdat['period_id'] = [period_id_calc(f, game_meta) for f in tdat['frameID']]
    print(".... adding attacking direction")
    tdat = add_attacking_direction(tdat, game_meta)
    print(".... adding player ids")
    tdat = add_player_id(f7_file, tdat)
    print(".... calc bounding boxes")
    game_data = parse_f7(f7_file)
    # list_of_gks = list(game_data[game_data['position'] == "Goalkeeper"]['player_id'])
    list_of_gks = list(game_data[game_data['position'] == "Goalkeeper"]['player_id'])
    ids = tdat['player_id']
    tdat['is_GK'] = add_GKs(ids, list_of_gks)
    x_bb = tdat[(tdat['is_GK'] == 0) & (tdat['ball_status'] == "Alive")].groupby(['frameID', 'team']).agg({'x': ['min', 'max']}).reset_index()
    x_bb.columns = ['frameID', 'team', 'x_bb_min', 'x_bb_max']
    y_bb = tdat[(tdat['is_GK'] == 0) & (tdat['ball_status'] == "Alive")].groupby(['frameID', 'team']).agg({'y': ['min', 'max']}).reset_index()
    y_bb.columns = ['frameID', 'team', 'y_bb_min', 'y_bb_max']
    print(".... merging bounding boxes")
    bb_df = pd.merge(x_bb, y_bb, on = ['frameID', 'team'])
    tdat = tdat.merge(bb_df, on = ['frameID', 'team'])
        # tdat = tdat.merge(bb_data, on=['frameID', 'team'])

    # def min_that(series_of_values):
        # agg({'Age': ['mean', 'min', 'max']})

    # tracking_data.groupby('one')['two'].agg(mean_gap)






    # list_of_dfs = []
    #
    # chunk_size = int(tdat.shape[0] / 4)
    # for start in range(0, tdat.shape[0], chunk_size):
    #     df_subset = tdat.iloc[start:start + chunk_size]
    #     list_of_dfs.append(df_subset)
    #
    # for i in range(4):
    #     list_of_dfs[i].to_csv(tracab_file.replace(".dat", "") + "part" + str(i+1) + ".csv")
    #     list_of_dfs[i].to_parquet(tracab_file.replace(".dat", "") + "part" + str(i+1) + '.gzip',compression='gzip')
    #
    print(".... saving to file")
    tdat.to_parquet(tracab_file.replace(".dat", "")  + '.gzip',compression='gzip')
    print(".... PROCESS COMPLETE")
if __name__ == '__main__':
    main()
