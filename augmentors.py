import pandas as pd
import numpy as np

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
        trackingdata['dist_to_ball'] = trackingdata[['x', 'y']].sub(np.array( trackingdata[['ball_x', 'ball_y']] )).pow(2).sum(1).pow(0.5)
        trackingdata.dist_to_ball = trackingdata.dist_to_ball.round(0).astype(int)
        return(trackingdata)
    else:
        print("x||----------------")
        print("Ball x and y coordinates missing - 'add_distance_to_ball' function failed")
        print("Use 'add_ball_xy' to add the missing coordinates")
        print("----------------||x")


def add_distance_to_goals(trackingdata, x = 5250):
    trackingdata['dist_to_goal1'] = trackingdata[['x', 'y']].sub(np.array( [-x, 0] )).pow(2).sum(1).pow(0.5)
    trackingdata['dist_to_goal2'] = trackingdata[['x', 'y']].sub(np.array( [x, 0] )).pow(2).sum(1).pow(0.5)
    trackingdata.dist_to_goal1 = trackingdata.dist_to_goal1.round(0).astype(int)
    trackingdata.dist_to_goal2 = trackingdata.dist_to_goal2.round(0).astype(int)
    return(trackingdata)


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


def add_attacking_direction(trackingdata, metadata):
    '''
    Attacking direction of 1 means the team is defending the goal -x and
    attacking the goal +x. An attacking direction of -1 means the team is
    defending the goal +x and attacking the goal -x.
    '''
    period1_start_frame = trackingdata[trackingdata['frameID'] == metadata['period1_start']].reset_index(drop=True)
    avg_starting_x_team1 = period1_start_frame[period1_start_frame['team'] == 1]['x'].mean()
    avg_starting_x_team0 = period1_start_frame[period1_start_frame['team'] == 0]['x'].mean()

    ## lists of attacking direction
    periods_list = []
    direction_list = []

    if avg_starting_x_team0 < avg_starting_x_team1:
        for value in [1,1,1,2,2,2]:
            periods_list.append(value)
        for value in [1,-1,1,-1,1,-1]:
            direction_list.append(value)
    else:
        for value in [1,1,1,2,2,2]:
            periods_list.append(value)
        for value in [-1,1,-1,1,-1,1]:
            direction_list.append(value)

    attacking_direction_ref = pd.DataFrame(
    {'period_id': periods_list,
    'att_dir': direction_list,
    'team': [0,1,10,0,1,10]})

    trackingdata = pd.merge(trackingdata, attacking_direction_ref, on = ["team", "period_id"])

    return(trackingdata)

def add_player_id(game_data, tracking_data):
    playerDB_ = game_data[['jersey_no','player_id', 'team', 'player_name']]

    ballDB = pd.Series(['999.0', '000000', '10.0', 'ball'], index=['jersey_no','player_id', 'team', 'player_name'])
    playerDB_ = playerDB_.append(ballDB, ignore_index=True)

    playerDB_['jersey_no'] = playerDB_['jersey_no'].transform(float)
    playerDB_['team'] = playerDB_['team'].transform(float)

    tracking_data = tracking_data.merge(playerDB_, on = ['jersey_no', 'team'])

    return(tracking_data)
#
#
# def check_in_each_half(trackingdata):
#     summary = trackingdata.groupby(['frameID', 'team'])['x'].apply(lambda x: (x>0).sum()).reset_index(name='no_in_plus_half')
#     print(summary.head())
#
#
#
def check_def_att_half(x, att_dir, team, ball_owning_team):
    '''
    0 = defensive half
    1 = attacking half
    '''
    if team == 10:
        if ball_owning_team == "A":
            att_dir = att_dir * -1

    if att_dir == 1:
        if x < 0:
            return(0)
        else:
            return(1)
    else:
        if x > 0:
            return(0)
        else:
            return(1)


def check_in_each_half(trackingdata):
    trackingdata['att_half'] = [check_def_att_half(a,b,c,d) for a,b,c,d in zip(trackingdata['x'],
                                                                               trackingdata['att_dir'],
                                                                               trackingdata['team'],
                                                                               trackingdata['ball_owning_team'])]
    return(trackingdata)


def check_which_third(x, att_dir, team, ball_owning_team, max_x):
    '''
    1 = att_def_third
    2 = att_mid_third
    3 = att_final_third
    -1 = def_def_third
    -2 = def_mid_third
    -3 = def_final_third
    '''
    value_of_third = (max_x) / 3
    out_of_bounds = 300
    end_zones = [ -out_of_bounds - (max_x/2), (max_x/2) + out_of_bounds ]
    thirds = [ - value_of_third/2, value_of_third/2]

    if team == 10:
        if ball_owning_team == "A":
            att_dir = att_dir * -1
            in_possession = True
        else:
            in_possession = True
    elif team == 0:
        if ball_owning_team == "H":
            in_possession = True
        else:
            in_possession = False
    elif team == 1:
        if ball_owning_team == "A":
            in_possession = True
        else:
            in_possession = False

    if in_possession:
        if att_dir == 1:
            if end_zones[0] <= x <= thirds[0]:
                return(1)
            elif thirds[0] <= x <= thirds[1]:
                return(2)
            else:
                return(3)
        else:
            if end_zones[0] <= x <= thirds[0]:
                return(3)
            elif thirds[0] <= x <= thirds[1]:
                return(2)
            else:
                return(1)
    else:
        if att_dir == 1:
            if end_zones[0] <= x <= thirds[0]:
                return(4)
            elif thirds[0] <= x <= thirds[1]:
                return(5)
            else:
                return(6)
        else:
            if end_zones[0] <= x <= thirds[0]:
                return(6)
            elif thirds[0] <= x <= thirds[1]:
                return(5)
            else:
                return(4)


def check_in_each_third(trackingdata, meta_data):
    max_x = int(meta_data['pitch_x']) * 100
    trackingdata['third'] = [check_which_third(a,b,c,d,max_x) for a,b,c,d in zip(trackingdata['x'],
                                                                               trackingdata['att_dir'],
                                                                               trackingdata['team'],
                                                                               trackingdata['ball_owning_team'])]
    return(trackingdata)


def create_reduced_name(playername):
    if len(playername.split(' ')) == 1:
        return(playername)
    else:
        return(playername.split(" ")[0][0] + ". " + playername.split(" ")[-1])

def create_all_reduced_name(trackingdata):
    trackingdata['player_name_reduced'] = [create_reduced_name(f) for f in trackingdata['player_name']]
    return(trackingdata)

        # box_edge = (int(meta_data['pitch_x']) * 50) - 1650 #edge of box
        # box_width = 2016
