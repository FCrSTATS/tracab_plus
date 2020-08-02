
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET


def parse_f24(file_name):

    # parse the xml and convert to a tree and root
    tree = ET.parse(file_name)
    root = tree.getroot()

    ## get the main game info from the single 'Game' node
    gameinfo = root.findall('Game')
    gameinfo = gameinfo[0]
    game_id = gameinfo.get('id')
    home_team_id = gameinfo.get('home_team_id')
    home_team_name = gameinfo.get('home_team_name')
    away_team_id = gameinfo.get('away_team_id')
    away_team_name = gameinfo.get('away_team_name')
    competition_id = gameinfo.get('competition_id')
    competition_name = gameinfo.get('competition_name')
    season_id = gameinfo.get('season_id')

    Edata_columns = ['id',
             'event_id',
             'type_id',
             'period_id',
             'min',
             'sec',
             'outcome',
             'player_id',
             'team_id',
             'x',
             'y',
             'sequence_id',
             'possession_id',
            ]

    Q_ids = []
    Q_values = []
    Edata = []

    # loop through each ball node and grab the information
    for i in root.iter('Event'):

        # get the info from the ball node main chunk
        id_ = int(i.get('id'))
        event_id = i.get('event_id')
        type_id = i.get('type_id')
        period_id = int(i.get('period_id'))
        outcome = int(i.get('outcome'))
        min_ = int(i.get('min'))
        sec = int(i.get('sec'))
        player_id = i.get('player_id')
        team_id = i.get('team_id')
        x = i.get('x')
        y = i.get('y')
        possession_id = i.get('possession_id')
        sequence_id = i.get('sequence_id')

        Edata_values = [id_, event_id, type_id, period_id, min_, sec, outcome, player_id, team_id,
                        x,y, sequence_id, possession_id]

        # find all of the Q information for that file
        Qs = i.findall("./Q")

        # create some empty lists to append the results to
        qualifier_id = []
        Q_value = []

        # loop through all of the Qs and grab the info
        for child in Qs:
            qualifier_id.append(child.get('qualifier_id'))
            Q_value__ = child.get('value')
            if Q_value__ == None:
                Q_value.append(1)
            else:
                Q_value.append(Q_value__)

        Q_ids.append(qualifier_id)
        Q_values.append(Q_value)
        Edata.append(Edata_values)

    #Stack all ball Data
    df = pd.DataFrame(np.vstack(Edata), columns = Edata_columns)


    unique_Q_ids = np.unique(np.concatenate(Q_ids))

    #create an array for fast assignments
    Qarray = np.zeros((df.shape[0] ,len(unique_Q_ids)))
    Qarray = Qarray.astype('O')
    Qarray[:] = np.nan

    #dict to relate Q_ids to array indices
    keydict = dict(zip(unique_Q_ids, range(len(unique_Q_ids))))

    #iter through all Q_ids, Q_values, assign values to appropriate indices
    for idx, (i, v) in enumerate(zip(Q_ids, Q_values)):
        Qarray[idx, [keydict.get(q) for q in Q_ids[idx]]] = Q_values[idx]

    #df from array
    Qdf = pd.DataFrame(Qarray, columns = unique_Q_ids, index = df.index)

    #combine
    game_df = pd.concat([df, Qdf], axis = 1)

    #assign game values
    game_df['competition_id'] = competition_id
    game_df['game_id'] = game_id
    game_df['home_team_id'] = home_team_id
    game_df['home_team_name'] = home_team_name
    game_df['away_team_id'] = away_team_id
    game_df['away_team_name'] = away_team_name
    game_df['competition_id'] = competition_id
    game_df['competition_name'] = competition_name
    game_df['season_id'] = season_id
    game_df['competition_id'] = competition_id

    game_df[['id','period_id','min','sec','outcome']] = \
                game_df[['id','period_id','min','sec','outcome']].astype('int')

    game_df["x"] = pd.to_numeric(game_df["x"])
    game_df["y"] = pd.to_numeric(game_df["y"])

    # write to csv
    game_df = game_df.fillna(0)
    return(game_df)


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
                   meta_data,
                   remove_officials = True):


    # OPEN THE FILE AND READ TO 'CONTENT' OBJECT
    with open(tracking_filename) as fn:
        content = fn.readlines()

    tdat_raw = [x.strip() for x in content]

    # TRIM FRAMES OUTSIDE OF THE MATCH
    # create the
    frame_offset = meta_data['period1_start'] - int(tdat_raw[0].split(":",2)[0])

    period1_raw = tdat_raw[frame_offset : (meta_data['period1_end'] - meta_data['period1_start']) + frame_offset]
    period2_raw = tdat_raw[(meta_data['period2_start'] - meta_data['period1_start']) + frame_offset : (meta_data['period2_end'] - meta_data['period1_start']) + frame_offset]
    tdat_raw_trimmed = period1_raw + period2_raw

    if meta_data['period3_start'] != 0:
        period3_raw = tdat_raw[(meta_data['period3_start'] - meta_data['period1_start']) + frame_offset : (meta_data['period3_end'] - meta_data['period1_start']) + frame_offset]
        period3_raw = tdat_raw[(meta_data['period4_start'] - meta_data['period1_start']) + frame_offset : (meta_data['period4_end'] - meta_data['period1_start']) + frame_offset]
        tdat_raw_trimmed = tdat_raw_trimmed + period3_raw
        tdat_raw_trimmed = tdat_raw_trimmed + period4_raw

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

    for f in tdat_raw_trimmed:

        string_items = f.split(":",2)

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

        for hraw in humans_raw:

            human_pieces = hraw.split(",")

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
        # tdat = tdat[tdat['team'] != 4]
        # tdat = tdat[tdat['team'] != -1]
        tdat = tdat[~tdat.team.isin([-1,4])]

    return(tdat.reset_index(drop=True))

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
