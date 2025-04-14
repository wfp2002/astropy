import streamlit as st
from skyfield.api import load, Topos, utc
from datetime import datetime, timedelta
import time
import matplotlib.pyplot as plt
import pandas as pd

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
        'sun': 10,
        'mercury': 199,
        'venus': 299,
        'earth': 399,
        'moon': 301,
        'mars': 499,
        'jupiter': 5,
        'saturn': 6,
        'uranus': 7,
        'neptune': 8,
        'pluto': 9
    }
    
    # Verifica se o nome do planeta é válido
    earth = planets['earth']
    observer = earth + Topos(latitude_degrees=latitude, longitude_degrees=longitude)
    
    # Verifica se o planeta está na lista de planetas válidos
    if planet_name.lower() in planetas_dict:
        planet = planets[planetas_dict[planet_name.lower()]]
    else:
        raise ValueError(f"Planeta '{planet_name}' não é válido!")

    astrometric = observer.at(tempo).observe(planet)
    alt, az, _ = astrometric.apparent().altaz()
    return az.degrees, alt.degrees, tempo.utc_iso()

def gerar_trajetoria(planet_name, latitude, longitude):
    ts = load.timescale()
    now = datetime.utcnow().replace(tzinfo=utc)  # Corrigido: adiciona timezone UTC
    times = [ts.utc(now + timedelta(minutes=i)) for i in range(0, 60 * 12 + 1, 10)]  # 12h, de 10 em 10 min
    dados = []

    for t in times:
        az, el, _ = calcular_posicao(planet_name, latitude, longitude, t)
        dados.append({'Tempo (UTC)': t.utc_datetime(), 'Azimute': az, 'Elevação': el})
    
    return pd.DataFrame(dados)

def plotar_trajetoria(df, planeta):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Gráfico de Elevação
    ax1.plot(df['Tempo (UTC)'], df['Elevação'], label='Elevação', color='orange')
    ax1.set_title(f"Trajetória de {planeta.capitalize()} (próximas 12 horas) - Elevação")
    ax1.set_xlabel("Horário (UTC)")
    ax1.set_ylabel("Elevação (°)")
    ax1.grid(True)

    print("")

    # Gráfico de Azimute
    ax2.plot(df['Tempo (UTC)'], df['Azimute'], label='Azimute', color='blue')
    ax2.set_title(f"Trajetória de {planeta.capitalize()} (próximas 12 horas) - Azimute")
    ax2.set_xlabel("Horário (UTC)")
    ax2.set_ylabel("Azimute (°)")
    ax2.grid(True)
    
    plt.subplots_adjust(hspace=0.5)
    plt.xticks(rotation=45)
    st.pyplot(fig)

# --- Streamlit App ---
st.set_page_config(page_title="Rastreamento de Planetas", layout="centered")

st.title("🔭 Planetas em Tempo Real")

# Menu de planetas
planetas_disponiveis = [
    'sun', 'moon', 'mercury', 'venus', 'mars',
    'jupiter', 'saturn', 'uranus', 'neptune', 'pluto'
]
planeta = st.selectbox("🌌 Escolha um planeta:", [p.capitalize() for p in planetas_disponiveis])

# Latitude e longitude
st.markdown("### 🌍 Sua localização:")
col1, col2 = st.columns(2)
with col1:
    latitude = st.number_input("Latitude", value=-23.5505, format="%.6f")
with col2:
    longitude = st.number_input("Longitude", value=-46.6333, format="%.6f")

# Botão para iniciar rastreamento + mostrar gráfico
if st.button("🚀 Iniciar Rastreamento + Ver Trajetória"):
    ts = load.timescale()
    placeholder = st.empty()
    chart_placeholder = st.container()

    # Gerar e exibir gráfico da trajetória
    df = gerar_trajetoria(planeta.lower(), latitude, longitude)
    plotar_trajetoria(df, planeta)

    st.success(f"Rastreando {planeta.capitalize()} em tempo real...")

    while True:
        tempo = ts.now()
        az, el, timestamp = calcular_posicao(planeta.lower(), latitude, longitude, tempo)
        az_dms = graus_para_dms(az)
        el_dms = graus_para_dms(el)

        placeholder.markdown(f"""
        ### 🪐 {planeta.capitalize()} (Atual)
        **Timestamp (UTC):** `{timestamp}`  
        **Azimute:** {az:.2f}° ({az_dms})  
        **Elevação:** {el:.2f}° ({el_dms})
        """)
        time.sleep(1)

