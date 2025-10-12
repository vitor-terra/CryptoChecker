import requests
import streamlit as st
from datetime import datetime
import time
import pandas as pd
import altair as alt
import base64

API_CALL_INTERVAL = 60

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

def buildCoinList(list):
    str = ""
    for s in list:
        str += f"{s},"
    return str

def getData(coin_list, preferred_money, api_key):
    list = buildCoinList(coin_list)
    url = "https://api.coingecko.com/api/v3/simple/price"
    headers = {"x-cg-demo-api-key": api_key}
    querystring = {"vs_currencies":"brl","names":list,"include_market_cap":"true","include_24hr_vol":"true","include_24hr_change":"true","include_last_updated_at":"true"}

    response = requests.get(url, headers = headers, params=querystring, timeout=5)
    response.raise_for_status()
    return [response.json(), datetime.now()]

# Função para buscar o preço atual de uma cripto sem usar a chave da API
def getCryptoPrice(coin_id, vs_currency="usd"):
    url = f"https://api.coingecko.com/api/v3/simple/price"
    querystring = {"ids": coin_id, "vs_currencies": vs_currency}
    try:
        response = requests.get(url, params=querystring, timeout=5)
        data = response.json()
        return data.get(coin_id, {}).get(vs_currency, None)
    except Exception:
        return None

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
    
def defineBounds():
    selected_coins = st.session_state.selected_coins

    if "bounds" not in st.session_state:
        st.session_state.bounds = {}

    if "current_index" not in st.session_state:
        st.session_state.current_index = 0

    if st.session_state.current_index < len(selected_coins):
        i = st.session_state.current_index
        current_coin = selected_coins[i]

        with st.form(key = current_coin):
            if "invalid_bounds" in st.session_state:
                if st.session_state.invalid_bounds:
                    st.write("Digite apenas valores numéricos")

            upper_bound = st.text_input(f"Notificar caso {current_coin} esteja acima de:")
            lower_bound = st.text_input(f"Notificar caso {current_coin} esteja abaixo de:")
            submitted = st.form_submit_button("Confirmar")

            if submitted:
                try:
                    st.session_state.bounds[current_coin] = {"upper": float(upper_bound), "lower": float(lower_bound)} #mudei isso pra dicionario pra ficar mais claro na hora de chamar
                    st.session_state.invalid_bounds = False
                    st.session_state.current_index += 1
                except ValueError:
                #Tecnicamente, o usuário pode definir um limite superior menor do que o limite inferior se ele quiser. O programa vai se comportar de acordo.
                    st.session_state.invalid_bounds = True
                st.rerun()
    else:
        st.success("Informações salvas")
        st.session_state.bounds_defined = True
        st.button("Ok")

def defineBounds2(coin):
    if "bounds2" not in st.session_state:
        st.session_state.bounds2 = {}
        
    if coin not in st.session_state.bounds2:
        st.session_state.bounds2[coin] = {"invalid_bounds": False} #Isto é para o sistema saber quando mostrar a mensagem de "Digite apenas valores numéricos" caso o usuário digite valores sem sentido
        st.session_state.bounds2[coin]["bounds_saved"] = False #Isto é para o sistema saber a partir de qual momento ele pode tentar verificar os limites


    with st.form(key = coin):
        #Mostra a mensagem "Digite apenas valores numéricos" caso o usuário tenha digite coisas sem sentido
        if "invalid_bounds" in st.session_state.bounds2[coin]:
            if st.session_state.bounds2[coin]["invalid_bounds"]:
                st.write("Digite apenas valores numéricos")

        upper_bound = st.text_input(f"Notificar caso {coin} esteja acima de:")
        lower_bound = st.text_input(f"Notificar caso {coin} esteja abaixo de:")
        submitted = st.form_submit_button("Confirmar")

        if submitted:
            try:
                st.session_state.bounds2[coin] = {"upper": float(upper_bound), "lower": float(lower_bound)}
                st.session_state.bounds2[coin]["invalid_bounds"] = False
                st.session_state.bounds2[coin]["bounds_saved"] = True
                st.success("Informações Salvas")
                st.rerun()

            except ValueError:
                #Caso o usuário tenha digitado coisas sem sentido, da próxima vez que o formulário for renderizado para esta moeda, o sistema saberá mostrar a mensagem "Digite apenas valores numéricos"
                st.session_state.bounds2[coin]["invalid_bounds"] = True       

def getApiKey():
    if "api_key" not in st.session_state:
        st.session_state.api_key = "CG-4xpQ29PLjhe6bmSBtYXVztM9"

    st.session_state.api_key = st.sidebar.text_input("Digite sua própria chave de API aqui. Deixe em branco se quiser usar a chave padrão.")

def writeHistoricalData(data):
    for entry in data[0]:
        with open(f"{entry}.txt", "a") as f:
            f.write(str(data[1]) + "\n")
            for item in data[0][entry].items():
                f.write(f"{item[0]}: {item[1]}\n")
            f.write("\n")

def getHistoricalData(coin_id, vs_currency, days):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        prices = data.get("prices", [])
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    except Exception:
        return pd.DataFrame(columns=["timestamp", "price"])

def checkBounds(data):
    for entry in data[0]:
        if not st.session_state.bounds2[entry]["bounds_saved"]:
            continue
        
        if data[0][entry][st.session_state.currency] > st.session_state.bounds2[entry]["upper"]:
            print(f"{entry} está com valor mais alto do que o limite superior")

        if data[0][entry][st.session_state.currency] < st.session_state.bounds2[entry]["lower"]:
            print(f"{entry} está com valor abaixo do limite inferior")

#Verifica os limites, retorna -1 caso eles ainda não tenham sido definidos, retorna 1 caso o valor esteja acima dos limites estabelecidos, 2 caso esteja abaixo e 0 caso esteja dentro dos limites
def checkBounds2(data, coin):
    if not st.session_state.bounds2[coin]["bounds_saved"]:
        return -1
        
    if data[0][coin][st.session_state.currency] > st.session_state.bounds2[coin]["upper"]:
        return 1

    if data[0][coin][st.session_state.currency] < st.session_state.bounds2[coin]["lower"]:
        return 2
    
    return 0

def plotPriceChart(dfHist, coin, vsCurrency):
    if not dfHist.empty:
        minPrice = float(dfHist["price"].min())
        maxPrice = float(dfHist["price"].max())

        if minPrice == maxPrice:
            pad = max(1.0, abs(minPrice) * 0.001)
            minPrice -= pad
            maxPrice += pad

        chart = (
            alt.Chart(dfHist)
            .mark_line()
            .encode(
                x=alt.X("timestamp:T", title="Data"),
                y=alt.Y(
                    "price:Q",
                    title=f"Preço ({vsCurrency.upper()})",
                    scale=alt.Scale(domain=[minPrice, maxPrice], nice=False),
                ),
                tooltip=[
                    alt.Tooltip("timestamp:T", title="Hora"),
                    alt.Tooltip("price:Q", format=".2f", title="Preço"),
                ],
            )
            .properties(height=400)
            .interactive()
        )

        st.altair_chart(chart, use_container_width=True)
        st.caption(f"Intervalo de valores exibido: {minPrice:.2f} — {maxPrice:.2f} {vsCurrency.upper()}")
    else:
        st.warning(f"Nenhum dado histórico de {coin} encontrado para o período selecionado.") 

def main():

    if "coins_selected" not in st.session_state:
        st.session_state.coins_selected = False
    
    if "bounds_defined" not in st.session_state:
        st.session_state.bounds_defined = False

    if "currency" not in st.session_state:
        st.session_state.currency = "brl"

    if not st.session_state.coins_selected:
        col1, col2, col3 = st.columns([2, 4, 2])
        with col2:
            st.markdown("<h1 style='text-align: center;'>Crypto Checker</h1>", unsafe_allow_html=True)
            selectCoins()
        
    #elif not st.session_state.bounds_defined:
    #    defineBounds()

    else:
        selected_coins = st.session_state.get("selected_coins", [])
        if not selected_coins:
            st.warning("Por favor, selecione ao menos uma moeda.")
        else:
            coin_map = {
                "Bitcoin": "bitcoin",
                "Ethereum": "ethereum",
            }

            vsCurrency = st.sidebar.selectbox("Converter ativos para:", ["usd", "brl", "eur"])
            timeRange = st.sidebar.selectbox("Intervalo de tempo:", ["últimas 24h", "última semana", "último mês"])
           
            daysMap = {"últimas 24h": 1, "última semana": 7, "último mês": 30}
            days = daysMap[timeRange]

            for coin in selected_coins:
                st.subheader(f"{coin}")
                coin_id = coin_map.get(coin.lower().capitalize(), coin.lower())

                price = getCryptoPrice(coin_id, vsCurrency)
                if price is not None:
                    st.metric("Preço Atual", f"{price:.2f} {vsCurrency.upper()}")

                dfHist = getHistoricalData(coin_id, vsCurrency, days)
                
                dfHist = dfHist.dropna(subset=["price"]).copy()
                dfHist["price"] = pd.to_numeric(dfHist["price"], errors="coerce")
                dfHist = dfHist.dropna(subset=["price"])

                plotPriceChart(dfHist, coin, vsCurrency)
                st.caption(f"Última atualização {coin}: {datetime.now().strftime('%H:%M:%S')}")

        
        if st.button("Reniniciar Escolha de Moedas"):
            del st.session_state.coins_selected
            st.rerun()

        getApiKey()

        st.sidebar.markdown("*Dados fornecidos por [CoinGecko](https://www.coingecko.com)")

        if "last_api_call" not in st.session_state:
            st.session_state["last_api_call"] = 0

        current_time = time.time()
        time_since_last_api_call = current_time - st.session_state["last_api_call"]
        if time_since_last_api_call > API_CALL_INTERVAL:
            st.session_state["current_data"] = getData(st.session_state.selected_coins, 0, st.session_state.api_key)
            st.session_state["last_api_call"] = current_time

        #st.write(data)

        #Escreve em um arquivo os dados históricos, caso seja bom pra fazer gráfico
        writeHistoricalData(st.session_state["current_data"])

        l = []
        i = 0
        for coin in st.session_state.selected_coins:
            l.append(st.empty())
            l[i].text(coin)
            defineBounds2(coin)

            bound_verification = checkBounds2(st.session_state["current_data"], coin)
            
            if bound_verification == 1:
                l[i].html(autoplay_audio("audiobom.mp3"))
                time.sleep(2) #O sistema espera 2 segundos antes de continuar para dar tempo de o audio tocar
                l[i].text(f"{coin}⬆")

            if bound_verification == 2:
                l[i].html(autoplay_audio("audiobom.mp3"))
                time.sleep(2)
                l[i].text(f"{coin}⬇︎")

            i += 1

        time.sleep(60)
        st.rerun()

if __name__ == "__main__":
    main()