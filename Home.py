from st_aggrid import *
from yaml.loader import SafeLoader
import yaml
import pandas as pd
import os
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st
import branca.colormap as cm
from wordcloud import WordCloud

# import altair_saver
from collections import Counter
import pyarrow as pa
import pyarrow.feather as feather
import pathlib
import altair as alt
from gensim import corpora
from functools import partial
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import streamlit as st
from wordcloud import WordCloud, STOPWORDS
import streamlit_authenticator as stauth
from streamlit_folium import folium_static
import pandas as pd
from nltkmodules import *
import altair as alt
import folium
from wordcloud import WordCloud, STOPWORDS
import nltk
import os
from nltk.corpus import stopwords

################################################################################################
#
#   Project: Streamlit app
#
#   Author: Timur Dzhafari
#   Purpose: To have a front end to various projects. (Prev. to display vizualizations for
#            'disasters' project)
#
#   todo: add documentation, cleanup, add classification prediction, lint
################################################################################################


################################################################################################
# Authentication and initial page setup
################################################################################################

st.set_page_config(layout="wide")

authorization_demo = False
authentication_status = False
username = ""

with st.sidebar:
    authorization_demo = st.checkbox(
        label="Authentication demo",
        help="If unchecked full access is granted.",
    )

user_groups = {"admin": ["tdzhafari"], "group1": ["jdoe"]}

if authorization_demo is True:
    config_path: pathlib.Path = pathlib.Path(os.getcwd(), "config.yaml")
    with open(config_path, "r") as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )

    if "key" not in st.session_state:
        st.session_state["key"] = "value"

    name, authentication_status, username = authenticator.login("login", "main")

    if authentication_status:
        authenticator.logout("Logout", "sidebar")
        st.write(f"Welcome *{name}* :wave:")

    elif authentication_status is False:
        st.error("Username/password is incorrect")
    elif authentication_status is None:
        st.warning("Please enter your username and password")
        promise = st.checkbox(label="I promise, I can keep a secret!")
        if promise:
            expander = st.expander("For guest access credentials please click here.")
            expander.write("login: 'jdoe', password: 'abc1' - just don't tell anyone")
    # st.write(f'Your authentication status is {authentication_status}')

    if authentication_status:
        with st.sidebar:
            if st.button("Reset Password"):
                try:
                    if authenticator.reset_password(username, "Reset password"):
                        st.success("Password modified successfully")
                except Exception as e:
                    st.error(e)
st.sidebar.empty()

if authentication_status == True or authorization_demo is False:
    demo_type_name = st.sidebar.selectbox(
        label="Choose a demo",
        options=["Disasters", "NLP"],
        # horizontal=True,
        help="Please choose between the available demos",
    )

    ################################################################################################
    # A separate function to retrieve data from github
    ################################################################################################

    if demo_type_name == "Disasters":
        st.title("Disasters 2000-2023")
        st.subheader(
            "The data has been collected from EM-DAT The International Disaster Database Centre for Research on The Epidemiology of Disasters (CRED)"
        )

        st.markdown(
            "[Tableau Dashboard](https://public.tableau.com/app/profile/timur.dzhafari/viz/EarthquakesinTurkeyvsdisasterssince2000/Dashboard1)"
        )

        @st.cache_data
        def fetch_and_clean_data():
            # URL of the raw CSV file on GitHub
            disaster_data_path = pathlib.Path(
                os.getcwd(), "data/2000-2023 disaster around the world.xlsx"
            )
            countries_conv_data_path = pathlib.Path(
                os.getcwd(), "data/country_loc_data.csv"
            )

            # Data with countries and their long, lat. For details see "country_location_notebook.ipynb"
            conv_df = pd.read_csv(countries_conv_data_path)

            # Read main dataset
            df = pd.read_excel(disaster_data_path, header=6, engine="openpyxl")

            # Cleaning
            df["Total Damages $$$"] = df["Total Damages, Adjusted ('000 US$)"]

            country_names_to_modify = {
                "Virgin Island (U.S)": "United States of America (the)",
                "Palestine, State of": "Palestine",
                "Taiwan (Province of China)": "Taiwan",
            }

            df["Country"] = df["Country"].replace(country_names_to_modify)

            df["Total Deaths"] = df["Total Deaths"].fillna(0)

            # merged_data = world_data.merge(df_m, left_on="name", right_on="Country")
            df = pd.merge(df, conv_df, on="Country", how="left")

            return df, conv_df

        ################################################################################################
        # Interactive dashboards and additional functionality
        ################################################################################################

        if authentication_status or authorization_demo is False:

            if username in user_groups.get("admin") or authorization_demo is False:
                visualizations, source = st.tabs(["Visualizations", "Source"])
            else:
                visualizations, source = st.tabs(["Visualizations", "Source"])

            with source:

                df, conv_df = fetch_and_clean_data()
                gb = GridOptionsBuilder.from_dataframe(df)
                # gb.configure_pagination(paginationAutoPageSize = True)
                gb.configure_side_bar()
                gb.configure_selection(
                    "multiple",
                    use_checkbox=True,
                    groupSelectsChildren="Group checkbox select children",
                )
                gridOptions = gb.build()

                grid_response = AgGrid(
                    df,
                    gridOptions=gridOptions,
                    data_return_mode="AS_INPUT",
                    update_mode="MODEL_CHANGED",
                    fit_columns_on_grid_load=False,
                    # theme="blue",
                    enable_enterprise_modules=True,
                    height=700,
                    width="100%",
                    reload_data=True,
                )

            ################################################################################################
            # Line plot tab
            ################################################################################################

            with visualizations:

                col1, col2 = st.columns(2)
                with col1:

                    d_type = st.multiselect(
                        "select a disaster type",
                        list(set(df["Disaster Type"])),
                        default="Earthquake",
                    )
                with col2:
                    country = st.selectbox(
                        "select a country",
                        list(set(df["Country"])),
                        index=list(set(df["Country"])).index("Turkey"),
                    )
                if st.button("Remove filters"):
                    d_type = None
                    country = None
                if d_type and country:
                    df1 = df[
                        (df["Country"] == country) & df["Disaster Type"].isin(d_type)
                    ]
                    st.line_chart(df1, x="Year", y="Total Affected")

                ################################################################################################
                # Box plot
                ################################################################################################

                expander = st.expander("How this works?")
                expander.write(
                    "Please choose a year to see which countries had the highest disaster related mortality for the year. Please note that if you hower over bars in the barplot you will see some useful information in the tooltip that will appear."
                )
                col1, col2 = st.columns(2)
                year = st.slider("Please choose a year", 2000, 2023, 2023)
                df2 = df[df["Year"] == year]
                c = (
                    alt.Chart(df2.sort_values(by=["Total Deaths"], ascending=False))
                    .mark_bar()
                    .encode(
                        y=alt.Y(
                            "Region:N",
                            sort=alt.EncodingSortField(
                                field="Total Deaths", order="descending"
                            ),
                            axis=alt.Axis(title="Region"),
                        ),
                        x=alt.X(
                            "Total Deaths",
                            sort="-x",
                            axis=alt.Axis(title="Total Deaths"),
                        ),
                        tooltip=[
                            alt.Tooltip("Country:N", title="Country"),
                            alt.Tooltip("Total Deaths:Q", title="Total Deaths"),
                            alt.Tooltip("Total Affected:Q", title="Total Affected"),
                        ],
                    )
                )
                st.altair_chart(c, use_container_width=True)

                ################################################################################################
                # Map
                ################################################################################################
                year_map = st.slider("Please choose a year:", 2000, 2023, 2023)
                url = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data"
                country_shapes = f"{url}/world-countries.json"

                map = folium.Map(
                    location=conv_df[conv_df["Country"] == "Turkey"][
                        ["latitude", "longitude"]
                    ],
                    zoom_start=2,
                    scrollWheelZoom=False,
                    tiles="CartoDB positron",
                )

                df["Total Deaths"] = df["Total Deaths"].fillna(0)

                grouped_df = (
                    df[df["Year"] == year_map][
                        ["Year", "Country", "latitude", "longitude", "Total Deaths"]
                    ]
                    .groupby(["Year", "Country", "latitude", "longitude"])
                    .agg("sum")
                )
                color_scale = cm.LinearColormap(
                    colors=["white", "darkred"],
                    vmin=0,
                    vmax=grouped_df["Total Deaths"].max(),
                    index=[0, 1],
                )
                grouped_df = grouped_df.reset_index()
                choropleth = folium.Choropleth(
                    geo_data=country_shapes,
                    name="choropleth",
                    data=grouped_df,
                    columns=["Country", "Total Deaths"],
                    key_on="feature.properties.name",
                    # highlight=True,
                    fill_color="Reds",
                    fill_opacity=0.4,
                    line_opacity=0.1,
                    legend_name="Total Deaths",
                ).add_to(map)

                df = df.set_index(["Country", "Year"])

                for feature in choropleth.geojson.data["features"]:
                    country_name = feature["properties"]["name"]
                    try:
                        if (country_name, year_map) in df.index:
                            total_deaths = (
                                df.loc[(country_name, year_map), "Total Deaths"]
                                .groupby("Country")
                                .sum()
                                .values[0]
                            )
                        else:
                            total_deaths = "No Data"
                        feature["properties"]["total deaths"] = "Total Deaths: " + str(
                            total_deaths
                        )
                    except KeyError:
                        total_deaths = "Error"
                        feature["properties"]["total deaths"] = "Total Deaths: " + str(
                            total_deaths
                        )

                choropleth.geojson.add_child(
                    folium.features.GeoJsonTooltip(["name", "total deaths"])
                )

                # grouped_df = grouped_df.index()
                st_map = folium_static(map)

    elif demo_type_name == "NLP":
        st.title("Shakespeare Demo")

        st.markdown(
            """
            # Analyzing Shakespeare Texts
            """
        )

        # Create a dictionary (not a list)
        books = {
            " ": " ",
            "A Mid Summer Night's Dream": "data/summer.txt",
            "The Merchant of Venice": "data/merchant.txt",
            "Romeo and Juliet": "data/romeo.txt",
        }

        # Sidebar
        st.sidebar.header("Word Cloud Settings")

        max_word = st.sidebar.slider(
            "Max Words", min_value=10, max_value=200, value=100, step=10
        )

        word_size = st.sidebar.slider(
            "Size of largest word", min_value=50, max_value=350, value=150, step=10
        )

        img_width = st.sidebar.slider(
            "Image width", min_value=100, max_value=800, value=600, step=10
        )

        rand_st = st.sidebar.slider(
            "Random State", min_value=20, max_value=100, value=50, step=1
        )

        remove_stop_words = st.sidebar.checkbox("Remove Stop Words?", value=True)

        st.sidebar.header("Word Count Settings")

        min_word_cnt = st.sidebar.slider(
            "Minimum count of words", min_value=5, max_value=100, value=30, step=1
        )
        # Select text files
        image = st.selectbox("Choose a text file", books.keys())

        # Get the value
        if image != " ":

            source_text = books.get(image)
            image = books.get(image)

        if image != " ":
            stop_words = []
            raw_text = open(image, "r").read().lower()
            nltk_stop_words = stopwords.words("english")

            if remove_stop_words:
                stop_words = set(nltk_stop_words)
                stop_words.update(
                    [
                        "us",
                        ",",
                        ".",
                        ";",
                        "?",
                        "!",
                        "'d",
                        "[",
                        "]",
                        ":",
                        "one",
                        "though",
                        "will",
                        "said",
                        "now",
                        "well",
                        "man",
                        "may",
                        "little",
                        "say",
                        "must",
                        "way",
                        "long",
                        "yet",
                        "mean",
                        "put",
                        "seem",
                        "asked",
                        "made",
                        "half",
                        "much",
                        "certainly",
                        "might",
                        "came",
                        "thou",
                    ]
                )
                # These are all lowercase

            tokens = nltk.word_tokenize(raw_text)

            # simple for loop to remove stop words
            if remove_stop_words:
                for item in tokens:
                    if item in stop_words:
                        tokens.remove(item)
        else:
            tokens = " "

        tab1, tab2, tab3 = st.tabs(["Word Cloud", "Bar Chart", "View Text"])

        with tab1:

            # Define some text for the word cloud
            if image != " " and tokens:
                text = " ".join(tokens)

                # Generate the word cloud image
                wordcloud = WordCloud(
                    width=img_width,
                    height=400,
                    max_words=max_word,
                    background_color="white",
                ).generate(text)

                # Display the word cloud image using Matplotlib
                fig, ax = plt.subplots()
                ax.imshow(wordcloud, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)

        with tab2:

            # simple for loop to remove stop words
            if remove_stop_words and tokens != " ":
                for item in tokens:
                    if item in stop_words:
                        tokens.remove(item)
            # create a dictionary using gensim library
            if tokens != " ":

                word_counts = Counter(tokens)

                # Convert the Counter object to a dictionary
                word_counts_dict = dict(word_counts)

                # Create a DataFrame from the dictionary
                df = pd.DataFrame.from_dict(
                    {
                        "word": list(word_counts_dict.keys()),
                        "count": list(word_counts_dict.values()),
                    }
                )

                df = df[(df["count"] > min_word_cnt)]

                chart = (
                    alt.Chart(df)
                    .mark_bar()
                    .encode(x="count", y=alt.Y("word", sort="-x"))
                )

                # Display the chart in Streamlit using Altair
                st.altair_chart(chart, use_container_width=True)

        with tab3:
            if image != " ":
                raw_text = open(image, "r").read()
                st.write(raw_text)
