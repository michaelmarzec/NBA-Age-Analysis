# https://15xu0h4j6i.execute-api.us-east-2.amazonaws.com/dev

from flask import Flask, render_template
from flask_table import Table, Col, LinkCol
from flask import Flask, request, url_for

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

from datetime import datetime
import math
# import matplotlib
# matplotlib.use('Agg')
# from matplotlib import pyplot as plt
import numpy as np
import pandas as pd



## Functions ##
def data_ingest(file_name='static/age_tracking.csv'):
	df = pd.read_csv(file_name)
	df['Team_Name'] = df['Team_Name'].str.title()
	# df.at['Team_Name','Philadelphia 76Ers'] = 'Philadelphia 76ers'
	# print(df)
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
def main():

	df_final = data_ingest()

	# Cleanse for current averages
	df_current = df_currentDate_operations(df_final)
	
	return df_current, df_final


class SortableTable(Table): # https://github.com/plumdog/flask_table/blob/master/examples/sortable.py # https://stackoverflow.com/questions/43552740/best-way-to-sort-table-based-on-headers-using-flask
    id = Col('#', allow_sort=False, show=False)
    Team_Name = Col('Team Name')
    Average_Age = Col('Average Age')
    Average_Age_by_Total_Min = Col('Average Age (by minutes)')
    Average_Age_by_USG = Col('Average Age (by usage)')		
    Point = Col('Point')	
    Combo = Col('Combo')	
    Wing = Col('Wing')	
    Forward = Col('Forward')	
    Big = Col('Big')	

    allow_sort = True

    def sort_url(self, col_key, reverse=False):
        if reverse:
            direction = 'desc'
        else:
            direction = 'asc'
        return url_for('index', sort=col_key, direction=direction)


## Main Execution ##
@app.route('/', methods=['GET','POST'])
def index():
	df, original_df = main()
	sort = request.args.get('sort', 'Team_Name')
	reverse = (request.args.get('direction', 'asc') == 'desc')
	df = df.sort_values(by=[sort], ascending=reverse)
	output_dict = df.to_dict(orient='records')
	table = SortableTable(output_dict,
                          sort_by=sort,
                          sort_reverse=reverse)

	return render_template('age_table.html',  table=table.__html__())

@app.route('/age_graph', methods=['GET','POST'])
def time_graph():
	#prep
	new_df, df = main()
	df = df[['date','Team_Name','Average_Age']]
	df = df.pivot(index='date', columns='Team_Name')
	df.columns = df.columns.droplevel()
	df = df.reset_index()
	# df['date'] = pd.to_datetime(df["date"]).dt.date
	df['date'] = pd.to_datetime(df['date'])
	df = df.sort_values(by=['date'])

	#chart.js variable collection
	# df['date'] = df['date'].apply(lambda x: df['date'].dt.datetime.strftime(x, '%Y-%m-%d'))
	df['date'] = df['date'].dt.strftime('%Y-%m-%d')
	date_series = df['date'].values.tolist()
	# print(date_series)

	atlanta_series = df['Atlanta Hawks'].values.tolist()
	boston_series = df['Boston Celtics'].values.tolist()
	brooklyn_series = df['Brooklyn Nets'].values.tolist()
	charlotte_series = df['Charlotte Hornets'].values.tolist()
	chicago_series = df['Chicago Bulls'].values.tolist()

	context = {"date_series":date_series,"atlanta_series":atlanta_series,"boston_series":boston_series,"brooklyn_series":brooklyn_series}
	

	return render_template("age_graph.html", context=context)


if __name__ == "__main__":
	# time_graph()
	app.run(debug=True)


