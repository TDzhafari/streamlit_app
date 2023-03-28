from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
from yaml.loader import SafeLoader
import yaml
import io
import pandas as pd
import io
import openpyxl
import os
import geopandas as gpd

# import altair_saver
import pyarrow as pa
import pyarrow.feather as feather
import pathlib
import requests
import openpyxl
import altair as alt
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd

# https://towardsdatascience.com/how-to-add-a-user-authentication-service-in-streamlit-a8b93bf02031
# for "forgot password" and other authorization features
# https://docs.streamlit.io/library/get-started/multipage-apps
# for multipage setup


# st.write('Streamlit day 1 dsba5122')
# st.title('this is the app title')
# st.markdown('this is the header')
# st.subheader('this is the subheader')
# st.caption('this is the caption')
# st.code('x=2020')
# st.latex(r''' a+a r^1+A r^2 r^3 ''')

# st.image("norm.jpg")
# st.audio("fight_song.mp3")

################################################################################################
# Authentication and initial page setup
################################################################################################

st.set_page_config(layout="wide")

user_groups = {"admin": ["tdzhafari"], "group1": ["jdoe"]}

config_path: pathlib.Path = pathlib.Path(os.getcwd(), "config.yaml")
with open(config_path, "r") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)


# Check if 'key' already exists in session_state
# If not, then initialize it
if "key" not in st.session_state:
    st.session_state["key"] = "value"

name, authentication_status, username = authenticator.login("login", "main")

if authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.write(f"Welcome *{name}* :wave:")
    st.title("Disasters 2000-2023")
    st.subheader(
        "The data has been collected from EM-DAT The International Disaster Database Centre for Research on THe Epidemiology of Disasters (CRED)"
    )
elif authentication_status is False:
    st.error("Username/password is incorrect")
elif authentication_status is None:
    st.warning("Please enter your username and password")
    st.write(
        "Here will be a button to register. Feel free to use below credentials for now:"
    )
    expander = st.expander("For guest access credentials please click here")
    expander.write("login: jdoe, password: abc1")
# st.write(f'Your authentication status is {authentication_status}')

if authentication_status:
    with st.sidebar:
        if st.button("Reset Password"):
            try:
                if authenticator.reset_password(username, "Reset password"):
                    st.success("Password modified successfully")
            except Exception as e:
                st.error(e)

################################################################################################
# A separate function to retrieve data from github
################################################################################################


@st.cache_data
def fetch_and_clean_data():
    # URL of the raw CSV file on GitHub
    disaster_data_path = pathlib.Path(
        os.getcwd(), "2000-2023 disaster around the world.xlsx"
    )
    df = pd.read_excel(disaster_data_path, header=6, engine="openpyxl")
    df["Total Damages $$$"] = df["Total Damages, Adjusted ('000 US$)"]

    # Download GeoJSON file of world map
    world_map_url = "https://raw.githubusercontent.com/deldersveld/topojson/master/world-countries.json"
    world_map = alt.topo_feature(world_map_url, "countries")

    # Aggregate the data by country and region
    df_m = df.groupby(["Country", "Region"]).sum().reset_index()

    # Join the data with the GeoJSON file based on the "Country" field
    world_data = gpd.read_file(world_map_url)
    # df_map = world_data.merge(df_m, left_on='name', right_on='Country')

    merged_data = world_data.merge(df_m, left_on="name", right_on="Country")

    # Convert geopandas dataframe to pandas dataframe
    merged_data = pd.DataFrame(merged_data)

    return df, merged_data, world_map


################################################################################################
# Interactive dashboards and additional functionality
################################################################################################

if authentication_status:
    # disease = st.selectbox('select a disease', set(my_df['Dim2']))
    # if not disease:
    #    AgGrid(my_df)
    # else:
    #    AgGrid(my_df[my_df['Dim2'] == disease])
    if username in user_groups.get("admin"):
        source, line_plot, box_plot, map, tab5 = st.tabs(
            ["Source", "Line Plot", "Box Plot", "Map", "Placeholder"]
        )
    else:
        source, line_plot, box_plot = st.tabs(["Source", "Line Plot", "Box Plot"])
    with source:
        expander = st.expander("How this works?")
        expander.write(
            "Please choose a disaster type and a country you would like learn more about. The line plot will show you the number of people affected by chosen type of disaster in a country from 2000 to 2023."
        )
        df, merged_data, world_map = fetch_and_clean_data()
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

    with line_plot:
        expander = st.expander("How this works?")
        expander.write(
            "Please choose a disaster type and a country you would like learn more about. The line plot will show you the number of people affected by chosen type of disaster in a country from 2000 to 2023."
        )
        col1, col2 = st.columns(2)
        with col1:
            d_type = st.multiselect("select a disaster type", set(df["Disaster Type"]))
            st.write(f"you chose {d_type}")
        with col2:
            country = st.selectbox("select a country", set(df["Country"]))
            st.write(f"you chose {country}")
        if st.button("Remove filters"):
            d_type = None
            country = None
        if d_type and country:
            df1 = df[(df["Country"] == country) & df["Disaster Type"].isin(d_type)]
            st.line_chart(
                df1,
                x="Year",
                y="Total Affected",
            )

    ################################################################################################
    # Box plot
    ################################################################################################

    with box_plot:
        expander = st.expander("How this works?")
        expander.write(
            "Please choose a year to see which countries had the highest disaster related mortality for the year. Please note that if you hower over bars in the barplot you will see some useful information in the tooltip that will appear."
        )
        col1, col2 = st.columns(2)
        year = st.slider("Please choose a year", 2000, 2023, 2010)
        df2 = df[df["Year"] == year]
        # c = alt.Chart(df2.sort_values(by=['Total Deaths'], ascending = False)).mark_bar().encode(y = alt.Y("Region:N", sort = alt.EncodingSortField(field='Region', op = 'sum', order = 'ascending')), x = alt.X("Total Deaths", sort = '-x'))
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
                x=alt.X("Total Deaths", sort="-x", axis=alt.Axis(title="Total Deaths")),
                tooltip=[
                    alt.Tooltip("Country:N", title="Country"),
                    alt.Tooltip("Total Deaths:Q", title="Total Deaths"),
                    alt.Tooltip("Total Affected:Q", title="Total Affected"),
                ],
            )
        )
        st.altair_chart(c, use_container_width=True)
    if username in user_groups.get("admin"):

        ################################################################################################
        # Map
        ################################################################################################

        with map:
            year_map = st.slider("Please choose a year:", 2000, 2023, 2010)

            ## Convert pandas dataframe to Arrow table
            # table = pa.Table.from_pandas(merged_data)

            ## Write Arrow table to Feather format
            # feather.write_feather(table, 'merged_data.feather')

            ## Read Feather file into Arrow table
            # table = feather.read_feather('merged_data.feather')

            ## Convert Arrow table to pandas dataframe
            # merged_data = table.to_pandas()

            ## Create a heatmap with a tooltip
            # heatmap = alt.Chart(merged_data).mark_geoshape().encode(
            #    color=alt.Color('Total Deaths:Q', scale=alt.Scale(scheme='reds')),
            #    #tooltip=[
            #    #    alt.Tooltip('name:N', title='Country'),
            #    #    alt.Tooltip('Total Deaths:Q', title='Total Deaths', format=',')
            #    #]
            # ).properties(
            #    width=600,
            #    height=400,
            #    title='Total Deaths by Country'
            # )

            ## Add world map outlines
            # world_outline = alt.Chart(world_map).mark_geoshape(stroke='white', strokeWidth=0.5).encode(
            #    color=alt.value('transparent')
            # ).properties(
            #    width=600,
            #    height=400,
            # )

            ## Combine the heatmap and world map outlines
            # map_chart = world_outline + heatmap

            ## Display the chart in Streamlit

            # countries = alt.topo_feature(df2, "Country")
            # source = df2[(df2['Year'] == year)]

            # base = alt.Chart(source).mark_geoshape(
            #    fill='#666666',
            #    stroke='white'
            # ).properties(
            #    width=300,
            #    height=180
            # )

            # projections = 'orthographic'
            # st.altair_chart(base.projections.properties(title = projections))

        with tab5:
            st.write(
                "There will be something cool and creative below. Meanwhile enjoy some art by Edward Hopper."
            )
            col1, col2 = st.columns(2)
            with col1:
                st.image(
                    "https://media.tate.org.uk/aztate-prd-ew-dg-wgtail-st1-ctr-data/images/edward_hopper_automat.width-600.jpg"
                )
            with col2:
                st.image(
                    "https://collectionapi.metmuseum.org/api/collection/v1/iiif/488730/1004971/restricted"
                )
            st.image(
                "https://www.speakeasy-news.com/wp-content/uploads/2020/04/SN_hopper_home02.jpg"
            )
# if authentication_status and username in user_groups.get('group1'):

#     uploaded_file = st.file_uploader(
#         label='Reconciled Datadump',
#         type='xlsx',
#         help='Please upload Datadump here. The file will be checked for filename, extension, column formats etc. max weight = 200mb'
#     )

# st.dataframe(my_df[my_df['Dim2'] == disease])
# print((my_df.head().to_string()))
