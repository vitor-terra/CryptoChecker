import requests
import streamlit as st
from datetime import datetime
import time
import pandas as pd
import altair as alt
import base64

###################------------------INSTRUÇÕES------------------###################

#PARA ACESSAR O APLICATIVO, SIMPLESMENTE ABRA O SEGUINTE LINK NO SEU NAVEGADOR DE PREFERÊNCIA:
# https://crypto-checker.streamlit.app/

#AS INSTRUÇÕES ABAIXO SÃO PARA RODAR O PROGRAMA LOCALMENTE, CASO QUEIRA

# 1. PARA RODAR O PROGRAMA VOCÊ DEVE PRIMEIRO INSTALAR OS MÓDULOS NECESSÁRIOS. ISSO É FEITO ATRAVÉS DOS SEGUINTES COMANDOS:
#PODE SER INTERESSANTE CRIAR UM AMBIENTE VIRTUAL ANTES DE INSTALAR OS MÓDULOS, CASO NÃO QUEIRA INSTALÁ-LOS GLOBALMENTE

#pip install streamlit
#Streamlit é usado para fazer a interface do programa, onde são exibidos os gráficos e permite a interação com o usuário

#pip install requests
#Requests é o módulo usado para fazer requisições para a API

#pip install pandas
#Pandas é usado para manipular os dados obtidos da API

#pip install altair
#Altair é usado para plotar os gráficos

#pip install pycoingecko
#Pycoingecko é uma biblioteca que facilita o uso da API da CoinGecko, mas não é estritamente necessária

# Para instalar todas as dependências de uma vez, você pode usar o comando:
# pip install streamlit requests pandas altair pycoingecko

# 2. APÓS INSTALAR OS MÓDULOS NECESSÁRIOS, CERTIFIQUE-SE DE QUE OS ARQUIVOS DE ÁUDIO "audio_higher.mp3" E "audio_lower.mp3" ESTÃO NA MESMA PASTA QUE "main.py"

# 3. ABRA O PROMPT DE COMANDO NA PASTA ONDE ESTÃO OS ARQUIVOS E RODE O COMANDO
#"streamlit run main.py"
#ISSO DEVE ABRIR UMA ABA NO SEU NAVEGADOR PADRÃO ONDE O PROGRAMA SERÁ EXECUTADO

#ESCOLHA AS MOEDAS QUE VOCÊ QUER QUE O SISTEMA ACOMPANHE
#COMO ISTO É APENAS UMA PROVA DE CONCEITO, POR ENQUANTO DEIXAMOS AS OPÇÕES APENAS PARA BITCOIN E ETHEREUM, QUE SÃO ESCOLHAS RELATIVAMENTE POPULARES
#APÓS ESCOLHER AS MOEDAS, ESCOLHA OS LIMITES SUPERIORES E INFERIORES FORA DOS QUAIS VOCÊ GOSTARIA DE RECEBER UMA NOTIFICAÇÃO AUDITIVA
#TAMBÉM APARECERÁ UMA SETINHA INDICANDO CASO A MOEDA ESTEJA FORA DOS LIMITES PROPOSTOS AO LADO DE SEU NOME

#APÓS OS LIMITES TEREM SIDO ESCOLHIDOS, O PROGRAMA VAI ESTAR RODANDO
#DURANTE A EXECUÇÃO, O PROGRAMA SALVA OS DADOS OBTIDOS EM UM ARQUIVO "NomeDaMoeda.txt", PARA ACESSOS FUTUROS

#!!!!!!!CASO QUEIRA FINALIZAR O PROGRAMA, SIMPLESMENTE VÁ ATÉ O TERMINAL ONDE ELE FOI INICIALIZADO E APERTE CTRL+C PARA MATAR O PROGRAMA!!!!!!!

###################---------------FIM DAS INSTRUÇÕES---------------###################

#Tempo mínimo entre chamadas de API para obter os dados atuais. Não deve ser um número muito pequeno para não estourar o limite grátis da API (por padrão o tempo mínimo é de 10 minutos ou 600 segundos)
API_CALL_INTERVAL = 600

#Tempo mínimo entre chamadas de API para obter os dados históricos. Não deve ser um número muito pequeno para não estourar o limite grátis da API (por padrão o tempo mínimo é de 10 minutos ou 600 segundos)
HIST_API_CALL_INTERVAL = 600

#Tempo mínimo de espera para tocar novamente os áudios após eles serem tocados uma vez (por padrão o tempo mínimo é 5 minutos ou 300 segundos)
AUDIO_PLAY_INTERVAL = 300

st.set_page_config(page_title="Crypto Checker", layout="wide")

#Função para tocar audio automaticamente para contornar uma limitação do frontend
def autoplay_audio(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        return md

#Função ajudante para getData abaixo. Recebe uma lista e transforma em uma string separada por vírgulas
def buildCoinList(list):
    str = ""
    for s in list:
        str += f"{s},"
    return str

#Chama a API para colher os dados das criptomoedas
def getData(coin_list, preferred_money, api_key):

    list = buildCoinList(coin_list)
    url = "https://api.coingecko.com/api/v3/simple/price"
    headers = {"x-cg-demo-api-key": api_key}
    querystring = {"vs_currencies":preferred_money,"names":list,"include_market_cap":"true","include_24hr_vol":"true","include_24hr_change":"true","include_last_updated_at":"true"}

    if "last_api_call" not in st.session_state:
        st.session_state["last_api_call"] = 0

    current_time = time.time()
    time_since_last_api_call = current_time - st.session_state["last_api_call"]
    if time_since_last_api_call > API_CALL_INTERVAL:
        st.session_state.currency = preferred_money

        response = requests.get(url, headers = headers, params=querystring, timeout=5)
        response.raise_for_status()
    
        st.session_state["current_data"] = [response.json(), datetime.now()]
        st.session_state["last_api_call"] = current_time

#Mostra o menu de seleção de moedas. Como isto é apenas uma prova de conceito, usamos apenas Ethereum e Bitcoin por enquanto.
def selectCoins():
    options = ["Ethereum", "Bitcoin"]
    selected_coins = st.multiselect(
        "Selecione as criptomoedas que você quer acompanhar",
        options
    )
    if st.button("Confirmar"):
        st.session_state.coins_selected = True
        st.session_state.selected_coins = selected_coins
        st.rerun()

#Exibe as caixas de texto para alterar os limites de cada moeda   
def defineBounds(coin):
    if "bounds" not in st.session_state:
        st.session_state.bounds = {}
        
    if coin not in st.session_state.bounds:
        st.session_state.bounds[coin] = {"invalid_bounds": False} #Isto é para o sistema saber quando mostrar a mensagem de "Digite apenas valores numéricos" caso o usuário digite valores sem sentido
        st.session_state.bounds[coin]["bounds_saved"] = False #Isto é para o sistema saber a partir de qual momento ele pode tentar verificar os limites


    with st.form(key = coin):
        #Mostra a mensagem "Digite apenas valores numéricos" caso o usuário tenha digite coisas sem sentido
        if "invalid_bounds" in st.session_state.bounds[coin]:
            if st.session_state.bounds[coin]["invalid_bounds"]:
                st.write("Digite apenas valores numéricos")

        upper_bound = st.text_input(f"Notificar caso {coin} esteja acima de:")
        lower_bound = st.text_input(f"Notificar caso {coin} esteja abaixo de:")
        submitted = st.form_submit_button("Confirmar")

        if submitted:
            try:
                st.session_state.bounds[coin] = {"upper": float(upper_bound), "lower": float(lower_bound)}
                st.session_state.bounds[coin]["invalid_bounds"] = False
                st.session_state.bounds[coin]["bounds_saved"] = True
                st.success("Informações Salvas")
                st.rerun()

            except ValueError:
                #Caso o usuário tenha digitado coisas sem sentido, da próxima vez que o formulário for renderizado para esta moeda, o sistema saberá mostrar a mensagem "Digite apenas valores numéricos"
                st.session_state.bounds[coin]["invalid_bounds"] = True       

#Usa a chave API fornecida pelo usuário, se não, usa a chave gratuita de um dos integrantes da dupla para rodar o programa.
def getApiKey():
    if "api_key" not in st.session_state:
        st.session_state.api_key = "CG-4xpQ29PLjhe6bmSBtYXVztM9"

    st.session_state.api_key = st.sidebar.text_input("Digite sua própria chave de API aqui. Deixe em branco se quiser usar a chave padrão.")

#Escreve em um arquivo "NomeDaMoeda.txt" os dados que são obtidos
def writeHistoricalData(data):
    for entry in data[0]:
        with open(f"{entry}.txt", "a") as f:
            f.write(str(data[1]) + "\n")
            for item in data[0][entry].items():
                f.write(f"{item[0]}: {item[1]}\n")
            f.write("\n")

#Pega os dados históricos da moeda. A API da CoinGecko permite pegar dados históricos de até 90 dias no plano grátis
def getHistoricalData(coin_id, vs_currency, days):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        prices = data.get("prices", [])
        df = pd.DataFrame(prices, columns=["timestamp", "price"]) #A API retorna os dados em milissegundos
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms") #Converte o timestamp de milissegundos para datetime
        return df
    except Exception:
        return pd.DataFrame(columns=["timestamp", "price"])

#Verifica os limites, retorna -1 caso eles ainda não tenham sido definidos, retorna 1 caso o valor esteja acima dos limites estabelecidos, 2 caso esteja abaixo e 0 caso esteja dentro dos limites
def checkBounds(data, coin):
    if not st.session_state.bounds[coin]["bounds_saved"]:
        return -1
        
    if data[0][coin][st.session_state.currency] > st.session_state.bounds[coin]["upper"]:
        return 1

    if data[0][coin][st.session_state.currency] < st.session_state.bounds[coin]["lower"]:
        return 2
    
    return 0

#Plota o gráfico de preços usando Altair
#Inclui linhas horizontais para os limites superior e inferior, se definidos
def plotPriceChart(dfHist, coin, vsCurrency, upper_bound=None, lower_bound=None):
    if not dfHist.empty:
        # Define os limites do eixo y com base nos dados
        minPrice = float(dfHist["price"].min())
        maxPrice = float(dfHist["price"].max())

        if minPrice == maxPrice:
            pad = max(1.0, abs(minPrice) * 0.001)
            minPrice -= pad
            maxPrice += pad

        zoom = alt.selection_interval(bind='scales', encodings=['y'])

        chart = (
            alt.Chart(dfHist)
            .mark_line()
            .encode(
                x=alt.X("timestamp:T", title="Data"), 
                y=alt.Y(
                    "price:Q",
                    title=f"Preço ({vsCurrency.upper()})", 
                    scale=alt.Scale(domain=[minPrice, maxPrice]),
                ),
                tooltip=[
                    alt.Tooltip("timestamp:T", title="Hora"),
                    alt.Tooltip("price:Q", format=".2f", title="Preço"),
                ],
            )
            .add_params(zoom)
            .properties(height=400)
        )

        # Linha de limite superior
        if upper_bound is not None:
            upper_line = alt.Chart(pd.DataFrame({"y": [upper_bound]})).mark_rule(
                color="red", strokeDash=[6, 4]
            ).encode(y="y:Q")
            chart += upper_line

        # Linha de limite inferior
        if lower_bound is not None:
            lower_line = alt.Chart(pd.DataFrame({"y": [lower_bound]})).mark_rule(
                color="green", strokeDash=[6, 4]
            ).encode(y="y:Q")
            chart += lower_line     

        st.altair_chart(chart, use_container_width=True)
        st.caption(f"Intervalo de valores exibido: {minPrice:.2f} — {maxPrice:.2f} {vsCurrency.upper()}")
    else:
        st.warning(f"Nenhum dado histórico de {coin} encontrado para o período selecionado.") 

def main():
    #Caso as moedas ainda não tenham sido selecionadas, o sistema deve exibir o menu de escolha
    if "coins_selected" not in st.session_state:
        st.session_state.coins_selected = False
    
    #Por padrão, usamos o dólar como moeda de conversão
    if "currency" not in st.session_state:
        st.session_state.currency = "usd"

    #Dicionário que guarda os limites de cada moeda
    if "bounds" not in st.session_state:
        st.session_state.bounds = {}

    if not st.session_state.coins_selected:
        col1, col2, col3 = st.columns([2, 4, 2])
        with col2:
            st.markdown("<h1 style='text-align: center; font-weight: bold; color: #31326F;'>Crypto<span style='color:#3A6F43;'>Checker</span></h1>", unsafe_allow_html=True)
            selectCoins()

    else:
        #Caso as moedas já tenham sido selecionadas, o sistema deve exibir os gráficos e tocar os áudios quando necessário
        selected_coins = st.session_state.get("selected_coins", [])
        if not selected_coins:
            st.warning("Por favor, selecione ao menos uma moeda.")
        else:
            #Mapeia o nome da moeda para o id usado na API
            coin_map = {
                "Bitcoin": "bitcoin",
                "Ethereum": "ethereum",
            }

            st.sidebar.markdown(
                """
                <div style='text-align: center; margin-bottom: 10px;'>
                    <span style='font-size: 32px; font-weight: bold; color: #31326F;'>Crypto<span style='color:#3A6F43;'>Checker</span></span>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.sidebar.markdown("---")

            #Opções de ativo e intervalo de tempo no sidebar
            vsCurrency = st.sidebar.selectbox("Converter ativos para:", ["usd", "brl", "eur"])
            timeRange = st.sidebar.selectbox("Intervalo de tempo:", ["últimas 24h", "última semana", "último mês"])

            getApiKey()
            getData(st.session_state.selected_coins, vsCurrency, st.session_state.api_key)

            current_data = st.session_state.get("current_data", [{}])[0]  # dicionário retornado pela API

            if "current_data" in st.session_state:
                #Escreve em um arquivo os dados históricos em um arquivo
                writeHistoricalData(st.session_state["current_data"])
           
            #Mapeia o intervalo de tempo selecionado para o número de dias correspondente
            daysMap = {"últimas 24h": 1, "última semana": 7, "último mês": 30}
            days = daysMap[timeRange]

            l = []
            i = 0

            for coin in selected_coins:
            #Este loop itera sobre todas as moedas selecionadas e faz algumas coisas, descritas a seguir.

                #Criamos uma lista com um container para cada moeda. O container será usado para exibir o nome da moeda na tela e tocar o audio
                l.append(st.empty())
                l[i].text(coin)

                #Esta função renderiza as caixas de texto que permitem alterar os valores limites de cada moeda
                defineBounds(coin)

                #Checa se o valor atual da moeda está dentro dos limites
                bound_verification = checkBounds(st.session_state["current_data"], coin)

                if bound_verification == 1 or bound_verification == 2:
                #Caso ele esteja fora dos limites, o sistema inicializa uma contagem de tempo para os audios
                #O tempo mínimo entre audios é controlado pela variável "AUDIO_PLAY_INTERVAL", definida na linha 10 (em segundos)
                #Isto é feito para o audio não tocar novamente a cada interação com a interface
                    if f"last_audio{coin}" not in st.session_state:
                        st.session_state[f"last_audio{coin}"] = 0

                    current_time = time.time()
                    if current_time - st.session_state[f"last_audio{coin}"] > AUDIO_PLAY_INTERVAL:
                        st.session_state[f"last_audio{coin}"] = current_time
            
                        if bound_verification == 1:
                        #Se o valor estiver acima do limite, tocamos o arquivo "audio_higher.mp3"
                            l[i].html(autoplay_audio("audio_higher.mp3"))
                            time.sleep(2) #O sistema espera 2 segundos antes de continuar para dar tempo de o audio tocar
                            l[i].text(f"{coin}⬆")
                        

                        if bound_verification == 2:
                            #Se o valor estiver abaixo do limite, tocamos o arquivo "audio_lower.mp3"
                            l[i].html(autoplay_audio("audio_lower.mp3"))
                            time.sleep(2)
                            l[i].text(f"{coin}⬇︎")

                #Incrementamos a posição da lista para criar os containers da próxima moeda na próxima iteração do loop
                i += 1
                
                st.subheader(f"{coin}")
                coin_id = coin_map.get(coin.lower().capitalize(), coin.lower()) #Mapeia o nome da moeda para o id usado na API

                # Pega o preço do dicionário retornado
                price = current_data.get(coin, {}).get(vsCurrency)
                if price is not None:
                    st.metric("Preço Atual", f"{price:.2f} {vsCurrency.upper()}")

                #Fazemos uma contagem de tempo para limitar as chamadas da função "getHistoricalData", pois ela faz uma chamada de API e caso não seja limitada, pode acabar estourando o limite
                current_time = time.time()
                if "hist_data" not in st.session_state:
                    #Se não houverem dados históricos, chamamos a função pela primeira vez
                    st.session_state["hist_data"] = st.session_state["hist_data"] = getHistoricalData(coin_id, vsCurrency, days)

                if "last_hist_data" not in st.session_state:
                    #O sistema incia a contagem de tempo, caso ela ainda não tenha sido iniciada antes
                    st.session_state["last_hist_data"] = current_time
                
                if current_time - st.session_state["last_hist_data"] > HIST_API_CALL_INTERVAL:
                    #Se o tempo mínimo entre as chamadas de API já tiver passado, fazemos a chamada da função.
                    st.session_state["hist_data"] = getHistoricalData(coin_id, vsCurrency, days)
                    st.session_state["last_hist_data"] = current_time

                #Caso o tempo ainda não tenha passado, simplesmente usamos os dados da última chamada
                dfHist = st.session_state["hist_data"]
                
                dfHist = dfHist.dropna(subset=["price"]).copy() # Remove linhas com valores NaN na coluna 'price'
                dfHist["price"] = pd.to_numeric(dfHist["price"], errors="coerce") # Converte a coluna 'price' para numérico, forçando erros a NaN
                dfHist = dfHist.dropna(subset=["price"]) # Remove novamente linhas com valores NaN na coluna 'price', caso a conversão tenha gerado novos NaNs

                bounds = st.session_state.bounds.get(coin, {}) #Pega os limites definidos para a moeda atual
                
                upper = bounds.get("upper", None)
                lower = bounds.get("lower", None)

                # Inicializa o histórico persistente, se necessário
                if "last_valid_df" not in st.session_state:
                    st.session_state.last_valid_df = {}

                # Se há dados válidos, atualiza o gráfico e salva o DataFrame
                if not dfHist.empty:
                    st.session_state.last_valid_df[coin] = dfHist
                    plotPriceChart(dfHist, coin, vsCurrency, upper_bound=upper, lower_bound=lower)
                    st.caption(f"Última atualização {coin}: {datetime.now().strftime('%H:%M:%S')}")
                else:
                    # Se não há dados novos, mantém o último gráfico válido
                    if coin in st.session_state.last_valid_df:
                        plotPriceChart(st.session_state.last_valid_df[coin], coin, vsCurrency, upper_bound=upper, lower_bound=lower)
                    else:
                        st.warning(f"Aguardando dados históricos para {coin}...")

        
        if st.button("Reiniciar Escolha de Moedas"):
            #O botão de reiniciar a seleção simplesmente deleta todos os dados persistentes exceto os tempos das últimas chamadas de API e os dados obtidos por elas
            for key in st.session_state.keys():
                if key == "last_api_call" or key == "current_data" or key == "last_hist_data" or key == "hist_data":
                    continue
                del st.session_state[key]
            st.rerun()

        st.sidebar.markdown("*Dados fornecidos por [CoinGecko](https://www.coingecko.com)")

        #De quanto em quanto tempo o programa deve rodar sem que ocorra interação do usuário. Os audios só podem tocar e os gráficos só são atualizados ao final do time.sleep() abaixo
        #O tempo do time.sleep() é dado em segundos
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()