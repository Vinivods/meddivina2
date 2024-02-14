import streamlit as st
import time
import math
import pandas as pd
import datetime
import smtplib
import pyodbc
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from medLista import mapa_medicamentos, nome_medicamentos
from email.message import EmailMessage


#info email recuperar senha
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_user = "medd.informacao@gmail.com"
smtp_password = "sekd nvmd nxyu wdry"

#* CRIAR AS TABELAS DO BANCO ANTES DE COMEÇAR O APLICATIVO
# Criar o banco MedD
try:
    conn = sqlite3.connect('MedD.db')
    cursor = conn.cursor()

    # st.toast('Banco criado com sucesso.')
except Exception as e:
    st.toast(f'Não foi possível criar o banco MedD. Erro: {e}')

# Cadastro
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Cadastro (
            LoginFarma VARCHAR(100) PRIMARY KEY NOT NULL,
            SenhaFarma VARCHAR(100) NOT NULL,
            Nome VARCHAR(20) NOT NULL,
            Sobrenome VARCHAR(50) NOT NULL,
            Farmacia VARCHAR(50) NOT NULL,
            Email VARCHAR(150) NOT NULL
            )
        """)
    conn.commit()

except Exception as e:
    st.toast(f'Não foi possível criar a tabela cadastro. Erro: {e}')

# Validades
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Validades (
            LoginFarma VARCHAR(100) NOT NULL,
            Tasy INT NOT NULL,
            Medicamento VARCHAR(200) NOT NULL,
            Lote VARCHAR(50) NOT NULL,
            Quantidade SMALLINT NOT NULL,
            Data_vencimento DATE NOT NULL
            )
        """)
    conn.commit()

except Exception as e:
    st.toast(f'Não foi possível criar a tabela validades. Erro: {e}')

# ControleFaltas
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ControleFaltas (
            LoginFarma VARCHAR(100) NOT NULL,
            Tasy INT NOT NULL,
            Medicamento VARCHAR (200) NOT NULL,
            Quantidade INT NOT NULL,
            Farmacia VARCHAR(50) NOT NULL,
            Data_falta DATE NOT NULL
            )
        """)
    conn.commit()

except Exception as e:
    st.toast(f'Não foi possível criar a tabela de controle de faltas. Erro: {e}')

try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Plantao (
            Data_plantao DATE NOT NULL,
            Turno VARCHAR(10) NOT NULL,
            Faltas VARCHAR(150) NOT NULL,
            Geladeira VARCHAR(200) NOT NULL,
            Caf VARCHAR(200) NOT NULL,
            Almox VARCHAR(200) NOT NULL,
            Meta VARCHAR(15) NOT NULL,
            Farma VARCHAR(150) NOT NULL,
            Equipe VARCHAR(250) NOT NULL,
            Descricao TEXT NOT NULL,
            Nome_passagem VARCHAR(100) NOT NULL,
            UNIQUE (Data_plantao, Turno)
            )
    """)
    conn.commit()
except Exception as e:
    st.toast(f'Não foi possível criar a tabela de passagem de plantão. Erro: {e}')

# conn.close()

def get_session():
    session = st.session_state
    if 'login_successful' not in session:
        session.login_successful = False
    return session

def check_login():
    session_state = get_session()
    if not session_state.login_successful:
        st.error("Você precisa fazer login para acessar esta página.")
        st.stop()

menu = st.sidebar.selectbox(
    "O que você precisa fazer?",
    ("Bem-vindo", "Login", "Validades", "Estoque", "Faltas", "Passar plantão", "Sair")
)

if menu == "Bem-vindo":
    with st.container():
        st.markdown("""
            <head>
                <link href="https://fonts.googleapis.com/css?family=Signika+Negative:300,regular,500,600,700" rel="stylesheet" />
                <link href="https://fonts.googleapis.com/css?family=Bebas+Neue:regular" rel="stylesheet" />
                <style>
                    .custom-font {
                        font-family: 'Signika Negative';
                        font-size: 38px;
                        font-weight: 200;
                        text-align:center;
                    }
                    #D {
                    color: #32de84;
                    }
                    .textos {
                    font-family: 'Signika Negative';
                    font-size: 24px;
                    text-align: center;
                    # margin-top: -1%;
                    # margin-bottom: 2%
                    }
                    .sbt {
                    font-family: 'Signika Negative';
                    text-align: center;
                    font-weight: 200;
                    }
                    .negrito {
                    color: #43C59E
                    }
                    #logo {
                    box-shadow: inset 0 0 0 0 #43C59E;
                    color: #43C59E;
                    margin: 0 -.25rem;
                    padding: 0 .25rem;
                    transition: color .3s ease-in-out, box-shadow .3s ease-in-out;
                    font-size: 64px;
                    font-family: 'Signika Negative';
                    font-weight: 700;
                    text-align: center;
                    }
                    #logo:hover {
                    box-shadow: inset 300px 0 0 0 #43C59E;
                    color: white;
                </style>
            </head>
        """, unsafe_allow_html=True)
        st.markdown('<p class="custom-font"><span id="logo">MEDD</span></p>', unsafe_allow_html=True)
        st.markdown('<p class="custom-font">SEJA MUITO BEM-VINDO À MED<span id="D">D</span>!</p>', unsafe_allow_html=True)

        st.markdown("<h3 class=sbt>VALIDADES</h3>", unsafe_allow_html=True)
        st.markdown('<p class="textos">Cadastre as <span class="negrito">validades</span> dos medicamentos que você quer acompanhar e tenha acesso a elas diretamente pela medD.</p>', unsafe_allow_html=True)
        st.markdown('<hr>', unsafe_allow_html=True)

        st.markdown("<h3 class=sbt>ESTOQUE</h3>", unsafe_allow_html=True)
        st.markdown('<p class="textos">Informe a quantidade de dispensações de um medicamento e descubra o <span class="negrito">estoque padrão</span> ideal para sua farmácia.</p>', unsafe_allow_html=True)
        st.markdown('<hr>', unsafe_allow_html=True)

        st.markdown("<h3 class=sbt>FALTAS</h3>", unsafe_allow_html=True)
        st.markdown('<p class="textos">Adicione diariamente <span class="negrito">faltas</span> de medicamento e receba avisos sobre faltas em excesso.</p>', unsafe_allow_html=True)

# *LOGIN
elif menu == "Login":
    logar, cadastrar, esqueci = st.tabs(["Login", "Cadastro", "Esqueci a senha"])

    with logar:
        st.subheader("Quem está aí?")
        login = st.text_input("Insira seu login para entrar")
        senha_logar = st.text_input('Insira sua senha', type='password')
        login_btn = st.button("Entrar", type="primary")

        if login_btn:
            # cursor.execute('DROP TABLE Plantao')
            # conn.commit()
            # st.toast('plantao apagado')
            if login == '' or senha_logar == '':
                st.error('Por favor, preencha todos os campos.')
            else:
                try:
                    conn = sqlite3.connect('MedD.db')
                    cursor = conn.cursor()

                    try:
                        cursor.execute('SELECT Nome, Sobrenome, SenhaFarma FROM Cadastro WHERE LoginFarma = ?', (login,))
                        se_cadastro_existe = cursor.fetchone()

                        if se_cadastro_existe is not None:
                            nome_entrar = se_cadastro_existe[0]
                            sobrenome_entrar = se_cadastro_existe[1]
                            #conferir senha hash
                            senha_login = se_cadastro_existe[2]

                            if senha_login == senha_logar:
                                session_state = get_session()
                                session_state.login_successful = True

                                st.divider()

                                st.subheader(f'Olá, {nome_entrar} {sobrenome_entrar}!')

                                try:
                                    #consulta resumo validades
                                    cursor.execute(f'SELECT COUNT(v.Medicamento) AS Qtt, c.Farmacia FROM Validades v JOIN Cadastro c ON v.LoginFarma = c.LoginFarma WHERE v.Data_vencimento <= date("now", "+30 days") AND v.LoginFarma = ? GROUP BY c.Farmacia', (login,))
                                    resultado_validade_cadastro = cursor.fetchone()

                                    if resultado_validade_cadastro is not None:
                                        quantidade_vencendo = resultado_validade_cadastro[0]
                                        farmacia_vencendo = resultado_validade_cadastro[1]

                                        st.info(f":warning: **Atenção:** Você tem **{quantidade_vencendo}** medicamentos vencendo em até **30 dias** na farmácia {farmacia_vencendo}.")
                                    else:
                                        st.info(f":thumbsup: Tudo tranquilo por aqui. Você **não** tem medicamentos vencendo em até **30 dias**.")

                                    st.divider()

                                    #consulta resumo faltas
                                    cursor.execute('SELECT cf.Medicamento, COUNT(cf.Medicamento) AS QttFaltas, cf.Tasy FROM ControleFaltas cf JOIN Cadastro c ON cf.Farmacia = c.Farmacia WHERE cf.Data_falta <= date("now", "+30 days") AND cf.LoginFarma = ? GROUP BY cf.Medicamento, cf.Tasy, c.Farmacia ORDER BY QttFaltas DESC', (login,))
                                    resultado_resumo_faltas = cursor.fetchall()

                                    if resultado_resumo_faltas:
                                        st.info("Há faltas adicionadas nos últimos **30 dias** para os seguintes medicamentos:")
                                        for medicamento, qtd_faltas, tasy_controle in resultado_resumo_faltas:
                                            st.info(f"- **{qtd_faltas}** faltas de **{medicamento}** | Tasy: **{tasy_controle}**")
                                    
                                    else:
                                        st.info("Você não teve faltas adicionadas nos últimos 30 dias.")

                                except Exception as e:
                                    print(f"Erro: {e}")
                            else:
                                st.error('Senha incorreta.')
                        
                        else:
                            st.error("Acho que não te conheço. Que tal criar seu cadastro rapidinho?")

                    except Exception as e:
                        print(f"Fazendo resumo para apresentar. Erro: {e}")

                except pyodbc.Error as e:
                    print(f"Erro na conexão: {e}")
                    st.toast("Sem conexão. Entre em contato.")

    with cadastrar:
        with st.container():
            st.subheader("Me conte sobre você")
            nome_cadastro = st.text_input("Qual é o seu nome?")
            sobrenome_cadastro = st.text_input("Qual é seu sobrenome?")
            login_cadastro = st.text_input("Crie um login")
            email_cadastro = st.text_input("Informe um email - ele servirá para recuperar sua conta")
            senha_cadastro = st.text_input("Agora crie uma senha", type="password")
            senha_cadastro_confirmar = st.text_input("Repita sua senha", type='password')
            #fazer hash da senha
            st.divider()
            farmacia_cadastro = st.radio("Qual é a sua farmácia?", ["Emergência", "Central", "CAF", "Endovascular", "Centro Obstétrico", "Bloco Cirúrgico"], index=None)
            enviar_cadastro = st.button("Fazer cadastro", type="primary")

            if enviar_cadastro:
                if nome_cadastro == '' or sobrenome_cadastro == '' or farmacia_cadastro == '' or login_cadastro == '' or senha_cadastro == '' or senha_cadastro_confirmar == '' or email_cadastro == '':
                    st.error("Por favor, preencha todas as informações")
                elif senha_cadastro != senha_cadastro_confirmar:
                    st.error('Suas senhas são diferentes')
                else:
                    try:
                        conn = sqlite3.connect('MedD.db')
                        cursor = conn.cursor()

                        try:
                            cursor.execute('INSERT INTO Cadastro (LoginFarma, SenhaFarma, Nome, Sobrenome, Farmacia, Email) VALUES (?, ?, ?, ?, ?, ?)', (login_cadastro, senha_cadastro, nome_cadastro, sobrenome_cadastro, farmacia_cadastro, email_cadastro))

                            time.sleep(.1)
                            st.toast("Salvando informações...")
                            time.sleep(2)
                            st.success('Cadastro criado com sucesso!')

                            conn.commit()
                        
                        except Exception as e:
                            print(f"Erro: {e}")
                            time.sleep(.1)
                            st.toast("Salvando informações...")
                            time.sleep(2)
                            st.error('Não foi possível fazer o cadastro.')

                        finally:
                            cursor.close()
                            conn.close()
                    
                    except Exception as e:
                        print(f"Erro na conexão: {e}")
                        st.toast("Sem conexão. Entre em contato.")
    with esqueci:
        st.subheader('Esqueceu a senha?')
        login_esqueci = st.text_input('Insira seu login')

        try:
            conn = sqlite3.connect('MedD.db')
            cursor = conn.cursor()

            cursor.execute('SELECT SenhaFarma, Nome, Sobrenome, Email FROM Cadastro WHERE LoginFarma = ?', (login_esqueci,))
            result_perguntas = cursor.fetchone()
            
            if result_perguntas is not None:
                senha_farma_retornada = result_perguntas[0]
                nome_farma = result_perguntas[1]
                sobrenome_farma = result_perguntas[2]
                email_farma = result_perguntas[3]

                st.divider()
                st.subheader('Recuperar senha')
                
                email_esqueci = st.text_input('Insira seu email cadastrado')

                assunto = 'Recuperação de senha'
                corpo_email = f"""
                <h2>Olá, {nome_farma} {sobrenome_farma}!</h2>
                <p>Sua senha é: <b>{senha_farma_retornada}</b>.
                <p>Atenciosamente,</p>
                <p><b>medD.</b></p>
                <small>Para dúvidas, sugestões ou reclamações: vinicius.vods.dev@gmail.com</small>
                <img src="https://i.imgur.com/RDJRyGx.png" alt="logo medd" style="width:200px;height:200px;">
                """

                msg = EmailMessage()
                msg.set_content(corpo_email, subtype="html")
                msg['Subject'] = 'Recuperar sua senha'
                msg['From'] = 'medD.informacao@gmail.com'
                msg['To'] = email_farma
                password = 'sekd nvmd nxyu wdry'

                if st.button('Enviar email', type='primary'):
                    try:
                        conn = sqlite3.connect('MedD.db')
                        cursor = conn.cursor()
                        try:
                            cursor.execute('SELECT Email, LoginFarma FROM Cadastro WHERE LoginFarma = ?', (login_esqueci,))
                            result_email_esqueci = cursor.fetchone()

                            if result_email_esqueci:
                                email_retornado_esqueci = result_email_esqueci[0]
                                login_email_esqueci = result_email_esqueci[1]

                                if email_retornado_esqueci != email_esqueci:
                                    st.error('Este email não confere com o email cadastrado.')
                                else:
                                    # Enviar o email
                                    try:
                                        with smtplib.SMTP('smtp.gmail.com', 587) as s:
                                            s.starttls()
                                            s.login(msg['From'], password)
                                            s.send_message(msg)
                                            s.quit()
                                        st.success('Email enviado com sucesso!')
                                    except:
                                        st.error('Não foi possível enviar o email.')
                        
                        except Exception as e:
                            print(f"Erro: {e}")

                    except Exception as e:
                        print(f"Erro: {e}")

                st.divider()

                st.subheader('Alterar senha')
                senha_antiga = st.text_input('Insira sua senha atual', type='password')
                nova_senha = st.text_input('Insira a nova senha', type='password')
                nova_senha_confirma = st.text_input('Insira a nova senha mais uma vez', type='password')

                alterar_btn = st.button('Alterar', type='primary')
                if alterar_btn:
                    if nova_senha != nova_senha_confirma:
                        st.error('Suas senhas são diferentes.')
                    else:
                        try:
                            conn = sqlite3.connect('MedD.db')
                            cursor = conn.cursor()

                            cursor.execute('UPDATE Cadastro SET SenhaFarma = ? WHERE SenhaFarma = ? and LoginFarma = ?', (nova_senha, senha_antiga, login_esqueci))
                            conn.commit()
                            st.success('Senha alterada com sucesso!')
                        except:
                            st.error('Não foi possível alterar sua senha.')
            
            else:
                st.error('Acho que eu não te conheço. Que tal criar seu cadastro rapidinho?')

        except Exception as e:
            print(f"Erro: {e}")

# *VALIDADES
elif menu == "Validades":
    check_login()
    with st.container():
        adicionar_tab, pesquisar_tab, excluir_tab = st.tabs(['Adicionar validades', 'Pesquisar validades', 'Excluir validades'])
        with adicionar_tab:
            st.title("Adicionar validades")
            login_validades = st.text_input("Insira seu login")

            st.subheader("Dados do medicamento")

            medicamento = st.selectbox("Insira o medicamento", nome_medicamentos)
            tasy_selecionado = None
            for id_medicamento, nome_medicamento in mapa_medicamentos.items():
                if nome_medicamento == medicamento:
                    tasy_selecionado = id_medicamento
                    break
            
            tasy = st.text_input("Tasy do medicamento", value=tasy_selecionado)

            if medicamento == 'Outro':
                st.divider()
                st.subheader('Insira as informações do medicamento sem cadastro')
                medicamento = st.text_input('Insira o medicamento')
                tasy = st.number_input('Insira o Tasy deste medicamento', value=1)

            lote = st.text_input("Insira o lote do medicamento")
            quantidade_validade = st.number_input("Insira a quantidade para este lote", value=0)

            st.subheader("Data de vencimento")
            
            data_vencimento = st.date_input("Insira a data de vencimento", format="DD/MM/YYYY")

            def add():
                # Estabeleça a conexão
                try:
                    conn = sqlite3.connect('MedD.db')
                    cursor = conn.cursor()

                    try:
                        cursor.execute('SELECT LoginFarma FROM Cadastro WHERE LoginFarma = ?', (login_validades,))
                        resultado_verificar_login = cursor.fetchone()

                        if resultado_verificar_login is None:
                            st.error('Não há cadastro para este login.')
                        else:
                            # # Execute a consulta
                            try:
                                # data_vencimento_formatada = data_vencimento.strftime('%d/%m/%Y')
                                cursor.execute("INSERT INTO Validades (LoginFarma, Tasy, Medicamento, Lote, Quantidade, Data_vencimento) VALUES (?, ?, ?, ?, ?, ?)", (login_validades, tasy, medicamento, lote, quantidade_validade, data_vencimento))

                                time.sleep(.1)
                                st.toast("Adicionando...")
                                time.sleep(2)
                                st.success("Validade adicionada com sucesso.")

                                conn.commit()

                            except Exception as e:
                                print(f"Erro: {e}")
                                time.sleep(.1)
                                st.toast("Adicionando...")
                                time.sleep(2)
                                st.error('Validada já adicionada.')

                            finally:
                                cursor.close()
                                conn.close()
                    except Exception as e:
                        print(f'Erro ao conectar para verificar email: {e}.')

                except pyodbc.Error as e:
                    print(f"Erro na conexão: {e}")
                    st.toast("Sem conexão. Entre em contato.")

            botao_adicionar = st.button("Adicionar", type="primary")
            if botao_adicionar:
                if login_validades == '' or tasy == '-' or medicamento == '-' or lote == '' or data_vencimento == '' or tasy == 0 or quantidade_validade == 0:
                    st.error("Por favor, preencha todas as informações")
                else:
                    add()

# *RETORNAR VALIDADES
    with st.container():
        with pesquisar_tab:
            st.title("Pesquisar validades")
            login_validade_pesquisar = st.text_input("Insira seu login para pesquisar suas validades")
            intervalo_validades_pesquisar = st.number_input("Insira o intervalo de dias", value=30)

            botao_pesquisar = st.button("Pesquisar", type="primary")

            if botao_pesquisar:

                conn = sqlite3.connect('MedD.db')
                cursor = conn.cursor()

                result_proxy = cursor.execute(f"SELECT Tasy, Medicamento, Lote, strftime('%d/%m/%Y', Data_vencimento) AS DataFormatada, Quantidade FROM Validades WHERE LoginFarma = ? AND Data_vencimento <= date('now', '+{intervalo_validades_pesquisar} days') ORDER BY Data_vencimento ASC", (login_validade_pesquisar,))

                resultados = []

                while True:
                    resultado = result_proxy.fetchone()
                    if resultado is None:
                        break
                    resultados.append(resultado)     

                if resultados:
                    num_colunas = len(resultados[0])
                    resultados = [list(row) for row in resultados]

                    df_validades = pd.DataFrame(resultados, columns=['Tasy', 'Medicamento', 'Lote', 'Data de vencimento', 'Quantidade'])

                    df_validades['Tasy'] = df_validades['Tasy'].astype(str)

                    st.dataframe(df_validades, use_container_width=True, hide_index=True)

                    def create_pdf(df):
                        # Criação de um arquivo PDF
                        buffer = BytesIO()
                        pdf_canvas = canvas.Canvas(buffer, pagesize=letter)

                        today_str = hoje.strftime("%d/%m/%Y")
                        gerado_em_msg = f"Gerado em {today_str}"
                        pdf_canvas.setFont("Helvetica", 10)
                        pdf_canvas.drawString(50, 780, gerado_em_msg)
                        
                        # Adicionando título
                        pdf_canvas.setFont("Helvetica-Bold", 14)
                        pdf_canvas.drawCentredString(300, 750, "Resumo de Medicamentos")
                        pdf_canvas.setFont("Helvetica", 12)
                        pdf_canvas.drawCentredString(300, 730, f"Medicamentos que vão vencer em até {intervalo_validades_pesquisar} dias")

                        # Reorganizando as colunas no DataFrame
                        df = df[['Medicamento', 'Tasy', 'Data_vencimento', 'Lote', 'Quantidade']]

                        medicamento_width = max(pdf_canvas.stringWidth(str(cell), "Helvetica", 10) for cell in df['Medicamento'])

                        # Adicionando a tabela
                        data = [df.columns.values.astype(str).tolist()] + df.values.tolist()
                        pdf_canvas.setFont("Helvetica", 10)

                        # Ajustando a largura de cada coluna
                        col_widths = [medicamento_width] + [max(pdf_canvas.stringWidth(str(cell), "Helvetica", 10), 50) for cell in data[0][1:]]

                        row_height = 15
                        for i, row in enumerate(data):
                            y = 700 - i * row_height
                            x = (pdf_canvas._pagesize[0] - sum(col_widths) - 10 * (len(col_widths) - 1)) / 2
                            for j, text in enumerate(row):
                                cell_width = col_widths[j] + 10
                                if df.columns[j] == 'Medicamento' and df.columns[j + 1] == 'Data_vencimento':
                                    # Adiciona um espaçamento extra entre 'Medicamento' e 'Data_vencimento'
                                    cell_width += 20
                                pdf_canvas.drawString(x, y, str(text)[:50])  # Limita o texto a 50 caracteres por célula
                                x += cell_width
                            
                            # Adicionando divider centralizado com cor personalizada
                            divider_color = (0, 0, 0)  # Cor azul para o divider (R, G, B)
                            divider_width_percentage = 80  # Largura percentual do divider

                            pdf_canvas.setLineWidth(1)  # Largura da linha do divider em pontos
                            pdf_canvas.setStrokeColorRGB(*divider_color)
                            
                            divider_width = pdf_canvas._pagesize[0] * (divider_width_percentage / 100)
                            divider_x_start = (pdf_canvas._pagesize[0] - divider_width) / 2
                            divider_x_end = divider_x_start + divider_width
                            divider_y = y - 4  # Posição vertical da linha de divisão

                            pdf_canvas.line(divider_x_start, divider_y, divider_x_end, divider_y)
                        
                        # Salvando o PDF
                        pdf_canvas.save()
                        buffer.seek(0)
                        return buffer.read()
                    
                    hoje = datetime.date.today()
                    today = pd.to_datetime(hoje)
                    tres_meses = today + datetime.timedelta(days=intervalo_validades_pesquisar)

                    query = f"SELECT Medicamento, strftime('%d/%m/%Y', Data_vencimento) AS Data_vencimento, Lote, Tasy, Quantidade FROM Validades WHERE Data_vencimento <= date('now', '+{intervalo_validades_pesquisar} days') ORDER BY Data_vencimento ASC"
                    # print(query)
                    df = pd.read_sql_query(query, conn)

                    create_pdf(df)

                    st.download_button("Baixar PDF", data=create_pdf(df), file_name="resumo_medicamentos.pdf", key="download_pdf")

                else:
                    st.error("Nenhuma informação para este login.")

                cursor.close()
                conn.close()

# *EXCLUIR VALIDADES
    with st.container():
        with excluir_tab:
            st.title("Excluir validade adicionada")

            login_excluir = st.text_input("Informe seu login")

            lote_excluir = st.text_input("Informe o lote do medicamento que você quer excluir")
            botao_excluir = st.button("Excluir", type="primary")

            if botao_excluir:
                conn = sqlite3.connect('MedD.db')
                cursor = conn.cursor()

                if lote_excluir == '' or login_excluir == '':
                    st.error("Por favor, preencha todas as informações")
                else:
                    try:
                        time.sleep(.1)
                        st.toast("Excluindo...")

                        cursor.execute("DELETE FROM Validades WHERE Lote = ? AND LoginFarma = ?", (lote_excluir, login_excluir))
                        cursor.commit()

                        time.sleep(2)
                        st.toast("Validade excluída!")
                    
                    except Exception as e:
                        st.toast("Não foi possível excluir esta validade.")

                    finally:
                        cursor.close()
                        conn.close()
# *ESTOQUE
elif menu == "Estoque":
    check_login()

    st.title("Estoque")
    st.subheader("Adicione a quantidade de saídas dos últimos três meses e descubra seu estoque padrão ideal")
    with st.container():
        antepe = st.number_input("Antepenúltimo mês", value=1)
        penul = st.number_input("Penúltimo mês", value=1)
        ultimo = st.number_input("Último mês", value=1)

        # Cálculo variação
        penul_antepe = round((int(penul) - int(antepe)) / int(antepe) * 100)
        ulti_penul = round((int(ultimo) - int(penul)) / int(penul) * 100)
        media_mes = round((int(antepe) + int(penul) + int(ultimo)) / 3)
        calculo_variacao = int(ulti_penul) + int(penul_antepe)

        # Média por dia dos últimos meses
        dias_antepe = int(antepe) / 30.41
        dias_penul = int(penul) / 30.41
        dias_ulti = int(ultimo) / 30.41
 
        media_todos_meses = (float(dias_antepe) + float(dias_penul) + float(dias_ulti)) / 3
        ideal_um_dia = math.ceil(media_todos_meses)
        ideal_tres_dias = ideal_um_dia * 3
        mais_20_porcento = (ideal_um_dia * 30) * 0.2
        ideal_um_mes = int(ideal_um_dia * 30) + int(mais_20_porcento)

        st.divider()

        st.write(f"O estoque padrão ideal para um dia é: **{ideal_um_dia}**")
        st.write(f"O estoque padrão ideal para três dias é: **{ideal_tres_dias}**")
        st.write(f"O estoque padrão ideal para um mês é: **{ideal_um_mes}***")
        st.caption("*Cálculo padrão ideal + 20%")

        ante_mes, penul_mes, ult_mes = st.columns(3)

        dias_antepe_round = round(dias_antepe, 1)
        dias_penul_round = round(dias_penul, 1)
        dias_ulti_round = round(dias_ulti, 1)

        with ante_mes:
            st.metric(label="Média diária do antepenúltimo mês", value=f"{dias_antepe_round}")
        with penul_mes:
            st.metric(label="Média diária do penúltimo mês", value=f"{dias_penul_round}", delta=f"{penul_antepe}%")
        with ult_mes:
            st.metric(label="Média diária do último mês", value=f"{dias_ulti_round}", delta=f"{ulti_penul}%")

        st.metric(label="Média dos últimos três meses", value=f"{media_mes}", delta=f"{calculo_variacao}%")

        if calculo_variacao >= 100:
            st.write(f":warning: A quantidade de saídas aumentou em :green[{calculo_variacao}%] nos últimos meses. Talvez o estoque precise ser ainda maior do que o recomendado.")
        elif calculo_variacao <= -50:
            st.markdown(f":warning: A quantidade de saídas diminuiu em :red[{calculo_variacao}%] nos últimos meses. Talvez o estoque precise ser ainda menor do que o recomendado.")
        else:
            pass

        st.divider()

        with st.expander('Que cálculos foram usados?'):
            st.markdown('**Variação**: para encontrar a variação (%) da quantidade de dispensações de um mês para o outro, calculamos (**mês atual** - **mês anterior**) / **mês anterior** * 100.')
            st.markdown('**Média diária**: calcula-se a média diária de dispensações de um medicamento dividindo a quantidade total de dispensações no mês por **30,41**.')
            st.markdown('**Estoque ideal para um dia**: para encontrarmos o estoque ideal para um dia, primeiro precisamos encontrar a média da média diária dos últimos meses, ou seja, **média diária mês 1** + **média diária mês 2** + **média diária mês 3** / 3.')
            st.markdown('**Estoque ideal para três dias**: encontramos o estoque ideal para três dias multiplicando o estoque ideal para um dia por 3.')
            st.markdown('**Estoque ideal para um mês**: o estoque ideal para um mês é calculado multiplicando o estoque ideal para um dia por 30,41, e multiplicando por 0,2 em seguida, o que adiciona uma margem de segurança de 20% no estoque, ou seja, (**estoque ideal um dia** * **30,41**) * **0,2**.')
            st.caption('*Se você quiser optar por uma margem de segurança ainda maior, por exemplo, 30%, substitua 0,2, por 0,3.')

# *FALTAS
elif menu == 'Faltas':
    check_login()

    st.title("Faltas")
    st.subheader("Controle as faltas com o registro de cada ocorrência")
    adicionar_falta_tab, pesquisar_falta_tab = st.tabs(['Adicionar falta', 'Pesquisar faltas'])

    with adicionar_falta_tab:
        login_adicionar_faltas = st.text_input('Informe seu login')
        st.divider()
        medicamento_falta = st.selectbox("Insira o nome do medicamento que faltou", nome_medicamentos)
        tasy_selecionado_falta = None
        
        for id_medicamento_falta, nome_medicamento_falta in mapa_medicamentos.items():
            if nome_medicamento_falta == medicamento_falta:
                tasy_selecionado_falta = id_medicamento_falta
                break

        tasy_selecionado_falta = st.text_input('Insira o Tasy do medicamento que faltou', value=tasy_selecionado_falta)

        quantidade_falta = st.number_input("Insira a quantidade que faltou", value=1)
        data_falta = st.date_input("Insira o dia que este medicamento faltou", format="DD/MM/YYYY")
        farmacia_falta = st.selectbox("Informe em qual farmácia este medicamento faltou", options=['','Emergência','Central', 'CAF', 'Endovascular', 'Centro Obstétrico', 'Bloco Cirúrgico'])

        adicionar_falta = st.button("Adicionar", type="primary")
        if adicionar_falta:
            if tasy_selecionado_falta == '' or medicamento_falta == '' or quantidade_falta == '' or data_falta == '' or farmacia_falta == '' or quantidade_falta == 0:
                st.error("Por favor, preencha todas as informações")
            else:
                try:
                    conn = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};Server=VINÖCIUSDESKTOP;Database=Medd2;Trusted_Connection=yes;")
                    cursor = conn.cursor()

                    # # Execute a consulta
                    try:
                        cursor.execute("INSERT INTO ControleFaltas (LoginFarma, Tasy, Medicamento, Quantidade, Farmacia, Data_falta) VALUES (?, ?, ?, ?, ?, ?)", login_adicionar_faltas, tasy_selecionado_falta, medicamento_falta, quantidade_falta, farmacia_falta, data_falta)

                        time.sleep(.1)
                        st.toast("Adicionando...")
                        time.sleep(2)
                        st.toast("Falta adicionada com sucesso!")

                        conn.commit()

                    except Exception as e:
                        st.toast("Não foi possível adicionar esta falta. Entre em contato.")

                    finally:
                        cursor.close()
                        conn.close()

                except pyodbc.Error as e:
                    st.toast("Sem conexão. Entre em contato.")
        

# *PESQUISAR FALTAS
    with pesquisar_falta_tab:
        st.subheader("Pesquise as faltas adicionadas nos últimos dias")
        login_farma_faltas = st.text_input('Insira seu login')
        farmacia_falta_pesquisar = st.selectbox("Farmácia", options=['', 'Emergência','Central', 'Endovascular', 'Centro Obstétrico', 'Bloco Cirúrgico'])
        intervalo = st.number_input("Intervalo de dias", value=30)

        pesquisar_falta = st.button("Pesquisar", type="primary")
        if pesquisar_falta:
            if farmacia_falta_pesquisar == '' or login_farma_faltas == '':
                st.error('Por favor, preencha todos os campos.')
            else:
                st.divider()
                conn = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};Server=VINÖCIUSDESKTOP;Database=Medd2;Trusted_Connection=yes;")
                cursor = conn.cursor()
                
                cursor.execute(f'SELECT Tasy, Medicamento, Quantidade, strftime("%d/%m/%Y", Data_vencimento), Farmacia, LoginFarma FROM ControleFaltas WHERE LoginFarma = ? AND Farmacia = ? AND Data_falta >= DATEADD(DAY, -{intervalo}, GETDATE())', login_farma_faltas, farmacia_falta_pesquisar)
                resultado_falta_pesquisar = cursor.fetchall()

                cursor.execute(f'SELECT Medicamento, COUNT(Medicamento), SUM(Quantidade) FROM ControleFaltas WHERE Data_falta >= DATEADD(DAY, -{intervalo}, GETDATE()) AND LoginFarma = ? AND Farmacia = ? GROUP BY Medicamento', login_farma_faltas, farmacia_falta_pesquisar)
                resultado_info_faltas = cursor.fetchall()

                medicamentos_com_quantidade_suficiente = [(medicamento_suficiente, vezes_suficiente, quantidade_suficiente) for medicamento_suficiente, vezes_suficiente, quantidade_suficiente in resultado_info_faltas if vezes_suficiente >= 3]

                if medicamentos_com_quantidade_suficiente:
                    st.info(f"Medicamentos com 3 ou mais faltas nos últimos {intervalo} dias:")
                    for medicamento_suficiente, vezes_suficiente, quantidade_suficiente in medicamentos_com_quantidade_suficiente:
                        st.info(f":warning: **{medicamento_suficiente}** **|** Quantidade de faltas: **{vezes_suficiente}** **|** Unidades ausentes: **{quantidade_suficiente}**")

                resultado_falta_pesquisar = [(str(row[0]), *row[1:]) for row in resultado_falta_pesquisar]

                if resultado_falta_pesquisar:
                    df = pd.DataFrame(
                        {
                            'Tasy': [row[0] for row in resultado_falta_pesquisar],
                            'Medicamento': [row[1] for row in resultado_falta_pesquisar],
                            'Quantidade': [row[2] for row in resultado_falta_pesquisar],
                            'Data da Falta': [row[3] for row in resultado_falta_pesquisar],
                            'Farmácia': [row[4] for row in resultado_falta_pesquisar]
                        }
                    )

                    st.dataframe(df, use_container_width=True, hide_index=True)

                else:
                    st.info(f'Não há faltas adicionadas para este login na farmácia **{farmacia_falta_pesquisar}** nos últimos {intervalo} dias. :thumbsup:')

elif menu == 'Passar plantão':
    # st.subheader('Passagem de plantão')
    passar_plantao, pesquisar_plantao = st.tabs(['Passar plantão', 'Pesquisar plantão'])

    with passar_plantao:
        st.markdown('<h1 style="text-align: center;">Passagem de Plantão</h1>', unsafe_allow_html=True)
        # st.markdown("<h2 style='text-align: center; margin-bottom: 5%;'>Farmácia Central</h2>", unsafe_allow_html=True)

        data_hoje = datetime.date.today()
        data_formatada = data_hoje.strftime('%d/%m/%Y')

        cData, cTurno = st.columns(2)
        with cData:
            st.header(data_formatada)

        with cTurno:
            turno = st.selectbox('Turno', ('Manhã', 'Tarde', 'Noite'), index=None, placeholder='Informe o turno')

        faltas_plantao = st.selectbox('Há faltas de medicamentos?', ('Sim', 'Não'), index=None, placeholder='')
        if faltas_plantao == 'Sim':
            faltas_plantao = st.text_input('Insira quais medicamentos estão em falta', placeholder='Por favor, separe com vírgula se houver mais de um medicamento. Ex: Dipirona, Morfina...')
            st.divider()

        geladeira = st.selectbox('Há medicamentos na geladeira?', ('Sim', 'Não'), index=None, placeholder='')
        if geladeira == 'Sim':
            geladeira = st.text_input('Por favor, informe qual medicamento e setor')
            st.divider()

        cCaf, cAlmox, = st.columns(2)

        with cCaf:
            caf = st.selectbox('CAF foi conferida?', ('Sim', 'Não'), index=None, placeholder='')
            if caf == 'Não':
                caf = st.selectbox('Insira o motivo', ('Não foi entregue', 'Não houve tempo', 'Outro'), index=None, placeholder='')
                if caf == 'Outro':
                    caf = st.text_input('Motivo')
                    cafnao = 'Não. ' + caf
                    st.divider()

        with cAlmox:
            almox = st.selectbox('Almox foi conferido?', ('Sim', 'Não'), index=None, placeholder='')
            if almox == 'Não':
                almox = st.selectbox('Por qual motivo?', ('Não foi entregue', 'Não houve tempo', 'Outro'), index=None, placeholder='')
                if almox == 'Outro':
                    almox = st.text_input('Especifique o motivo')
                    almoxnao = 'Não. ' + almox
                    st.divider()

        farmaceutico_plantao = st.text_input('Farmacêutico')
        equipe = st.text_input('Equipe')

        meta = st.selectbox('Meta', ('Verde', 'Azul', 'Amarela', 'Laranja', 'Vermelha'), index=None, placeholder='')
        if meta == 'Verde':
            st.success('Plantão sem ocorrências. :thumbsup:')
        elif meta == 'Azul':
            st.info('Circunstâncias de risco. :sweat_smile:')
        elif meta == 'Amarela':
            st.warning('Quase falha. :fearful:')
        elif meta == 'Laranja':
            st.error('Evento, mas sem danos. :grimacing:')
        elif meta == 'Vermelha':
            st.error('Evento adverso. :slightly_frowning_face:')
        else:
            pass

        descricao = st.text_area('Como foi o dia?', placeholder='Há algo importante que precise ser informado para a próxima equipe?')

        confirmar_plantao = st.checkbox('Confirmo que todas as informações foram conferidas.')

        nome_passagem = st.text_input('Nome de quem está passando o plantão')

        passar = st.button('Passar plantão', type='primary')
        if passar:
            if faltas_plantao is None or geladeira is None or caf == '' or caf is None or almox == '' or almox is None or farmaceutico_plantao == '' or len(equipe) <= 3 or meta is None:
                st.error('Por favor, preencha todos os campos.')
            if len(descricao) <= 5:
                st.error('Por favor, elabore um pouco mais a descrição.')
            else:
                if confirmar_plantao is False:
                    st.error('Por favor, confirme que está tudo correto.')
                else:
                    try:
                        cursor.execute("INSERT INTO Plantao (Data_plantao, Turno, Faltas, Geladeira, Caf, Almox, Meta, Farma, Equipe, Descricao, Nome_passagem) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (data_formatada, turno, faltas_plantao, geladeira, cafnao, almoxnao, meta, farmaceutico_plantao, equipe, descricao, nome_passagem))
                        conn.commit()

                        time.sleep(2)
                        st.success(f'Plantão passado com sucesso! Bom descanso, {nome_passagem}.')

                    except Exception as e:
                        # st.write(f'Não foi possível adicionar à tabela plantão. Erro: {e}')
                        st.error('Já existe uma passagem de plantão para esta data e turno.')

    
    with pesquisar_plantao:
        st.subheader('Pesquisar plantão')
        dataPesquisarPlantao = st.date_input('Insira a data', format="DD/MM/YYYY")
        turno_pesquisar_op = ['Manhã', 'Tarde', 'Noite']
        turnoPesquisarPlantao = st.selectbox('Insira o turno', options=turno_pesquisar_op)

        pesquisar_plantao_btn = st.button('Pesquisar plantão', type='primary')

        if pesquisar_plantao_btn:
            dataPesquisarPlantaoFormatada = dataPesquisarPlantao.strftime('%d/%m/%Y')
            cursor.execute('SELECT * FROM Plantao WHERE Data_plantao = ? AND Turno = ?', (dataPesquisarPlantaoFormatada, turnoPesquisarPlantao,))
            resultado_plantao  = cursor.fetchone()

            if resultado_plantao:
                st.divider()
                st.subheader(f'Plantão dia {dataPesquisarPlantaoFormatada} | Turno: {turnoPesquisarPlantao}')
                st.write(f'**Faltas:** {resultado_plantao[2]}')
                st.write(f'**Geladeira:** {resultado_plantao[3]}')
                st.write(f'**CAF conferida:** {resultado_plantao[4]}')
                st.write(f'**Almox conferido:** {resultado_plantao[5]}')
                st.write(f'**Meta:** {resultado_plantao[6]}')
                st.write(f'**Farmacêutico:** {resultado_plantao[7]}')
                st.write(f'**Equipe:** {resultado_plantao[8]}')
                st.write(f'**Descrição:** {resultado_plantao[9]}')
                st.write(f'**Quem passou o plantão:** {resultado_plantao[10]}')
            else:
                st.error('Sem informações para esta data e turno.')

elif menu == 'Sair':
    session_state = get_session()
    session_state.login_successful = False
    st.success('Você se desconectou com sucesso. Até a próxima! :thumbsup:')