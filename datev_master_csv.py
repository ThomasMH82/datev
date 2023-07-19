import streamlit as st
import plotly.express as px
import pandas as pd
import os
#import pdfkit
#import base64
#from io import BytesIO

#Seiteneinstellungen
st.set_page_config(page_title="Datev Auswertung", page_icon=':bar_chart:', layout='wide')

#Uploadmöglichkeit initialisieren
uploaded_file = st.sidebar.file_uploader("Bitte Datei hochladen", type=['csv'])

def replace_comma(s):
    if isinstance(s, str):
        return s.replace(',', '.')
    else:
        return s

# Upload der Datei
if uploaded_file is not None:
  df = pd.read_csv('win_csv.csv', encoding='windows-1252', sep=';', skiprows=1, usecols=[0,1, 2, 6, 7, 9, 13, 58], index_col=False)
  df = df.rename(columns={"Umsatz (ohne Soll/Haben-Kz)": 'Umsatz',"Soll/Haben-Kennzeichen":'Soll-Haben',
                        'Gegenkonto (ohne BU-Schlüssel)':'Gegenkonto','Zusatzinformation- Inhalt 6':'Steuersatz' })

  # Konvertieren Sie die Spalte 'Umsatz' zu float
  df['Umsatz'] = df['Umsatz'].replace(',', '.', regex=True).astype(float)
  
  # Erstellen Sie eine neue Spalte 'Umsatz_in_Euro', die die Währungseinheit enthält
  df['Umsatz_in_Euro'] = df['Umsatz'].map('{:,.2f}€'.format)
  
  # Speichern Sie die DataFrame in einer temporären Excel-Datei
  df.to_excel('temp.xlsx', index=False)
  
  # Lesen Sie die temporäre Excel-Datei wieder ein
  df = pd.read_excel('temp.xlsx')
  df['Belegdatum'] = df['Belegdatum'].astype(int)
  
  # Definieren Sie die Funktion 'convert_date'
  def convert_date(x):
      if x < 100:  # Format ist t/mm
          day = x // 10
          month = x % 10
      else:  # Format ist tt/mm
          day = x // 100
          month = x % 100  # Corrected calculation for month
  
      timestamp = pd.Timestamp(year=2023, month=month, day=day)  # Hier nehmen wir an, dass das Jahr 2023 ist.
      formated_timestamp = timestamp.strftime('%d.%m.%Y')
      return formated_timestamp
  
  # Wenden Sie die Funktion 'convert_date' auf die Spalte 'Belegdatum' an
  df['Belegdatum'] = df['Belegdatum'].apply(convert_date)
  df["Soll-Haben"] = df["Soll-Haben"].replace({"H": "Haben", "S": "Soll"})
  df['Gegenkonto'] = df['Gegenkonto'].replace({8400: '19%', 8300: '7%'})
  
  # Speichern Sie die DataFrame in der Excel-Datei
  df.to_excel('temp1.xlsx', index=False)
  
  #print(df)
  def berechung7monat(df):
      monat7 = df[(df['Gegenkonto'].isin(['7%'])) & (df['Soll-Haben'] == 'Soll')]
      grouped2 = monat7.groupby(by=["Gegenkonto"]).sum()[["Umsatz"]].reset_index(drop=True)
      total = grouped2['Umsatz'].sum()
      steuer7 = total * 0.07
      netto7 = total - steuer7
  
      return '{:,.2f} €'.format(total), '{:,.2f} €'.format(steuer7), '{:,.2f} €'.format(netto7)
  
  monat7gesamt, steuer7, netto7 = berechung7monat(df)
  
  #print(f"Gesamtbetrag für den 7. Monat: {monat7gesamt}, Steuer für den 7. Monat: {steuer7}, Netto für den 7. Monat: {netto7}")
  def berechung19monat(df):
      monat19 = df[(df['Gegenkonto'].isin(['19%'])) & (df['Soll-Haben'] == 'Soll')]
      grouped3 = monat19.groupby(by=["Gegenkonto"]).sum()[["Umsatz"]].reset_index(drop=True)
      total1 = grouped3['Umsatz'].sum()
      steuer19 = total1 * 0.19
      netto19 = total1 - steuer19
      
  
      return '{:,.2f} €'.format(total1), '{:,.2f} €'.format(steuer19), '{:,.2f} €'.format(netto19)
  
  monat19gesamt, steuer19, netto19 = berechung19monat(df)
  
  #print(f"Gesamtbetrag für den 7. Monat: {monat19gesamt}, Steuer für den 7. Monat: {steuer19}, Netto für den 7. Monat: {netto19}")
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
    
