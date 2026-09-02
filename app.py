
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------- PAGE SETTINGS ----------------
st.set_page_config(
    page_title="NASA Infrasound Monitoring System",
    page_icon="🌍",
    layout="wide"
)

# ---------------- CUSTOM NASA THEME ----------------
st.markdown("""
<style>
.stApp{
    background-color:#050816;
    color:white;
}

h1,h2,h3{
    color:#00E5FF;
}

[data-testid="metric-container"]{
    background:#101B33;
    border:1px solid #00E5FF;
    padding:15px;
    border-radius:15px;
    box-shadow:0px 0px 15px #00E5FF55;
}

.alert-box{
    background:#160A2A;
    border-left:8px solid cyan;
    padding:15px;
    border-radius:12px;
    color:white;
    font-size:18px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.markdown("""
# 🌍 NASA Mission Control

## High-Sensitivity Microbarometer Infrasound Monitoring System
""")

st.markdown(
    "<div class='alert-box'>📡 Real-Time Atmospheric Infrasound Monitoring | Earthquake • Tsunami • Volcano Detection</div>",
    unsafe_allow_html=True
)

# ---------------- LOAD DATA ----------------
df = pd.read_excel("Microbarometer_Infrasound_100_Dataset.xlsx")

# ---------------- TOP METRICS ----------------
earthquake = len(df[df["Detected Event"]=="Earthquake"])
tsunami = len(df[df["Detected Event"]=="Tsunami"])
volcano = len(df[df["Detected Event"]=="Volcanic Eruption"])
normal = len(df[df["Detected Event"]=="Normal Noise"])

col1,col2,col3,col4,col5 = st.columns(5)

col1.metric("🌍 Total Events",len(df))
col2.metric("🚨 Earthquake",earthquake)
col3.metric("🌊 Tsunami",tsunami)
col4.metric("🌋 Volcano",volcano)
col5.metric("✅ Normal",normal)

st.divider()

# ---------------- FILTER ----------------
event = st.selectbox(
    "🛰️ Select Monitoring Event",
    ["All"] + list(df["Detected Event"].unique())
)

if event=="All":
    filtered=df
else:
    filtered=df[df["Detected Event"]==event]

# ---------------- GAUGE ----------------
freq=filtered.iloc[-1]["Frequency (Hz)"]

gauge=go.Figure(go.Indicator(
    mode="gauge+number",
    value=freq,
    title={"text":"Current Frequency (Hz)"},
    gauge={
        "axis":{"range":[0,30]},
        "bar":{"color":"cyan"},
        "steps":[
            {"range":[0,0.5],"color":"blue"},
            {"range":[0.5,10],"color":"red"},
            {"range":[10,20],"color":"orange"},
            {"range":[20,30],"color":"green"}
        ]
    }
))

# ---------------- SENSOR STATUS ----------------
pressure=filtered.iloc[-1]["Pressure (Pa)"]
amp=filtered.iloc[-1]["Amplitude"]

left,right=st.columns([2,1])

with left:
    st.plotly_chart(gauge,use_container_width=True)

with right:
    st.subheader("📡 Sensor Status")

    st.metric("Frequency (Hz)",freq)
    st.metric("Pressure (Pa)",pressure)
    st.metric("Amplitude",amp)

st.divider()

# ---------------- LINE GRAPH ----------------
st.subheader("📈 Live Frequency Monitoring")

fig1=px.line(
    filtered,
    x="Timestamp",
    y="Frequency (Hz)",
    color="Detected Event",
    markers=True,
    template="plotly_dark"
)
st.plotly_chart(fig1,use_container_width=True)

# ---------------- PRESSURE GRAPH ----------------
st.subheader("📊 Pressure vs Frequency")

fig2=px.scatter(
    filtered,
    x="Frequency (Hz)",
    y="Pressure (Pa)",
    size="Amplitude",
    color="Detected Event",
    template="plotly_dark"
)
st.plotly_chart(fig2,use_container_width=True)

# ---------------- BAR GRAPH ----------------
st.subheader("📉 Average Frequency by Event")

bar=df.groupby("Detected Event")["Frequency (Hz)"].mean().reset_index()

fig3=px.bar(
    bar,
    x="Detected Event",
    y="Frequency (Hz)",
    color="Detected Event",
    template="plotly_dark"
)
st.plotly_chart(fig3,use_container_width=True)

# ---------------- PIE CHART ----------------
st.subheader("🥧 Event Distribution")

fig4=px.pie(
    df,
    names="Detected Event",
    hole=0.5,
    template="plotly_dark"
)
st.plotly_chart(fig4,use_container_width=True)

# ---------------- ALERT SYSTEM ----------------
st.subheader("🚨 NASA Alert Center")

alert=filtered.iloc[-1]["Alert"]

if "Earthquake" in alert:
    st.error("🚨 CRITICAL EARTHQUAKE DETECTED")
elif "Tsunami" in alert:
    st.warning("🌊 TSUNAMI WARNING ISSUED")
elif "Volcano" in alert:
    st.warning("🌋 VOLCANIC ERUPTION DETECTED")
else:
    st.success("✅ SAFE ATMOSPHERIC CONDITIONS")

# ---------------- LIVE DATA TABLE ----------------
st.subheader("📋 Live Sensor Feed")

st.dataframe(filtered,use_container_width=True)
