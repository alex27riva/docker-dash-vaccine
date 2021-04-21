#!/usr/bin/python3
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas

# data URL
consegne = 'https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/consegne-vaccini-latest.csv'
somministrazioni = 'https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/somministrazioni-vaccini-latest.csv'
fascia_anagrafica = 'https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/anagrafica-vaccini-summary-latest.csv'
decessicontagi = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv'

last_update = ''  # last update

plotly_js_minified = ['https://cdn.plot.ly/plotly-basic-latest.min.js']
app = dash.Dash(__name__, external_scripts=plotly_js_minified,
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=0.8, maximum-scale=1.2, minimum-scale=0.5'}])
app.title = 'Dashboard Vaccini'
server = app.server

# chart config
chart_config = {'displaylogo': False, 'displayModeBar': False, 'responsive': True}

# slider buttons (1m, 3m, 6m, all)
slider_button = list([
    dict(count=1,
         label="1m",
         step="month",
         stepmode="backward"),
    dict(count=3,
         label="3m",
         step="month",
         stepmode="backward"),
    dict(count=6,
         label="6m",
         step="month",
         stepmode="backward"),
    dict(step="all")
])

# refresh data
def refresh_data():
    global today
    global dc, ds, dfa, ddc, ds_dosi
    global tot_prima_dose, tot_seconda_dose, tot_prima, tot_seconda
    # read csv for url and get date
    dc = pandas.read_csv(consegne)
    ds = pandas.read_csv(somministrazioni)
    dfa = pandas.read_csv(fascia_anagrafica)
    ddc = pandas.read_csv(decessicontagi)
    today = date.today()

    # doses delivered
    dc = dc.groupby('data_consegna').agg({'numero_dosi': 'sum'}).reset_index()

    # doses administered
    ds_dosi = ds.groupby('data_somministrazione').agg({'prima_dose': 'sum', 'seconda_dose': 'sum', 'categoria_operatori_sanitari_sociosanitari': 'sum', 'categoria_personale_non_sanitario': 'sum', 'categoria_ospiti_rsa': 'sum', 'categoria_over80': 'sum', 'categoria_forze_armate': 'sum', 'categoria_personale_scolastico': 'sum', 'categoria_altro': 'sum'}).reset_index()
    # first dose from the start
    tot_prima = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['prima_dose']].sum()
    tot_prima_dose = '{:,}'.format(int(tot_prima)).replace(',', '.')
    # second dose from the start
    tot_seconda = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['seconda_dose']].sum()
    tot_seconda_dose = '{:,}'.format(int(tot_seconda)).replace(',', '.')

    # deaths
    ddc['nuovi_decessi'] = ddc.deceduti.diff().fillna(ddc.deceduti)

# total vaccine status
def vaccine_update():
    refresh_data()
    # update day for later
    global last_update
    ds_prime_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'prima_dose']
    if len(ds_prime_dosi) == 0:
        last_update = date.today()
    else:
        last_update = date.today() - timedelta(days=1)

    # percentage
    primadose = round((int(tot_prima)/60360000)*100, 2)
    secondadose = round((int(tot_seconda)/60360000)*100, 2)
    return html.Div([
        html.Div(
            html.Table([
                # Header
                html.Tr([
                    html.Td('Prima dose', style={'font-size': '14px'}), html.Td('Persone Vaccinate', style={'font-size': '14px'})
                ])
            ]+[
                # Body
                html.Tr([
                    html.Td(
                        html.H1(tot_prima_dose, style={'color': '#F5C05F', 'font-size': '45px'})
                    ),
                    html.Td(
                        html.H1(tot_seconda_dose, style={'color': '#E83A8E', 'font-size': '45px'})
                    )
                ]),
                # Percentage
                html.Tr([
                    html.Td(html.B(
                        ''+str(primadose)+'% della popolazione', style={'color': '#F5C05F', 'font-size': '14px'}
                    )),
                    html.Td(html.B(
                        ''+str(secondadose)+'% della popolazione', style={'color': '#E83A8E', 'font-size': '14px'}
                    ))
                ])
            ], id='vaccine_table')
        )
    ])

# vaccine horozzonatal bar
def vaccine_update_bar():
    refresh_data()
    return html.Div([
        dcc.Graph(
            figure={
                'data': [go.Bar(x=[60360000, int(tot_prima), int(tot_seconda)],
                                y=['Popolazione', 'Prima dose', 'Vaccinati'],
                                orientation='h',
                                marker_color=['#6181E8', '#F5C05F', '#E83A8E'])
                         ],
                'layout': {
                    'height': 240,  # px
                    'xaxis': dict(
                        rangeslider=dict(visible=False),
                        type=''
                    )
                },
            },
            config=chart_config
        )
    ], id='vaccine_bar')

# daily vaccine
def vaccine_daily():
    refresh_data()
    # total data
    tot_consegne = dc.loc[dc['data_consegna'].between('2020-12-27', str(today)), ['numero_dosi']].sum()
    tot_consegne = '{:,}'.format(int(tot_consegne)).replace(',', '.')
    tot_vaccini = int(tot_prima) + int(tot_seconda)
    tot_vaccini = '{:,}'.format(int(tot_vaccini)).replace(',', '.')

    # today data
    dc_dosi_consegnate = dc.loc[dc['data_consegna'] == str(today), 'numero_dosi']
    ds_dosi_totali = 0
    ds_prime_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'prima_dose']
    ds_seconde_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'seconda_dose']

    # check today data
    if len(dc_dosi_consegnate) == 0 and len(ds_prime_dosi) == 0 and len(ds_seconde_dosi) == 0:
        dc_dosi_consegnate = dc.loc[dc['data_consegna'] == str(date.today() - timedelta(days=1)), 'numero_dosi']
        ds_prime_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'prima_dose']
        ds_seconde_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'seconda_dose']

    # formatting data
    if len(dc_dosi_consegnate) == 0:
        dc_dosi_consegnate = 0
    else:
        dc_dosi_consegnate = '{:,}'.format(int(dc_dosi_consegnate)).replace(',', '.')
    if len(ds_prime_dosi) == 0:
        ds_prime_dosi = 0
        ds_dosi_totali = int(ds_prime_dosi)
    else:
        ds_dosi_totali = int(ds_prime_dosi)
        ds_prime_dosi = '{:,}'.format(int(ds_prime_dosi)).replace(',', '.')
    if len(ds_seconde_dosi) == 0:
        ds_seconde_dosi = 0
        ds_dosi_totali = ds_dosi_totali + int(ds_seconde_dosi)
    else:
        ds_dosi_totali = ds_dosi_totali + int(ds_seconde_dosi)
        ds_seconde_dosi = '{:,}'.format(int(ds_seconde_dosi)).replace(',', '.')

    if ds_dosi_totali != 0:
        ds_dosi_totali = '{:,}'.format(int(ds_dosi_totali)).replace(',', '.')

    return html.Div([
        html.Div(
            html.Table([
                # Header
                html.Tr([
                    html.Td('Vaccini Consegnati', style={'font-size': '14px'}),
                    html.Td('Dosi Somministrate', style={'font-size': '14px'}),
                    html.Td('Prime Dosi', style={'font-size': '14px'}),
                    html.Td('Persone Vaccinate', style={'font-size': '14px'})
                ])
            ]+[
                # Body
                html.Tr([
                    html.Td(
                        html.H1('+ '+str(dc_dosi_consegnate)+'', style={'color': '#29CF8A', 'font-size': '45px'})
                    ),
                    html.Td(
                        html.H1('+ '+str(ds_dosi_totali)+'', style={'color': '#376FDB', 'font-size': '45px'})
                    ),
                    html.Td(
                        html.H1('+ '+str(ds_prime_dosi)+'', style={'color': '#F5C05F', 'font-size': '45px'})
                    ),
                    html.Td(
                        html.H1('+ '+str(ds_seconde_dosi)+'', style={'color': '#E83A8E', 'font-size': '45px'})
                    )
                ]),
                # Yesterday
                html.Tr([
                    html.Td(html.B(
                        'Totali: '+str(tot_consegne), style={'color': '#29CF8A', 'font-size': '14px'}
                    )),
                    html.Td(html.B(
                        'Totali: '+str(tot_vaccini), style={'color': '#376FDB', 'font-size': '14px'}
                    )),
                    html.Td(html.B(
                        'Totali: ' + str(tot_prima_dose), style={'color': '#F5C05F', 'font-size': '14px'}
                    )),
                    html.Td(html.B(
                        'Totali: ' + str(tot_seconda_dose), style={'color': '#E83A8E', 'font-size': '14px'}
                    ))
                ])
            ], id='vaccine_table_daily')
        )
    ])

def vaccine_and_dosi_graph():
    refresh_data()
    # vaccine
    ds_pfizer = ds.loc[ds['fornitore'] == 'Pfizer/BioNTech'].groupby('data_somministrazione').agg(
        {'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
    ds_moderna = ds.loc[ds['fornitore'] == 'Moderna'].groupby('data_somministrazione').agg(
        {'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
    ds_astra = ds.loc[ds['fornitore'] == 'Vaxzevria (AstraZeneca)'].groupby('data_somministrazione').agg(
        {'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
    ds_janssen = ds.loc[ds['fornitore'] == 'Janssen'].groupby('data_somministrazione').agg(
        {'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
    return html.Div([
        html.Div(
            html.Table([
                html.Tr([
                    html.Td(
                        dbc.Container([
                            dbc.Row(
                                dbc.Col(
                                    dcc.Graph(
                                        figure={
                                            'data': [
                                                {'x': ds_pfizer['data_somministrazione'],
                                                 'y': ds_pfizer['prima_dose'] + ds_pfizer['seconda_dose'],
                                                 'type': 'bar',
                                                 'name': 'Pfizer',
                                                 'marker': dict(color='#95A9DE')},
                                                {'x': ds_moderna['data_somministrazione'],
                                                 'y': ds_moderna['prima_dose'] + ds_moderna['seconda_dose'],
                                                 'type': 'bar',
                                                 'name': 'Moderna',
                                                 'marker': dict(color='#395499')},
                                                {'x': ds_astra['data_somministrazione'],
                                                 'y': ds_astra['prima_dose'] + ds_astra['seconda_dose'], 'type': 'bar',
                                                 'name': 'AstraZeneca',
                                                 'marker': dict(color='#537BE0')},
                                                {'x': ds_janssen['data_somministrazione'],
                                                 'y': ds_janssen['prima_dose'] + ds_janssen['seconda_dose'],
                                                 'type': 'bar',
                                                 'name': 'Janssen',
                                                 'marker': dict(color='#243561')},
                                            ],
                                            'layout': {
                                                'barmode': 'stack',
                                                'xaxis': dict(
                                                    rangeselector=dict(buttons=slider_button),
                                                    rangeslider=dict(visible=False),
                                                    type='date'
                                                )
                                            }
                                        },
                                        config=chart_config
                                    )
                                )
                            )
                        ])
                    ),
                    # sencond table
                    html.Td(
                        dbc.Container([
                            dbc.Row(
                                dbc.Col(
                                    dcc.Graph(
                                        figure={
                                            'data': [
                                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['prima_dose'],
                                                 'type': 'bar',
                                                 'name': 'Prima Dose',
                                                 'marker': dict(color='#F5C05F')},
                                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['seconda_dose'],
                                                 'type': 'bar',
                                                 'name': 'Seconda Dose',
                                                 'marker': dict(color='#78F5B3')},
                                            ],
                                            'layout': {
                                                'barmode': 'stack',
                                                'xaxis': dict(
                                                    rangeselector=dict(buttons=slider_button),
                                                    rangeslider=dict(visible=False),
                                                    type='date'
                                                )
                                            }
                                        },
                                        config=chart_config
                                    )
                                )
                            )
                        ])
                    )
                ])
            ], id='vaccine_dose_graph')
        )
    ])

# category
def category():
    refresh_data()
    # total data
    # sanitari
    tot_sanitario = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_operatori_sanitari_sociosanitari']].sum()
    tot_sanitario = '{:,}'.format(int(tot_sanitario)).replace(',', '.')
    # non sanitari
    tot_non_sanitario = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_personale_non_sanitario']].sum()
    tot_non_sanitario = '{:,}'.format(int(tot_non_sanitario)).replace(',', '.')
    # rsa
    tot_rsa = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_ospiti_rsa']].sum()
    tot_rsa = '{:,}'.format(int(tot_rsa)).replace(',', '.')
    # over 80
    tot_over80 = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_over80']].sum()
    tot_over80 = '{:,}'.format(int(tot_over80)).replace(',', '.')
    # forze armate
    tot_forze_armate = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_forze_armate']].sum()
    tot_forze_armate = '{:,}'.format(int(tot_forze_armate)).replace(',', '.')
    # scuola
    tot_scuola = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_personale_scolastico']].sum()
    tot_scuola = '{:,}'.format(int(tot_scuola)).replace(',', '.')
    # altro
    tot_altro = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_altro']].sum()
    tot_altro = '{:,}'.format(int(tot_altro)).replace(',', '.')

    # today data
    sanitario = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_operatori_sanitari_sociosanitari']
    non_sanitario = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_personale_non_sanitario']
    rsa = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_ospiti_rsa']
    over80 = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_over80']
    forze_armate = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_forze_armate']
    scuola = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_personale_scolastico']
    altro = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_altro']

    # check today data
    if len(sanitario) == 0 and len(non_sanitario) == 0 and len(rsa) == 0 and len(over80) == 0 and len(forze_armate) == 0 and len(scuola) == 0 and len(altro) == 0:
        sanitario = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_operatori_sanitari_sociosanitari']
        non_sanitario = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_personale_non_sanitario']
        rsa = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_ospiti_rsa']
        over80 = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_over80']
        forze_armate = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_forze_armate']
        scuola = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_personale_scolastico']
        altro = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_altro']

    # formatting data
    if len(sanitario) == 0:
        sanitario = 0
    else:
        sanitario = '{:,}'.format(int(sanitario)).replace(',', '.')
    if len(non_sanitario) == 0:
        non_sanitario = 0
    else:
        non_sanitario = '{:,}'.format(int(non_sanitario)).replace(',', '.')
    if len(rsa) == 0:
        rsa = 0
    else:
        rsa = '{:,}'.format(int(rsa)).replace(',', '.')
    if len(over80) == 0:
        over80 = 0
    else:
        over80 = '{:,}'.format(int(over80)).replace(',', '.')
    if len(forze_armate) == 0:
        forze_armate = 0
    else:
        forze_armate = '{:,}'.format(int(forze_armate)).replace(',', '.')
    if len(scuola) == 0:
        scuola = 0
    else:
        scuola = '{:,}'.format(int(scuola)).replace(',', '.')
    if len(altro) == 0:
        altro = 0
    else:
        altro = '{:,}'.format(int(altro)).replace(',', '.')

    return html.Div([
        html.Div(children=[
            html.Table([
                # Header
                html.Tr([
                    html.Td('Operatori Sanitari', style={'font-size': '14px'}),
                    html.Td('Operatori non Sanitari', style={'font-size': '14px'}),
                    html.Td('RSA', style={'font-size': '14px'}),
                    html.Td('Over 80', style={'font-size': '14px'})
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(sanitario) + '', style={'color': '#FF4272', 'font-size': '45px'})
                    ),
                    html.Td(
                        html.H1('+ ' + str(non_sanitario) + '', style={'color': '#F2665C', 'font-size': '45px'})
                    ),
                    html.Td(
                        html.H1('+ ' + str(rsa) + '', style={'color': '#DBAF48', 'font-size': '45px'})
                    ),
                    html.Td(
                        html.H1('+ ' + str(over80) + '', style={'color': '#50DE8B', 'font-size': '45px'})
                    )
                ]),
                # Total
                html.Tr([
                    html.Td(html.B(
                        'Totali: ' + str(tot_sanitario), style={'color': '#FF4272', 'font-size': '14px'}
                    )),
                    html.Td(html.B(
                        'Totali: ' + str(tot_non_sanitario), style={'color': '#F2665C', 'font-size': '14px'}
                    )),
                    html.Td(html.B(
                        'Totali: ' + str(tot_rsa), style={'color': '#DBAF48', 'font-size': '14px'}
                    )),
                    html.Td(html.B(
                        'Totali: ' + str(tot_over80), style={'color': '#50DE8B', 'font-size': '14px'}
                    ))
                ]),
            ], id='vaccine_category0'),
            html.Br(),
            # second row
            html.Table([
                html.Tr([
                    html.Td('Forze Armate', style={'font-size': '14px'}),
                    html.Td('Personale Scolastico', style={'font-size': '14px'}),
                    html.Td('Altro', style={'font-size': '14px'})
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(forze_armate) + '', style={'color': '#4B8CDE', 'font-size': '45px'})
                    ),
                    html.Td(
                        html.H1('+ ' + str(scuola) + '', style={'color': '#68D8DE', 'font-size': '45px'})
                    ),
                    html.Td(
                        html.H1('+ ' + str(altro) + '', style={'color': '#844BDB', 'font-size': '45px'})
                    )
                ]),
                # Total
                html.Tr([
                    html.Td(html.B(
                        'Totali: ' + str(tot_forze_armate), style={'color': '#4B8CDE', 'font-size': '14px'}
                    )),
                    html.Td(html.B(
                        'Totali: ' + str(tot_scuola), style={'color': '#68D8DE', 'font-size': '14px'}
                    )),
                    html.Td(html.B(
                        'Totali: ' + str(tot_altro), style={'color': '#844BDB', 'font-size': '14px'}
                    ))
                ])
            ], id='vaccine_category1')
        ])
    ])

# graph tot category
def category_global():
    refresh_data()
    return html.Div(  # main div
        dbc.Container([
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        figure={
                            'data': [
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_operatori_sanitari_sociosanitari'],
                                 'type': 'bar',
                                 'name': 'Operatori Sanitari',
                                 'marker': dict(color='#FF4272')},
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_personale_non_sanitario'],
                                 'type': 'bar',
                                 'name': 'Operatori non Sanitari',
                                 'marker': dict(color='#F2665C')},
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_ospiti_rsa'],
                                 'type': 'bar',
                                 'name': 'RSA',
                                 'marker': dict(color='#DBAF48')},
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_over80'],
                                 'type': 'bar',
                                 'name': 'Over 80',
                                 'marker': dict(color='#50DE8B')},
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_forze_armate'],
                                 'type': 'bar',
                                 'name': 'Forze Armate',
                                 'marker': dict(color='#4B8CDE')},
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_personale_scolastico'],
                                 'type': 'bar',
                                 'name': 'Personale Scolastico',
                                 'marker': dict(color='#68D8DE')},
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_altro'],
                                 'type': 'bar',
                                 'name': 'Altro',
                                 'marker': dict(color='#844BDB')},
                            ],
                            'layout': {
                                'barmode': 'stack', # stack data
                                'xaxis': dict(
                                    rangeselector=dict(buttons=slider_button),
                                    rangeslider=dict(visible=False),
                                    type='date'
                                )
                            }
                        },
                        config=chart_config
                    )
                )
            )
        ])
    )

# age
def vaccine_age_bar():
    refresh_data()
    return html.Div([
        dcc.Graph(
            figure={
                'data': [go.Bar(x=[dfa['totale'][0], dfa['totale'][1], dfa['totale'][2], dfa['totale'][3], dfa['totale'][4], dfa['totale'][5], dfa['totale'][6], dfa['totale'][7], dfa['totale'][8]],
                                y=['16-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90+'],
                                orientation='h',
                                marker_color=['#DEB1FA', '#D298FA', '#CD85F9', '#C670F9', '#BF53FB', '#A93AE0', '#832DAD', '#491961']
                                )
                         ],
                'layout': {
                    'height': 340,  # px
                    'xaxis': dict(
                        rangeslider=dict(visible=False),
                        type=''
                    )
                },
            },
            config=chart_config
        )
    ], id='vaccine_age_bar')

# forecast
def previsione():
    refresh_data()
    date_format = "%Y-%m-%d" # date format
    inizio = datetime.strptime('2020-12-27', date_format)
    ora = datetime.strptime(str(today), date_format)

    # best day
    l = len(ds_dosi['data_somministrazione'])  # total vaccine day
    i = 0
    max = 0  # best day
    for i in range(l):
        if ds_dosi['prima_dose'][i] > max:
            max = ds_dosi['prima_dose'][i]
    best_day = ((60360000 - int(tot_prima)) / max) - l
    best_last_day = str(ora + timedelta(days=best_day))[:10]

    # month
    month_prima = ds_dosi.loc[ds_dosi['data_somministrazione'].between(str(ora-relativedelta(months=1))[:10], str(ora)[:10]), ['prima_dose']].sum()
    month_day_passati = (ora - (ora-relativedelta(months=1))).days
    month_day = (60360000 / int(month_prima)) * month_day_passati
    month_last_day = str(ora + timedelta(days=month_day))[:10]

    return html.Div(  # main div
        dbc.Container([
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        figure={
                            'data': [
                                {'x': ds_dosi['data_somministrazione'], 'y': (ds_dosi['prima_dose'].cumsum())/60360000, 'type': 'bar', 'name': 'Incremento Prime Dosi'},
                                go.Scatter(x=[ds_dosi['data_somministrazione'][0], '2021-10-30'],
                                           y=[0, 1],
                                           mode='lines',
                                           name='Previsione del Governo',
                                           line=go.scatter.Line(color="#FA5541")),
                                go.Scatter(x=[ds_dosi['data_somministrazione'][l-1], month_last_day],
                                           y=[int(tot_prima)/60360000, 1],
                                           mode='lines',
                                           name='Previsione Mensile',
                                           line=go.scatter.Line(color="#FA924E")),
                                go.Scatter(x=[ds_dosi['data_somministrazione'][l-1], best_last_day],
                                           y=[int(tot_prima)/60360000, 1],
                                           mode='lines',
                                           name='Previsione Migliore*',
                                           line=go.scatter.Line(color="#FAC35A"))
                            ],
                            'layout': {
                                'xaxis': dict(
                                    rangeslider=dict(visible=False),
                                    type='date'
                                ),
                                'yaxis': dict(
                                    tickformat=',.0%',  # percentage on y axis
                                    range=[0, 1]
                                )
                            }
                        },
                        config=chart_config
                    )
                )
            )
        ])
    )

# effect
def effetti_decessi_contagi_graph():
    refresh_data()
    return html.Div([
        html.Div(
            html.Table([
                html.Tr([
                    html.Td(
                        dbc.Container([
                            dbc.Row(
                                dbc.Col(
                                    dcc.Graph(
                                        figure={
                                            'data': [
                                                {'x': ddc['data'], 'y': ddc['nuovi_positivi'], 'type': 'bar', 'name': 'Nuovi Positivi',
                                                 'marker': dict(color='#D9615D')},
                                                # line start vaccine
                                                go.Scatter(x=['2020-12-27', '2020-12-27'],
                                                           y=[0, 40000],
                                                           mode='lines',
                                                           name='Inizio Vaccini',
                                                           hoverinfo='none',
                                                           line=go.scatter.Line(color="#4F4747"))
                                            ],
                                            'layout': {
                                                'xaxis': dict(
                                                    rangeselector=dict(buttons=slider_button),
                                                    rangeslider=dict(visible=False),
                                                    type='date'
                                                )
                                            }
                                        },
                                        config=chart_config
                                    )
                                )
                            )
                        ])
                    ),
                    html.Td(
                        dbc.Container([
                            dbc.Row(
                                dbc.Col(
                                    dcc.Graph(
                                        figure={
                                            'data': [
                                                {'x': ddc['data'], 'y': ddc['nuovi_decessi'], 'type': 'bar', 'name': 'Decessi',
                                                 'marker': dict(color='#756B6B')},
                                                # line start vaccine
                                                go.Scatter(x=['2020-12-27', '2020-12-27'],
                                                           y=[0, 1000],
                                                           mode='lines',
                                                           name='Inizio Vaccini',
                                                           hoverinfo='none',
                                                           line=go.scatter.Line(color="#1F1C1C"))
                                            ],
                                            'layout': {
                                                'xaxis': dict(
                                                    rangeselector=dict(buttons=slider_button),
                                                    rangeslider=dict(visible=False),
                                                    type='date'
                                                ),
                                            }
                                        },
                                        config=chart_config
                                    )
                                )
                            )
                        ])
                    )
                ])
            ], id='effect_graph')
        )
    ])

app.layout = html.Div([
    html.Div([vaccine_update()]),
    html.Div([vaccine_update_bar()]),
    html.Div(html.Center(html.I([html.Br(), "L'obiettivo della campagna di vaccinazione della popolazione è prevenire le morti da COVID-19 e raggiungere al più presto l'immunità di gregge per il SARS-CoV2.", html.Br(), "La campagna è partita il ", html.B("27 dicembre"), ", vista l'approvazione da parte dell'EMA (European Medicines Agency) del primo vaccino anti COVID-19.", html.Br(), "Dopo una fase iniziale, che dovrà essere limitata, per il numero di dosi consegnate, essa si svilupperà in continuo crescendo.", html.Br(), "I vaccini saranno offerti a tutta la popolazione, secondo un ordine di priorità, che tiene conto del rischio di malattia, dei tipi di vaccino e della loro disponibilità."], style={'font-size': 'large'}))),
    html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H1('Dati del Giorno')), html.Center(html.I('dati aggionati del '+str(last_update), style={'font-size': '14px'})), html.Br(), html.Br()]),
    html.Div([vaccine_daily()]),
    html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H2('Vaccini & Dosi'))]),
    html.Div([vaccine_and_dosi_graph()]),
    html.Div([html.Br(), html.Center(html.H2('Categorie')), html.Br(), html.Br()]),
    html.Div([category()]),
    html.Div([category_global()]),
    html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H2('Vaccini per fascia di età'))]),
    html.Div([vaccine_age_bar()]),
    html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H1('Previsioni')), html.Center(html.I('Il modello utilizza i dati giornalieri sulle somministrazioni delle prime dosi', style={'font-size': '14px'})), html.Center(html.I('*Media basata sul valore massimo di prime dosi fatte in un giorno', style={'font-size': '14px'}))]),
    html.Div([previsione()]),
    html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H2('Effetti dei Vaccini nel Tempo'))]),
    html.Div([effetti_decessi_contagi_graph()])
])

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
