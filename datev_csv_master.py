import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import pdfkit
import base64
from tempfile import NamedTemporaryFile

#Seiteneinstellungen
st.set_page_config(page_title="Datev Auswertung", page_icon=':bar_chart:', layout='wide')

#Uploadmöglichkeit initialisieren
uploaded_file = st.sidebar.file_uploader("Bitte Datei hochladen", type=['csv'])

# Upload der Datei
if uploaded_file is not None:
  df = pd.read_csv(uploaded_file, encoding='windows-1252', sep=';', skiprows=1, usecols=[0,1, 2, 6, 7, 9, 13, 58], index_col=False)
  df = df.rename(columns={"Umsatz (ohne Soll/Haben-Kz)": 'Umsatz',"Soll/Haben-Kennzeichen":'Soll-Haben',
                        'Gegenkonto (ohne BU-Schlüssel)':'Gegenkonto','Zusatzinformation- Inhalt 6':'Steuersatz' })

  # Konvertieren Sie die Spalte 'Umsatz' zu float
  df['Umsatz'] = df['Umsatz'].replace(',', '.', regex=True).astype(float)
  
  # Erstellen Sie eine neue Spalte 'Umsatz_in_Euro', die die Währungseinheit enthält
  df['Umsatz_in_Euro'] = df['Umsatz'].map('{:,.2f}€'.format)
  
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

  # The rest of your code 
  def berechung7monat(df):
      monat7 = df[(df['Gegenkonto'].isin(['7%'])) & (df['Soll-Haben'] == 'Soll')]
      grouped2 = monat7.groupby(by=["Gegenkonto"]).sum()[["Umsatz"]].reset_index(drop=True)
      total = grouped2['Umsatz'].sum()
      steuer7 = total * 0.07
      netto7 = total - steuer7
  
      return '{:,.2f} €'.format(total), '{:,.2f} €'.format(steuer7), '{:,.2f} €'.format(netto7)
  
  monat7gesamt, steuer7, netto7 = berechung7monat(df)

  # def liste7tageweise(df):
  #   monat7liste = df[(df['Gegenkonto'].isin(['7%'])) & (df['Soll-Haben'] == 'Soll')]
  #   grouped7liste = monat7liste.groupby(by=["Belegdatum"]).sum()[["Umsatz"]]
  #   grouped7liste['Umsatz'] = grouped7liste['Umsatz'].apply(lambda x: '€{:,.2f}'.format(x))
    
  #   return (grouped7liste)

  #grouped7liste = liste7tageweise(df)      
  
  def berechung19monat(df):
      monat19 = df[(df['Gegenkonto'].isin(['19%'])) & (df['Soll-Haben'] == 'Soll')]
      grouped3 = monat19.groupby(by=["Gegenkonto"]).sum()[["Umsatz"]].reset_index(drop=True)
      total1 = grouped3['Umsatz'].sum()
      steuer19 = total1 * 0.19
      netto19 = total1 - steuer19
      
      return '{:,.2f} €'.format(total1), '{:,.2f} €'.format(steuer19), '{:,.2f} €'.format(netto19)
  
  monat19gesamt, steuer19, netto19 = berechung19monat(df)

  def liste19tageweise(df):
      monat19liste = df[(df['Gegenkonto'].isin(['19%'])) & (df['Soll-Haben'] == 'Soll')]
      grouped19liste = monat19liste.groupby(by=["Belegdatum"]).sum()[["Umsatz"]]
      grouped19liste['Umsatz'] = grouped19liste['Umsatz'].apply(lambda x: '€{:,.2f}'.format(x))
    
      return (grouped19liste)

  #grouped19liste = liste19tageweise(df) 

  def tagesumsatzgesamt(df):
        df['Belegdatum'] = pd.to_datetime(df['Belegdatum'], format='%d.%m.%Y')
        tagesumsatz = df.groupby(df['Belegdatum'].dt.date)['Umsatz'].sum()
        return tagesumsatz.reset_index()
    
  #tagesumsatz_df = tagesumsatzgesamt(df)
    
  # fig_monats_bar = px.bar(
  #     tagesumsatz_df,
  #     x="Belegdatum",  # dates on x-axis
  #     y="Umsatz",  # sum of sales on y-axis
  #     orientation="v",  # making the bar vertical
  #     title="<b>Umsatz gesamt</b>",
  #     color_discrete_sequence=["#0083B8"]*len(tagesumsatz_df),
  #     template="plotly_white")

  def stb_pivot(df):
    # Stellen Sie sicher, dass 'Belegdatum' im richtigen Datumsformat ist
    df['Belegdatum'] = pd.to_datetime(df['Belegdatum'], dayfirst=True)

    # Filtern Sie die Daten entsprechend Ihren Kriterien
    df_filtered = df[(df['Soll-Haben'] == 'Soll') & (df['Gegenkonto'].isin(['7%', '19%']))]

    # Erstellen Sie die Pivot-Tabelle ohne 'Soll-Haben' in der Indexliste
    pivot_table = df_filtered.pivot_table(values='Umsatz', index=df['Belegdatum'].dt.date, columns=['Gegenkonto'], aggfunc=np.sum, fill_value=0)

    # Hilfsfunktion, um date in datetime zu konvertieren und dann ins ursprüngliche Format zurückzukonvertieren
    def date_to_string(date, format='%d.%m.%Y'):
        return pd.to_datetime(date).strftime(format)

    # Wenden Sie die Hilfsfunktion auf den Datumsindex an
    pivot_table.index = pivot_table.index.map(date_to_string)

    # Formatieren Sie die 'Umsatz'-Werte als Strings mit dem Euro-Symbol
    pivot_table = pivot_table.applymap(lambda x: f"{x:.2f}€")
    
    return pivot_table

  # Verwenden Sie Streamlit, um die Pivot-Tabelle auszugeben
  stb_umstz = stb_pivot(df)
  #st.table(stb_umstz)


  # ---- Mainpage ----
  st.title("Datev Board")
  #st.divider()
  #KPI´s
  col1 , col2 = st.columns(2)
   
  col1.subheader(f"Umsatz 7%: {monat7gesamt}")
  col1.subheader(f"Steuer 7%: {steuer7}")
  col1.subheader(f"Netto 7%:  {netto7}")
  col2.subheader(f"Umsatz 19%:  {monat19gesamt}")
  col2.subheader(f"Steuer 19%: {steuer19}")
  col2.subheader(f"Netto 19%: {netto19}")
  #st.divider() 
  st.title("Umsatz tageweise")
  #col1_1 , col2_1 = st.columns(2)
  #col1_1.write("Umsatz 7% tageweise")
  #col1.dataframe(grouped7liste)
  #col1_1.table(grouped7liste)
  #col2_1.write("Umsatz 19% tageweise")
  #col2.dataframe(grouped19liste)
  #col2_1.table(grouped19liste)
  #Grafik
  #st.divider()
  st.table(stb_umstz)
  #st.divider("trennung")
  #st.divider()
  #st.plotly_chart(fig_monats_bar, use_container_width=True)
  

  

  df_pdf_output = {
    'Monat 7% Gesamt': monat7gesamt,
    'Steuer 7%': steuer7,
    'Netto 7%': netto7,
    'Tägliche Umsatzliste 7%': grouped7liste,
    'Monat 19% Gesamt': monat19gesamt,
    'Steuer 19%': steuer19,
    'Netto 19%': netto19,
    'Tägliche Umsatzliste 19%': grouped19liste,
    #'Täglicher Gesamtumsatz': tagesumsatz_df
    }


  def df_to_pdf(df_dict):
    # Convert the dictionary to HTML string
    html_string = ''
    for key in df_dict:
        if isinstance(df_dict[key], pd.DataFrame):
            html_string += df_dict[key].to_html()
        else:
            html_string += f'<p>{key}: {df_dict[key]}</p>'

    # Convert the HTML string to PDF
    pdfkit.from_string(html_string, 'output.pdf')

  # Call the function with your dictionary
  df_to_pdf(df_pdf_output)

  # Function to get download link for the pdf
  def get_pdf_download_link(pdf_file, download_name):
    with open(pdf_file, 'rb') as f:
        pdf = f.read()
    
    # b64 encode
    b64 = base64.b64encode(pdf)
    b64 = b64.decode()
    
    href = f'<a href="data:file/pdf;base64,{b64}" download="{download_name}.pdf">Download PDF</a>'
    return href

  # Call the function to generate download link
  download_link = get_pdf_download_link('output.pdf', 'output')
  st.sidebar.markdown(download_link, unsafe_allow_html=True)
  
  

  
  #Erklärung und Beispiel
  st.sidebar.markdown("<h3 style='text-align: center;'>Erklärung:</h3>", unsafe_allow_html=True)
  st.sidebar.markdown("In der App kannst du eine CSV Datei hochladen. Nach dem Hochladen werden dir die Umsätze angezeigt.")
