import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
from data_load import DataReader
import plotly
import plotly.graph_objs as go

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

covid = DataReader()

df = covid.data[covid.data["Region"]=='Total']

app.layout = html.Div([
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='country',
                options=[{'label': i, 'value': i} for i in df['Country'].unique()],
                multi=True,
                value=["Switzerland"]
            ),
            dcc.Dropdown(
                id='type',
                options=[{'label': i, 'value': i} for i in ['confirmed cases','deceased cases', 'recovered cases', 'active cases']],
                value='confirmed cases'
            ),
            dcc.Dropdown(
                id='scale',
                options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                value='Linear',
            ),
            dcc.Dropdown(
                id='count',
                options=[{'label': i, 'value': i} for i in ['absolute', 'relative']],
                value='absolute',
            ),
            dcc.Dropdown(
                id='numbers',
                options=[{'label': i, 'value': i} for i in ['Total', 'Change']],
                value='Total',
            ),
            dcc.Dropdown(
                id='align',
                options=[{'label': i, 'value': i} for i in ['actual date', 'date from 1st case', 'date from 100th case']],
                value='actual date',
            )
        ],
        style={'width': '50%', 'display': 'inline-block'}),
    ]),

    dcc.Graph(id='indicator-graphic')
])

@app.callback(
    Output('indicator-graphic', 'figure'),
    [Input('country', 'value'),
     Input('type', 'value'),
     Input('scale', 'value'),
     Input('align', 'value'),
     Input('count', 'value'),
     Input('numbers', 'value')])
def update_graph(country, type, scale, align, count, numbers):
    if len(country) == 0 or len(type) == 0:
        return {
            'data': [],
            'layout': dict(
                yaxis={
                    'title': 'cases',
                    'type': 'linear' if scale == 'Linear' else 'log'
                },
                xaxis={
                    'title': 'date'
                },
                margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
                hovermode='closest'
            )
        }

    dff = df[df['count']==count]

    traces = []
    annotations = []
    for label in country:
        data = dff[dff["Country"]==label]

        y = data[type] if numbers=='Total' else data[type].diff()

        if align == 'date from 1st case':
            index = next((index for index, value in enumerate(y) if value != 0), None)
            y = y[index:]
            x = list(range(0,len(y)))
        elif align == 'date from 100th case':
            index = next((index for index, value in enumerate(y) if value > 100), None)
            y = y[index:]
            x = list(range(0,len(y)))
        else:
            x = data['Date']
        
        trace = go.Scatter(
            x=x,
            y=y,
            text=label,
            name='Scatter',
            mode= 'lines+markers',
            marker={
                'size': 5,
                'opacity': 0.5,
                'line': {'width': 0.5, 'color': 'white'}
            })
        traces.append(trace)

        # labeling the left_side of the plot
        last_value = y.iloc[-1]
        annotations.append(dict(xref='paper', x=0.95, y=last_value,
                                xanchor='left', yanchor='middle',
                                text=label, # + ' {}'.format(last_value),
                                font=dict(family='Arial', size=16),
                                showarrow=False))

    return {
        'data': traces,
        'layout': dict(
            yaxis={
                'title': 'cases',
                'type': 'linear' if scale == 'Linear' else 'log'
            },
            xaxis={
                'title': 'date'
            },
            margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
            hovermode='closest',
            annotations=annotations
        )
    }

if __name__ == '__main__':
    app.run_server(debug=True)