from turtle import pd
import plotly.express as px
import pandas as pd

f = 'all.csv'
df = pd.read_csv(f)
fig = px.scatter_3d(df, x='x', y='y', z='z', symbol='activity', color='activity')
fig.show()
