# https://15xu0h4j6i.execute-api.us-east-2.amazonaws.com/dev

from flask import Flask, render_template
from flask import Flask, request, url_for

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

import boto3
from datetime import datetime
from datetime import date
from io import StringIO
import math
import numpy as np
import os
import pandas as pd
import sys
import gviz_api
import json

## Functions ##
def data_ingest(file_name='static/age_tracking.csv'):
	df = pd.read_csv(file_name)
	df['Team_Name'] = df['Team_Name'].str.title()
	
	return df

def aws_ingest(filename='age_tracking.csv'):
	aws_id = os.getenv("aws_id")
	aws_secret = os.getenv("aws_secret")
	client = boto3.client('s3', aws_access_key_id=aws_id, aws_secret_access_key=aws_secret)

	bucket_name = 'nba-age-analysis'
	# object_key = 'age_tracking.csv'

	csv_obj = client.get_object(Bucket=bucket_name, Key=filename)
	body = csv_obj['Body']
	csv_string = body.read().decode('utf-8')

	df = pd.read_csv(StringIO(csv_string))
	df['Team_Name'] = df['Team_Name'].str.title()
	df['Team_Name'] = df['Team_Name'].str.replace('Philadelphia 76Ers','Philadelphia 76ers')

	return df


def df_currentDate_operations(df):
	# reduce to current date
	df_current = (df['date'] == df['date'].max())
	df_current = df[df_current]
	del df_current['date']
	df_current = df_current.reset_index(drop=True)
	df_current.index += 1

	df_current.insert(0, 'id', range(1, 1 + len(df_current)))

	# column names
	return df_current


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
def main(filename='age_tracking.csv'):

	df_final = aws_ingest(filename)

	# Cleanse for current averages
	df_current = df_currentDate_operations(df_final)

	df_current = df_current.round(1)
	df_final = df_final.round(1)

	return df_current, df_final

## Main Execution ##
@app.route('/', methods=['GET','POST'])
def index():
	df, original_df = main()
	sort = request.args.get('sort', 'Team_Name')
	reverse = (request.args.get('direction', 'asc') == 'desc')
	df = df.sort_values(by=[sort], ascending=reverse)

	table_description = {"Team_Name": ("string", "Team Name"),
						"Average_Age": ("number", "Average Age"),
						"Average_Age_by_Total_Min": ("number", "Average Age (by minutes)"),
						"Average_Age_by_USG": ("number", "Average Age (by usage)"),
						"Point": ("number", "Point"),
						"Combo": ("number", "Combo"),
						"Wing": ("number", "Wing"),
						"Forward": ("number", "Forward "),
						"Big": ("number", "Big")}
	
	data_table = gviz_api.DataTable(table_description)
	table_data = df.to_dict(orient='records')	
	data_table.LoadData(table_data)
	json_table = data_table.ToJSon(columns_order=("Team_Name",'Average_Age','Average_Age_by_Total_Min', 'Average_Age_by_USG',"Point","Combo","Wing","Forward","Big"))

	today = date.today()
	update_date = today.strftime("%m/%d/%Y")

	context = {"update_date": update_date}

	return render_template('age_table.html',  table=json_table, context=context)

@app.route('/age_graph', methods=['GET','POST'])
def time_graph():
	#prep
	new_df, df = main()
	df = df[['date','Team_Name','Average_Age_by_Total_Min']]
	df = df.pivot(index='date', columns='Team_Name')
	df.columns = df.columns.droplevel()
	df = df.reset_index()
	# df['date'] = pd.to_datetime(df["date"]).dt.date
	df['date'] = pd.to_datetime(df['date'])
	df = df.sort_values(by=['date'])

	#chart.js variable collection
	df['date'] = df['date'].dt.strftime('%Y-%m-%d')
	date_series = df['date'].values.tolist()

	atlanta_series = df['Atlanta Hawks'].values.tolist()
	boston_series = df['Boston Celtics'].values.tolist()
	brooklyn_series = df['Brooklyn Nets'].values.tolist()
	charlotte_series = df['Charlotte Hornets'].values.tolist()
	chicago_series = df['Chicago Bulls'].values.tolist()
	cleveland_series = df['Cleveland Cavaliers'].values.tolist()
	dallas_series = df['Dallas Mavericks'].values.tolist()
	denver_series = df['Denver Nuggets'].values.tolist()
	detroit_series = df['Detroit Pistons'].values.tolist()
	gsw_series = df['Golden State Warriors'].values.tolist()
	houston_series = df['Houston Rockets'].values.tolist()
	indiana_series = df['Indiana Pacers'].values.tolist()
	lac_series = df['Los Angeles Clippers'].values.tolist()
	lal_series = df['Los Angeles Lakers'].values.tolist()
	memphis_series = df['Memphis Grizzlies'].values.tolist()
	miami_series = df['Miami Heat'].values.tolist()
	milwaukee_series = df['Milwaukee Bucks'].values.tolist()
	minnesota_series = df['Minnesota Timberwolves'].values.tolist()
	nop_series = df['New Orleans Pelicans'].values.tolist()
	ny_series = df['New York Knicks'].values.tolist()
	okc_series = df['Oklahoma City Thunder'].values.tolist()
	orlando_series = df['Orlando Magic'].values.tolist()
	philadelphia_series = df['Philadelphia 76ers'].values.tolist()
	phoenix_series = df['Phoenix Suns'].values.tolist()
	portland_series = df['Portland Trail Blazers'].values.tolist()
	sacramento_series = df['Sacramento Kings'].values.tolist()
	sas_series = df['San Antonio Spurs'].values.tolist()
	toronto_series = df['Toronto Raptors'].values.tolist()
	utah_series = df['Utah Jazz'].values.tolist()
	washington_series = df['Washington Wizards'].values.tolist()

	today = date.today()
	update_date = today.strftime("%m/%d/%Y")

	context = {"date_series":date_series,"atlanta_series":atlanta_series,"boston_series":boston_series,"brooklyn_series":brooklyn_series, 
				"charlotte_series": charlotte_series,"chicago_series": chicago_series, "cleveland_series": cleveland_series, "dallas_series": dallas_series, 
				"denver_series": denver_series, "detroit_series": detroit_series, "gsw_series": gsw_series, "houston_series": houston_series, 
				"indiana_series": indiana_series, "lac_series": lac_series, "lal_series": lal_series, "memphis_series": memphis_series, 
				"miami_series": miami_series, "milwaukee_series": milwaukee_series, "minnesota_series": minnesota_series, "nop_series": nop_series, 
				"ny_series": ny_series, "okc_series": okc_series, "orlando_series": orlando_series, "philadelphia_series": philadelphia_series, 
				"phoenix_series": phoenix_series, "portland_series": portland_series, "sacramento_series": sacramento_series, "sas_series": sas_series, 
				"toronto_series": toronto_series, "utah_series": utah_series, "washington_series": washington_series, "update_date": update_date}

	return render_template("age_graph.html", context=context)

@app.route('/21_22', methods=['GET','POST'])
def index_21_22():
	df, original_df = main('age_tracking_2122.csv')
	sort = request.args.get('sort', 'Team_Name')
	reverse = (request.args.get('direction', 'asc') == 'desc')
	df = df.sort_values(by=[sort], ascending=reverse)

	table_description = {"Team_Name": ("string", "Team Name"),
						"Average_Age": ("number", "Average Age"),
						"Average_Age_by_Total_Min": ("number", "Average Age (by minutes)"),
						"Average_Age_by_USG": ("number", "Average Age (by usage)"),
						"Point": ("number", "Point"),
						"Combo": ("number", "Combo"),
						"Wing": ("number", "Wing"),
						"Forward": ("number", "Forward "),
						"Big": ("number", "Big")}
	
	data_table = gviz_api.DataTable(table_description)
	table_data = df.to_dict(orient='records')	
	data_table.LoadData(table_data)
	json_table = data_table.ToJSon(columns_order=("Team_Name",'Average_Age','Average_Age_by_Total_Min', 'Average_Age_by_USG',"Point","Combo","Wing","Forward","Big"))

	today = date.today()
	update_date = today.strftime("%m/%d/%Y")

	context = {"update_date": update_date}

	return render_template('age_table_2122.html',  table=json_table, context=context)

@app.route('/age_graph_21_22', methods=['GET','POST'])
def time_graph_21_22():
	#prep
	new_df, df = main('age_tracking_2122.csv')
	df = df[['date','Team_Name','Average_Age_by_Total_Min']]
	df = df.pivot(index='date', columns='Team_Name')
	df.columns = df.columns.droplevel()
	df = df.reset_index()
	# df['date'] = pd.to_datetime(df["date"]).dt.date
	df['date'] = pd.to_datetime(df['date'])
	df = df.sort_values(by=['date'])

	#chart.js variable collection
	df['date'] = df['date'].dt.strftime('%Y-%m-%d')
	date_series = df['date'].values.tolist()

	atlanta_series = df['Atlanta Hawks'].values.tolist()
	boston_series = df['Boston Celtics'].values.tolist()
	brooklyn_series = df['Brooklyn Nets'].values.tolist()
	charlotte_series = df['Charlotte Hornets'].values.tolist()
	chicago_series = df['Chicago Bulls'].values.tolist()
	cleveland_series = df['Cleveland Cavaliers'].values.tolist()
	dallas_series = df['Dallas Mavericks'].values.tolist()
	denver_series = df['Denver Nuggets'].values.tolist()
	detroit_series = df['Detroit Pistons'].values.tolist()
	gsw_series = df['Golden State Warriors'].values.tolist()
	houston_series = df['Houston Rockets'].values.tolist()
	indiana_series = df['Indiana Pacers'].values.tolist()
	lac_series = df['Los Angeles Clippers'].values.tolist()
	lal_series = df['Los Angeles Lakers'].values.tolist()
	memphis_series = df['Memphis Grizzlies'].values.tolist()
	miami_series = df['Miami Heat'].values.tolist()
	milwaukee_series = df['Milwaukee Bucks'].values.tolist()
	minnesota_series = df['Minnesota Timberwolves'].values.tolist()
	nop_series = df['New Orleans Pelicans'].values.tolist()
	ny_series = df['New York Knicks'].values.tolist()
	okc_series = df['Oklahoma City Thunder'].values.tolist()
	orlando_series = df['Orlando Magic'].values.tolist()
	philadelphia_series = df['Philadelphia 76ers'].values.tolist()
	phoenix_series = df['Phoenix Suns'].values.tolist()
	portland_series = df['Portland Trail Blazers'].values.tolist()
	sacramento_series = df['Sacramento Kings'].values.tolist()
	sas_series = df['San Antonio Spurs'].values.tolist()
	toronto_series = df['Toronto Raptors'].values.tolist()
	utah_series = df['Utah Jazz'].values.tolist()
	washington_series = df['Washington Wizards'].values.tolist()

	today = date.today()
	update_date = today.strftime("%m/%d/%Y")

	context = {"date_series":date_series,"atlanta_series":atlanta_series,"boston_series":boston_series,"brooklyn_series":brooklyn_series, 
				"charlotte_series": charlotte_series,"chicago_series": chicago_series, "cleveland_series": cleveland_series, "dallas_series": dallas_series, 
				"denver_series": denver_series, "detroit_series": detroit_series, "gsw_series": gsw_series, "houston_series": houston_series, 
				"indiana_series": indiana_series, "lac_series": lac_series, "lal_series": lal_series, "memphis_series": memphis_series, 
				"miami_series": miami_series, "milwaukee_series": milwaukee_series, "minnesota_series": minnesota_series, "nop_series": nop_series, 
				"ny_series": ny_series, "okc_series": okc_series, "orlando_series": orlando_series, "philadelphia_series": philadelphia_series, 
				"phoenix_series": phoenix_series, "portland_series": portland_series, "sacramento_series": sacramento_series, "sas_series": sas_series, 
				"toronto_series": toronto_series, "utah_series": utah_series, "washington_series": washington_series, "update_date": update_date}

	return render_template("age_graph_2122.html", context=context)

@app.route('/22_23', methods=['GET','POST'])
def index_22_23():
	df, original_df = main('age_tracking_2223.csv')
	sort = request.args.get('sort', 'Team_Name')
	reverse = (request.args.get('direction', 'asc') == 'desc')
	df = df.sort_values(by=[sort], ascending=reverse)

	table_description = {"Team_Name": ("string", "Team Name"),
						"Average_Age": ("number", "Average Age"),
						"Average_Age_by_Total_Min": ("number", "Average Age (by minutes)"),
						"Average_Age_by_USG": ("number", "Average Age (by usage)"),
						"Point": ("number", "Point"),
						"Combo": ("number", "Combo"),
						"Wing": ("number", "Wing"),
						"Forward": ("number", "Forward "),
						"Big": ("number", "Big")}
	
	data_table = gviz_api.DataTable(table_description)
	table_data = df.to_dict(orient='records')	
	data_table.LoadData(table_data)
	json_table = data_table.ToJSon(columns_order=("Team_Name",'Average_Age','Average_Age_by_Total_Min', 'Average_Age_by_USG',"Point","Combo","Wing","Forward","Big"))

	today = date.today()
	update_date = today.strftime("%m/%d/%Y")

	context = {"update_date": update_date}

	return render_template('age_table_2223.html',  table=json_table, context=context)

@app.route('/age_graph_22_23', methods=['GET','POST'])
def time_graph_22_23():
	#prep
	new_df, df = main('age_tracking_2223.csv')
	df = df[['date','Team_Name','Average_Age_by_Total_Min']]
	df = df.pivot(index='date', columns='Team_Name')
	df.columns = df.columns.droplevel()
	df = df.reset_index()
	# df['date'] = pd.to_datetime(df["date"]).dt.date
	df['date'] = pd.to_datetime(df['date'])
	df = df.sort_values(by=['date'])

	#chart.js variable collection
	df['date'] = df['date'].dt.strftime('%Y-%m-%d')
	date_series = df['date'].values.tolist()

	atlanta_series = df['Atlanta Hawks'].values.tolist()
	boston_series = df['Boston Celtics'].values.tolist()
	brooklyn_series = df['Brooklyn Nets'].values.tolist()
	charlotte_series = df['Charlotte Hornets'].values.tolist()
	chicago_series = df['Chicago Bulls'].values.tolist()
	cleveland_series = df['Cleveland Cavaliers'].values.tolist()
	dallas_series = df['Dallas Mavericks'].values.tolist()
	denver_series = df['Denver Nuggets'].values.tolist()
	detroit_series = df['Detroit Pistons'].values.tolist()
	gsw_series = df['Golden State Warriors'].values.tolist()
	houston_series = df['Houston Rockets'].values.tolist()
	indiana_series = df['Indiana Pacers'].values.tolist()
	lac_series = df['Los Angeles Clippers'].values.tolist()
	lal_series = df['Los Angeles Lakers'].values.tolist()
	memphis_series = df['Memphis Grizzlies'].values.tolist()
	miami_series = df['Miami Heat'].values.tolist()
	milwaukee_series = df['Milwaukee Bucks'].values.tolist()
	minnesota_series = df['Minnesota Timberwolves'].values.tolist()
	nop_series = df['New Orleans Pelicans'].values.tolist()
	ny_series = df['New York Knicks'].values.tolist()
	okc_series = df['Oklahoma City Thunder'].values.tolist()
	orlando_series = df['Orlando Magic'].values.tolist()
	philadelphia_series = df['Philadelphia 76ers'].values.tolist()
	phoenix_series = df['Phoenix Suns'].values.tolist()
	portland_series = df['Portland Trail Blazers'].values.tolist()
	sacramento_series = df['Sacramento Kings'].values.tolist()
	sas_series = df['San Antonio Spurs'].values.tolist()
	toronto_series = df['Toronto Raptors'].values.tolist()
	utah_series = df['Utah Jazz'].values.tolist()
	washington_series = df['Washington Wizards'].values.tolist()

	today = date.today()
	update_date = today.strftime("%m/%d/%Y")

	context = {"date_series":date_series,"atlanta_series":atlanta_series,"boston_series":boston_series,"brooklyn_series":brooklyn_series, 
				"charlotte_series": charlotte_series,"chicago_series": chicago_series, "cleveland_series": cleveland_series, "dallas_series": dallas_series, 
				"denver_series": denver_series, "detroit_series": detroit_series, "gsw_series": gsw_series, "houston_series": houston_series, 
				"indiana_series": indiana_series, "lac_series": lac_series, "lal_series": lal_series, "memphis_series": memphis_series, 
				"miami_series": miami_series, "milwaukee_series": milwaukee_series, "minnesota_series": minnesota_series, "nop_series": nop_series, 
				"ny_series": ny_series, "okc_series": okc_series, "orlando_series": orlando_series, "philadelphia_series": philadelphia_series, 
				"phoenix_series": phoenix_series, "portland_series": portland_series, "sacramento_series": sacramento_series, "sas_series": sas_series, 
				"toronto_series": toronto_series, "utah_series": utah_series, "washington_series": washington_series, "update_date": update_date}

	return render_template("age_graph_2223.html", context=context)


@app.route('/23_24', methods=['GET', 'POST'])
def index_23_24():
	df, original_df = main('age_tracking_2324.csv')
	sort = request.args.get('sort', 'Team_Name')
	reverse = (request.args.get('direction', 'asc') == 'desc')
	df = df.sort_values(by=[sort], ascending=reverse)

	table_description = {"Team_Name": ("string", "Team Name"),
						 "Average_Age": ("number", "Average Age"),
						 "Average_Age_by_Total_Min": ("number", "Average Age (by minutes)"),
						 "Average_Age_by_USG": ("number", "Average Age (by usage)"),
						 "Point": ("number", "Point"),
						 "Combo": ("number", "Combo"),
						 "Wing": ("number", "Wing"),
						 "Forward": ("number", "Forward "),
						 "Big": ("number", "Big")}

	data_table = gviz_api.DataTable(table_description)
	table_data = df.to_dict(orient='records')
	data_table.LoadData(table_data)
	json_table = data_table.ToJSon(columns_order=(
	"Team_Name", 'Average_Age', 'Average_Age_by_Total_Min', 'Average_Age_by_USG', "Point", "Combo", "Wing", "Forward",
	"Big"))

	today = date.today()
	update_date = today.strftime("%m/%d/%Y")

	context = {"update_date": update_date}

	return render_template('age_table_2324.html', table=json_table, context=context)


@app.route('/age_graph_23_24', methods=['GET', 'POST'])
def time_graph_23_24():
	# prep
	new_df, df = main('age_tracking_2324.csv')
	df = df[['date', 'Team_Name', 'Average_Age_by_Total_Min']]
	df = df.pivot(index='date', columns='Team_Name')
	df.columns = df.columns.droplevel()
	df = df.reset_index()
	# df['date'] = pd.to_datetime(df["date"]).dt.date
	df['date'] = pd.to_datetime(df['date'])
	df = df.sort_values(by=['date'])

	# chart.js variable collection
	df['date'] = df['date'].dt.strftime('%Y-%m-%d')
	date_series = df['date'].values.tolist()

	atlanta_series = df['Atlanta Hawks'].values.tolist()
	boston_series = df['Boston Celtics'].values.tolist()
	brooklyn_series = df['Brooklyn Nets'].values.tolist()
	charlotte_series = df['Charlotte Hornets'].values.tolist()
	chicago_series = df['Chicago Bulls'].values.tolist()
	cleveland_series = df['Cleveland Cavaliers'].values.tolist()
	dallas_series = df['Dallas Mavericks'].values.tolist()
	denver_series = df['Denver Nuggets'].values.tolist()
	detroit_series = df['Detroit Pistons'].values.tolist()
	gsw_series = df['Golden State Warriors'].values.tolist()
	houston_series = df['Houston Rockets'].values.tolist()
	indiana_series = df['Indiana Pacers'].values.tolist()
	lac_series = df['Los Angeles Clippers'].values.tolist()
	lal_series = df['Los Angeles Lakers'].values.tolist()
	memphis_series = df['Memphis Grizzlies'].values.tolist()
	miami_series = df['Miami Heat'].values.tolist()
	milwaukee_series = df['Milwaukee Bucks'].values.tolist()
	minnesota_series = df['Minnesota Timberwolves'].values.tolist()
	nop_series = df['New Orleans Pelicans'].values.tolist()
	ny_series = df['New York Knicks'].values.tolist()
	okc_series = df['Oklahoma City Thunder'].values.tolist()
	orlando_series = df['Orlando Magic'].values.tolist()
	philadelphia_series = df['Philadelphia 76ers'].values.tolist()
	phoenix_series = df['Phoenix Suns'].values.tolist()
	portland_series = df['Portland Trail Blazers'].values.tolist()
	sacramento_series = df['Sacramento Kings'].values.tolist()
	sas_series = df['San Antonio Spurs'].values.tolist()
	toronto_series = df['Toronto Raptors'].values.tolist()
	utah_series = df['Utah Jazz'].values.tolist()
	washington_series = df['Washington Wizards'].values.tolist()

	today = date.today()
	update_date = today.strftime("%m/%d/%Y")

	context = {"date_series": date_series, "atlanta_series": atlanta_series, "boston_series": boston_series,
			   "brooklyn_series": brooklyn_series,
			   "charlotte_series": charlotte_series, "chicago_series": chicago_series,
			   "cleveland_series": cleveland_series, "dallas_series": dallas_series,
			   "denver_series": denver_series, "detroit_series": detroit_series, "gsw_series": gsw_series,
			   "houston_series": houston_series,
			   "indiana_series": indiana_series, "lac_series": lac_series, "lal_series": lal_series,
			   "memphis_series": memphis_series,
			   "miami_series": miami_series, "milwaukee_series": milwaukee_series, "minnesota_series": minnesota_series,
			   "nop_series": nop_series,
			   "ny_series": ny_series, "okc_series": okc_series, "orlando_series": orlando_series,
			   "philadelphia_series": philadelphia_series,
			   "phoenix_series": phoenix_series, "portland_series": portland_series,
			   "sacramento_series": sacramento_series, "sas_series": sas_series,
			   "toronto_series": toronto_series, "utah_series": utah_series, "washington_series": washington_series,
			   "update_date": update_date}

	return render_template("age_graph_2324.html", context=context)


@app.route('/24_25', methods=['GET', 'POST'])
def index_24_25():
	df, original_df = main('age_tracking_2425.csv')
	sort = request.args.get('sort', 'Team_Name')
	reverse = (request.args.get('direction', 'asc') == 'desc')
	df = df.sort_values(by=[sort], ascending=reverse)

	table_description = {"Team_Name": ("string", "Team Name"),
						 "Average_Age": ("number", "Average Age"),
						 "Average_Age_by_Total_Min": ("number", "Average Age (by minutes)"),
						 "Average_Age_by_USG": ("number", "Average Age (by usage)"),
						 "Point": ("number", "Point"),
						 "Combo": ("number", "Combo"),
						 "Wing": ("number", "Wing"),
						 "Forward": ("number", "Forward "),
						 "Big": ("number", "Big")}

	data_table = gviz_api.DataTable(table_description)
	table_data = df.to_dict(orient='records')
	data_table.LoadData(table_data)
	json_table = data_table.ToJSon(columns_order=(
	"Team_Name", 'Average_Age', 'Average_Age_by_Total_Min', 'Average_Age_by_USG', "Point", "Combo", "Wing", "Forward",
	"Big"))

	today = date.today()
	update_date = today.strftime("%m/%d/%Y")

	context = {"update_date": update_date}

	return render_template('age_table_2425.html', table=json_table, context=context)


@app.route('/age_graph_24_25', methods=['GET', 'POST'])
def time_graph_24_25():
	# prep
	new_df, df = main('age_tracking_2425.csv')
	df = df[['date', 'Team_Name', 'Average_Age_by_Total_Min']]
	df = df.pivot(index='date', columns='Team_Name')
	df.columns = df.columns.droplevel()
	df = df.reset_index()
	# df['date'] = pd.to_datetime(df["date"]).dt.date
	df['date'] = pd.to_datetime(df['date'])
	df = df.sort_values(by=['date'])

	# chart.js variable collection
	df['date'] = df['date'].dt.strftime('%Y-%m-%d')
	date_series = df['date'].values.tolist()

	atlanta_series = df['Atlanta Hawks'].values.tolist()
	boston_series = df['Boston Celtics'].values.tolist()
	brooklyn_series = df['Brooklyn Nets'].values.tolist()
	charlotte_series = df['Charlotte Hornets'].values.tolist()
	chicago_series = df['Chicago Bulls'].values.tolist()
	cleveland_series = df['Cleveland Cavaliers'].values.tolist()
	dallas_series = df['Dallas Mavericks'].values.tolist()
	denver_series = df['Denver Nuggets'].values.tolist()
	detroit_series = df['Detroit Pistons'].values.tolist()
	gsw_series = df['Golden State Warriors'].values.tolist()
	houston_series = df['Houston Rockets'].values.tolist()
	indiana_series = df['Indiana Pacers'].values.tolist()
	lac_series = df['Los Angeles Clippers'].values.tolist()
	lal_series = df['Los Angeles Lakers'].values.tolist()
	memphis_series = df['Memphis Grizzlies'].values.tolist()
	miami_series = df['Miami Heat'].values.tolist()
	milwaukee_series = df['Milwaukee Bucks'].values.tolist()
	minnesota_series = df['Minnesota Timberwolves'].values.tolist()
	nop_series = df['New Orleans Pelicans'].values.tolist()
	ny_series = df['New York Knicks'].values.tolist()
	okc_series = df['Oklahoma City Thunder'].values.tolist()
	orlando_series = df['Orlando Magic'].values.tolist()
	philadelphia_series = df['Philadelphia 76ers'].values.tolist()
	phoenix_series = df['Phoenix Suns'].values.tolist()
	portland_series = df['Portland Trail Blazers'].values.tolist()
	sacramento_series = df['Sacramento Kings'].values.tolist()
	sas_series = df['San Antonio Spurs'].values.tolist()
	toronto_series = df['Toronto Raptors'].values.tolist()
	utah_series = df['Utah Jazz'].values.tolist()
	washington_series = df['Washington Wizards'].values.tolist()

	today = date.today()
	update_date = today.strftime("%m/%d/%Y")

	context = {"date_series": date_series, "atlanta_series": atlanta_series, "boston_series": boston_series,
			   "brooklyn_series": brooklyn_series,
			   "charlotte_series": charlotte_series, "chicago_series": chicago_series,
			   "cleveland_series": cleveland_series, "dallas_series": dallas_series,
			   "denver_series": denver_series, "detroit_series": detroit_series, "gsw_series": gsw_series,
			   "houston_series": houston_series,
			   "indiana_series": indiana_series, "lac_series": lac_series, "lal_series": lal_series,
			   "memphis_series": memphis_series,
			   "miami_series": miami_series, "milwaukee_series": milwaukee_series, "minnesota_series": minnesota_series,
			   "nop_series": nop_series,
			   "ny_series": ny_series, "okc_series": okc_series, "orlando_series": orlando_series,
			   "philadelphia_series": philadelphia_series,
			   "phoenix_series": phoenix_series, "portland_series": portland_series,
			   "sacramento_series": sacramento_series, "sas_series": sas_series,
			   "toronto_series": toronto_series, "utah_series": utah_series, "washington_series": washington_series,
			   "update_date": update_date}

	return render_template("age_graph_2425.html", context=context)


if __name__ == "__main__":
	app.run(debug=True)


