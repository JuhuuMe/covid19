import pandas as pd
import math

import plotly
import plotly.graph_objs as go

import dash
import dash_daq as daq
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output
from data_load import DataReader

dash_app  = dash.Dash(__name__, 
    external_stylesheets=[dbc.themes.SLATE],
    meta_tags = [
        {
            "name": "description",
            "content": "Corona visualizations tracking the number of cases and death toll due to COVID-19.",
        },
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
    ])

colors = {
    'background': '#222222',
    'text': '#7FDBFF'
}

app = dash_app.server

covid = DataReader()

df = covid.data[covid.data["Region"]=='Total']

dash_app.layout = html.Div(children= [
    dbc.Container([
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.H2(children='Covid-19 statistics'), 
                ], style={'textAlign': 'center'}), 
            )
        ]),
        dbc.Row([
            dbc.Col(
                html.Div([
                    dcc.Dropdown(
                        id='country',
                        options=[{'label': i, 'value': i} for i in df['Country'].unique()],
                        multi=True,
                        #value=["Switzerland", "US", "Spain", "China", "Italy"]
                        value=["Switzerland", "Italy", "Spain", "South Korea", "US", "China"]
                    ),
                ]),
            ),
        ]),
        dbc.Row([
            dbc.Col(
                html.Div([
                    dcc.Dropdown(
                        id='type',
                        options=[{'label': i, 'value': i} for i in ['confirmed cases','deceased cases', 'recovered cases', 'active cases']],
                        value='active cases'
                    )
                ]),
            ),
            dbc.Col(
                html.Div([
                    dcc.Dropdown(
                        id='align',
                        options=[{'label': i, 'value': i} for i in ['actual date', 'date from 1st case', 'date from 100th case']],
                        value='actual date',
                    )
                ]),
            )
        ]),
        dbc.Row([
            dbc.Col(
                html.Div([
                    daq.ToggleSwitch(
                        id='scale',
                        label=['Linear', 'Log'],
                        value=True,
                    )
                ], style={'width': '50%', 'display': 'inline-block'}),
            )
        ]),
        dbc.Row([
            dbc.Col(
                html.Div(dcc.Graph(id='plot-abs-total', style = {'padding': 5}, config={'displayModeBar': False})
                ), lg=6, md=12, xs=12),
            dbc.Col(
                html.Div(dcc.Graph(id='plot-abs-change', style = {'padding': 5}, config={'displayModeBar': False})
                ), lg=6, md=12, xs=12),
        ]),
        dbc.Row([
            dbc.Col(
                html.Div(dcc.Graph(id='plot-rel-total', style = {'padding': 5}, config={'displayModeBar': False})
                ), lg=6, md=12, xs=12),
            dbc.Col(
                html.Div(dcc.Graph(id='plot-rel-change', style = {'padding': 5}, config={'displayModeBar': False})
                ), lg=6, md=12, xs=12)
        ]),
    ]),
    html.Div(children='''
        The data is from Johns Hopkins CSSE. 
        ''', style={'textAlign': 'center'}),
])

@dash_app .callback(
    Output('plot-abs-total', 'figure'),
    [Input('country', 'value'),
     Input('type', 'value'),
     Input('scale', 'value'),
     Input('align', 'value')])
def graph_callback(country, type, scale, align):
    return update_graph(country, type, scale, align, 'absolute', 'Total', 'Covid-19 cases')

@dash_app .callback(
    Output('plot-abs-change', 'figure'),
    [Input('country', 'value'),
     Input('type', 'value'),
     Input('scale', 'value'),
     Input('align', 'value')])
def graph_callback(country, type, scale, align):
    return update_graph(country, type, False, align, 'absolute', 'Change', 'Covid-19 cases daily change')

@dash_app .callback(
    Output('plot-rel-total', 'figure'),
    [Input('country', 'value'),
     Input('type', 'value'),
     Input('scale', 'value'),
     Input('align', 'value')])
def graph_callback(country, type, scale, align):
    return update_graph(country, type, False, align, 'relative', 'Total', 'Covid-19 cases per million people')

@dash_app .callback(
    Output('plot-rel-change', 'figure'),
    [Input('country', 'value'),
     Input('type', 'value'),
     Input('scale', 'value'),
     Input('align', 'value')])
def graph_callback(country, type, scale, align):
    return update_graph(country, type, False, align, 'relative', 'Change', 'Covid-19 cases daily change per million people')

def update_graph(country, type, scale, align, count, numbers, title):
    if len(country) == 0 or len(type) == 0:
        return {
            'data': [],
            'layout': dict(
                title=title,
                yaxis={
                    'title': 'cases',
                    'type': 'log' if scale else 'linear',
                    'fixedrange': True
                },
                xaxis={
                    'title': 'date',
                    'fixedrange': True
                },
                margin={'l': 50, 'b': 50, 't': 50, 'r': 50},
                hovermode='closest',
                plot_bgcolor=colors['background'],
                paper_bgcolor=colors['background'],
                font={'color': colors['text']}
            )
        }

    dff = df[df['count']==count]

    traces = []
    annotations = []
    for label in country:
        data = dff[dff["Country"]==label]

        base_y = df[(df['count']=='absolute') & (df["Country"]==label)][type]
        y = data[type] if numbers=='Total' else data[type].diff()

        if align == 'date from 1st case':
            index = next((index for index, value in enumerate(base_y) if value != 0), None)
            y = y[index:]
            x = list(range(0,len(y)))
            last_value = x[-1]
        elif align == 'date from 100th case':
            index = next((index for index, value in enumerate(base_y) if value > 100), None)
            y = y[index:]
            x = list(range(0,len(y)))
            last_value = x[-1]
        else:
            x = data['Date']
            last_value = x.iloc[-1]
        
        trace = go.Scatter(
            x=x,
            y=y,
            name=label,
            mode= 'lines+markers',
            marker={
                'size': 5,
                'opacity': 0.5,
                'line': {'width': 0.5, 'color': 'white'}
            })
        traces.append(trace)

        # labeling the left_side of the plot
        annotations.append(dict(xref='x', x=last_value, y=math.log(y.iloc[-1])/math.log(10) if scale else y.iloc[-1],
                                xanchor='left', yanchor='middle',
                                text=label, 
                                font=dict(family='Arial', size=12),
                                showarrow=False))

    return {
        'data': traces,
        'layout': dict(
            title=title,
            yaxis={
                'title': 'cases',
                'type': 'log' if scale else 'linear',
                'fixedrange': True
            },
            xaxis={
                'title': 'date',
                'fixedrange': True
            },
            showlegend=False,
            margin={'l': 50, 'b': 50, 't': 50, 'r': 50},
            annotations=annotations,
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            font={'color': colors['text']}
        )
    }

if __name__ == '__main__':
            dash_app .run_server(debug=True, port='8000')