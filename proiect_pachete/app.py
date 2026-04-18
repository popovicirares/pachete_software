import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, confusion_matrix
import statsmodels.api as sm


# citire date
df = pd.read_csv('date.csv')

# tratare valori lipsa
df = df.fillna(0)

# conversie numerica
df['order_value_EUR'] = pd.to_numeric(df['order_value_EUR'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
df['cost'] = pd.to_numeric(df['cost'], errors='coerce').fillna(0)

# configurare aplicatie
st.set_page_config(page_title="Analiza organizatie", layout="wide")
st.title("Analiza organizatiei")

# meniu
sectiune = st.sidebar.radio("Sectiuni:",
                            ["Analiza Statistica", "Clusterizare", "Predictie",
                             "Regresie", "Distributie"])

if sectiune == "Analiza Statistica":
    st.write(df.describe())
    grupare = df.groupby('category')['order_value_EUR'].sum().reset_index()
    st.table(grupare)
    grafic, ax = plt.subplots()
    df.groupby('country')['order_value_EUR'].sum().plot(kind='bar', ax=ax)
    st.pyplot(grafic)

elif sectiune == "Clusterizare":
    X = df[['order_value_EUR', 'cost']]
    kmeans = KMeans(n_clusters=3, random_state=42)
    df['cluster'] = kmeans.fit_predict(X)
    grafic = go.Figure(
        data=[go.Scatter(x=df['order_value_EUR'], y=df['cost'], mode='markers', marker=dict(color=df['cluster']))])
    st.plotly_chart(grafic)

elif sectiune == "Predictie":
    df['target'] = (df['order_value_EUR'] > df['order_value_EUR'].median()).astype(int)
    X = df[['cost']]
    y = df['target']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    model = LogisticRegression().fit(X_train, y_train)
    st.write("Acuratetea modelului:", accuracy_score(y_test, model.predict(X_test)))

elif sectiune == "Regresie":
    X = sm.add_constant(df[['cost']])
    y = df['order_value_EUR']
    model = sm.OLS(y, X).fit()
    st.text(str(model.summary()))

elif sectiune == "Distributie":
    date_tari = df.groupby('country')['order_value_EUR'].sum().reset_index()
    grafic = px.choropleth(
        date_tari,
        locations="country",
        locationmode="country names",
        color="order_value_EUR",
        color_continuous_scale="Viridis",
        title="Distributia Vanzarilor"
    )
    st.plotly_chart(grafic)