import os
import json
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Configuração da página
st.set_page_config(page_title="Dashboard de Monitoramento de Colmeias", layout="wide")

# Pastas de dados
FOLDERS = {
    "CSV": "processing_csv/saida",
    "JSON": "processing_json/saida",
    "BD": "processing_bd/saida"
}

@st.cache_data(ttl=5)
def carregar_dados():
    dataframes = []
    for origem, pasta in FOLDERS.items():
        if not os.path.exists(pasta):
            continue
            
        for arquivo in os.listdir(pasta):
            if not arquivo.startswith("transf"):
                continue
                
            caminho = os.path.join(pasta, arquivo)
            try:
                if arquivo.endswith(".csv"):
                    df = pd.read_csv(caminho)
                    # Converte campos numéricos
                    num_cols = ['temp', 'humidity', 'fullWeight', 'honeyWeight', 
                               'pressure', 'battery', 'variacao_peso']
                    for col in num_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                elif arquivo.endswith(".json"):
                    with open(caminho, 'r') as f:
                        data = json.load(f)
                    
                    # Converte strings numéricas para float
                    if isinstance(data, dict):
                        for key in ['temp', 'humidity', 'battery']:
                            if key in data and isinstance(data[key], str):
                                try:
                                    data[key] = float(data[key])
                                except:
                                    data[key] = None
                    
                    df = pd.DataFrame([data] if isinstance(data, dict) else data)
                
                df["origem"] = origem
                df["arquivo"] = arquivo
                dataframes.append(df)
                
            except Exception as e:
                st.error(f"Erro ao processar {caminho}: {str(e)}")
    
    return pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()

# Funções de detecção de alertas
def detectar_alertas(df):
    alertas = []
    
    # Para dados CSV
    df_csv = df[df["origem"] == "CSV"] if "origem" in df.columns else pd.DataFrame()
    if not df_csv.empty:
        # Alerta: Variação de peso
        if 'variacao_peso' in df_csv.columns:
            for _, row in df_csv[df_csv['variacao_peso'].abs() > 0.5].iterrows():
                alertas.append({
                    "tipo": "⚖️ Variação de Peso",
                    "mensagem": f"Colmeia {row['id_colmeia']} - Variação anormal: {row['variacao_peso']:.2f}kg",
                    "gravidade": "alta"
                })
        
        # Alerta: Necessidade de alimentação
        if 'necessidade_alimentacao' in df_csv.columns:
            for _, row in df_csv[df_csv['necessidade_alimentacao'] == True].iterrows():
                alertas.append({
                    "tipo": "🍯 Necessidade de Alimentação",
                    "mensagem": f"Colmeia {row['id_colmeia']} - Necessita de alimentação urgente",
                    "gravidade": "media"
                })
        
        # Alerta: Pressão anômala
        if 'pressao_anomala' in df_csv.columns:
            for _, row in df_csv[df_csv['pressao_anomala'] == True].iterrows():
                alertas.append({
                    "tipo": "📊 Pressão Anômala",
                    "mensagem": f"Colmeia {row['id_colmeia']} - Pressão fora do normal",
                    "gravidade": "alta"
                })
    
    # Para dados JSON
    df_json = df[df["origem"] == "JSON"] if "origem" in df.columns else pd.DataFrame()
    if not df_json.empty:
        # Alerta: Temperatura
        if 'temp' in df_json.columns:
            for _, row in df_json.iterrows():
                try:
                    temp = float(row['temp'])
                    if temp < 20 or temp > 30:
                        alertas.append({
                            "tipo": "🌡️ Temperatura",
                            "mensagem": f"Colmeia {row['id_colmeia']} - Temperatura crítica: {temp:.1f}°C",
                            "gravidade": "alta" if temp < 15 or temp > 35 else "media"
                        })
                except:
                    continue
        
        # Alerta: Umidade
        if 'humidity' in df_json.columns:
            for _, row in df_json.iterrows():
                try:
                    umid = float(row['humidity'])
                    if umid < 40 or umid > 60:
                        alertas.append({
                            "tipo": "💧 Umidade",
                            "mensagem": f"Colmeia {row['id_colmeia']} - Umidade fora do ideal: {umid:.1f}%",
                            "gravidade": "media"
                        })
                except:
                    continue
        
        # Alerta: Bateria baixa (do JSON também)
        if 'battery' in df_json.columns:
            for _, row in df_json.iterrows():
                try:
                    bat = float(row['battery'])
                    if bat < 20:
                        alertas.append({
                            "tipo": "🔋 Bateria Crítica",
                            "mensagem": f"Colmeia {row['id_colmeia']} - Bateria muito baixa: {bat:.1f}%",
                            "gravidade": "alta"
                        })
                    elif bat < 40:
                        alertas.append({
                            "tipo": "🔋 Bateria Baixa",
                            "mensagem": f"Colmeia {row['id_colmeia']} - Bateria baixa: {bat:.1f}%",
                            "gravidade": "media"
                        })
                except:
                    continue
    
    # Para dados BD (se houver)
    df_bd = df[df["origem"] == "BD"] if "origem" in df.columns else pd.DataFrame()
    if not df_bd.empty:
        if 'battery_status' in df_bd.columns:
            for _, row in df_bd[df_bd['battery_status'] == 'battery_below_80'].iterrows():
                alertas.append({
                    "tipo": "🔋 Bateria",
                    "mensagem": f"Colmeia {row['id_colmeia']} - Bateria abaixo de 80%: {row['battery']:.1f}%",
                    "gravidade": "baixa"
                })
    
    return alertas

# Interface do Dashboard
st.title("🐝 Dashboard de Monitoramento de Colmeias")
st_autorefresh(interval=5000, limit=None, key="autorefresh")

dados = carregar_dados()

if dados.empty:
    st.info("⏳ Aguardando dados dos sensores...")
else:
    alertas = detectar_alertas(dados)
    
    # Mostra resumo
    col1, col2, col3 = st.columns(3)
    col1.metric("Colmeias Monitoradas", dados['id_colmeia'].nunique())
    col2.metric("Total de Alertas", len(alertas))
    col3.metric("Última Atualização", pd.to_datetime('now').strftime('%H:%M:%S'))
    
    # Filtros
    st.sidebar.header("Filtros")
    tipos_alertas = list(set(a["tipo"] for a in alertas))
    tipo_selecionado = st.sidebar.selectbox("Tipo de Alerta", ["Todos"] + sorted(tipos_alertas))
    
    gravidades = list(set(a["gravidade"] for a in alertas))
    gravidade_selecionada = st.sidebar.selectbox("Gravidade", ["Todas"] + sorted(gravidades))
    
    # Filtra alertas
    alertas_filtrados = alertas
    if tipo_selecionado != "Todos":
        alertas_filtrados = [a for a in alertas_filtrados if a["tipo"] == tipo_selecionado]
    if gravidade_selecionada != "Todas":
        alertas_filtrados = [a for a in alertas_filtrados if a["gravidade"] == gravidade_selecionada]
    
    # Mostra alertas
    if not alertas_filtrados:
        st.success("✅ Nenhum alerta encontrado com os filtros atuais")
    else:
        st.subheader(f"🚨 Alertas ({len(alertas_filtrados)})")
        
        for alerta in alertas_filtrados:
            if alerta["gravidade"] == "alta":
                st.error(f"{alerta['tipo']}: {alerta['mensagem']}")
            elif alerta["gravidade"] == "media":
                st.warning(f"{alerta['tipo']}: {alerta['mensagem']}")
            else:
                st.info(f"{alerta['tipo']}: {alerta['mensagem']}")
    
    # Mostra dados completos se solicitado
    if st.checkbox("Mostrar dados brutos"):
        st.subheader("Dados Completos")
        st.dataframe(dados)