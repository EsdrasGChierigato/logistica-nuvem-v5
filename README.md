# 🚚 EGC Logística - Gestão Logística Integrada na Nuvem

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

## 📌 Sobre o Projeto
O **EGC Logística** é uma aplicação web *Full-Stack* desenvolvida para o controle, monitoramento e análise financeira de operações de *last-mile delivery* (entregas de última milha em plataformas como Mercado Livre e Shopee). 

O sistema substitui planilhas estáticas por uma arquitetura em nuvem, permitindo o lançamento de dados em tempo real via dispositivos móveis e a geração instantânea de KPIs operacionais.

## ⚙️ Arquitetura e Tecnologias
* **Front-end & Deploy:** Streamlit Community Cloud (Interface responsiva e dinâmica).
* **Back-end:** Python (Processamento lógico e cálculos de eficiência).
* **Banco de Dados:** Supabase / PostgreSQL (Armazenamento relacional em nuvem).
* **Manipulação de Dados:** Pandas & SQLAlchemy (Filtros, agregações e conexão ORM).

## 🚀 Funcionalidades Principais
- **Integração CRUD Completa:** Criação, leitura, edição e exclusão de rotas diretamente comunicadas com o banco PostgreSQL.
- **Métricas de Produtividade:** Cálculo automático de volume de pacotes por hora e paradas por hora.
- **Inteligência Financeira:** Apuração de Lucro Líquido Real, isolando custos operacionais (combustível e pedágio).
- **Indicadores de Eficiência (KPIs):** Cálculo dinâmico do Custo por KM e Lucro médio por KM rodado.
- **Análise Geográfica:** Gráficos interativos mapeando o volume de pacotes por cidade.
- **Fechamento Mensal e Exportação:** Filtro analítico por mês e geração de relatórios consolidados em `.csv` para auditoria ou apresentações.

## 🧠 Lógica de Negócio e Impacto
Este projeto foi desenhado para resolver o problema de visão fragmentada nas rotas logísticas. Ao cruzar dados de quilometragem, tempo de percurso e consumo do veículo, a aplicação entrega uma visão cirúrgica sobre quais rotas e cidades oferecem a melhor margem de lucro, fundamentando a tomada de decisão com dados reais e objetivos.
