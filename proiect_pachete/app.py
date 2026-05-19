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
                            ["Descrierea Problemei", "Preprocesare",
                             "Analiza Statistica", "Clusterizare",
                             "Predictie", "Regresie", "Distributie"])

# descrierea problemei
if sectiune == "Descrierea Problemei":
    st.header("Descrierea Problemei")

    st.subheader("Contextul economic")
    st.markdown("""
    In contextul unui mediu comercial tot mai competitiv si digitalizat, organizatiile care activeaza
    in retail se confrunta cu provocarea de a gestiona eficient
    un volum mare de tranzactii efectuate de clienti din mai multe piete europene.

    Aceasta aplicatie raspunde unei nevoi reale de **analiza si optimizare activitatii**,
    oferind o imagine clara asupra:

    - **Profitabilitatii pe categorii de produse** — identificarea categoriilor cu marja de profit cea mai buna
      si a celor care genereaza costuri disproportionat de mari in raport cu veniturile;
    - **Comportamentului clientilor** — segmentarea clientilor dupa valoarea comenzilor si costurile asociate,
      pentru a permite strategii de marketing diferentiate;
    - **Performantei echipelor de vanzari** — evaluarea managerilor si agentilor de vanzari in functie
      de volumul si valoarea comenzilor gestionate;
    - **Distributiei geografice a vanzarilor** — intelegerea contributiei fiecarei tari la cifra de afaceri
      totala, pentru alocarea optima a resurselor;
    - **Canalului de achizitie** — analiza comportamentului de cumparare pe Mobile, PC si Tablet,
      relevanta pentru deciziile de investitie in platforme digitale.

    Prin tehnici de **machine learning** (clusterizare KMeans, regresie logistica, regresie multipla OLS),
    aplicatia transforma datele brute de vanzari intr-un instrument decizional ce sprijina:
    planificarea strategica, optimizarea costurilor si cresterea veniturilor.
    """)

    st.subheader("Descrierea setului de date")
    st.markdown("""
    Setul de date contine **1.000 de inregistrari** reprezentand comenzile realizate in perioada
    **2019–2020**, acoperind mai multe tari europene. Fiecare rand corespunde unei tranzactii individuale
    si include urmatoarele coloane:

    | Coloana | Descriere |
    |---|---|
    | `country` | Tara in care s-a realizat comanda (ex: Portugalia, Suedia, Marea Britanie, Franta etc.) |
    | `order_value_EUR` | Valoarea comenzii in EUR (variabila tinta principala) |
    | `cost` | Costul asociat comenzii in EUR |
    | `date` | Data plasarii comenzii (format MM/DD/YYYY) |
    | `category` | Categoria produsului (Books, Electronics, Clothing, Games, Beauty etc.) |
    | `customer_name` | Numele clientului / firmei cumparatoare |
    | `sales_manager` | Managerul de vanzari responsabil |
    | `sales_rep` | Reprezentantul de vanzari care a gestionat comanda |
    | `device_type` | Dispozitivul folosit la plasarea comenzii (PC, Mobile, Tablet) |
    | `order_id` | Identificatorul unic al comenzii |

    - Categoriile de produse includ: Books, Games, Clothing, Beauty, Electronics, Appliances, Smartphones, Accessories, Outdoors, Other
    - Tarile acoperite includ: Portugalia, Suedia, Marea Britanie, Franta, Spania, Finlanda, Olanda, Belgia, Bulgaria, Irlanda, Italia, Luxemburg
    - Canalele de vanzare: **PC**, **Mobile** si **Tablet**
    - Perioada de timp: **ianuarie 2019 – decembrie 2020** (2 ani fiscali completi)
    """)

# preprocesare
elif sectiune == "Preprocesare":
    st.header("Preprocesare Date")

    st.subheader("1. Valori lipsa")
    st.caption("Detecteaza coloanele cu date incomplete. Valorile lipsa sunt inlocuite cu mediana coloanei.")
    valori_lipsa = df.isnull().sum()
    procent_lipsa = (df.isnull().sum() / len(df)) * 100
    tabel_lipsa = pd.DataFrame({
        'Valori lipsa': valori_lipsa,
        'Procent (%)': procent_lipsa.round(2)
    })
    st.write(tabel_lipsa)
    total_lipsa = valori_lipsa.sum()
    st.caption(f"**Rezultat:** {'Nu exista valori lipsa in set.' if total_lipsa == 0 else f'{total_lipsa} valori lipsa detectate si completate cu mediana.'}")

    st.subheader("2. Tratarea valorilor extreme (IQR)")
    st.caption("Identifica comenzile cu valori anormal de mici sau mari fata de distributia generala.")
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
    st.caption(f"**Rezultat:** {len(outlieri)} comenzi au valori in afara intervalului [{limita_inf:.0f} EUR, {limita_sup:.0f} EUR] si reprezinta tranzactii atipice ce necesita verificare.")

    st.subheader("3. Codificarea datelor")
    st.caption("Transforma variabilele de tip text (device_type, category) in valori numerice pentru utilizarea in algoritmi.")
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
    st.caption("**Rezultat:** Mobile = 0, PC = 1, Tablet = 2. Variabila este acum utilizabila in modele.")

    st.subheader("4. Scalarea datelor (StandardScaler)")
    st.caption("Aduce variabilele numerice la aceeasi scara (medie 0, deviatie standard 1) pentru a evita dominarea algoritmilor de catre variabila cu valorile cele mai mari.")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[['order_value_EUR', 'cost']])
    df_scaled = pd.DataFrame(X_scaled, columns=['order_value_EUR_scaled', 'cost_scaled'])
    st.write(df_scaled.head())
    st.write(f"Medie dupa scalare: {df_scaled.mean().round(4).to_dict()}")
    st.write(f"Std dupa scalare: {df_scaled.std().round(4).to_dict()}")
    st.caption("**Rezultat:** Ambele variabile au medie ~0 si std ~1. Datele sunt pregatite pentru modelare.")

# analiza statistica
elif sectiune == "Analiza Statistica":
    st.header("Analiza Statistica")

    st.subheader("Statistici descriptive")
    st.caption("Prezinta distributia valorilor pentru fiecare variabila numerica: medie, mediana, deviatie standard, minim si maxim.")
    st.write(df.describe())
    medie = df['order_value_EUR'].mean()
    mediana = df['order_value_EUR'].median()
    st.caption(f"**Rezultat:** Valoarea medie a unei comenzi este **{medie:,.0f} EUR**, iar mediana **{mediana:,.0f} EUR**. Diferenta dintre ele indica prezenta comenzilor de valoare foarte mare care ridica media.")

    st.subheader("Vanzari totale pe categorie")
    st.caption("Arata care categorii de produse genereaza cel mai mare volum de vanzari, numar de comenzi si valoare medie per comanda.")
    grupare = df.groupby('category').agg(
        Vanzari_totale=('order_value_EUR', 'sum'),
        Numar_comenzi=('order_value_EUR', 'count'),
        Valoare_medie=('order_value_EUR', 'mean')
    ).reset_index()
    st.table(grupare)
    top_cat = grupare.loc[grupare['Vanzari_totale'].idxmax(), 'category']
    top_val = grupare['Vanzari_totale'].max()
    st.caption(f"**Rezultat:** Categoria cu cele mai mari vanzari totale este **{top_cat}** cu **{top_val:,.0f} EUR**.")

    st.subheader("Vanzari pe tara")
    st.caption("Compara contributia fiecarei tari la vanzarile totale.")
    grafic, ax = plt.subplots()
    df.groupby('country')['order_value_EUR'].sum().sort_values(ascending=False).plot(kind='bar', ax=ax)
    ax.set_xlabel('Tara')
    ax.set_ylabel('Valoare EUR')
    plt.tight_layout()
    st.pyplot(grafic)
    top_tara = df.groupby('country')['order_value_EUR'].sum().idxmax()
    top_tara_val = df.groupby('country')['order_value_EUR'].sum().max()
    st.caption(f"**Rezultat:** Cea mai performanta piata este **{top_tara}** cu **{top_tara_val:,.0f} EUR** in vanzari totale.")

# clusterizare
elif sectiune == "Clusterizare":
    st.header("Clusterizare KMeans")

    scaler = StandardScaler()
    X = scaler.fit_transform(df[['order_value_EUR', 'cost']])

    st.subheader("Elbow Method")
    st.caption("Determina numarul optim de clustere. Punctul unde scaderea erorii WCSS incetineste indica numarul recomandat.")
    wcss = []
    for i in range(1, 11):
        kmeans = KMeans(n_clusters=i, init='k-means++', random_state=42)
        kmeans.fit(X)
        wcss.append(kmeans.inertia_)

    fig, ax = plt.subplots()
    sns.lineplot(x=range(1, 11), y=wcss, marker='o', color='red', ax=ax)
    ax.set_title('Elbow Method')
    ax.set_xlabel('Numar clustere')
    ax.set_ylabel('WCSS')
    st.pyplot(fig)
    st.caption("**Rezultat:** Graficul indica k=3 ca numar optim de clustere, unde scaderea WCSS devine lenta.")

    st.subheader("Rezultate clustering (k=3)")
    st.caption("Imparte comenzile in 3 segmente pe baza valorii si costului. Silhouette Score masoara calitatea separarii clusterelor (0-1, mai mare = mai bine).")
    kmeans = KMeans(n_clusters=3, init='k-means++', random_state=42)
    df['cluster'] = kmeans.fit_predict(X)

    sil = silhouette_score(X, df['cluster'])
    st.write(f"Silhouette Score: **{sil:.4f}** (aproape de 1 = clustere bine definite)")
    st.caption(f"**Rezultat:** Scorul de **{sil:.4f}** indica {'clustere bine separate si distincte.' if sil > 0.5 else 'o separare moderata intre clustere, cu unele suprapuneri intre segmente.'}")

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
    st.caption("Caracterizeaza fiecare segment prin numarul de comenzi, valoarea medie si costul mediu.")
    stats_cluster = df.groupby('cluster').agg(
        Numar=('order_value_EUR', 'count'),
        Valoare_medie=('order_value_EUR', 'mean'),
        Cost_mediu=('cost', 'mean')
    ).round(2)
    st.write(stats_cluster)
    best_cluster = (stats_cluster['Valoare_medie'] - stats_cluster['Cost_mediu']).idxmax()
    marja = (stats_cluster['Valoare_medie'] - stats_cluster['Cost_mediu']).max()
    st.caption(f"**Rezultat:** Clusterul **{best_cluster}** are cea mai mare marja bruta medie ({marja:,.0f} EUR/comanda) si reprezinta segmentul cel mai profitabil.")

# predictie
elif sectiune == "Predictie":
    st.header("Regresie Logistica")

    st.caption("Clasifica comenzile ca valoare mare (peste mediana) sau mica (sub mediana) pe baza costului si tipului de dispozitiv.")

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
    st.caption(f"**Rezultat:** Modelul prezice corect **{acuratete:.2%}** din comenzi. {'Performanta buna — costul si dispozitivul sunt predictori relevanti.' if acuratete >= 0.70 else 'Performanta moderata — variabilele folosite explica partial valoarea comenzii.'}")

    st.subheader("Matricea de confuzie")
    st.caption("Arata numarul de clasificari corecte si eronate pentru fiecare clasa.")
    cm = confusion_matrix(y_test, model.predict(X_test))
    fig, ax = plt.subplots()
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax)
    ax.set_xlabel('Prezis')
    ax.set_ylabel('Real')
    st.pyplot(fig)
    st.caption(f"**Rezultat:** {cm[0,0]} comenzi mici si {cm[1,1]} comenzi mari clasificate corect. {cm[0,1]+cm[1,0]} erori totale de clasificare.")

# regresie
elif sectiune == "Regresie":
    st.header("Regresie Multipla (OLS)")

    st.caption("Modeleaza influenta costului si a tipului de dispozitiv asupra valorii comenzii. R-squared arata cat la suta din variatia vanzarilor este explicata de model.")

    le = LabelEncoder()
    df['device_type_cod'] = le.fit_transform(df['device_type'].astype(str))

    X = sm.add_constant(df[['cost', 'device_type_cod']])
    y = df['order_value_EUR']
    model = sm.OLS(y, X).fit()
    st.text(str(model.summary()))

    r2 = model.rsquared
    coef_cost = model.params['cost']
    pval_cost = model.pvalues['cost']
    pval_device = model.pvalues['device_type_cod']
    st.caption(f"**Rezultat:** R²={r2:.4f} — modelul explica {r2:.1%} din variatia valorii comenzilor. "
               f"Costul {'este' if pval_cost < 0.05 else 'nu este'} semnificativ statistic (p={pval_cost:.4f}), coeficient {coef_cost:.4f}. "
               f"Tipul dispozitivului {'influenteaza' if pval_device < 0.05 else 'nu influenteaza'} semnificativ valoarea comenzii (p={pval_device:.4f}).")

# distributie
elif sectiune == "Distributie":
    st.header("Distributia Geografica a Vanzarilor")

    st.caption("Vizualizeaza vanzarile totale per tara pe harta. Culorile mai inchise indica vanzari mai mari.")

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

    top_tara = date_tari.loc[date_tari['order_value_EUR'].idxmax(), 'country']
    top_val = date_tari['order_value_EUR'].max()
    total_val = date_tari['order_value_EUR'].sum()
    pct_top = top_val / total_val * 100
    st.caption(f"**Rezultat:** Cea mai performanta piata este **{top_tara}** cu **{top_val:,.0f} EUR** ({pct_top:.1f}% din totalul vanzarilor).")
