import streamlit as st
import plotly.express as px
import pandas as pd
#import pdfkit
#import base64
#from io import BytesIO

#Seiteneinstellungen
st.set_page_config(page_title="Datev Auswertung", page_icon=':bar_chart:', layout='wide')

#Uploadmöglichkeit initialisieren
uploaded_file = st.sidebar.file_uploader("Bitte Datei hochladen", type=['xlsx'])

def replace_comma(s):
    if isinstance(s, str):
        return s.replace(',', '.')
    else:
        return s

#Upload der Datei
if uploaded_file is not None:
    df = pd.read_excel(
        io=uploaded_file,
        engine="openpyxl",
        skiprows=1,
        usecols="A:C,G:H,J,N,BG",
    )
    #bearbieten der Datei für die weiterverwendung
    df.columns.values[0] = 'Umsatz'
    df.columns.values[4] = 'Gegenkonto'
    df.columns.values[7] = 'Steuersatz'
   #df.columns.values[3] = ''
   # df.columns.values[4] = ''
   # df.columns.values[5] = ''
   # df = df.rename(columns={"Gegenkonto (ohne BU-Schlssel)": "Gegenkonto", "Zusatzinformation- Inhalt 6": "Steuersatz"})
    df["Soll/Haben-Kennzeichen"] = df["Soll/Haben-Kennzeichen"].replace({"H": "Haben", "S": "Soll"})
    df['Gegenkonto'] = df['Gegenkonto'].replace({8400: '19%', 8300: '7%'})
    #datum anpassen
    def convert_date(x):
        if x < 100:  # Format ist t/mm
            day = x // 10
            month = x % 10
        else:  # Format ist tt/mm
            day = x // 100
            month = x % 100  # Corrected calculation for month
    
        timestamp = pd.Timestamp(year=2023, month=month, day=day)  # Hier nehmen wir an, dass das Jahr 2023 ist.
        #print(timestamp)
        formated_timestamp = timestamp.strftime('%d.%m.%Y')
        #print (formated_timestamp)
        return formated_timestamp
    df['Belegdatum'] = df['Belegdatum'].apply(convert_date)
    #Berechungen
    #KPI
    # gesamter Zeitraum
    # Umsatz 7%
    def berechung7monat(df):
        monat7 = df[(df['Gegenkonto'].isin(['7%'])) & (df['Soll/Haben-Kennzeichen'] == 'Soll')]
        grouped2 = monat7.groupby(by=["Gegenkonto"]).sum()[["Umsatz"]].reset_index(drop=True)
        total = grouped2['Umsatz'].sum()
        steuer7 = total * 0.07
        netto7 = total - steuer7
        
        return '{:,.2f} €'.format(total), '{:,.2f} €'.format(steuer7), '{:,.2f} €'.format(netto7)

    monat7gesamt, steuer7, netto7 = berechung7monat(df)
    
    def berechung19monat(df):
        monat7 = df[(df['Gegenkonto'].isin(['19%'])) & (df['Soll/Haben-Kennzeichen'] == 'Soll')]
        grouped2 = monat7.groupby(by=["Konto"]).sum()[["Umsatz"]].reset_index(drop=True)
        total = grouped2['Umsatz'].sum()
        steuer19 = total * 0.19
        netto19 = total - steuer19
        
        return '{:,.2f} €'.format(total), '{:,.2f} €'.format(steuer19), '{:,.2f} €'.format(netto19)

    monat19gesamt, steuer19, netto19 = berechung19monat(df)
    
    
    def tagesumsatzgesamt(df):
        df['Belegdatum'] = pd.to_datetime(df['Belegdatum'], format='%d.%m.%Y')
        tagesumsatz = df.groupby(df['Belegdatum'].dt.date)['Umsatz'].sum()
        return tagesumsatz.reset_index()
    
    tagesumsatz_df = tagesumsatzgesamt(df)
    
    fig_monats_bar = px.bar(
        tagesumsatz_df,
        x="Belegdatum",  # dates on x-axis
        y="Umsatz",  # sum of sales on y-axis
        orientation="v",  # making the bar vertical
        title="<b>Umsatz gesamt</b>",
        color_discrete_sequence=["#0083B8"]*len(tagesumsatz_df),
        template="plotly_white")
    # steuern 7% umsatz / 100 *7
    # nettoumsatz 7% Umsatz-steuern
    # Umsatz 19%
    # steuern 19% Umsatz / 100 * 19
    # Nettoumsatz 19%
    
    # umsatz 19% liste / barchart tageweise
    # Umsatz 7% liste / barchart tageweise
    
    
    
    # ---- Mainpage ----
    st.title("Datev Board")
    st.markdown("##")
    #KPI´s
    col1 , col2 = st.columns(2)
     
    col1.subheader(f"Umsatz 7%: {monat7gesamt}")
    col1.subheader(f"Steuer 7%: {steuer7}")
    col1.subheader(f"Netto 7%:  {netto7}")
    col2.subheader(f"Umsatz 19%:  {monat19gesamt}")
    col2.subheader(f"Steuer 19%: {steuer19}")
    col2.subheader(f"Netto 19%:  {netto19}")
    st.markdown("----")
    #col1, col2 = st.columns(2)  # creating 2 columns in Streamlit
    st.plotly_chart(fig_monats_bar, use_container_width=True)
   # col2.plotly_chart(fig_monats_bar, user_container_width=True)
   #st.dataframe(df)
   
#     html = f"""
#     <html>
#     <body>
#     <h1>Ergebnisse der Datev Auswertung</h1>
#     <p>Umsatz 7%: {monat7gesamt}</p>
#     <p>Steuer 7%: {steuer7}</p>
#     <p>Netto 7%: {netto7}</p>
#     <p>Umsatz 19%: {monat19gesamt}</p>
#     <p>Steuer 19%: {steuer19}</p>
#     <p>Netto 19%: {netto19}</p>
#     </body>
#     </html>
#         """     
#     pdf = pdfkit.from_string(html, False)

# # Erstelle einen BytesIO-Buffer und schreibe das PDF hinein
#     b64 = base64.b64encode(pdf)
#     pdf_io = BytesIO(b64)
    
# # Erzeuge einen Downloadlink
#     st.sidebar.download_button(
#     label="Ergebnisse als PDF herunterladen",
#     data=pdf_io,
#     file_name='datev_auswertung_ergebnisse.pdf',
#     mime='application/pdf'
# )
    
    # ''' st.sidebar.header("Bitte filtern")
    # umsatz = st.sidebar.multiselect(
    #     "Wähle S / H aus",
    #     options=df["Soll_Haben-Kennzeichen"].unique(),
    #     default=df["Soll_Haben-Kennzeichen"].unique(),
    # )
    # konto = st.sidebar.multiselect(
    #     "Wähle Konto",
    #     options=df["Konto"].unique(),
    #     default=df["Konto"].unique(),
    # )

    # # Aktualisierte Zeile: Extrahiere eindeutige Gegenkonto-Optionen aus df
    # gegenkonto_options = df["Gegenkonto"].unique()
    # gegenkonto = st.sidebar.multiselect(
    #     "Wähle Gegenkonto",
    #     options=gegenkonto_options,
    #     default=gegenkonto_options,
    # )

    # # Aktualisierte Zeile: Filtere df_selection basierend auf den ausgewählten Werten
    # df_selection = df[
    #     df["Gegenkonto"].isin(gegenkonto) & (df["Soll_Haben-Kennzeichen"].isin(umsatz)) & (df["Konto"].isin(konto))]

    # df_selection.loc[df_selection['Konto'] == '19%', 'Konto'] = '19%'
    # df_selection.loc[df_selection['Konto'] == '7%', 'Konto'] = '7%'

    # df_selection['Umsatz (ohne Soll/Haben-Kz)'] = df_selection['Umsatz (ohne Soll/Haben-Kz)'].astype(
    #     float)  # Umwandlung in float

    # df_selection['Umsatz (ohne Soll/Haben-Kz)'] = df_selection['Umsatz (ohne Soll/Haben-Kz)'].apply(
    # lambda x: float(x.replace('€', '').replace(',', '')) if isinstance(x, str) else x
    # )


    # # Berechnung der KPIs
    # sum_umsatz_8400 = df_selection.loc[df_selection['Konto'] == '19%', 'Umsatz (ohne Soll/Haben-Kz)'].sum()
    # sum_umsatz_8300 = df_selection.loc[df_selection['Konto'] == '7%', 'Umsatz (ohne Soll/Haben-Kz)'].sum()
    # sum_gesamt_umsatz = df_selection['Umsatz (ohne Soll/Haben-Kz)'].sum()

    # # DataFrame anzeigen
    # #st.write(f"Summe Umsatz (Konto 8400): {sum_umsatz_8400:.2f}")
    # #st.write(f"Summe Umsatz (Konto 8300): {sum_umsatz_8300:.2f}")
    # #st.write(f"Gesamtsumme Umsatz: {sum_gesamt_umsatz:.2f}")
    # #st.write("---")  # Trennlinie
    # # st.dataframe(df_selection)
    # st.title(":bar_chart:,Datev Board")
    # st.markdown("##")

    # left_column, middle_column, right_column = st.columns(3)
    # with left_column:
    #     st.subheader(" 19%")
    #     st.subheader(f" EUR € {sum_umsatz_8400:,}")
    # with middle_column:
    #     st.subheader(" 19%")
    #     st.subheader(f" EUR € {sum_umsatz_8300:,}")
    # with right_column:
    #     st.subheader(" 19%")
    #     st.subheader(f" EUR € {sum_gesamt_umsatz:,}")

    # st.markdown("-----")
    
    # #test_df = df.groupby(by=["Belegdatum","Konto"]).sum()[["Umsatz (ohne Soll/Haben-Kz)"]]
    # st.dataframe(df)
    # filtered_df = df[df["Konto"] == '19%']
    # st.dataframe(filtered_df)
    # grouped_df = filtered_df.groupby(by=["Belegdatum"]).sum()[["Umsatz (ohne Soll/Haben-Kz)"]]
        
    
    # fig = px.bar(grouped_df,
    #         x=grouped_df.index,
    #         y='Umsatz (ohne Soll/Haben-Kz)',
    #         labels={'x':'Belegdatum', 'y':'Umsatz (ohne Soll/Haben-Kz)'},
    #         title='Umsatz nach Belegdatum')
    
    # fig_monats_bar = px.bar(
    # grouped_df,
    # x="Umsatz (ohne Soll/Haben-Kz)",
    # y =grouped_df.index,
    # labels={'x':'Datum','y':'Unsatz'},
    # orientation="h",
    # title="<b>Monat</b>",
    # color_discrete_sequence=["#0083B8"]*len(grouped_df),
    # template="plotly_white"
    # ) 
    # st.plotly_chart(fig)
    # # berechenungen

    # # summierung auf 7% und 19% je buchungstag
    # #st.dataframe(grouped_df)
    # #st.dataframe(df_selection)
   
    
       
    # # gruppiert nach tag und konto 8400
    # # filtered_df = df[df["Konto"] == 8400]
    # # grouped_df = filtered_df.groupby(by=["Belegdatum"]).sum()[["Umsatz (ohne Soll/Haben-Kz)"]]
    
    # #gruppiert auf tag und konto 8300
    # # filtered_df = df[df["Konto"] == 8300]
    # # grouped_df = filtered_df.groupby(by=["Belegdatum"]).sum()[["Umsatz (ohne Soll/Haben-Kz)"]] '''