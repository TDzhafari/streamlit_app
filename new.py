# import streamlit as st

# st.write('hello world')


import pandas as pd
import io
import openpyxl
import gdown
import requests
import altair as alt

# URL of the raw CSV file on GitHub
url = "https://raw.githubusercontent.com/{username}/{repository}/{branch}/{file_name}"

# Update the variables with your specific GitHub repository and file details
username = "TimurDzh"
repository = "streamlit_demo"
branch = "main"  # Or any other branch you want to use
file_name = (
    "2000-2023 disaster around the world.xlsx"  # Replace with the name of your CSV file
)

# Download the CSV file from GitHub
response = requests.get(
    url.format(
        username=username, repository=repository, branch=branch, file_name=file_name
    )
)

# Read the CSV data into a Pandas DataFrame
df = pd.read_excel(io.BytesIO(response.content), header=6)

alt.Chart(df).mark_line().encode(x="x", y="f(x)")


# # Shareable link of the Google Drive file
# url = "https://docs.google.com/spreadsheets/d/1d5DDzyxuHk6vv1C-qKp4GRvRG-GU9n0P/edit?usp=share_link&ouid=106057437112350446472&rtpof=true&sd=true"

# # Download the Google Drive file and save it locally
# gdown.download(url, "2000-2023 disaster around the world.xlsx", quiet=False)

# # Read the Excel data into a Pandas DataFrame
# df = pd.read_excel("2000-2023 disaster around the world.xlsx", engine="openpyxl")

# print(df.tail().to_string())
