import streamlit as st
import pandas as pd
from datetime import datetime, time
from sqlalchemy import create_engine, text

# 1. Banco de Dados em Nuvem (Supabase)
DB_URL = "postgresql+psycopg2://postgres.vtyfmfpijfjkxkrcvnoi:151060Violao16!@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
engine = create_engine(DB_URL)

def carregar_dados():
    try:
        df_bd = pd.read_sql("SELECT * FROM entregas_logistica ORDER BY data DESC", engine)
        
        df_bd = df_bd.rename(columns={
            "id": "ID", "data": "Data", "plataforma": "Plataforma", "cidade": "Cidade",
            "pacotes": "Pacotes", "paradas": "Paradas", "faturamento_bruto": "Faturamento Bruto (R$)",
            "pedagio": "Pedágio (R$)", "combustivel": "Combustível (R$)",
            "tipo_combustivel": "Tipo Combustível", "consumo_kml": "Consumo (km/L)",
            "km_rodado": "KM Rodado", "hora_inicio": "Hora Início", "hora_termino": "Hora Término"
        })
        
        if "Cidade" not in df_bd.columns:
            df_bd["Cidade"] = "Não informada"

        df_bd['Data'] = df_bd['Data'].astype(str)
        df_bd['Hora Início'] = df_bd['Hora Início'].astype(str)
        df_bd['Hora Término'] = df_bd['Hora Término'].astype(str)
        return df_bd
        
    except Exception as e:
        st.error(f"⚠️ Erro de Conexão: {e}")
        return pd.DataFrame(columns=["ID", "Data", "Plataforma", "Cidade", "Pacotes", "Paradas", "Faturamento Bruto (R$)", "Pedágio (R$)", "Combustível (R$)", "Tipo Combustível", "Consumo (km/L)", "KM Rodado", "Hora Início", "Hora Término"])

def calcular_horas_decimais(h_ini, h_fim):
    fmt = "%H:%M:%S"
    try:
        t_ini = datetime.strptime(str(h_ini), fmt)
        t_fim = datetime.strptime(str(h_fim), fmt)
        diferenca = t_fim - t_ini
        segundos = diferenca.total_seconds()
        if segundos < 0: 
            segundos += 24 * 3600
        return segundos / 3600
    except:
        return 0.0

st.set_page_config(page_title="EGC Logística", layout="wide", page_icon="🚚")
st.title("🚚 EGC Logística")
st.markdown("---")

df_full = carregar_dados()

# Controle de Estado (Modo Edição)
if "modo_edicao" not in st.session_state:
    st.session_state.modo_edicao = False
    st.session_state.id_edicao = None

if st.session_state.modo_edicao:
    st.sidebar.header("✏️ Editar Rota")
    st.sidebar.info(f"ID do registro: {st.session_state.id_edicao}")
    linha_editar = df_full[df_full["ID"] == st.session_state.id_edicao].iloc[0]
    
    data_padrao = datetime.strptime(linha_editar["Data"], "%Y-%m-%d")
    plat_idx = ["Mercado Livre", "Shopee", "Outra"].index(linha_editar["Plataforma"]) if linha_editar["Plataforma"] in ["Mercado Livre", "Shopee", "Outra"] else 0
    cidade_padrao = str(linha_editar["Cidade"]) if pd.notna(linha_editar["Cidade"]) and str(linha_editar["Cidade"]) != "None" else ""
    comb_idx = ["Gasolina", "Etanol"].index(linha_editar["Tipo Combustível"]) if linha_editar["Tipo Combustível"] in ["Gasolina", "Etanol"] else 0
    cons_idx = [7, 8, 9, 10, 11, 12].index(int(linha_editar["Consumo (km/L)"])) if int(linha_editar["Consumo (km/L)"]) in [7, 8, 9, 10, 11, 12] else 3
    
    ini_time = datetime.strptime(linha_editar["Hora Início"], "%H:%M:%S").time()
    fim_time = datetime.strptime(linha_editar["Hora Término"], "%H:%M:%S").time()
else:
    st.sidebar.header("🗺️ Dados da Rota")
    data_padrao = datetime.now()
    plat_idx = 0
    cidade_padrao = ""
    comb_idx = 0
    cons_idx = 3 
    ini_time = time(6, 0)
    fim_time = time(14, 0)

with st.sidebar.form(key="formulario_entrega", clear_on_submit=True):
    data_entrega = st.date_input("Data da Rota", data_padrao)
    plataforma = st.selectbox("Plataforma", ["Mercado Livre", "Shopee", "Outra"], index=plat_idx)
    cidade_rota = st.text_input("📍 Cidade", value=cidade_padrao, placeholder="Ex: Valparaíso, Araçatuba...")
    
    st.markdown("**📦 Operacional**")
    col_A, col_B = st.columns(2)
    qtd_pacotes = col_A.number_input("Pacotes", min_value=0, step=1, value=int(linha_editar["Pacotes"]) if st.session_state.modo_edicao else 0)
    qtd_paradas = col_B.number_input("Paradas", min_value=0, step=1, value=int(linha_editar["Paradas"]) if st.session_state.modo_edicao else 0)
    
    st.markdown("**💰 Financeiro**")
    col_C, col_D = st.columns(2)
    faturamento = col_C.number_input("Faturamento (R$)", min_value=0.0, format="%.2f", value=float(linha_editar["Faturamento Bruto (R$)"]) if st.session_state.modo_edicao else 0.0)
    pedagio = col_D.number_input("Pedágio (R$)", min_value=0.0, format="%.2f", value=float(linha_editar["Pedágio (R$)"]) if st.session_state.modo_edicao else 0.0)
    
    st.markdown("**⛽ Veículo e Rodagem**")
    col_E, col_F = st.columns(2)
    combustivel = col_E.number_input("Gasto Combust. (R$)", min_value=0.0, format="%.2f", value=float(linha_editar["Combustível (R$)"]) if st.session_state.modo_edicao else 0.0)
    tipo_comb = col_F.selectbox("Combustível", ["Gasolina", "Etanol"], index=comb_idx)
    
    col_km, col_cons = st.columns(2)
    km_rodado = col_km.number_input("KM Rodado", min_value=0.0, format="%.2f", value=float(linha_editar["KM Rodado"]) if st.session_state.modo_edicao else 0.0)
    consumo_carro = col_cons.selectbox("Consumo (km/L)", [7, 8, 9, 10, 11, 12], index=cons_idx)
    
    st.markdown("**⏱️ Horários**")
    col_G, col_H = st.columns(2)
    h_inicio = col_G.time_input("Início", ini_time)
    h_termino = col_H.time_input("Término", fim_time)
    
    label_botao = "💾 Salvar Alterações" if st.session_state.modo_edicao else "🚀 Salvar Rota"
    botao_salvar = st.form_submit_button(label=label_botao, use_container_width=True)

if botao_salvar:
    nova_linha_bd = {
        "data": data_entrega.strftime("%Y-%m-%d"),
        "plataforma": plataforma,
        "cidade": cidade_rota.strip() if cidade_rota else "Não informada",
        "pacotes": qtd_pacotes,
        "paradas": qtd_paradas,
        "faturamento_bruto": faturamento,
        "pedagio": pedagio,
        "combustivel": combustivel,
        "tipo_combustivel": tipo_comb,
        "consumo_kml": consumo_carro,
        "km_rodado": km_rodado,
        "hora_inicio": h_inicio.strftime("%H:%M:%S"),
        "hora_termino": h_termino.strftime("%H:%M:%S")
    }
    
    if st.session_state.modo_edicao:
        query_update = text("""
            UPDATE entregas_logistica 
            SET data=:data, plataforma=:plataforma, cidade=:cidade, pacotes=:pacotes, paradas=:paradas, 
                faturamento_bruto=:faturamento_bruto, pedagio=:pedagio, combustivel=:combustivel, 
                tipo_combustivel=:tipo_combustivel, consumo_kml=:consumo_kml, km_rodado=:km_rodado, 
                hora_inicio=:hora_inicio, hora_termino=:hora_termino 
            WHERE id=:id
        """)
        nova_linha_bd["id"] = int(st.session_state.id_edicao)
        
        with engine.begin() as conn:
            conn.execute(query_update, nova_linha_bd)
            
        st.session_state.modo_edicao = False
        st.session_state.id_edicao = None
    else:
        pd.DataFrame([nova_linha_bd]).to_sql('entregas_logistica', engine, if_exists='append', index=False)
        
    st.rerun()

if st.session_state.modo_edicao:
    if st.sidebar.button("❌ Cancelar Edição", use_container_width=True):
        st.session_state.modo_edicao = False
        st.session_state.id_edicao = None
        st.rerun()

# --- NOVO: FILTRO DE MÊS ---
st.sidebar.markdown("---")
st.sidebar.header("📅 Fechamento Mensal")

if not df_full.empty:
    df_full['Mes_Ano'] = pd.to_datetime(df_full['Data']).dt.strftime('%m/%Y')
    meses_disponiveis = ["Todos"] + list(df_full['Mes_Ano'].unique())
    mes_selecionado = st.sidebar.selectbox("Filtrar por Mês", meses_disponiveis)
    
    if mes_selecionado != "Todos":
        df = df_full[df_full['Mes_Ano'] == mes_selecionado].copy()
    else:
        df = df_full.copy()
else:
    df = df_full.copy()
    mes_selecionado = "Todos"

# --- MÉTRICAS GLOBAIS (AGORA FILTRADAS) ---
total_faturamento = df["Faturamento Bruto (R$)"].sum() if not df.empty else 0.0
total_combustivel = df["Combustível (R$)"].sum() if not df.empty else 0.0
total_pedagio = df["Pedágio (R$)"].sum() if not df.empty else 0.0
lucro_liquido = total_faturamento - total_combustivel - total_pedagio

# Painel de Destaque
st.markdown(f"""
<div style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 25px;">
    <div style="flex: 1; background-color: #1e293b; padding: 25px; border-radius: 12px; border-left: 8px solid #4caf50; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h3 style="margin: 0; font-weight: 500; color: #a5d6a7;">💰 Faturamento Bruto ({mes_selecionado})</h3>
        <h1 style="margin: 10px 0 0 0; font-size: 3.5rem; color: #4caf50;">R$ {total_faturamento:,.2f}</h1>
    </div>
    <div style="flex: 1; background-color: #1e293b; padding: 25px; border-radius: 12px; border-left: 8px solid #2196f3; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h3 style="margin: 0; font-weight: 500; color: #90caf9;">📈 Lucro Líquido Real ({mes_selecionado})</h3>
        <h1 style="margin: 10px 0 0 0; font-size: 3.5rem; color: #2196f3;">R$ {lucro_liquido:,.2f}</h1>
    </div>
</div>
""", unsafe_allow_html=True)

aba_dashboard, aba_historico = st.tabs(["📊 Dashboard Analítico", "🗄️ Histórico de Rotas"])

if not df.empty:
    df["Litros_Consumidos"] = df["KM Rodado"] / df["Consumo (km/L)"]
    df["Horas_Duracao"] = df.apply(lambda row: calcular_horas_decimais(row["Hora Início"], row["Hora Término"]), axis=1)
    df["Lucro_Linha"] = df["Faturamento Bruto (R$)"] - df["Combustível (R$)"] - df["Pedágio (R$)"]
    
    total_pacotes = df["Pacotes"].sum()
    total_km = df["KM Rodado"].sum()
    total_litros = df["Litros_Consumidos"].sum()
    total_horas = df["Horas_Duracao"].sum()
    
    paradas_hora = df["Paradas"].sum() / total_horas if total_horas > 0 else 0
    pacotes_hora = total_pacotes / total_horas if total_horas > 0 else 0
    custo_km = (total_combustivel + total_pedagio) / total_km if total_km > 0 else 0
    preco_litro = total_combustivel / total_litros if total_litros > 0 else 0
    lucro_por_km = lucro_liquido / total_km if total_km > 0 else 0

    with aba_dashboard:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Desempenho", f"{pacotes_hora:.1f} pac/h", f"{total_pacotes} Pac. no Mês")
        col2.metric("⛽ Custo de Rodagem", f"R$ {custo_km:.2f} / KM", f"{total_km:,.1f} KM Totais")
        col3.metric("💧 Combustível", f"{total_litros:.1f} L consumidos", f"R$ {preco_litro:.2f} / L")
        col4.metric("🏆 Lucro Médio", f"R$ {lucro_por_km:.2f} / KM", "Eficiência Geral")
        
        st.markdown("---")
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("#### 📈 Evolução Financeira")
            df_grafico = df.groupby("Data")[["Faturamento Bruto (R$)", "Lucro_Linha"]].sum().reset_index()
            st.line_chart(data=df_grafico, x="Data", y=["Faturamento Bruto (R$)", "Lucro_Linha"], use_container_width=True)

        with col_graf2:
            st.markdown("#### 📍 Entregas por Cidade")
            df_cidades = df[df["Cidade"] != "Não informada"]
            if not df_cidades.empty:
                df_cidades = df_cidades.groupby("Cidade")["Pacotes"].sum().reset_index()
                df_cidades = df_cidades.rename(columns={"Pacotes": "Volume de Pacotes"})
                st.bar_chart(data=df_cidades, x="Cidade", y="Volume de Pacotes", use_container_width=True)
            else:
                st.info("Lance a sua primeira rota com o nome da cidade para gerar este gráfico.")
                
        # --- NOVO: BOTÃO DE EXPORTAÇÃO ---
        st.markdown("---")
        st.markdown("#### 📥 Exportar Resumo Mensal")
        st.write("Baixe a planilha com os dados filtrados deste mês para montar as suas artes e relatórios.")
        
        # Limpa colunas de controle interno antes de exportar
        df_export = df.drop(columns=["Mes_Ano", "Litros_Consumidos", "Horas_Duracao", "Lucro_Linha"], errors='ignore')
        csv = df_export.to_csv(index=False).encode('utf-8')
        
        nome_arquivo = f"Fechamento_{mes_selecionado.replace('/', '_')}.csv" if mes_selecionado != "Todos" else "Historico_Completo.csv"
        
        st.download_button(
            label="📄 Baixar Dados (CSV)",
            data=csv,
            file_name=nome_arquivo,
            mime="text/csv",
            type="primary"
        )

    with aba_historico:
        for i, row in df.iterrows():
            with st.container():
                c_info, c_edit, c_del = st.columns([7, 1, 1])
                
                tempo_str = f"{int(row['Horas_Duracao'])}h {int((row['Horas_Duracao']%1)*60)}min"
                p_hora = row['Paradas'] / row['Horas_Duracao'] if row['Horas_Duracao'] > 0 else 0
                
                lucro_rota_km = row['Lucro_Linha'] / row['KM Rodado'] if row['KM Rodado'] > 0 else 0
                cidade_exibicao = f" — 📍 **{row['Cidade']}**" if str(row['Cidade']) != "Não informada" else ""
                
                c_info.markdown(
                    f"**ID {row['ID']} | {row['Data']}** — **{row['Plataforma']}** {cidade_exibicao} | "
                    f"📦 {int(row['Pacotes'])} pac. | 🛑 {int(row['Paradas'])} paradas (**{p_hora:.1f}/h**) | "
                    f"⏱️ {tempo_str} | 🛣️ {row['KM Rodado']} KM a {int(row['Consumo (km/L)'])}km/L<br>"
                    f"💸 Faturou: **R$ {row['Faturamento Bruto (R$)']:.2f}** | 🏆 Lucro/KM: **R$ {lucro_rota_km:.2f}**",
                    unsafe_allow_html=True
                )
                
                if c_edit.button("✏️ Editar", key=f"edit_{row['ID']}", use_container_width=True):
                    st.session_state.modo_edicao = True
                    st.session_state.id_edicao = row["ID"]
                    st.rerun()
                    
                if c_del.button("🗑️ Apagar", key=f"del_{row['ID']}", type="primary", use_container_width=True):
                    with engine.begin() as conn:
                        conn.execute(text("DELETE FROM entregas_logistica WHERE id=:id"), {"id": int(row["ID"])})
                    st.rerun()
                st.markdown("<hr style='margin: 0.8em 0px; border: 1px solid #333;'>", unsafe_allow_html=True)
else:
    st.info("Nenhum dado registrado. Preencha o formulário para lançar a sua primeira rota!")