import streamlit as st
import pandas as pd
from datetime import datetime, time
import hashlib
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EGC Logística App", layout="wide", page_icon="🚚")

# --- CONEXÃO COM O BANCO BLINDADA (NULLPOOL) ---
DB_URL = "postgresql+psycopg2://postgres.vtyfmfpijfjkxkrcvnoi:151060Violao16!@aws-1-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
engine = create_engine(DB_URL, poolclass=NullPool, connect_args={'connect_timeout': 15})
TAXA_DESGASTE_KM = 0.35

# --- FUNÇÕES DE SEGURANÇA E AUTENTICAÇÃO ---
def gerar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_login(email, senha):
    senha_hash = gerar_hash(senha)
    query = text("SELECT id, nome FROM usuarios_logistica WHERE email = :email AND senha_hash = :senha_hash")
    with engine.connect() as conn:
        resultado = conn.execute(query, {"email": email, "senha_hash": senha_hash}).fetchone()
        return resultado

def cadastrar_usuario(nome, email, senha):
    senha_hash = gerar_hash(senha)
    query = text("INSERT INTO usuarios_logistica (nome, email, senha_hash) VALUES (:nome, :email, :senha_hash)")
    try:
        with engine.begin() as conn:
            conn.execute(query, {"nome": nome, "email": email, "senha_hash": senha_hash})
        return True
    except Exception as e:
        return False

# --- GERENCIAMENTO DE ESTADO (SESSION) BLINDADO ---
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "usuario_nome" not in st.session_state:
    st.session_state.usuario_nome = ""

# --- TELAS DE ACESSO ---
def tela_login():
    st.markdown("<h1 style='text-align: center; color: #2196f3;'>🚚 EGC Logística</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>Gestão de Last Mile Multi-Plataforma</h4>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        aba_login, aba_cadastro = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
        
        with aba_login:
            with st.form("form_login"):
                email_login = st.text_input("E-mail")
                senha_login = st.text_input("Senha", type="password")
                btn_entrar = st.form_submit_button("Acessar Painel", use_container_width=True)
                
                if btn_entrar:
                    usuario = verificar_login(email_login, senha_login)
                    if usuario:
                        st.session_state.logado = True
                        st.session_state.usuario_id = usuario[0]
                        st.session_state.usuario_nome = usuario[1]
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas. Tente novamente.")
                        
        with aba_cadastro:
            with st.form("form_cadastro"):
                nome_cad = st.text_input("Nome Completo")
                email_cad = st.text_input("E-mail")
                senha_cad = st.text_input("Senha", type="password")
                btn_cadastrar = st.form_submit_button("Cadastrar Nova Conta", use_container_width=True)
                
                if btn_cadastrar:
                    if nome_cad and email_cad and senha_cad:
                        sucesso = cadastrar_usuario(nome_cad, email_cad, senha_cad)
                        if sucesso:
                            st.success("Conta criada! Volte para a aba 'Entrar' para acessar.")
                        else:
                            st.error("Erro: Este e-mail já está em uso ou houve falha no banco.")
                    else:
                        st.warning("Preencha todos os campos obrigatórios.")

# --- NÚCLEO DO SISTEMA (ISOLADO POR USUÁRIO) ---
def aplicativo_principal():
    st.sidebar.markdown(f"👤 **Piloto:** {st.session_state.usuario_nome}")
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_id = None
        st.session_state.usuario_nome = ""
        st.rerun()
        
    st.title("🚚 Painel Operacional")
    st.markdown("---")

    def carregar_dados_usuario(uid):
        try:
            query = text("SELECT * FROM entregas_logistica WHERE usuario_id = :uid ORDER BY data DESC")
            df_bd = pd.read_sql(query, engine, params={"uid": uid})
            
            df_bd = df_bd.rename(columns={
                "id": "ID", "data": "Data", "plataforma": "Plataforma", "cidade": "Cidade",
                "pacotes": "Pacotes", "paradas": "Paradas", "faturamento_bruto": "Faturamento Bruto (R$)",
                "pedagio": "Pedágio (R$)", "combustivel": "Combustível (R$)",
                "tipo_combustivel": "Tipo Combustível", "consumo_kml": "Consumo (km/L)",
                "km_rodado": "KM Rodado", "hora_inicio": "Hora Início", "hora_termino": "Hora Término"
            })
            if "Cidade" not in df_bd.columns: df_bd["Cidade"] = "Não informada"
            df_bd['Data'] = df_bd['Data'].astype(str)
            return df_bd
        except Exception as e:
            st.error(f"Erro de Conexão: {e}")
            return pd.DataFrame()

    def calcular_horas_decimais(h_ini, h_fim):
        fmt = "%H:%M:%S"
        try:
            diferenca = datetime.strptime(str(h_fim), fmt) - datetime.strptime(str(h_ini), fmt)
            segundos = diferenca.total_seconds()
            return (segundos + 24 * 3600 if segundos < 0 else segundos) / 3600
        except: return 0.0

    df_full = carregar_dados_usuario(st.session_state.usuario_id)

    if "modo_edicao" not in st.session_state:
        st.session_state.modo_edicao = False
        st.session_state.id_edicao = None

    if st.session_state.modo_edicao:
        st.sidebar.header("✏️ Editar Rota")
        try:
            linha_editar = df_full[df_full["ID"] == int(st.session_state.id_edicao)].iloc[0]
            data_padrao = datetime.strptime(linha_editar["Data"], "%Y-%m-%d")
            plat_idx = ["Mercado Livre", "Shopee", "Outra"].index(linha_editar["Plataforma"]) if linha_editar["Plataforma"] in ["Mercado Livre", "Shopee", "Outra"] else 0
            cidade_padrao = str(linha_editar["Cidade"]) if str(linha_editar["Cidade"]) != "None" else ""
            comb_idx = 0 if linha_editar["Tipo Combustível"] == "Gasolina" else 1
            
            try: cons_idx = [7, 8, 9, 10, 11, 12].index(int(linha_editar["Consumo (km/L)"]))
            except: cons_idx = 3
            
            try: ini_time = datetime.strptime(str(linha_editar["Hora Início"]), "%H:%M:%S").time()
            except: ini_time = time(6,0)
            
            try: fim_time = datetime.strptime(str(linha_editar["Hora Término"]), "%H:%M:%S").time()
            except: fim_time = time(14,0)
            
            km_edit = float(linha_editar["KM Rodado"]) if pd.notna(linha_editar["KM Rodado"]) else 0.0
            cons_edit = int(linha_editar["Consumo (km/L)"]) if pd.notna(linha_editar["Consumo (km/L)"]) else 10
            comb_total_edit = float(linha_editar["Combustível (R$)"]) if pd.notna(linha_editar["Combustível (R$)"]) else 0.0
            preco_litro_padrao = comb_total_edit / (km_edit / cons_edit) if (km_edit > 0 and cons_edit > 0) else 5.80
        except Exception as e:
            st.sidebar.error("Erro interno ao ler a linha. Cancele e tente novamente.")
            st.session_state.modo_edicao = False
            st.rerun()
    else:
        st.sidebar.header("🗺️ Lançar Nova Rota")
        data_padrao, plat_idx, cidade_padrao, comb_idx, cons_idx, ini_time, fim_time, preco_litro_padrao = datetime.now(), 0, "", 0, 3, time(6, 0), time(14, 0), 5.80

    with st.sidebar.form(key="formulario_entrega", clear_on_submit=True):
        data_entrega = st.date_input("Data da Rota", data_padrao)
        plataforma = st.selectbox("Plataforma", ["Mercado Livre", "Shopee", "Outra"], index=plat_idx)
        cidade_rota = st.text_input("📍 Cidade", value=cidade_padrao)
        
        c1, c2 = st.columns(2)
        qtd_pacotes = c1.number_input("Pacotes", min_value=0, step=1, value=int(linha_editar["Pacotes"]) if st.session_state.modo_edicao else 0)
        qtd_paradas = c2.number_input("Paradas", min_value=0, step=1, value=int(linha_editar["Paradas"]) if st.session_state.modo_edicao else 0)
        
        c3, c4 = st.columns(2)
        faturamento = c3.number_input("Faturamento (R$)", min_value=0.0, format="%.2f", value=float(linha_editar["Faturamento Bruto (R$)"]) if st.session_state.modo_edicao else 0.0)
        pedagio = c4.number_input("Pedágio (R$)", min_value=0.0, format="%.2f", value=float(linha_editar["Pedágio (R$)"]) if st.session_state.modo_edicao else 0.0)
        
        c5, c6 = st.columns(2)
        preco_litro_input = c5.number_input("Preço Litro (R$)", min_value=0.0, format="%.2f", value=float(preco_litro_padrao))
        tipo_comb = c6.selectbox("Combustível", ["Gasolina", "Etanol"], index=comb_idx)
        
        c7, c8 = st.columns(2)
        km_rodado = c7.number_input("KM Rodado", min_value=0.0, format="%.2f", value=float(linha_editar["KM Rodado"]) if st.session_state.modo_edicao else 0.0)
        consumo_carro = c8.selectbox("Consumo (km/L)", [7, 8, 9, 10, 11, 12], index=cons_idx)
        
        c9, c10 = st.columns(2)
        h_inicio = c9.time_input("Início", ini_time)
        h_termino = c10.time_input("Término", fim_time)
        
        btn_salvar = st.form_submit_button("💾 Salvar Alterações" if st.session_state.modo_edicao else "🚀 Gravar Rota", use_container_width=True)

    if btn_salvar:
        custo_combustivel_total = (km_rodado / consumo_carro) * preco_litro_input if consumo_carro > 0 else 0
        nova_linha_bd = {
            "usuario_id": st.session_state.usuario_id, 
            "data": data_entrega.strftime("%Y-%m-%d"), "plataforma": plataforma, "cidade": cidade_rota.strip() if cidade_rota else "Não informada",
            "pacotes": qtd_pacotes, "paradas": qtd_paradas, "faturamento_bruto": faturamento, "pedagio": pedagio,
            "combustivel": custo_combustivel_total, "tipo_combustivel": tipo_comb, "consumo_kml": consumo_carro,
            "km_rodado": km_rodado, "hora_inicio": h_inicio.strftime("%H:%M:%S"), "hora_termino": h_termino.strftime("%H:%M:%S")
        }
        
        if st.session_state.modo_edicao:
            query_update = text("""
                UPDATE entregas_logistica 
                SET data=:data, plataforma=:plataforma, cidade=:cidade, pacotes=:pacotes, paradas=:paradas, 
                    faturamento_bruto=:faturamento_bruto, pedagio=:pedagio, combustivel=:combustivel, 
                    tipo_combustivel=:tipo_combustivel, consumo_kml=:consumo_kml, km_rodado=:km_rodado, 
                    hora_inicio=:hora_inicio, hora_termino=:hora_termino 
                WHERE id=:id AND usuario_id=:usuario_id
            """) 
            nova_linha_bd["id"] = int(st.session_state.id_edicao)
            with engine.begin() as conn: conn.execute(query_update, nova_linha_bd)
            st.session_state.modo_edicao = False
            st.session_state.id_edicao = None
        else:
            pd.DataFrame([nova_linha_bd]).to_sql('entregas_logistica', engine, if_exists='append', index=False)
        st.rerun()

    if st.session_state.modo_edicao and st.sidebar.button("❌ Cancelar Edição", use_container_width=True):
        st.session_state.modo_edicao = False; st.session_state.id_edicao = None; st.rerun()

    # --- FILTRO MENSAL ---
    st.sidebar.markdown("---")
    mes_atual_sistema = datetime.now().strftime('%m/%Y')
    
    if not df_full.empty:
        df_full['Mes_Ano'] = pd.to_datetime(df_full['Data']).dt.strftime('%m/%Y')
        meses_unicos = list(df_full['Mes_Ano'].unique())
        if mes_atual_sistema not in meses_unicos: meses_unicos.insert(0, mes_atual_sistema)
        mes_selecionado = st.sidebar.selectbox("Filtrar por Mês", [mes_atual_sistema, "Todos"] + [m for m in meses_unicos if m != mes_atual_sistema])
        df = df_full[df_full['Mes_Ano'] == mes_selecionado].copy() if mes_selecionado != "Todos" else df_full.copy()
    else:
        df = pd.DataFrame()
        mes_selecionado = st.sidebar.selectbox("Filtrar por Mês", [mes_atual_sistema, "Todos"])

    # --- MÉTRICAS GLOBAIS DA TELA ---
    t_fat = df["Faturamento Bruto (R$)"].sum() if not df.empty else 0.0
    t_comb = df["Combustível (R$)"].sum() if not df.empty else 0.0
    t_ped = df["Pedágio (R$)"].sum() if not df.empty else 0.0
    t_km = df["KM Rodado"].sum() if not df.empty else 0.0
    t_gastos = t_comb + t_ped + (t_km * TAXA_DESGASTE_KM)
    t_lucro = t_fat - t_gastos
    
    # NOVAS MÉTRICAS DE ESFORÇO OPERACIONAL
    qtd_rotas = len(df)
    total_pacotes = int(df["Pacotes"].sum()) if not df.empty else 0

    st.markdown(f"""
    <div style="display: flex; gap: 20px; margin-bottom: 25px;">
        <div style="flex: 1; background: #1e293b; padding: 20px; border-radius: 10px; border-left: 6px solid #4caf50; text-align: center;">
            <h4 style="margin:0; color:#a5d6a7;">Faturamento Bruto</h4>
            <h2 style="margin:5px 0 0 0; color:#4caf50;">R$ {t_fat:,.2f}</h2>
        </div>
        <div style="flex: 1; background: #1e293b; padding: 20px; border-radius: 10px; border-left: 6px solid #f44336; text-align: center;">
            <h4 style="margin:0; color:#ef9a9a;">Gastos Operacionais</h4>
            <h2 style="margin:5px 0 0 0; color:#f44336;">R$ {t_gastos:,.2f}</h2>
        </div>
        <div style="flex: 1; background: #1e293b; padding: 20px; border-radius: 10px; border-left: 6px solid #2196f3; text-align: center;">
            <h4 style="margin:0; color:#90caf9;">Lucro Líquido</h4>
            <h2 style="margin:5px 0 0 0; color:#2196f3;">R$ {t_lucro:,.2f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # BLOCO DE RESUMO FÍSICO/OPERACIONAL
    st.markdown("### 📦 Esforço Operacional")
    col_op1, col_op2, col_op3 = st.columns(3)
    col_op1.metric("🚚 Rotas Realizadas", f"{qtd_rotas} rotas")
    col_op2.metric("📦 Volume Entregue", f"{total_pacotes} pacotes")
    col_op3.metric("🛣️ Distância Percorrida", f"{t_km:,.1f} KM")
    st.markdown("<br>", unsafe_allow_html=True)

    aba_dash, aba_hist = st.tabs(["📊 Dashboard Analítico", "🗄️ Histórico de Rotas"])

    if not df.empty:
        df["Custo_Total"] = df["Combustível (R$)"] + df["Pedágio (R$)"] + (df["KM Rodado"] * TAXA_DESGASTE_KM)
        df["Lucro_Linha"] = df["Faturamento Bruto (R$)"] - df["Custo_Total"]
        
        with aba_dash:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown("#### Evolução Financeira")
                st.line_chart(df.groupby("Data")[["Faturamento Bruto (R$)", "Custo_Total", "Lucro_Linha"]].sum().reset_index(), x="Data", y=["Faturamento Bruto (R$)", "Custo_Total", "Lucro_Linha"], color=["#4caf50", "#f44336", "#2196f3"])
            with col_g2:
                st.markdown("#### Lucro por Plataforma")
                df_plat = df.groupby("Plataforma")[["Faturamento Bruto (R$)", "Custo_Total", "Lucro_Linha"]].sum()
                st.bar_chart(df_plat, color=["#4caf50", "#f44336", "#2196f3"])
                
        with aba_hist:
            for i, row in df.iterrows():
                c1, c2, c3 = st.columns([8, 1, 1])
                c1.markdown(f"**{row['Data']}** | {row['Plataforma']} 📍 {row['Cidade']} | 📦 {row['Pacotes']} pac.<br>Faturou: **R$ {row['Faturamento Bruto (R$)']:.2f}** | Gastos: R$ {row['Custo_Total']:.2f} | Lucro: **R$ {row['Lucro_Linha']:.2f}**", unsafe_allow_html=True)
                if c2.button("✏️", key=f"e_{row['ID']}"): st.session_state.modo_edicao = True; st.session_state.id_edicao = row["ID"]; st.rerun()
                if c3.button("🗑️", key=f"d_{row['ID']}"): 
                    with engine.begin() as conn: conn.execute(text("DELETE FROM entregas_logistica WHERE id=:id AND usuario_id=:uid"), {"id": int(row["ID"]), "uid": st.session_state.usuario_id})
                    st.rerun()
                st.markdown("<hr style='margin: 0.5em 0;'>", unsafe_allow_html=True)
    else:
        st.info("Nenhuma entrega encontrada para este usuário neste mês.")

# --- ROTEAMENTO PRINCIPAL ---
if st.session_state.logado:
    aplicativo_principal()
else:
    tela_login()