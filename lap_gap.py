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

yeartoanalyze = 2021

fastf1.Cache.enable_cache('TestCache')  # replace with your cache directory

# we only want support for timedelta plotting in this example
fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme=None, misc_mpl_mods=False)

# each year has a different number of races to iterate over
listyear = [x for x in range(2003,2022)]
numraces = [16,18,19,18,17,18,17,19,19,20,19,19,19,19,20,21,21,17,9]
data = {'Year':listyear, 'NumRaces':numraces}
year_ref = pd.DataFrame(data)
year_ref = year_ref.set_index('Year')
num_of_races_in_the_season = year_ref.loc[yeartoanalyze][0]

##############################################################################
# get all races in a season, some seasons have fewer than 
for i in range(num_of_races_in_the_season):
    try:
        quali = fastf1.get_session(yeartoanalyze, i, 'Q')
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
    race_add = race_add.rename(columns={"LapTimeDeltaSec":str(i)})
    
    if i == 0:
        lap_delta_by_race = race_add.copy()
    else:
        lap_delta_by_race = pd.concat([lap_delta_by_race, race_add],axis=1)
    
        
    ##############################################################################
    # We can take a quick look at the laps we have to check if everything
    # looks all right. For this, we'll just check the 'Driver', 'LapTime'
    # and 'LapTimeDelta' columns.
    
    #print(fastest_laps[['Driver', 'LapTime', 'LapTimeDelta']])
    
##############################################################################
# average the fastest lap deltas, get their standard deviation and then sort
# by team performance. Round to thousandths of a second.        
lap_delta_by_race['SeasonAverageDelta'] = lap_delta_by_race.mean(axis=1)
lap_delta_by_race['SeasonSTDDelta'] = lap_delta_by_race.std(axis=1)
lap_delta_by_race = lap_delta_by_race.sort_values(by='SeasonAverageDelta')
#lap_delta_by_race = lap_delta_by_race.round(3)



##############################################################################
# Finally, we'll create a list of team colors per lap to color our plot.
# Note depending on the season the team colors will return nothing and the 
# the plot will issue an error

team_colors = list()
for tms in lap_delta_by_race.index:
    if tms == 'Renault':
        color = fastf1.plotting.team_color('Alpine F1 Team')
    elif tms == 'Toro Rosso':
        color = fastf1.plotting.team_color('AlphaTauri')
    elif tms == 'Racing Point':
        color = fastf1.plotting.team_color('Aston Martin')
    elif tms == 'Force India':
        color = fastf1.plotting.team_color('Aston Martin')
    elif fastf1.plotting.team_color(tms) is None:
        color = 'k'
    else:
        color = fastf1.plotting.team_color(tms)
    team_colors.append(color)

##############################################################################
def plotseason(lap_delta_by_race, team_colors):
    # Now, we can plot all the data, round to thousandths of a second
    fig, ax = plt.subplots()
    #ax.barh(fastest_laps.index, fastest_laps['LapTimeDeltaSec'], color=team_colors, edgecolor='grey')
    bars = ax.barh(lap_delta_by_race.index, lap_delta_by_race['SeasonAverageDelta'].round(3), color=team_colors, xerr = lap_delta_by_race['SeasonSTDDelta'], edgecolor='grey')
    #ax.barh(lap_delta_by_race.index, lap_delta_by_race['SeasonAverageDelta'], xerr = lap_delta_by_race['SeasonSTDDelta'], edgecolor='grey')
    ax.set_yticks(lap_delta_by_race.index)
    ax.set_yticklabels(lap_delta_by_race.index)
    
    # show fastest at the top
    ax.invert_yaxis()
    
    # draw vertical lines behind the bars
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, linestyle='--', color='black', zorder=-1000)
    
    ax.bar_label(bars, fmt='%.3f')
    # for bar in bars:
    #   width = bar.get_width() + 0.08
    #   label_y_pos = bar.get_y() + bar.get_height() / 8
    #   ax.text(width, label_y_pos, s=f'{width}', va='center')
    
    ##############################################################################
    # Finally, give the plot a meaningful title
    
    plt.xlabel('\u0394 Lap Time (s)')
    plt.suptitle(f"Time difference to fastest qualifying lap \n"
                 f"{quali.weekend.year} season average")
    
    plt.show()

plotseason(lap_delta_by_race, team_colors)