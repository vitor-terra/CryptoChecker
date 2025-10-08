import requests
import streamlit as st
from datetime import datetime
import time

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

if __name__ == "__main__":
    main()