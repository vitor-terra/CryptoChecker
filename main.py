import requests
import streamlit as st
from datetime import datetime

def buildCoinList(list):
    str = ""
    for s in list:
        str += f"{s},"
    return str

def getData(coin_list, preferred_money, api_key):
    coin_list = buildCoinList(coin_list)
    url = "https://api.coingecko.com/api/v3/simple/price"
    headers = {"x-cg-demo-api-key": api_key}
    querystring = {"vs_currencies":"brl","names":coin_list,"include_market_cap":"true","include_24hr_vol":"true","include_24hr_change":"true","include_last_updated_at":"true"}

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
            upper_bound = st.text_input(f"Notificar caso {current_coin} esteja acima de:")
            lower_bound = st.text_input(f"Notificar caso {current_coin} esteja abaixo de:")
            submitted = st.form_submit_button("Confirmar")

            if submitted:
                st.session_state.bounds[current_coin] = (upper_bound, lower_bound)
                st.session_state.current_index += 1
                st.rerun()
    else:
        st.success("Informações salvas")
        st.session_state.bounds_defined = True
        st.button("Ok")



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
        st.write("### Resultados finais:")
        st.json(st.session_state.bounds)


def main():
    doUI()
    api_key = "CG-VeKmL7uUadCQACDheMQ7E7hM"
    

    #print(getData(coin_list,0,api_key))
    


if __name__ == "__main__":
    main()