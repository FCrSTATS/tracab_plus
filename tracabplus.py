

import sys
from helpers import *
import time

# 984517



def main():

    tic = time.clock()

    # set up the file names ready for parsing
    tracking_file, tracking_meta_file, f24_file, f7_file = setup(sys.argv)
    tdat, meta_data, edat, game_data = parse_all_raw(tracking_file, tracking_meta_file, f24_file, f7_file)

    tdat = augment_tracking(tdat, meta_data, game_data, verbose = True)


    tdat = tdat.sort_values(by=['frameID'])
    print(tdat.head(200))
    print(tdat.tail(200))

    toc = time.clock()
    print(toc - tic)

if __name__ == '__main__':
    main()

# tracab_file = sys.argv[1]
# meta_file = sys.argv[2]
# f7_file = sys.argv[3]
