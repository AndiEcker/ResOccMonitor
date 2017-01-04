'''
Created on 13/02/2014

    public application constants

- V1.0    15-Mar-2014    first test version
- V1.1    19-Mar-2014    added cell tool tip for to display threshold value


@author: aecker
'''
APP_TITLE = 'Reservation Occupation Counter Monitor'
APP_VERSION = '1.1'

# data base refresh interval in ms
REFRESH_INTERVAL = 5000


PKEY_COL_CNT = 3

"""
NO LONGER NEEDED - because we only allow new rows to be inserted by extra calls

PKEY_VALUES = [
               ['BHC', 'BHH', 'HMC', 'PBC'],
               [str(yr) for yr in range(2014, 2020)],
               [str(wk + 1) for wk in range(53)]
              ]

# calculate next year/week value
def PKeyNextValue(pkey):
    pkeylist = list(pkey)
    nI = PKEY_VALUES[2].index(pkey[2])
    if nI == len(PKEY_VALUES[2]) - 1:       # if reached week 53 already
        pkeylist[2] = PKEY_VALUES[2][0]     # .. go to week 1 in next year 
        nI = PKEY_VALUES[1].index(pkey[1])
        if nI < len(PKEY_VALUES[1]) - 1:
            pkeylist[1] = PKEY_VALUES[1][nI+1]
    else:
        pkeylist[2] = PKEY_VALUES[2][nI+1]
    return tuple(pkeylist)

"""
