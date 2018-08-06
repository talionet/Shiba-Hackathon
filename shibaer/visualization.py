
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
from pandas import DataFrame as df
import os
import sys
import datetime

def stack_plot(data, index_axis, stack_var='age',title=None, ylim=None):
    if title is None:
        title=stack_var +' by ' + index_axis.dtype
    data[stack_var].groupby(index_axis).value_counts().unstack().plot(kind='bar', 
                                                                      stacked=True, figsize=(20,5), title=title, ylim=ylim)
    
def plot_with_legend(data,group_var='gender', plot_var='age_on_date',drop_values=[]):
    fig, ax = plt.subplots()
    groups = data.groupby(group_var)[plot_var]
    for k, v in groups:
        if k not in drop_values:
            v.hist(label=k, alpha=.75, ax=ax, bins = 40)
    ax.legend()
    
    
def plot_events_by_time(death_events, by_time, stack_var = ''):
      death_events.sort_values(by=by_time)
      times = pd.DatetimeIndex(death_events[by_time]).sort_values()
      stack_plot(death_events, index_axis = [times.month,times.year], 
      stack_var=stack_var, title = 'Death %s by %s month' %(stack_var,by_time))