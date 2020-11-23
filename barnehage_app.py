import streamlit as st
import datetime
import plotly.express as px
import numpy as np

from Classes.Utils import Utils
from Classes.Barnehager import Barnehager

def main():

    st.markdown('<h1>Ledige barnehageplasser Oslo kommune</h1>', unsafe_allow_html=True)

    st.markdown('<br><br>Dette verktøyet er laget for å gi en oversikt over, de til enhver tid, '
                'ledige barnehageplassene '
                'i Oslo kommune<br><br>Bruk menyen til venstre for å sortere på ønsket bydel, oppstartsmåned, småbarn- '
                'eller storbarnsavdeling og resultat i foreldreundersøkelsen.', unsafe_allow_html=True)

    today = datetime.datetime.now().date()

    @st.cache(allow_output_mutation=True)
    def get_data(link, update=today):
        barnehager = Barnehager(link)
        updated = datetime.datetime.now().date()
        return barnehager, updated

    link = 'https://www.oslo.kommune.no/barnehage/ledige-barnehageplasser/#gref'

    barnehager, updated = get_data(link, update=today)


    upd = st.sidebar.button('Force update')
    if upd:
        force_update = np.random.randint(10000)
        barnehager, updated = get_data(link, update=force_update)

    st.sidebar.markdown('<span style="color:darkblue"><i>Last updated {}</i></span>'.format(str(updated)),
                        unsafe_allow_html=True)


    #Filter plot data

    st.sidebar.markdown('<br><br>', unsafe_allow_html=True)
    st.sidebar.markdown('<h2>Filtrer data:</h2>', unsafe_allow_html=True)

    bydeler = st.sidebar.multiselect(label='Velg bydel(er)', options=[''] + list(barnehager.dataframe.Bydel.sort_values(
    ).unique()))
    oppstart = st.sidebar.multiselect(label='Velg oppstartstidspunkt(er)', options=[''] + Utils.unique_months(
        barnehager))
    alder = st.sidebar.multiselect(label='Avdeling', options=['','Småbarn','Storbarn'])
    fundersokelse = st.sidebar.slider(label='Resultat foreldreundersøkelse',
                                       max_value=barnehager.dataframe['Total tilfredshet'].max(),
                                       min_value=barnehager.dataframe['Total tilfredshet'].min(),
                                       value=barnehager.dataframe['Total tilfredshet'].min())




    if bydeler != []:
        filter_bydel = Utils.assert_list(bydeler)
    else:
        filter_bydel = list(barnehager.dataframe.Bydel.sort_values().unique())

    if oppstart != []:
        filter_oppstart = Utils.assert_list(oppstart)
    else:
        filter_oppstart = list(barnehager.dataframe.month.unique())

    if alder != []:
        filter_alder = Utils.assert_list(alder)
    else:
        filter_alder = ['Ledige småbarnsplasser','Ledige storbarnsplasser']


    #filter data
    filtered_1 = barnehager.dataframe.loc[(barnehager.dataframe.Bydel.isin(filter_bydel)) &
                                              (barnehager.dataframe['Ledig fra'].isin(filter_oppstart)) &
                                              (barnehager.dataframe['Total tilfredshet'] >= fundersokelse)]
    if len(filter_alder) == 1:
        filtered_data = filtered_1.loc[filtered_1[filter_alder[0]] > 0]
    else:
        filtered_data = filtered_1


    fig = px.scatter_mapbox(filtered_data, lat="Latitude", lon="Longitude", hover_name="Barnehage",
                            hover_data=['Ledige småbarnsplasser', 'Ledige storbarnsplasser', 'Ledig fra', 'År',
                                        'Svarprosent', 'Total tilfredshet','Ute- og innemiljø',
                                        'Barnets trivsel', 'Informasjon', 'Barnets utvikling'],
                            zoom=9, color='Total tilfredshet', color_discrete_sequence=["redblue"],
                            size=np.ones(len(filtered_data))*0.5,
                            color_continuous_scale=['#FF1493', '#483D8B'])
    fig.update_layout(mapbox_style="stamen-terrain", width=700)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(filtered_data[['Barnehage', 'Bydel', 'Ledige småbarnsplasser',
                                'Ledige storbarnsplasser', 'Ledig fra']].rename(columns={
                                                            'Ledige småbarnsplasser':'Ledig småbarn',
                                                            'Ledige storbarnsplasser':'Ledig storbarn'}))


    st.markdown('<br><br>', unsafe_allow_html=True)

    select_dict = filtered_data[['Barnehage','Link']].set_index('Barnehage').to_dict()
    selected = st.selectbox('Velg barnehage for mer info og hjemmeside', options=list(filtered_data.Barnehage))
    if selected in list(filtered_data.Barnehage):
        st.markdown('<h1><br>{}</h1><br>'.format(selected), unsafe_allow_html=True)
        st.markdown('<h2>Link til nettside</h2><br>', unsafe_allow_html=True)
        st.markdown(select_dict['Link'][selected])
        st.markdown('')
        st.markdown('<h2>Resultater fra foreldreundersøkelsen</h2>', unsafe_allow_html=True)
        st.markdown('', unsafe_allow_html=True)

        st.dataframe(barnehager.data[1][selected])
        st.markdown('<br><br>', unsafe_allow_html=True)

        text, nettside = Utils.get_barnehage_info(select_dict['Link'][selected])
        print(text)
        st.markdown(text, unsafe_allow_html=True)

    st.markdown('<br><br>', unsafe_allow_html=True)
    st.markdown('---', unsafe_allow_html=True)
    st.markdown('<i>Denne webappen er skrevet av Hilde Tveit Håland i november 2020, kode er tilgjengelig på'
                '<a href=https://github.com/hildeha/Ledige_barnehageplasser_i_Oslo> Github</a>. Appen er '
                'hosted med Streamlit for Teams.</i>', unsafe_allow_html=True)
    st.markdown('<i>All data er hentet fra https://www.oslo.kommune.no/barnehage/ledige-barnehageplasser/#gref '
                '</i>', unsafe_allow_html=True)
if __name__ == "__main__":
    main()