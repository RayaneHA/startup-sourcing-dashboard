# Scraper multi-sources pour détection de startups + Dashboard Streamlit (MVP)

import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# --------------------
# CONFIG SUPABASE
# --------------------
SUPABASE_URL = "https://kstklwlzczickixrzsqm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzdGtsd2x6Y3ppY2tpeHJ6c3FtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1MzU5ODYsImV4cCI6MjA2MTExMTk4Nn0.o7s7zDFy6e_rAA5Gwas08a1WWqx8NkyFONiFbXw0eLM"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------
# PRODUCT HUNT SCRAPER (Réel)
# --------------------
def scrape_product_hunt_real():
    url = "https://www.producthunt.com/"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')

    data = []
    posts = soup.find_all('div', class_='styles_post__container')

    for post in posts:
        try:
            name_tag = post.find('h3')
            tagline_tag = post.find('p')
            link_tag = post.find('a', href=True)

            if name_tag and tagline_tag and link_tag:
                name = name_tag.text.strip()
                tagline = tagline_tag.text.strip()
                link = "https://www.producthunt.com" + link_tag['href']

                data.append({
                    "source": "ProductHunt",
                    "name": name,
                    "tagline": tagline,
                    "link": link
                })
        except Exception as e:
            print(f"Error parsing a post: {e}")
            continue

    return pd.DataFrame(data)

# --------------------
# TWITTER / X SEARCH MOCK
# --------------------
def mock_twitter_search():
    tweets = [
        {"text": "Founder of SolarX — currently raising our seed round. #buildinpublic", "user": "@solarx"},
        {"text": "Launching MindAI — an AI coach for focus & clarity. #raising", "user": "@mindai"}
    ]
    data = [{"source": "Twitter", "name": tweet['user'], "tagline": tweet['text'], "link": "https://twitter.com/" + tweet['user'][1:]} for tweet in tweets]
    return pd.DataFrame(data)

# --------------------
# FUSION DES SOURCES
# --------------------
def aggregate_sources():
    df_ph = scrape_product_hunt_real()
    df_tw = mock_twitter_search()
    df_all = pd.concat([df_ph, df_tw], ignore_index=True)
    return df_all

# --------------------
# ENVOI VERS SUPABASE
# --------------------
def push_to_supabase(df):
    for _, row in df.iterrows():
        data = {
            "source": row["source"],
            "name": row["name"],
            "tagline": row["tagline"],
            "link": row.get("link", "")
        }
        supabase.table("startups").insert(data).execute()

# --------------------
# DASHBOARD STREAMLIT
# --------------------
def load_from_supabase():
    response = supabase.table("startups").select("*").execute()
    data = response.data
    return pd.DataFrame(data)

# --------------------
# MAIN APP
# --------------------
if __name__ == '__main__':
    st.set_page_config(page_title="Startup Sourcing Dashboard", layout="wide")
    st.title("🚀 Startup Sourcing Tracker")

    df = load_from_supabase()

    with st.sidebar:
        source_filter = st.multiselect("Filtrer par source:", options=df["source"].unique(), default=df["source"].unique())

    filtered_df = df[df["source"].isin(source_filter)]

    st.dataframe(filtered_df, use_container_width=True)

    st.markdown("---")
    st.caption("Data collected via real scrapers and stored in Supabase.")
