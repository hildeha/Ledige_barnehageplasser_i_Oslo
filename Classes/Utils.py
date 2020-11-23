import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz


class Utils:

    def assert_list(input):
        if isinstance(input, str):
            return [input]
        else:
            return input

    def column_names():
        return ['Barnehage', 'Link', 'Ledige småbarnsplasser', 'Ledige storbarnsplasser', 'Ledig fra']

    def rename_df_columns(df):
        columns = Utils.column_names()
        for column, new_columns in zip(df.columns, columns):
            df.rename(columns={column: new_columns}, inplace=True)
        return df

    def extract_data_from_table(table):

        df = pd.DataFrame()  # part df

        for row in table.find_all('tr'):
            table_row = []
            if len(row.find_all('td')) > 0:
                for x in row:
                    if len(re.findall('<a href="(.+?)/">', str(x))) > 0:
                        table_row.append(re.findall('/">(.+?)</a', str(x))[0])
                        table_row.append(re.findall('<a href="(.+?)/">', str(x))[0])
                    else:
                        if str(x)[4:-5] != '':
                            table_row.append(str(x)[4:-5])
            if len(table_row) == 5:
                df = df.append([table_row])
        Utils.rename_df_columns(df)

        return df

    def get_score_dataframe(table):

        df = pd.DataFrame()  # part df
        for row in table.find_all('tr'):
            table_row = []
            if len(row.find_all('td')) > 0:
                for x in row:
                    xlist = str(x).split('"row">')
                    if len(xlist) > 1:
                        table_row.append(xlist[1][:-5])
                    else:
                        table_row.append(xlist[0][4:-5])
            df = df.append([table_row])
        columns = []
        columns.extend(re.findall('class="osg-sr-only">(.+?)</span>', str(table)))
        columns.extend(re.findall('scope="col">(.+?)</th>', str(table))[1:])

        df.columns = columns[1:]
        return df.iloc[1:]

    def get_score_summary(d):

        df = pd.DataFrame()
        for key in d.keys():
            columns = ['Barnehage', 'År']
            columns.extend(d[key][d[key].columns[0]])
            values = [key, d[key].columns[1]]
            values.extend(list(d[key][d[key].columns[1]]))

            df = df.append(pd.DataFrame(data=[values], columns=columns))
        return df

    def get_lat_lons(dataframe):

        lats, lons = [], []
        for link in dataframe.Link:
            page = requests.get(link)
            soup = BeautifulSoup(page.content, 'html.parser')
            t = re.findall('46fe0cad-c520-42cf-8c34-204e8ad1da2f/static/(.+?),14/290x', str(soup))
            lons.append(t[0].split(',')[0])
            lats.append(t[0].split(',')[1])
        dataframe['Latitude'] = lats
        dataframe['Longitude'] = lons

        return dataframe

    def create_full_df(hage):

        dataframe = pd.DataFrame(columns=Utils.column_names())

        for table, bydel in zip(hage.tables, hage.bydeler):
            part_dataframe = Utils.extract_data_from_table(table)
            part_dataframe.index = [bydel] * len(part_dataframe)
            part_dataframe['Bydel'] = bydel.split('Ledige plasser i Bydel ')[1]
            dataframe['month'] = dataframe['Ledig fra'].apply(lambda x: Utils.match_month(x))
            dataframe['Småbarn'] = dataframe['Ledige småbarnsplasser'].apply(lambda x: int(x) > 0)
            dataframe['Storbarn'] = dataframe['Ledige storbarnsplasser'].apply(lambda x: int(x) > 0)
            dataframe = dataframe.append(part_dataframe)

        dataframe = Utils.get_lat_lons(dataframe)

        d = {}
        for link, name in zip(dataframe.Link, dataframe.Barnehage):
            p = requests.get(link)
            soup = BeautifulSoup(p.content, 'html.parser')
            tables = soup.find_all('table')
            for table in tables:
                d.update({name: Utils.get_score_dataframe(table)})

        foreldreundersokelse = Utils.get_score_summary(d)
        dataframe = dataframe.merge(foreldreundersokelse, left_on='Barnehage', right_on='Barnehage')

        for col in dataframe.columns[9:]:
            dataframe[col] = dataframe[col].apply(lambda x: x.replace(',', '.'))

        for col in dataframe.columns:
            try:
                dataframe[col] = pd.to_numeric(dataframe[col])
            except:
                pass
        dataframe['Total tilfredshet'] = dataframe['Total tilfredshet'].replace(np.nan, 0)

        return (dataframe, d)

    months = ['Januar',
              'Februar',
              'Mars',
              'April',
              'Mai',
              'Juni',
              'Juli',
              'August',
              'September',
              'Oktober',
              'November',
              'Desember']

    def match_month(month):
        match = 0
        return_month = ''
        for mo in Utils.months:
            if fuzz.ratio(mo, month) > match:
                match = fuzz.ratio(mo, month)
                return_month = mo

        return return_month

    def unique_months(barnehager):
        available = []
        for month in barnehager.dataframe['Ledig fra'].unique():
            available.append(Utils.match_month(month))
        return [x for x in Utils.months if x in set(available)]

    def get_barnehage_info(link):

        # get soup
        page = requests.get(link)
        soup = BeautifulSoup(page.content, 'html.parser')

        # informasjon
        informasjon = soup.findAll("div", {"class": "io-tile-common io-tile-preschool io-tile-preschool-information"})
        nokkelinfo = [x for x in re.findall('<li>(.+?)</li>', str(informasjon[0]))]

        # mat
        mat = soup.findAll("div", {"class": "io-tile-common io-tile-preschool io-tile-preschool-prices"})
        mat_overskrifter = re.findall('<h2>(.+?)</h2>', str(mat[0]))[:2]
        matpriser = [''.join(''.join(x.split('<strong>')).split('</strong>')) for x in
                     re.findall('<p>(.+?)</p>', str(mat[0]))[:2]]
        mat_beskrivelse = re.findall('<span>(.+?)</span>', str(mat[0]))[:2]

        # ledelse
        ledelse = soup.findAll("div",
                               {"class": "io-tile-common ioMultiContact toggle-xs-open toggle-md-disabled toggleable"})
        ledelse_info = re.findall('<h2>(.+?)</h2>', str(ledelse[0]))[:-1]
        leder = re.findall('<p>(.+?)</p>', str(ledelse[0]))[0]
        telefonnummer = re.findall('href="tel:(.+?)">', str(ledelse))[0]

        # apningstider
        apningstider = soup.findAll("div", {"class": "opening-hour-element-body"})
        apningstider_info = [re.findall('>(.+?)<', str(x))[0] + x.split('</span>')[1] for x in
                             re.findall('<li>(.+?)</li>', str(apningstider[0]))]

        # fridager
        fridager = soup.findAll("div", {"class": "io-tile-common io-tile-vacations"})
        fridager_header = re.findall('<h3>(.+?)</h3>', str(fridager[0]))[0]
        fridager_info = re.findall('<div>(.+?)</div>', str(fridager[0]))[0]

        # nettside
        nettside = soup.findAll("div", {"class": "io-tile-common io-preschool io-preschool-staff"})
        nettside_adresse = re.findall('<a href="(.+?)">Årsplan', str(nettside))[0]

        # build html
        html_text = '<h2>Nøkkelinformasjon:</h2><br>'

        for info in nokkelinfo:
            html_text = html_text + '{}<br>'.format(info)
        html_text = html_text + '<br>'

        html_text = html_text + '<h2>{}</h2><br>'.format(mat_overskrifter[0])
        for priser in matpriser:
            html_text = html_text + '{}<br>'.format(priser)
        html_text = html_text + '<br>'

        try:
            html_text = html_text + '<h2>{}</h2><br>'.format(mat_overskrifter[1])
            html_text = html_text + '{}<br>'.format(mat_beskrivelse[0])
            html_text = html_text + '<br>'
        except:
            pass

        html_text = html_text + '<h2>Åpningstider:</h2><br>'
        for apningstid in apningstider_info:
            html_text = html_text + '{}<br>'.format(apningstid)
        html_text = html_text + '<br>'


        html_text = html_text + '<h2>{}</h2><br>'.format('Barnehagens ledelse')
        html_text = html_text + 'Leder: {}<br>'.format(leder)
        html_text = html_text + 'Telefon: {}<br>'.format(telefonnummer)
        html_text = html_text + '<br>'


        return html_text, nettside_adresse