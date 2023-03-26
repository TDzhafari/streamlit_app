from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
from yaml.loader import SafeLoader
import yaml
import io
import pandas as pd
import io
import openpyxl
import gdown
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

with open(r"D:\School\UNCC\projects\repos\streamlit_app\config.yaml") as file:
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
    url = (
        "https://raw.githubusercontent.com/{username}/{repository}/{branch}/{file_name}"
    )
    # Update the variables with your specific GitHub repository and file details
    username = "TimurDzh"
    repository = "streamlit_demo"
    branch = "main"  # Or any other branch you want to use
    file_name = "2000-2023 disaster around the world.xlsx"  # Replace with the name of your CSV file
    # Download the CSV file from GitHub
    response = requests.get(
        url.format(
            username=username, repository=repository, branch=branch, file_name=file_name
        )
    )
    # Read the CSV data into a Pandas DataFrame
    df = pd.read_excel(io.BytesIO(response.content), header=6)
    df["Total Damages $$$"] = df["Total Damages, Adjusted ('000 US$)"]
    return df


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
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Source", "Line Plot", "Box Plot", "Map", "Placeholder"]
        )
    else:
        tab1, tab2, tab3 = st.tabs(["Source", "Line Plot", "Box Plot"])
    with tab1:
        df = fetch_and_clean_data()
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
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            d_type = st.multiselect("select a disaster type", set(df["Disaster Type"]))
            st.write(f"you chose {d_type}")
        with col2:
            country = st.selectbox("select a country", set(df["Country"]))
            st.write(f"you chose {country}")
        # with col3:
        #     region = st.selectbox("select a region", set(df["Region"]))
        #     st.write(f"you chose {region}")
        if st.button("Remove all filters"):
            d_type = None
            country = None
            # region = None
        if d_type and country:
            df1 = df[(df["Country"] == country) & df["Disaster Type"].isin(d_type)]
            st.line_chart(
                df1,
                x="Year",
                y="Total Affected",
            )
    with tab3:
        year = st.slider("Please choose a year", 2000, 2023, 2010)
        df2 = df[df["Year"] == year]
        c = alt.Chart(df2).mark_bar().encode(y="Total Deaths", x="Region")
        st.altair_chart(c, use_container_width=True)
    if username in user_groups.get("admin"):
        with tab4:
            st.write("Map coming soon. Meanwhile please feel free to check out my")
        with tab5:
            st.write(
                "There will be something cool and creative below. Meanwhile check out some art by Edward Hopper."
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
