# https://15xu0h4j6i.execute-api.us-east-2.amazonaws.com/dev

from flask import Flask, render_template, request, url_for, Response

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

ADSENSE_CLIENT = os.getenv('ADSENSE_CLIENT', '')
ADSENSE_SLOT = os.getenv('ADSENSE_SLOT', '')
ADSENSE_ENABLED = os.getenv('ADSENSE_ENABLED', 'false').lower() in ('1', 'true', 'yes')


@app.context_processor
def inject_adsense():
	return {
		'adsense_enabled': ADSENSE_ENABLED and bool(ADSENSE_CLIENT) and bool(ADSENSE_SLOT),
		'adsense_client': ADSENSE_CLIENT,
		'adsense_slot': ADSENSE_SLOT,
	}


@app.route('/ads.txt')
def ads_txt():
	client = ADSENSE_CLIENT if ADSENSE_CLIENT.startswith('ca-pub-') else 'ca-pub-9713390835850351'
	pub_id = client.replace('ca-pub-', 'pub-', 1)
	content = f'google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n'
	return Response(content, mimetype='text/plain')


@app.route('/privacy')
def privacy():
	return render_template('privacy.html')


## Functions ##
def normalize_team_names(df):
	if df is None or len(df) == 0 or 'Team_Name' not in df.columns:
		return df
	df['Team_Name'] = df['Team_Name'].str.title()
	df['Team_Name'] = df['Team_Name'].str.replace('Philadelphia 76Ers', 'Philadelphia 76ers', regex=False)
	return df


def prepare_graph_df(df):
	df = df[['date', 'Team_Name', 'Average_Age_by_Total_Min']]
	df = df.pivot(index='date', columns='Team_Name')
	df.columns = df.columns.droplevel()
	df = df.reset_index()
	df['date'] = pd.to_datetime(df['date'])
	df = df.sort_values(by=['date'])
	df['date'] = df['date'].dt.strftime('%Y-%m-%d')
	if 'Philadelphia 76Ers' in df.columns:
		df = df.rename(columns={'Philadelphia 76Ers': 'Philadelphia 76ers'})
	return df


GRAPH_TEAM_SERIES = [
	('atlanta_series', 'Atlanta Hawks'),
	('boston_series', 'Boston Celtics'),
	('brooklyn_series', 'Brooklyn Nets'),
	('charlotte_series', 'Charlotte Hornets'),
	('chicago_series', 'Chicago Bulls'),
	('cleveland_series', 'Cleveland Cavaliers'),
	('dallas_series', 'Dallas Mavericks'),
	('denver_series', 'Denver Nuggets'),
	('detroit_series', 'Detroit Pistons'),
	('gsw_series', 'Golden State Warriors'),
	('houston_series', 'Houston Rockets'),
	('indiana_series', 'Indiana Pacers'),
	('lac_series', 'Los Angeles Clippers'),
	('lal_series', 'Los Angeles Lakers'),
	('memphis_series', 'Memphis Grizzlies'),
	('miami_series', 'Miami Heat'),
	('milwaukee_series', 'Milwaukee Bucks'),
	('minnesota_series', 'Minnesota Timberwolves'),
	('nop_series', 'New Orleans Pelicans'),
	('ny_series', 'New York Knicks'),
	('okc_series', 'Oklahoma City Thunder'),
	('orlando_series', 'Orlando Magic'),
	('philadelphia_series', 'Philadelphia 76ers'),
	('phoenix_series', 'Phoenix Suns'),
	('portland_series', 'Portland Trail Blazers'),
	('sacramento_series', 'Sacramento Kings'),
	('sas_series', 'San Antonio Spurs'),
	('toronto_series', 'Toronto Raptors'),
	('utah_series', 'Utah Jazz'),
	('washington_series', 'Washington Wizards'),
]


def build_graph_context(df):
	"""Build Chart.js context; safe when season CSV has no rows yet."""
	context = {key: [] for key, _ in GRAPH_TEAM_SERIES}
	context['date_series'] = []
	context['update_date'] = date.today().strftime("%m/%d/%Y")
	if df is None or len(df) == 0:
		return context

	gdf = prepare_graph_df(df)
	context['date_series'] = gdf['date'].values.tolist()
	for key, team in GRAPH_TEAM_SERIES:
		context[key] = gdf[team].values.tolist() if team in gdf.columns else []
	return context


def data_ingest(file_name='static/age_tracking.csv'):
	df = pd.read_csv(file_name)
	normalize_team_names(df)
	return df

def aws_ingest(filename='age_tracking.csv'):
	aws_id = os.getenv("aws_id")
	aws_secret = os.getenv("aws_secret")
	# Prefer explicit keys when set; otherwise use the Lambda IAM role / default chain
	if aws_id and aws_secret:
		client = boto3.client('s3', aws_access_key_id=aws_id, aws_secret_access_key=aws_secret)
	else:
		client = boto3.client('s3')

	bucket_name = 'nba-age-analysis'
	# object_key = 'age_tracking.csv'

	csv_obj = client.get_object(Bucket=bucket_name, Key=filename)
	body = csv_obj['Body']
	csv_string = body.read().decode('utf-8')

	df = pd.read_csv(StringIO(csv_string))
	normalize_team_names(df)
	return df


def df_currentDate_operations(df):
	# reduce to current date (no-op when season file has no rows yet)
	if df is None or len(df) == 0 or 'date' not in df.columns:
		return df if df is not None else pd.DataFrame()

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
	# LOCAL_DATA=1 forces reading flask/static for local dev.
	# In Lambda, always load from S3 (IAM role or aws_id/aws_secret).
	if os.getenv("LOCAL_DATA", "").lower() in ("1", "true", "yes"):
		df_final = data_ingest(f'static/{filename}')
	else:
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
	new_df, df = main()
	return render_template("age_graph.html", context=build_graph_context(df))

@app.route('/25_26', methods=['GET', 'POST'])
def index_25_26():
	df, original_df = main('age_tracking_2526.csv')
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

	return render_template('age_table_2526.html', table=json_table, context=context)


@app.route('/age_graph_25_26', methods=['GET', 'POST'])
def time_graph_25_26():
	new_df, df = main('age_tracking_2526.csv')
	return render_template("age_graph_2526.html", context=build_graph_context(df))

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
	new_df, df = main('age_tracking_2122.csv')
	return render_template("age_graph_2122.html", context=build_graph_context(df))

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
	new_df, df = main('age_tracking_2223.csv')
	return render_template("age_graph_2223.html", context=build_graph_context(df))


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
	new_df, df = main('age_tracking_2324.csv')
	return render_template("age_graph_2324.html", context=build_graph_context(df))


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
	new_df, df = main('age_tracking_2425.csv')
	return render_template("age_graph_2425.html", context=build_graph_context(df))


if __name__ == "__main__":
	app.run(debug=True)


