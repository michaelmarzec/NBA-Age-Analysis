# Next Steps
	# flask app
	# zappa for AWS online (check the Ethan: zappa blog)
		# figure out Zappa scheduling
	# add multi-indexing for the position breakdowns

#################################################################

# Data Prep
	# extract table for each team
	# reduce to player, age, pos, gp, min, mpg, usage #
	# identify team name
# Data Calculation
	# average team age
	# weighted average team age by total minutes
	# weighted average team age by USG% (statistical leader awards use a 58 / 82 (70.7%) threshold to be considered)
	# weighted average team age by total minutes ... by position
# Data Export
	# export new data (by date) to local CSV file


### archive ###
# url = "https://www.basketball-reference.com/teams/MIN/2021.html"
# table = soup.find("table", id = "advanced")

## multi-indexing for positions
# d_mpg = {} 
# for i in positions: 
#     d_mpg[i] = 'Age_By_MPG'
# return_df.columns = pd.MultiIndex.from_tuples([(d_mpg[k], k) for k in return_df.columns])
###############
# from flask import Flask, render_template
# app = Flask(__name__)
# app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# app.config['TEMPLATES_AUTO_RELOAD'] = True

from bs4 import BeautifulSoup
# from jinja2 import Template
import math
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import numpy as np
import os
import pandas as pd
import re
from urllib.request import urlopen

## Functions ##

# Data Prep #

def ctg_extract(url, columns, remove_rank):
	html = urlopen(url)
	soup = BeautifulSoup(html, 'html.parser')
	table = soup.find("table")
	df = pd.read_html(str(table))[0]
	df = df.drop(remove_rank, axis=1, level=1)
	df.columns = df.columns.droplevel(-1)
	df = df[columns]
	return df

def ctg_team_name(url):
	html = urlopen(url)
	soup = BeautifulSoup(html, 'html.parser')
	html_team_name = str(soup.findAll("span", {"class": "hidden-mobile"}))
	team_name = re.search(">(.*)<", html_team_name)
	team_name = team_name.group(1)
	return team_name

# Data Calcs #

def avg_age_by_mpg(df, min_var, age_var):
	df = df.copy()
	df['minute_weight'] = df[min_var] / df[min_var].sum()
	df['age_weight'] = df['minute_weight'] * df[age_var]
	avg_age_by_mpg = round(df['age_weight'].sum(),2)
	return avg_age_by_mpg

### note: using threshold of 58 / 82 (70.7%) of GP
### note: gp calculated as sum of minutes and raised to ceiling integer (as CTG tosses out garbage time, risks an 81 GP total)
def avg_age_by_usg(df, min_var, age_var, usg_var, gp_var):
	total_gp_threshold = math.ceil(df[min_var].sum() / 240) * (58/82)
	df = df.loc[df[gp_var] >= total_gp_threshold].copy()
	df[usg_var] = df[usg_var].str.rstrip('%').astype('float') / 100.0
	df['usage_weight'] = df[usg_var] / df[usg_var].sum()
	df['age_weight'] = df['usage_weight'] * df[age_var]
	avg_age_by_usg = round(df['age_weight'].sum(),2)
	return avg_age_by_usg

def avg_age_by_position_by_mpg(df, min_var, age_var, pos_var):
	pos_list = list(df[pos_var].unique())
	return_df = pd.DataFrame()
	for x in pos_list:
		positional_df = df.loc[df[pos_var] == x].copy()
		positional_df['minute_weight'] = positional_df[min_var] / positional_df[min_var].sum()
		positional_df['age_weight'] = positional_df['minute_weight'] * positional_df[age_var]
		avg_age_by_mpg_by_pos = round(positional_df['age_weight'].sum(),2)
		return_df.loc[0, x] = avg_age_by_mpg_by_pos
	return return_df

# Data Export #
def data_tracking_export(df, file_name = 'age_tracking.csv', team_var = 'Team_Name', date_var = 'date'):
	df[date_var] = pd.to_datetime('today').normalize()
	df[date_var] = df[date_var].apply(lambda x: x.strftime('%Y-%m-%d'))
	archive_df = pd.read_csv(file_name)#, parse_dates=[date_var], date_parser=lambda x: pd.to_datetime(x).normalize())
	df = pd.concat([archive_df, df], axis = 0).drop_duplicates(subset=[team_var, date_var], keep='last', ignore_index=True)
	df.to_csv(file_name, index=False)
	return df


def data_plot_export(df, age_var, export_file_name='static/avg_age_plot.png', date_var = 'date', team_var = 'Team_Name'):
	# df[date_var] = pd.to_datetime(df[date_var])
	df.pivot(index="date", columns="Team_Name", values="Average_Age").plot(figsize=(20,10)).legend(loc='center',bbox_to_anchor=(1.0, 0.5))
	plt.savefig(export_file_name, format='png')

## Hard Codes ##
df_columns_ind0 = ['Player','Age','Pos','GP','MIN','MPG','Usage']
url_p1 = 'https://cleaningtheglass.com/stats/team/'
url_p2 = '#tab-offensive_overview'
player_var = 'Player'
age_var = 'Age'
pos_var = 'Pos'
gp_var = 'GP'
min_var = 'MIN'
mpg_var = 'MPG'
usg_var = 'Usage'
positions = ['Point','Combo','Wing','Forward','Big']


## Main Process ##
# Flask application
def main():
	return_df = pd.DataFrame()
	# Data Extract
	for i in range(30):
		url = url_p1 + str(i+1) + url_p2
		df = ctg_extract(url, df_columns_ind0, '%')
		return_df.loc[i,'Team_Name'] = ctg_team_name(url)		
		return_df.loc[i, 'Average_Age'] = round(df.Age.mean(),2)
		return_df.loc[i, 'Average_Age_by_Total_Min'] = avg_age_by_mpg(df, min_var, age_var)
		return_df.loc[i, 'Average_Age_by_USG'] = avg_age_by_usg(df, min_var, age_var, usg_var, gp_var)
		avg_age_by_pos_by_mpg = avg_age_by_position_by_mpg(df, min_var, age_var, pos_var)
		if i == 0: 
			column_order = list(return_df.columns) + positions
			return_df = pd.concat([return_df, avg_age_by_pos_by_mpg], axis = 1)
			return_df = return_df.reindex(return_df.columns.union(positions, sort=False), axis=1, fill_value=np.nan)
		else: 
			return_df.loc[i, list(avg_age_by_pos_by_mpg.columns)] = avg_age_by_pos_by_mpg.squeeze()
	
	# Data Prep (Multi-Indexing, add the average_age_by_usage by position?)
	return_df = return_df[column_order]

	# Local Exports (Data & Plots)
	full_df = data_tracking_export(return_df)
	# data_plot_export(full_df, 'Average_Age')

	# #Print Current DF
	print(full_df)
	
	# # Flask return
	# return render_template('view.html',  tables=[return_df.to_html(classes='data', header='true')])


## Main Execution ##
# @app.route('/', methods=['GET','POST'])
# def execute():
# 	return main()

# @app.after_request
# def add_header(response):
#     response.cache_control.max_age = 0
#     return response

if __name__ == "__main__":
	print("Execution Started")
	## local run ##
	main()
	## app run ##
	# app.run()

