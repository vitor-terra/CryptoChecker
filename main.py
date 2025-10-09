import requests
import streamlit as st
from datetime import datetime
import time
import pandas as pd
import altair as alt

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

    response = requests.get(url, headers=headers, params=querystring)
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

def getApiKey():
    if "api_key" not in st.session_state:
        st.session_state.api_key = "CG-VeKmL7uUadCQACDheMQ7E7hM"

    st.session_state.api_key = st.text_input("Digite sua própria chave de API aqui. Deixe em branco se quiser usar a chave padrão.")

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
        if data[0][entry][st.session_state.currency] > st.session_state.bounds[entry]["upper"]:
            print(f"{entry} está com valor mais alto do que o limite superior")

def doUI():
    
    if "coins_selected" not in st.session_state:
        st.session_state.coins_selected = False
    
    if "bounds_defined" not in st.session_state:
        st.session_state.bounds_defined = False

    if not st.session_state.coins_selected:
        selectCoins()
        
    elif not st.session_state.bounds_defined:
        defineBounds()

    else:
        st.markdown("*Dados fornecidos por [CoinGecko](https://www.coingecko.com)")
        getApiKey()
        data = getData(st.session_state.selected_coins, 0, st.session_state.api_key)

        st.write(data)

        #Escreve em um arquivo os dados históricos, caso seja bom pra fazer gráfico
        writeHistoricalData(data)

        time.sleep(5)
        st.rerun()

def main():

    if "coins_selected" not in st.session_state:
        st.session_state.coins_selected = False
    
    if "bounds_defined" not in st.session_state:
        st.session_state.bounds_defined = False

    if "currency" not in st.session_state:
        st.session_state.currency = "brl"

    if not st.session_state.coins_selected:
        selectCoins()
        
    elif not st.session_state.bounds_defined:
        defineBounds()

    else:
        st.markdown("*Dados fornecidos por [CoinGecko](https://www.coingecko.com)")
        getApiKey()
        data = getData(st.session_state.selected_coins, 0, st.session_state.api_key)

        st.write(data)

        #Escreve em um arquivo os dados históricos, caso seja bom pra fazer gráfico
        writeHistoricalData(data)

        l = []
        i = 0
        for coin in st.session_state.selected_coins:
            l.append(st.empty())
            l[i].text(coin)
            i += 1
            

        checkBounds(data)

        time.sleep(5)
        st.rerun()

    coin = st.selectbox("Escolha a criptomoeda:", ["bitcoin", "ethereum", "dogecoin"])
    vsCurrency = st.selectbox("Converter para:", ["usd", "brl", "eur"])
    timeRange = st.selectbox("Intervalo de tempo:", ["últimas 24h", "última semana", "último mês"])

    daysMap = {"últimas 24h": 1, "última semana": 7, "último mês": 30}
    days = daysMap[timeRange]

    price = getCryptoPrice(coin, vsCurrency)
    if price is not None:
        st.metric("Preço Atual", f"{price:.2f} {vsCurrency.upper()}")

    dfHist = getHistoricalData(coin, vsCurrency, days)
    st.subheader(f"Histórico - {coin.capitalize()} / {vsCurrency.upper()}")

    dfHist = dfHist.dropna(subset=["price"]).copy()
    dfHist["price"] = pd.to_numeric(dfHist["price"], errors="coerce")
    dfHist = dfHist.dropna(subset=["price"])

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
        st.warning("Nenhum dado histórico encontrado para o período selecionado.")    
    
    st.caption(f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()