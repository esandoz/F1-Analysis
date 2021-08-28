"""Qualifying results overview
==============================

Plot the qualifying result with visualization the fastest times.
"""

import matplotlib.pyplot as plt
import pandas as pd
from timple.timedelta import strftimedelta
import fastf1
import fastf1.plotting
from fastf1.core import Laps

num_years_back = 4

fastf1.Cache.enable_cache('TestCache')  # replace with your cache directory
# we only want support for timedelta plotting in this example
fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme=None, misc_mpl_mods=False)

# each year has a different number of races to iterate over
listyear = [x for x in range(2003,2022)]
numraces = [16,18,19,18,17,18,17,19,19,20,19,19,19,19,20,21,21,17,9]
# get the last number of years (so 4 years back from 2021: 2021, 2020, 2019, 2018)
listyearnew = listyear[-num_years_back:]
data = {'Year':listyear, 'NumRaces':numraces}
year_ref = pd.DataFrame(data)
year_ref = year_ref.set_index('Year')

##############################################################################
# get all races in a season, some seasons have fewer than 

def getseasongap(yeartoanalyze, num_of_races_in_the_season):
    countiter = 0
    for i in range(num_of_races_in_the_season):
        
        try:
            quali = fastf1.get_session(yeartoanalyze, i+1, 'Q')
        except LookupError:
            print("ended on race # "+str(i+1))
            break
        laps = quali.load_laps()
        
        
        ##############################################################################
        # First, we need to get an array of all teams.
        
        teams = pd.unique(laps['Team'])
        teams = [x for x in teams if pd.isnull(x) == False]
    
        ##############################################################################
        # After that we'll get each teams fastest lap, create a new laps object
        # from these laps, sort them by lap time and have pandas reindex them to
        # number them nicely by starting position.
        
        list_fastest_laps = list()
        for tms in teams:
            tms_fastest_lap = laps.pick_team(tms).pick_fastest()
            list_fastest_laps.append(tms_fastest_lap)
        fastest_laps = Laps(list_fastest_laps).sort_values(by='LapTime').reset_index(drop=True)
        
        
        ##############################################################################
        # The plot is nicer to look at and more easily understandable if we just plot
        # the time differences. Therefore we subtract the fastest lap time from all
        # other lap times. I like to look at seconds, not full HH:MM:SS format since
        # there are a lot of insignificant digits
        
        pole_lap = fastest_laps.pick_fastest()
        fastest_laps['LapTimeDelta'] = fastest_laps['LapTime'] - pole_lap['LapTime']
        
        # fastest_laps is a dataframe, the column LapTimeDelta is filled with timedelta
        # objects, and to convert those to seconds the attribute .total_seconds must be
        # called. However, an element (timedelta.total_seconds()) attribute cannot be 
        # called by the dataframe column, so fastest_laps['LapTimeDelta'].total_seconds()
        # doesn't work, while fastest_laps['LapTimeDelta'][6].total_seconds() does work
        # To do this automatically create a function that calls the attribute, and use
        # the dataframe.apply() attribute to apply the function to the whole column
        def convert_to_seconds(LapDelta):
            return LapDelta.total_seconds()
        
        fastest_laps['LapTimeDeltaSec'] = fastest_laps['LapTimeDelta'].apply(convert_to_seconds)    
        
        
        ##############################################################################
        # Concatenate dataframe to track teams Lap Time Delta per race in a season
        selected_columns=fastest_laps[["Team","LapTimeDeltaSec"]]
        race_add = selected_columns.copy()
        race_add = race_add.set_index("Team")
        race_add = race_add.rename(columns={"LapTimeDeltaSec":str(i+1)})
        
        if countiter == 0:
            lap_delta_by_race = race_add.copy()
        else:
            lap_delta_by_race = pd.concat([lap_delta_by_race, race_add.copy()],axis=1)
        
        countiter = countiter+1    
        
    ##############################################################################
    # average the fastest lap deltas, get their standard deviation and then sort
    # by team performance. Round to thousandths of a second.        
    lap_delta_by_race['SeasonAverageDelta_'+str(yeartoanalyze)] = lap_delta_by_race.mean(axis=1)
    lap_delta_by_race['SeasonSTDDelta_'+str(yeartoanalyze)] = lap_delta_by_race.std(axis=1)
    season_delta_stats = pd.DataFrame(index=lap_delta_by_race.index)
    season_delta_stats = lap_delta_by_race[['SeasonAverageDelta_'+str(yeartoanalyze),'SeasonSTDDelta_'+str(yeartoanalyze)]].copy()
    
    return season_delta_stats

countyear=0

for yeartoanalyze in listyearnew:
    num_of_races_in_the_season = year_ref.loc[yeartoanalyze][0]
    
    append_year_stats = getseasongap(yeartoanalyze, num_of_races_in_the_season)
    as_list = append_year_stats.index.tolist()
    if 'Renault' in append_year_stats.index:    
        idx = as_list.index('Renault')
        as_list[idx] = 'Alpine F1 Team'
    if 'Sauber' in append_year_stats.index: 
        idy = as_list.index('Sauber')
        as_list[idy] = 'Alfa Romeo'
    if 'Force India' in append_year_stats.index: 
        idz = as_list.index('Force India')
        as_list[idz] = 'Aston Martin'
    if 'Racing Point' in append_year_stats.index: 
        ida = as_list.index('Racing Point')
        as_list[ida] = 'Aston Martin'
    if 'Toro Rosso' in append_year_stats.index: 
        ida = as_list.index('Toro Rosso')
        as_list[ida] = 'AlphaTauri'
    append_year_stats.index = as_list
    
    if countyear == 0:
        total_delta_stats = append_year_stats.copy()
    else:
        total_delta_stats = pd.concat([total_delta_stats, append_year_stats.copy()],axis=1)
    
    countyear = countyear+1
    

##############################################################################
# Finally, we'll create a list of team colors per lap to color our plot.
# Note depending on the season the team colors will return nothing and the 
# the plot will issue an error

team_colors = list()
for tms in total_delta_stats.index:
    color = fastf1.plotting.team_color(tms)
    if tms == 'Haas F1 Team':
        color = 'k'
    team_colors.append(color)

##############################################################################

def plotdelta_season(total_delta_stats, team_colors, listyearnew):
    fig, ax = plt.subplots()
    average_lap_delta = total_delta_stats[total_delta_stats.columns[::2]]
    std_lap_delta = total_delta_stats[total_delta_stats.columns[1::2]]
    for tms in range(len(total_delta_stats.index)):
        plt.plot(listyearnew, average_lap_delta.iloc[tms], 'o-', color = team_colors[tms], label = total_delta_stats.index[tms])
        label = total_delta_stats.index[tms]
        plt.annotate(label, # this is the text
                 (listyearnew[-1],average_lap_delta.iloc[tms][-1]), # these are the coordinates to position the label
                 textcoords="offset points", # how to position the text
                 xytext=(25,0), # distance from text to points (x,y)
                 color = team_colors[tms],
                 ha='left') # horizontal alignment can be left, right or center
    #plt.errorbar(listyearnew, average_lap_delta.iloc[tms], yerr = std_lap_delta.iloc[tms], fmt="o")

    plt.xlabel('Formula 1 Season')
    plt.ylabel('\u0394 Lap Time (s)')
    ax.set_xticks(listyearnew)
    plt.gca().invert_yaxis()
    
    plt.show()

plotdelta_season(total_delta_stats, team_colors, listyearnew)