import os
from datetime import datetime, timedelta
import platform
import pandas as pd
import numpy as np
from datetime import datetime as dt
import pickle

class DataReader():
    data = None

    def __init__(self):
        if os.path.exists("data.pickle"):
            file_time = datetime.fromtimestamp(os.path.getmtime("data.pickle"))
            last_update = datetime.now()
            #update always at 20 oclock
            if last_update.hour < 20:
                last_update = datetime(last_update.year, last_update.month, last_update.day, 20, 0, 0, 0)-timedelta(1)
            else:
                last_update = datetime(last_update.year, last_update.month, last_update.day, 20, 0, 0, 0)

            if file_time > last_update :
                self.data = pickle.load(open("data.pickle", "rb"))
            else:
                self.create_pickle()
        else:
            self.create_pickle()

    def create_pickle(self):
        df_global = self.covid_df('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
        #df_global.to_clipboard()

        df_global_death = self.covid_df('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv', case = 'deceased cases')
        #df_global_death.to_clipboard()
        df_global = pd.merge(df_global, df_global_death[['Region','Country','Date','deceased cases']], how='left', on=['Region','Country','Date'])

        df_global_recovered = self.covid_df('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv', case = 'recovered cases')
        #df_global_recovered.to_clipboard()
        df_global = pd.merge(df_global, df_global_recovered[['Region','Country','Date','recovered cases']], how='left', on=['Region','Country','Date'])

        df_global['active cases'] = df_global['confirmed cases'] - df_global['deceased cases'] - df_global['recovered cases']

        #df_us = self.covid_df('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv', us=True)
        #df_us_death = self.covid_df('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv', us=True, confirmed=False)
        #df_us['deceased cases'] = df_us_death['deceased cases']
        #df = df_global.append(df_us, ignore_index=True)

        #Country,Population,Change,Change,Density,Land Area,Migrants,FertRate,MedAge,UrbanPop,WorldShare
        df_pop = pd.read_csv('pop.csv', error_bad_lines=False)
        df_global = pd.merge(df_global, df_pop[['Country','Population']], how='left', on=['Country'])

        df_global["count"]='absolute'

        df_rel = df_global.copy()
        df_rel["count"]='relative'
        df_rel["confirmed cases"]=df_rel["confirmed cases"]/(df_rel["Population"]/1000000)
        df_rel["deceased cases"]=df_rel["deceased cases"]/(df_rel["Population"]/1000000)
        df_rel["recovered cases"]=df_rel["recovered cases"]/(df_rel["Population"]/1000000)
        df_rel["active cases"]=df_rel["active cases"]/(df_rel["Population"]/1000000)

        df_global = df_global.append(df_rel)

        df = df_global

        self.data = df

        pickle.dump(self.data, open("data.pickle", "wb"))

    def covid_df(self, url, us = False, case = 'confirmed cases'):
        df = pd.read_csv(url, error_bad_lines=False)
        if(not us):
            df = pd.melt(df, id_vars=["Province/State","Country/Region","Lat","Long"])
            df = df.rename(columns={'Province/State': 'Region'})
            df = df.rename(columns={'Country/Region': 'Country'})
            df = df.rename(columns={'variable': 'Date'})
            df.loc[df['Country']=='Korea, South','Country'] = 'South Korea' #exception
            df['Region'].fillna('Total', inplace=True)
        else:
            df.drop(['UID','iso2','iso3','code3','FIPS','Combined_Key','Population'], axis=1, inplace=True, errors='ignore')
            df = pd.melt(df, id_vars=["Province_State","Country_Region","Lat","Long_","Admin2"])
            df = df.rename(columns={'Province_State': 'Region'})
            df = df.rename(columns={'Country_Region': 'Country'})
            df = df.rename(columns={'Long_': 'Long'})
            df = df.rename(columns={'variable': 'Date'})
            df.groupby(["Region","Country","Date"]).agg(
                value   =pd.NamedAgg(column='value', aggfunc='sum'),
                Long    =pd.NamedAgg(column="Long", aggfunc=lambda x: (max(x) - min(x))/2),
                Lat     =pd.NamedAgg(column="Lat", aggfunc=lambda x: (max(x) - min(x))/2)
            ).reset_index()
            df = df[['Region', 'Country', 'Lat', 'Long', 'Date','value']]
        
        df['Date'] = pd.to_datetime(df['Date'], format = "%m/%d/%y")
        
        list_tobetotaled = []
        for item in df['Country'].unique():
            if item not in df[df['Region'] == 'Total']['Country'].unique().tolist():
                list_tobetotaled.append(item)

        for label in list_tobetotaled:
            totals = df[df["Country"]==label].groupby(['Date']).agg(
                value   =pd.NamedAgg(column='value', aggfunc='sum'),
                Long    =pd.NamedAgg(column="Long", aggfunc=lambda x: (max(x) - min(x))/2),
                Lat     =pd.NamedAgg(column="Lat", aggfunc=lambda x: (max(x) - min(x))/2)
            ).reset_index()
            totals['Region'] = 'Total'
            totals['Country'] = label
            totals = totals[['Region', 'Country', 'Lat', 'Long', 'Date','value']]
            df = df.append(totals, ignore_index=True)

        df = df.rename(columns={'value': case})
        
        return df

    


