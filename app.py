import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ============================================================
# PART 1 — LOAD AND CLEAN DATASET
# ============================================================
st.set_page_config(page_title="Microbarometer | Mission Control", page_icon="🌍", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {font-family: Inter, sans-serif;}
.stApp {background: radial-gradient(circle at 15% 0%, #10213c 0%, #070b17 42%, #050711 100%); color:#e8f0ff;}
.block-container {padding-top:1.4rem; padding-bottom:2rem; max-width:1500px;}
h1,h2,h3 {color:#eaf6ff;}
[data-testid="stMetric"] {background:linear-gradient(135deg,rgba(15,31,56,.96),rgba(8,17,33,.96));border:1px solid rgba(0,212,255,.4);padding:15px;border-radius:14px;box-shadow:0 0 18px rgba(0,212,255,.06);}
[data-testid="stMetricLabel"] {color:#9eb5d3;} [data-testid="stMetricValue"] {color:#eaf6ff;}
section[data-testid="stSidebar"] {background:#080f20;border-right:1px solid #172946;}
div[data-testid="stPlotlyChart"] {border:1px solid rgba(105,153,204,.2);border-radius:14px;padding:5px;background:rgba(9,18,35,.55);}
.small-muted {color:#91a8c7;font-size:.88rem;}
</style>
""", unsafe_allow_html=True)
st.markdown("# 🌍 MICROBAROMETER **MISSION CONTROL**")
st.markdown('<div class="small-muted">HIGH-SENSITIVITY INFRASOUND MONITORING · PRESSURE ANALYTICS · SIGNAL EXPLORER</div>', unsafe_allow_html=True)

DATA_FILE=Path('microbarometer_uncleaned_200.csv')
if not DATA_FILE.exists():
    st.error('Dataset not found. Keep app.py and microbarometer_uncleaned_200.csv in the same folder.')
    st.stop()
raw_df=pd.read_csv(DATA_FILE)
raw_rows=len(raw_df); raw_missing=int(raw_df.isna().sum().sum())
clean_df=raw_df.copy()
clean_df['timestamp']=pd.to_datetime(clean_df['timestamp'],errors='coerce')
numeric_cols=['pressure_hpa','frequency_hz','amplitude_pa','temperature_c','humidity_pct']
for col in numeric_cols: clean_df[col]=pd.to_numeric(clean_df[col],errors='coerce')
limits={'pressure_hpa':(800,1100),'frequency_hz':(0,100),'temperature_c':(-40,85),'humidity_pct':(0,100)}
for col,(low,high) in limits.items():
    clean_df.loc[clean_df[col].notna() & ~clean_df[col].between(low,high),col]=np.nan
clean_df.loc[clean_df['amplitude_pa'].notna() & (clean_df['amplitude_pa']<0),'amplitude_pa']=np.nan
clean_df['event_label']=clean_df['event_label'].fillna('').astype(str).str.strip().str.title()
clean_df['sensor_status']=clean_df['sensor_status'].fillna('').astype(str).str.strip().str.upper()
label_map={'Normal':'Normal','Earthquake-Like':'Earthquake-like','Volcanic-Like':'Volcanic-like','Tsunami-Like':'Tsunami-like','':'Normal'}
clean_df['event_label']=clean_df['event_label'].replace(label_map)
clean_df['sensor_status']=clean_df['sensor_status'].replace({'':'OK'})
clean_df=clean_df.drop_duplicates().copy().sort_values('timestamp')
clean_df['timestamp']=clean_df['timestamp'].ffill().bfill()
for col in numeric_cols: clean_df[col]=clean_df[col].fillna(clean_df[col].median())
clean_df['event_label']=clean_df['event_label'].fillna('Normal')
clean_df['sensor_status']=clean_df['sensor_status'].replace('','OK')
clean_df=clean_df.sort_values('timestamp').reset_index(drop=True)
clean_df.to_csv('microbarometer_cleaned.csv',index=False)
clean_rows=len(clean_df); missing_after=int(clean_df.isna().sum().sum()); duplicates_removed=raw_rows-clean_rows

# ============================================================
# PART 2 — PROFESSIONAL DASHBOARD + MOVING DEMO CHARTS
# Note: simulated readings demonstrate motion; no physical sensor connected.
# ============================================================
with st.sidebar:
    st.markdown('## ⚙️ CONTROL PANEL')
    live_mode=st.toggle('Enable moving charts',value=True)
    refresh_seconds=st.select_slider('Refresh interval',options=[2,3,5,10],value=3,format_func=lambda x:f'{x} seconds')
    event_options=sorted(clean_df['event_label'].unique().tolist())
    selected_events=st.multiselect('Event categories',event_options,default=event_options)
    st.divider(); st.markdown('### Dataset quality')
    st.write(f'Raw records: **{raw_rows}**')
    st.write(f'Clean records: **{clean_rows}**')
    st.download_button('⬇ Download cleaned CSV',clean_df.to_csv(index=False).encode('utf-8'),file_name='microbarometer_cleaned.csv',mime='text/csv',use_container_width=True)
    st.caption('Moving values are simulated for demo purposes.')
if live_mode: st_autorefresh(interval=refresh_seconds*1000,key='auto_refresh')

if 'live_history' not in st.session_state:
    st.session_state.live_history=clean_df.tail(45)[['timestamp','pressure_hpa','frequency_hz','amplitude_pa','temperature_c','humidity_pct','event_label']].copy().reset_index(drop=True)
if live_mode:
    hist=st.session_state.live_history; last=hist.iloc[-1]
    new_row=pd.DataFrame([{'timestamp':pd.Timestamp.now().floor('s'),
        'pressure_hpa':float(last['pressure_hpa'])+float(np.random.normal(0,.025)),
        'frequency_hz':float(np.clip(np.random.normal(5.5,2.5),.2,20)),
        'amplitude_pa':float(np.clip(abs(np.random.normal(.45,.16)),.02,1.5)),
        'temperature_c':float(np.clip(float(last['temperature_c'])+np.random.normal(0,.08),15,40)),
        'humidity_pct':float(np.clip(float(last['humidity_pct'])+np.random.normal(0,.35),20,95)),
        'event_label':'Normal'}])
    st.session_state.live_history=pd.concat([hist,new_row],ignore_index=True).tail(60)
chart_data=st.session_state.live_history.copy()
chart_data['timestamp']=pd.to_datetime(chart_data['timestamp'],errors='coerce')
chart_data=chart_data[chart_data['event_label'].isin(selected_events)] if selected_events else chart_data.iloc[0:0]

status='● LIVE SIMULATION' if live_mode else '● UPDATES PAUSED'
status_color='#35e6a5' if live_mode else '#ffca6a'
st.markdown(f'<div style="padding:11px 15px;background:rgba(12,25,46,.8);border:1px solid #1b3454;border-radius:12px;margin:14px 0 18px;"><span style="color:{status_color};font-weight:800;">{status}</span>　<span class="small-muted">Last refresh: {datetime.now().strftime("%H:%M:%S")} · Synthetic demonstration readings</span></div>',unsafe_allow_html=True)
latest=st.session_state.live_history.iloc[-1]
k1,k2,k3,k4,k5=st.columns(5)
k1.metric('Atmospheric Pressure',f"{latest['pressure_hpa']:.2f} hPa")
k2.metric('Signal Frequency',f"{latest['frequency_hz']:.2f} Hz")
k3.metric('Signal Amplitude',f"{latest['amplitude_pa']:.3f} Pa")
k4.metric('Temperature',f"{latest['temperature_c']:.1f} °C")
k5.metric('Humidity',f"{latest['humidity_pct']:.1f} %")
st.markdown('## 📡 SIGNAL ANALYTICS')
st.caption('Five interactive charts · Hover to inspect values · Use chart toolbar to zoom or save an image.')
layout=dict(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(5,12,25,.7)',font=dict(family='Inter, sans-serif',color='#dce9fa'),margin=dict(l=25,r=20,t=60,b=35),title_font=dict(size=17,color='#eaf6ff'))
left,right=st.columns(2,gap='large')
with left:
    f1=go.Figure(go.Scatter(x=chart_data['timestamp'],y=chart_data['pressure_hpa'],mode='lines+markers',name='Pressure',line=dict(color='#00d4ff',width=3),marker=dict(size=5),fill='tozeroy',fillcolor='rgba(0,212,255,.08)'))
    f1.update_layout(title='01 · Atmospheric Pressure Timeline',xaxis_title='Time',yaxis_title='Pressure (hPa)',**layout); st.plotly_chart(f1,use_container_width=True,key='pressure_chart')
with right:
    f2=px.histogram(chart_data,x='frequency_hz',nbins=18,title='02 · Infrasound Frequency Distribution',labels={'frequency_hz':'Frequency (Hz)','count':'Readings'})
    f2.update_traces(marker_color='#9b8cff',marker_line_color='#d5ccff',marker_line_width=1); f2.update_layout(yaxis_title='Readings',**layout); st.plotly_chart(f2,use_container_width=True,key='frequency_chart')
left,right=st.columns(2,gap='large')
with left:
    f3=px.scatter(chart_data,x='pressure_hpa',y='amplitude_pa',color='event_label',title='03 · Pressure vs Signal Amplitude',labels={'pressure_hpa':'Pressure (hPa)','amplitude_pa':'Amplitude (Pa)'},color_discrete_sequence=['#00d4ff','#ffb454','#ff6384','#9b8cff'])
    f3.update_traces(marker=dict(size=9,opacity=.82,line=dict(width=1,color='#eaf6ff'))); f3.update_layout(**layout); st.plotly_chart(f3,use_container_width=True,key='scatter_chart')
with right:
    counts=clean_df['event_label'].value_counts().rename_axis('event_label').reset_index(name='records')
    f4=px.bar(counts,x='event_label',y='records',color='event_label',title='04 · Dataset Event Label Counts',labels={'event_label':'Label','records':'Records'},color_discrete_sequence=['#00d4ff','#9b8cff','#ffb454','#ff6384'])
    f4.update_traces(marker_line_width=0,opacity=.9); f4.update_layout(showlegend=False,**layout); st.plotly_chart(f4,use_container_width=True,key='event_chart')
f5=px.line(chart_data.sort_values('timestamp'),x='timestamp',y='amplitude_pa',title='05 · Signal Amplitude — Moving Trace',markers=True,labels={'timestamp':'Time','amplitude_pa':'Amplitude (Pa)'})
f5.update_traces(line=dict(color='#ffb454',width=3),marker=dict(size=5),fill='tozeroy',fillcolor='rgba(255,180,84,.08)'); f5.update_layout(**layout); st.plotly_chart(f5,use_container_width=True,key='amplitude_chart')
with st.expander('🧹 View data-cleaning summary'):
    a,b,c,d=st.columns(4); a.metric('Raw rows',raw_rows); b.metric('Clean rows',clean_rows); c.metric('Duplicates removed',duplicates_removed); d.metric('Missing cells after cleaning',missing_after)
    st.write('Cleaning sequence: type conversion → invalid-range handling → text normalization → duplicate removal → missing-value imputation → cleaned CSV export.')
    st.dataframe(clean_df,use_container_width=True,height=260)
st.markdown('---')
st.markdown('<div class="small-muted">MICROBAROMETER MONITORING PROTOTYPE · Moving readings are simulated and are not connected to actual sensors. Event labels are illustrative, not confirmed disaster detections.</div>',unsafe_allow_html=True)
