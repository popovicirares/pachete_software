import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, confusion_matrix, silhouette_score
import statsmodels.api as sm

# citire date
df = pd.read_csv('date.csv')

# conversie numerica
df['order_value_EUR'] = pd.to_numeric(df['order_value_EUR'].astype(str).str.replace(',', ''), errors='coerce')
df['cost'] = pd.to_numeric(df['cost'], errors='coerce')

# tratare valori lipsa
df = df.fillna(df.select_dtypes(include='number').median())

# configurare aplicatie
st.set_page_config(page_title="Analiza organizatie", layout="wide")
st.title("Analiza organizatiei")

# meniu
sectiune = st.sidebar.radio("Sectiuni:",
                            ["Analiza Statistica", "Preprocesare",
                             "Clusterizare", "Predictie", "Regresie", "Distributie"])

# analiza statistica
if sectiune == "Analiza Statistica":
    st.header("Analiza Statistica")

    st.subheader("Statistici descriptive")
    st.write(df.describe())

    st.subheader("Vanzari totale pe categorie")
    grupare = df.groupby('category').agg(
        Vanzari_totale=('order_value_EUR', 'sum'),
        Numar_comenzi=('order_value_EUR', 'count'),
        Valoare_medie=('order_value_EUR', 'mean')
    ).reset_index()
    st.table(grupare)

    st.subheader("Vanzari pe tara")
    grafic, ax = plt.subplots()
    df.groupby('country')['order_value_EUR'].sum().sort_values(ascending=False).plot(kind='bar', ax=ax)
    ax.set_xlabel('Tara')
    ax.set_ylabel('Valoare EUR')
    plt.tight_layout()
    st.pyplot(grafic)

# preprocesare
elif sectiune == "Preprocesare":
    st.header("Preprocesare Date")

    st.subheader("1. Valori lipsa")
    valori_lipsa = df.isnull().sum()
    procent_lipsa = (df.isnull().sum() / len(df)) * 100
    tabel_lipsa = pd.DataFrame({
        'Valori lipsa': valori_lipsa,
        'Procent (%)': procent_lipsa.round(2)
    })
    st.write(tabel_lipsa)

    st.subheader("2. Tratarea valorilor extreme (IQR)")
    col_analiza = 'order_value_EUR'
    Q1 = df[col_analiza].quantile(0.25)
    Q3 = df[col_analiza].quantile(0.75)
    IQR = Q3 - Q1
    limita_inf = Q1 - 1.5 * IQR
    limita_sup = Q3 + 1.5 * IQR
    outlieri = df[(df[col_analiza] < limita_inf) | (df[col_analiza] > limita_sup)]

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Limita inferioara: **{limita_inf:.2f}**")
        st.write(f"Limita superioara: **{limita_sup:.2f}**")
        st.write(f"Outlieri detectati: **{len(outlieri)}**")
    with col2:
        fig, ax = plt.subplots()
        ax.boxplot(df[col_analiza].dropna())
        ax.set_title('Boxplot - Order Value EUR')
        st.pyplot(fig)

    st.subheader("3. Codificare categorica")
    le = LabelEncoder()
    df_encoded = df.copy()
    df_encoded['device_type_cod'] = le.fit_transform(df['device_type'].astype(str))
    df_encoded['category_cod'] = le.fit_transform(df['category'].astype(str))
    st.write("Codificare device_type:")
    st.write(
        df_encoded[['device_type', 'device_type_cod']]
        .drop_duplicates()
        .sort_values('device_type_cod')
        .reset_index(drop=True)
    )

    st.subheader("4. Scalare date (StandardScaler)")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[['order_value_EUR', 'cost']])
    df_scaled = pd.DataFrame(X_scaled, columns=['order_value_EUR_scaled', 'cost_scaled'])
    st.write("Primele randuri dupa scalare (medie~0, deviatie standard~1):")
    st.write(df_scaled.head())
    st.write(f"Medie dupa scalare: {df_scaled.mean().round(4).to_dict()}")
    st.write(f"Std dupa scalare: {df_scaled.std().round(4).to_dict()}")

# clusterizare
elif sectiune == "Clusterizare":
    st.header("Clusterizare KMeans")

    scaler = StandardScaler()
    X = scaler.fit_transform(df[['order_value_EUR', 'cost']])

    st.subheader("Metoda Cotului (Elbow Method)")
    wcss = []
    for i in range(1, 11):
        kmeans = KMeans(n_clusters=i, init='k-means++', random_state=42)
        kmeans.fit(X)
        wcss.append(kmeans.inertia_)

    fig, ax = plt.subplots()
    sns.lineplot(x=range(1, 11), y=wcss, marker='o', color='red', ax=ax)
    ax.set_title('Metoda Cotului')
    ax.set_xlabel('Numar clustere')
    ax.set_ylabel('WCSS')
    st.pyplot(fig)

    st.subheader("Rezultate clustering (k=3)")
    kmeans = KMeans(n_clusters=3, init='k-means++', random_state=42)
    df['cluster'] = kmeans.fit_predict(X)

    sil = silhouette_score(X, df['cluster'])
    st.write(f"Silhouette Score: **{sil:.4f}** (aproape de 1 = clustere bine definite)")

    grafic = go.Figure(data=[go.Scatter(
        x=df['order_value_EUR'],
        y=df['cost'],
        mode='markers',
        marker=dict(color=df['cluster'], colorscale='Viridis', showscale=True)
    )])
    grafic.update_layout(
        title='Clustere clienti',
        xaxis_title='Order Value EUR',
        yaxis_title='Cost'
    )
    st.plotly_chart(grafic)

    st.subheader("Statistici pe cluster")
    st.write(df.groupby('cluster').agg(
        Numar=('order_value_EUR', 'count'),
        Valoare_medie=('order_value_EUR', 'mean'),
        Cost_mediu=('cost', 'mean')
    ).round(2))

# predictie
elif sectiune == "Predictie":
    st.header("Predictie - Regresie Logistica")

    df['target'] = (df['order_value_EUR'] > df['order_value_EUR'].median()).astype(int)

    le = LabelEncoder()
    df['device_type_cod'] = le.fit_transform(df['device_type'].astype(str))

    scaler = StandardScaler()
    X = scaler.fit_transform(df[['cost', 'device_type_cod']])
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LogisticRegression().fit(X_train, y_train)

    acuratete = accuracy_score(y_test, model.predict(X_test))
    st.write(f"Acuratetea modelului: **{acuratete:.2%}**")

    st.subheader("Matricea de confuzie")
    cm = confusion_matrix(y_test, model.predict(X_test))
    fig, ax = plt.subplots()
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax)
    ax.set_xlabel('Prezis')
    ax.set_ylabel('Real')
    st.pyplot(fig)

# regresie
elif sectiune == "Regresie":
    st.header("Regresie Multipla (OLS)")

    le = LabelEncoder()
    df['device_type_cod'] = le.fit_transform(df['device_type'].astype(str))

    X = sm.add_constant(df[['cost', 'device_type_cod']])
    y = df['order_value_EUR']
    model = sm.OLS(y, X).fit()
    st.text(str(model.summary()))

# distributie
elif sectiune == "Distributie":
    st.header("Distributia Geografica a Vanzarilor")

    date_tari = df.groupby('country')['order_value_EUR'].sum().reset_index()

    grafic = px.choropleth(
        date_tari,
        locations="country",
        locationmode="country names",
        color="order_value_EUR",
        color_continuous_scale="Viridis",
        title="Distributia Vanzarilor pe Tari"
    )
    st.plotly_chart(grafic)