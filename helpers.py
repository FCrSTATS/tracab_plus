# import libaries
from glob import *
from parsing_functions import *
from augmentors import *

# functions
def setup(cmdline_args, verbose = True):
    '''
    Take the matchID added in the command line and create all needed file paths
    The verbose argument allows for progress to be tracking via print()'s
    '''

    if len(cmdline_args) == 1:
        print("|||||  No matchID selected, rerun using: 'python3 tracabplus.py <YOUR-MATCHID>'")
        quit()
    else:
        if cmdline_args[1] in [f.replace(".dat", "").replace("data/", "") for f in glob('data/*.dat')]:
            if verbose:
                print("||||| setup:      ", str(cmdline_args[1]), " found and ready")
            return(['data/' + cmdline_args[1] + '.dat',
                    'data/' + cmdline_args[1] + '_metadata.xml',
                    'data/' + cmdline_args[1] + '_f24.xml',
                    'data/' + cmdline_args[1] + '_f7.xml'])
        else:
            print("|||||  No match found with matchID ", str(cmdline_args[1]))
            quit()


def parse_all_raw(tracking_file, tracking_meta_file, f24_file, f7_file, verbose = True):
    '''
    Take all raw data and parse to the most basic format with no augmentation.
    The verbose argument allows for progress to be tracking via print()'s
    '''

    if verbose:
        print("||||| parsing:     tracking metadata")
    meta_data = parse_tracking_metadata(tracking_meta_file)

    if verbose:
        print("||||| parsing:     tracking data")
    tdat = parse_tracab(tracking_file, meta_data)

    if verbose:
        print("||||| parsing:     events data")
    edat = parse_f24(f24_file)

    if verbose:
        print("||||| parsing:     gamedata")
    game_data = parse_f7(f7_file)

    if verbose:
        print("||||| parsing:     successfully parse all raw data")

    return([tdat, meta_data, edat, game_data])


def augment_tracking(tdat, meta_data, game_data, verbose = True):
    '''
    '''

    ## AUGMENT DATA
    if verbose:
        print("||||| augmenting:  adding team in possession")
    tdat = add_team_in_possession(tdat)

    if verbose:
        print("||||| augmenting:  adding ball xy")
    tdat = add_ball_xy(tdat)

    if verbose:
        print("||||| augmenting:  adding distance to the ball")
    tdat = add_distance_to_ball(tdat)

    if verbose:
        print("||||| augmenting:  adding distance to the goals")
    tdat = add_distance_to_goals(tdat)

    if verbose:
        print("||||| augmenting:  adding periods")
    tdat['period_id'] = [period_id_calc(f, meta_data) for f in tdat['frameID']]

    if verbose:
        print("||||| augmenting:  adding attacking direction")
    tdat = add_attacking_direction(tdat, meta_data)

    if verbose:
        print("||||| augmenting:  adding player ids")
    tdat = add_player_id(game_data, tdat)

    if verbose:
        print("||||| augmenting:  adding which half")
    tdat = check_in_each_half(tdat)

    if verbose:
        print("||||| augmenting:  adding which third")
    tdat = check_in_each_third(tdat, meta_data)

    if verbose:
        print("||||| augmenting:  create reduced player name")
    tdat = create_all_reduced_name(tdat)










    # if verbose:
    #     print("||||| augmenting:  adding periods")
    #     tdat['period_id'] = [period_id_calc(f, meta_data) for f in tdat['frameID']]
    #

    return(tdat)
    #
    #
    #

    # print(".... adding distance to the ball")
    # tdat = add_distance_to_ball(tdat)
    # print(".... adding distance to the goals")
    # tdat = add_distance_to_goals(tdat)
    # print(".... adding periods")
    # tdat['period_id'] = [period_id_calc(f, game_meta) for f in tdat['frameID']]
    # print(".... adding attacking direction")
    # tdat = add_attacking_direction(tdat, game_meta)
    # print(".... adding player ids")
    # tdat = add_player_id(f7_file, tdat)
