import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


age_tracking_df = pd.read_csv('age_tracking.csv', parse_dates = ['date'])

# average age plot
def line_plot_all(df, date_index, age_col, legend_col):
	df.set_index(date_index, inplace=True)
	df = df[[age_col, legend_col]]
	df = df.pivot(columns=legend_col, values=age_col)
	df.plot()
	plt.show()

def percent_change(df, date_index, age_col, legend_col):
	df.set_index(date_index, inplace=True)
	df = df[[age_col, legend_col]]
	df = df.pivot(columns=legend_col, values=age_col)
	change_result = ((df.iloc[-1] - df.iloc[0]) / df.iloc[0] * 100)
	return change_result


def variance_calc(df, date_index, age_col, legend_col):
	df.set_index(date_index, inplace=True)
	df = df[[age_col, legend_col]]
	df = df.pivot(columns=legend_col, values=age_col)
	variance_result = df.std()
	return variance_result


# line_plot_all(age_tracking_df, 'date','Average_Age_by_Total_Min','Team_Name')
# season_percent_change = percent_change(age_tracking_df, 'date','Average_Age_by_Total_Min','Team_Name')
# season_variance_calc = variance_calc(age_tracking_df, 'date','Average_Age_by_Total_Min','Team_Name')


