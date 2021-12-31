# https://15xu0h4j6i.execute-api.us-east-2.amazonaws.com/dev

from flask import Flask, render_template

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

import math
# import matplotlib
# matplotlib.use('Agg')
# from matplotlib import pyplot as plt
import numpy as np
import pandas as pd



## Functions ##

def data_ingest(file_name='age_tracking.csv'):
	df = pd.read_csv(file_name)
	return df

# def data_plot_export(df, age_var, export_file_name='static/avg_age_plot.png', date_var = 'date', team_var = 'Team_Name'):
# 	# df[date_var] = pd.to_datetime(df[date_var])
# 	df.pivot(index="date", columns="Team_Name", values="Average_Age").plot(figsize=(20,10)).legend(loc='center',bbox_to_anchor=(1.0, 0.5))
# 	plt.savefig(export_file_name, format='png')

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

	# Local Exports (Data & Plots)
	# data_plot_export(df_final, 'Average_Age')

	# Print Current DF
	print(df_final)
	
	# Flask return
	return render_template('view.html',  tables=[df_final.to_html(classes='data', header='true')])


## Main Execution ##
@app.route('/', methods=['GET','POST'])
def execute():
	return main()

# @app.after_request
# def add_header(response):
#     response.cache_control.max_age = 0
#     return response

if __name__ == "__main__":
# 	print("Execution Started")
# 	## app run ##
	app.run()


