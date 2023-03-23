
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
from yaml.loader import SafeLoader
import yaml
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd

# https://towardsdatascience.com/how-to-add-a-user-authentication-service-in-streamlit-a8b93bf02031
# for "forgot password" and other authorization features
# https://docs.streamlit.io/library/get-started/multipage-apps
# for multipage setup


#st.write('Streamlit day 1 dsba5122')
#st.title('this is the app title')
#st.markdown('this is the header')
#st.subheader('this is the subheader')
#st.caption('this is the caption')
#st.code('x=2020')
#st.latex(r''' a+a r^1+A r^2 r^3 ''')

#st.image("norm.jpg")
#st.audio("fight_song.mp3")
st.set_page_config(layout="wide")

user_groups = {'admin': ['tdzhafari', 'rlinkier'], 'group1': ['jdoe']}

with open(r'C:\Users\tdzhafari\Documents\streamlit\config.yaml') as file:
    config = yaml.load(file, Loader = SafeLoader)
        
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
    )



name, authentication_status, username = authenticator.login('login', 'main')

if authentication_status:
    authenticator.logout('Logout', 'sidebar')
    st.write(f"Welcome *{name}* :wave:")
    st.title('DEMO')
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
#st.write(f'Your authentication status is {authentication_status}')

if authentication_status:
    if st.button('Reset Password'):
        try:
            if authenticator.reset_password(username, 'Reset password'):
                st.success('Password modified successfully')
        except Exception as e:
            st.error(e)

#st.checkbox('yes')
#st.button('click')
#st.radio('Pick your gender', ['Male', 'Female'])
#st.selectbox('Pick your gender', ['Male', 'Female'])
#st.multiselect('choose a planet', ['jupiter','uranus'])
#st.select_slider('pick a mark', ['bad', 'good'])
#st.slider('pick a num', 0,50)

#if st.button('clickme'):
#    st.write('hello!')
#else: st.button('clickme!')

#my_df = pd.read_csv(r'C:\Users\tdzhafari\Downloads\af92f6a9-ace9-4111-9eb8-ac36ee7fe960.csv')

try: my_df
except NameError: my_df = None

if not my_df:
    my_df = pd.read_csv(r'C:\Users\tdzhafari\Downloads\susbset1.csv')

#if authentication_status:
#    disease = st.selectbox('select a disease', my_df['Dim2'])

if authentication_status and username in user_groups.get('admin'):
    #disease = st.selectbox('select a disease', set(my_df['Dim2']))
    #if not disease:
    #    AgGrid(my_df)
    #else:
    #    AgGrid(my_df[my_df['Dim2'] == disease])
    gb = GridOptionsBuilder.from_dataframe(my_df)
    #gb.configure_pagination(paginationAutoPageSize = True)
    gb.configure_side_bar()
    gb.configure_selection('multiple', use_checkbox = True, groupSelectsChildren = 'Group checkbox select children')
    gridOptions = gb.build()

    grid_response = AgGrid(
        my_df,
        gridOptions=gridOptions,
        data_return_mode = 'AS_INPUT',
        update_mode = 'MODEL_CHANGED',
        fit_columns_on_grid_load = False,
        theme = 'blue',
        enable_enterprise_modules = True,
        height = 700,
        width = '100%',
        reload_data = True
        )

if authentication_status and username in user_groups.get('group1'):
    
    uploaded_file = st.file_uploader(
        label = 'Reconciled Datadump',
        type = 'xlsx', 
        help = 'Please upload Datadump here. The file will be checked for filename, extension, column formats etc. max weight = 200mb'
        )

    #st.dataframe(my_df[my_df['Dim2'] == disease])
#print((my_df.head().to_string()))