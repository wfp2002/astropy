import streamlit as st
from skyfield.api import load, Topos, utc
from datetime import datetime, timedelta, timezone
import time
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import numpy as np

# Configuração da página
st.set_page_config(page_title="Rastreamento de Planetas", layout="centered")

# Carrega efemérides só uma vez
@st.cache_resource
def carregar_planetas():
    return load('de421.bsp')

planets = carregar_planetas()

# --- Funções auxiliares ---
def graus_para_dms(graus_float):
    graus = int(graus_float)
    minutos_float = abs(graus_float - graus) * 60
    minutos = int(minutos_float)
    segundos = (minutos_float - minutos) * 60
    return f"{graus}° {minutos}′ {segundos:.2f}″"

def calcular_posicao(planet_name, latitude, longitude, tempo):
    planetas_dict = {
        'sun': 10, 'mercury': 199, 'venus': 299, 'earth': 399, 'moon': 301,
        'mars': 499, 'jupiter': 5, 'saturn': 6, 'uranus': 7, 'neptune': 8, 'pluto': 9
    }
    earth = planets['earth']
    observer = earth + Topos(latitude_degrees=latitude, longitude_degrees=longitude)

    if planet_name.lower() in planetas_dict:
        planet = planets[planetas_dict[planet_name.lower()]]
    else:
        raise ValueError(f"Planeta '{planet_name}' não é válido!")

    astrometric = observer.at(tempo).observe(planet)
    alt, az, _ = astrometric.apparent().altaz()
    return az.degrees, alt.degrees, tempo.utc_iso(), tempo.utc_datetime()

def gerar_trajetoria(planet_name, latitude, longitude):
    ts = load.timescale()
    now = datetime.now(timezone.utc)
    times = [ts.utc(now + timedelta(minutes=i)) for i in range(-60 * 6, 60 * 6 + 1, 10)]  # 6h antes e 6h depois
    dados = []

    for t in times:
        az, el, _, _ = calcular_posicao(planet_name, latitude, longitude, t)
        dados.append({'Tempo (UTC)': t.utc_datetime(), 'Azimute': az, 'Elevação': el})
    
    return pd.DataFrame(dados)

def plotar_trajetoria(df, planeta, az_atual=None, el_atual=None, tempo_atual=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Elevação
    ax1.plot(df['Tempo (UTC)'], df['Elevação'], label='Elevação', color='orange')
    if tempo_atual and el_atual is not None:
        ax1.plot(tempo_atual, el_atual, 'ro')
        ax1.annotate(f"{el_atual:.1f}°", (tempo_atual, el_atual),
                     textcoords="offset points", xytext=(0, 10), ha='center', color='red')
    ax1.set_title(f"Trajetória de {planeta.capitalize()} (6h antes e 6h depois) - Elevação")
    ax1.set_xlabel("Horário (UTC)")
    ax1.set_ylabel("Elevação (°)")
    ax1.grid(True)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    # Azimute
    ax2.plot(df['Tempo (UTC)'], df['Azimute'], label='Azimute', color='blue')
    if tempo_atual and az_atual is not None:
        ax2.plot(tempo_atual, az_atual, 'ro')
        ax2.annotate(f"{az_atual:.1f}°", (tempo_atual, az_atual),
                     textcoords="offset points", xytext=(0, 10), ha='center', color='red')
    ax2.set_title(f"Trajetória de {planeta.capitalize()} (6h antes e 6h depois) - Azimute")
    ax2.set_xlabel("Horário (UTC)")
    ax2.set_ylabel("Azimute (°)")
    ax2.grid(True)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    plt.subplots_adjust(hspace=0.5)
    plt.xticks(rotation=45)
    st.pyplot(fig)
    plt.close(fig)

def plotar_azimute_polar(az_atual):
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})

    az_rad = np.radians(az_atual)
    ax.plot(az_rad, 1, 'ro')
    ax.text(az_rad, 1.15, f"{az_atual:.0f}°", color='red', fontsize=13, ha='center', va='bottom', fontweight='bold')

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_ylim(0, 1.5)
    ax.set_yticklabels([])

    ax.set_xticks(np.radians([0, 90, 180, 270]))
    ax.set_xticklabels(['Norte', 'Leste', 'Sul', 'Oeste'])

    ax.set_title("Azimute Atual (Bússola)", fontsize=15)
    ax.grid(True)
    plt.close(fig)
    return fig

# --- Streamlit App ---
st.title("🔭 Planetas em Tempo Real")

planetas_disponiveis = [
    'sun', 'moon', 'mercury', 'venus', 'mars',
    'jupiter', 'saturn', 'uranus', 'neptune', 'pluto'
]
planeta = st.selectbox("🌌 Escolha um planeta:", [p.capitalize() for p in planetas_disponiveis])

st.markdown("### 🌍 Sua localização:")
col1, col2 = st.columns(2)
with col1:
    latitude = st.number_input("Latitude", value=-23.5505, format="%.6f")
with col2:
    longitude = st.number_input("Longitude", value=-46.6333, format="%.6f")

if st.button("🚀 Iniciar Rastreamento em Tempo Real"):
    ts = load.timescale()
    placeholder = st.empty()
    chart_placeholder = st.empty()
    compass_placeholder = st.empty()

    df = gerar_trajetoria(planeta.lower(), latitude, longitude)

    while True:
        tempo = ts.now()
        az, el, timestamp, dt_obj = calcular_posicao(planeta.lower(), latitude, longitude, tempo)
        az_dms = graus_para_dms(az)
        el_dms = graus_para_dms(el)

        with chart_placeholder:
            plotar_trajetoria(df, planeta, az, el, dt_obj)

        with compass_placeholder:
            compass_fig = plotar_azimute_polar(az)
            st.pyplot(compass_fig)

        with placeholder:
            st.markdown(f"""
            ### 🪐 {planeta.capitalize()} (Atual)
            **Timestamp (UTC):** `{timestamp}`  
            **Azimute:** {az:.2f}° ({az_dms})  
            **Elevação:** {el:.2f}° ({el_dms})
            """)

        time.sleep(0.1)

