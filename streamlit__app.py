# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

st.title(":cup_with_straw: Customize your Smoothie :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Fetch fruit options
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_dataframe.to_pandas()

# Display available fruits
st.dataframe(data=pd_df, use_container_width=True)

# Debug: Print available search terms
st.write("Available search terms in database:", pd_df['SEARCH_ON'].unique())

# Multi-select for ingredients
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'],
    max_selections=5
)

# Process selected ingredients
if ingredients_list:
    ingredients_string = ', '.join(ingredients_list)

    for fruit_chosen in ingredients_list:
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]

        if search_on:
            st.subheader(f"{fruit_chosen} Nutrition Information")
            api_url = f"https://fruityvice.com/api/fruit/{search_on}"
            st.write(f"Fetching data from: {api_url}")  # Debugging

            fruityvice_response = requests.get(api_url)

            if fruityvice_response.status_code == 200:
                fruit_data = fruityvice_response.json()
                st.json(fruit_data)  # Debugging: Show raw JSON

                df = pd.DataFrame([fruit_data]) if isinstance(fruit_data, dict) else pd.DataFrame(fruit_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.error(f"API Request Failed! Status Code: {fruityvice_response.status_code}")
        else:
            st.error(f"No search term found for {fruit_chosen}. Please check the database.")

    # Insert order into database
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """

    # Submit order button
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
