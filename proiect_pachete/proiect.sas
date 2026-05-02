/* 1. creare set de date din fisier extern */

PROC IMPORT
    DATAFILE="/home/u64488865/sasuser.v94/date.csv"
    OUT=WORK.vanzari_raw
    DBMS=CSV
    REPLACE;
    GETNAMES=YES;
    GUESSINGROWS=MAX;
RUN;

PROC CONTENTS DATA=WORK.vanzari_raw; RUN;

PROC PRINT DATA=WORK.vanzari_raw (OBS=5);
    TITLE "Primele 5 inregistrari din setul de date";
RUN;

/* conversie order_value_EUR (sir cu virgule) in numeric */
DATA WORK.vanzari;
    SET WORK.vanzari_raw;
    valoare_EUR = INPUT(COMPRESS(order_value_EUR, ','), BEST20.);
    data_comanda = INPUT(date, MMDDYY10.);
    FORMAT data_comanda DATE9.;
    DROP date order_value_EUR;
    RENAME data_comanda = date;
RUN;


/* 2. formate definite de utilizator */

PROC FORMAT;
    /* format pentru categorii de produse */
    VALUE $catfmt
        'Electronics' = 'Electronice'
        'Smartphones' = 'Telefoane'
        'Appliances'  = 'Electrocasnice'
        'Clothing'    = 'Imbracaminte'
        'Books'       = 'Carti'
        'Games'       = 'Jocuri'
        'Beauty'      = 'Cosmetice'
        'Accessories' = 'Accesorii'
        'Outdoors'    = 'Outdoor'
        OTHER         = 'Altele';

    /* format pentru tip dispozitiv */
    VALUE $devfmt
        'Mobile' = 'Mobil'
        'PC'     = 'Calculator'
        'Tablet' = 'Tableta';

    /* format pentru intervalele de valoare a vanzarii */
    VALUE valfmt
        LOW    -  50000 = 'Mica (<50K)'
        50001  - 150000 = 'Medie (50K-150K)'
        150001 -   HIGH = 'Mare (>150K)';
RUN;

/* aplicare formate pe setul de date */
DATA WORK.vanzari;
    SET WORK.vanzari;
    FORMAT category $catfmt.
           device_type $devfmt.
           valoare_EUR valfmt.;
RUN;

PROC PRINT DATA=WORK.vanzari (OBS=10);
    TITLE "Date cu formate aplicate";
RUN;


/* 3. procesare iterativa si conditionala */

DATA WORK.vanzari_procesate;
    SET WORK.vanzari;

    /* calcul profit */
    profit = valoare_EUR - cost;

    /* clasificare profit */
    IF profit > 150000 THEN categorie_profit = 'Profit mare';
    ELSE IF profit > 50000 THEN categorie_profit = 'Profit mediu';
    ELSE IF profit >= 0   THEN categorie_profit = 'Profit mic';
    ELSE                       categorie_profit = 'Pierdere';

    /* clasificare regiune geografica */
    IF country IN ('Germany', 'Austria', 'Belgium', 'Netherlands',
                   'Luxembourg') THEN regiune = 'Europa Centrala';
    ELSE IF country IN ('France', 'Spain', 'Portugal',
                        'Italy')  THEN regiune = 'Europa de Sud';
    ELSE IF country IN ('Sweden', 'Finland',
                        'Denmark') THEN regiune = 'Europa de Nord';
    ELSE                               regiune = 'Alte tari';

    /* calcul obiectiv trimestrial prin bucla DO */
    DO trimestru = 1 TO 4;
        obiectiv_trim = valoare_EUR * (1 + 0.05 * trimestru);
        OUTPUT;
    END;

    DROP trimestru;
RUN;

PROC PRINT DATA=WORK.vanzari_procesate (OBS=10);
    VAR country category valoare_EUR cost profit categorie_profit regiune;
    TITLE "Date procesate - profit si regiune";
RUN;


/* 4. subseturi de date */

/* subset - vanzari mari */
DATA WORK.vanzari_mari;
    SET WORK.vanzari_procesate;
    WHERE valoare_EUR > 150000;
RUN;

/* subset - vanzari profitabile din europa de nord */
DATA WORK.vanzari_nord;
    SET WORK.vanzari_procesate;
    WHERE regiune = 'Europa de Nord' AND profit > 0;
RUN;

/* subset - vanzari pe mobil */
DATA WORK.vanzari_mobile;
    SET WORK.vanzari_procesate;
    WHERE device_type = 'Mobile';
RUN;

PROC PRINT DATA=WORK.vanzari_mari (OBS=10);
    TITLE "Vanzari mari (valoare > 150,000 EUR)";
RUN;

PROC PRINT DATA=WORK.vanzari_nord (OBS=10);
    TITLE "Vanzari profitabile - Europa de Nord";
RUN;


/* 5. functii sas */

DATA WORK.vanzari_functii;
    SET WORK.vanzari_procesate;

    /* functii caracter */
    tara_upper     = UPCASE(country);
    initiale_mgr   = SUBSTR(sales_manager, 1, 1);
    lungime_client = LENGTH(customer_name);

    /* functii numerice */
    profit_rotunjit = ROUND(profit, 1000);
    valoare_log     = ROUND(LOG(valoare_EUR + 1), 0.01);
    valoare_sqrt    = ROUND(SQRT(valoare_EUR), 0.01);

    /* functii de data */
    an_comanda        = YEAR(date);
    luna_comanda      = MONTH(date);
    trimestru_comanda = QTR(date);
    zi_saptamana      = WEEKDAY(date);
RUN;

PROC PRINT DATA=WORK.vanzari_functii (OBS=10);
    VAR country tara_upper sales_manager initiale_mgr
        valoare_EUR profit_rotunjit an_comanda trimestru_comanda;
    TITLE "Date cu functii SAS aplicate";
RUN;


/* 6. combinarea seturilor de date - merge si sql */

/* set de date cu obiectivele managerilor */
DATA WORK.obiective_manageri;
    INPUT sales_manager $ & 30. obiectiv_anual;
    DATALINES;
Maxie Marrow       2000000
Hube Corey         1800000
Celine Tumasian    2200000
Emalia Dinse       1500000
Jessamine Apark    1900000
Othello Bowes      2100000
;
RUN;

/* proc sql - left join */
PROC SQL;
    CREATE TABLE WORK.vanzari_sql AS
    SELECT v.country, v.category, v.sales_manager,
           v.valoare_EUR, v.profit, v.regiune,
           m.obiectiv_anual,
           ROUND(v.valoare_EUR / m.obiectiv_anual * 100, 0.01)
               AS procent_obiectiv
    FROM WORK.vanzari_procesate AS v
    LEFT JOIN WORK.obiective_manageri AS m
        ON v.sales_manager = m.sales_manager;
QUIT;

PROC PRINT DATA=WORK.vanzari_sql (OBS=10);
    TITLE "Vanzari cu obiective - PROC SQL JOIN";
RUN;

/* merge cu by */
PROC SORT DATA=WORK.vanzari_procesate OUT=WORK.vanzari_sort;
    BY sales_manager;
RUN;

PROC SORT DATA=WORK.obiective_manageri;
    BY sales_manager;
RUN;

DATA WORK.vanzari_merge;
    MERGE WORK.vanzari_sort       (IN=a)
          WORK.obiective_manageri (IN=b);
    BY sales_manager;
    IF a;
    procent_obiectiv = ROUND(valoare_EUR / obiectiv_anual * 100, 0.01);
RUN;

PROC PRINT DATA=WORK.vanzari_merge (OBS=10);
    VAR sales_manager country valoare_EUR obiectiv_anual procent_obiectiv;
    TITLE "Vanzari cu obiective - MERGE";
RUN;


/* 7. masive (arrays) */

DATA WORK.vanzari_scenarii;
    SET WORK.vanzari_procesate;

    /* array pentru scenarii de crestere a pretului */
    ARRAY scenarii{4} scen_5pct scen_10pct scen_15pct scen_20pct;
    ARRAY rate{4} _TEMPORARY_ (0.05, 0.10, 0.15, 0.20);

    DO i = 1 TO 4;
        scenarii{i} = ROUND(valoare_EUR * (1 + rate{i}), 0.01);
    END;
    DROP i;
RUN;

PROC PRINT DATA=WORK.vanzari_scenarii (OBS=10);
    VAR country category valoare_EUR scen_5pct scen_10pct scen_15pct scen_20pct;
    TITLE "Scenarii de crestere a valorii vanzarilor (5%, 10%, 15%, 20%)";
RUN;


/* 8. proceduri de raportare */

PROC PRINT DATA=WORK.vanzari_procesate (OBS=20);
    VAR country category device_type valoare_EUR cost profit categorie_profit;
    TITLE "Raport general vanzari";
RUN;

PROC MEANS DATA=WORK.vanzari_procesate N MEAN STD MIN MAX SUM;
    CLASS category;
    VAR valoare_EUR cost profit;
    TITLE "Statistici agregate pe categorie de produs";
RUN;

PROC MEANS DATA=WORK.vanzari_procesate N MEAN SUM;
    CLASS regiune;
    VAR valoare_EUR profit;
    TITLE "Statistici agregate pe regiune geografica";
RUN;

PROC FREQ DATA=WORK.vanzari_procesate;
    TABLES country / NOCUM;
    TITLE "Distributia vanzarilor pe tara";
RUN;

PROC FREQ DATA=WORK.vanzari_procesate;
    TABLES device_type * categorie_profit / NOCUM NOPERCENT;
    TITLE "Tip dispozitiv vs categorie profit";
RUN;


/* 9. proceduri statistice */

PROC UNIVARIATE DATA=WORK.vanzari_procesate;
    VAR valoare_EUR cost profit;
    TITLE "Analiza univariata - valoare, cost, profit";
RUN;

PROC CORR DATA=WORK.vanzari_procesate;
    VAR valoare_EUR cost profit;
    TITLE "Analiza corelatiei dintre valoare, cost si profit";
RUN;

PROC REG DATA=WORK.vanzari_procesate;
    MODEL valoare_EUR = cost;
    TITLE "Regresie simpla: valoare vanzare in functie de cost";
RUN;
QUIT;


/* 10. grafice */

/* grafic bara - vanzari totale pe categorie */
PROC SGPLOT DATA=WORK.vanzari_procesate;
    VBAR category / RESPONSE=valoare_EUR STAT=SUM;
    TITLE "Vanzari totale pe categorie de produs";
    XAXIS LABEL="Categorie";
    YAXIS LABEL="Valoare totala (EUR)";
RUN;

/* grafic scatter - relatia cost vs valoare */
PROC SGPLOT DATA=WORK.vanzari_procesate;
    SCATTER X=cost Y=valoare_EUR / GROUP=device_type MARKERATTRS=(SIZE=7);
    TITLE "Relatia dintre cost si valoarea vanzarii";
    XAXIS LABEL="Cost (EUR)";
    YAXIS LABEL="Valoare vanzare (EUR)";
RUN;

/* grafic bara stivuita - vanzari pe tara si tip dispozitiv */
PROC SGPLOT DATA=WORK.vanzari_procesate;
    VBAR country / RESPONSE=valoare_EUR STAT=SUM GROUP=device_type;
    TITLE "Vanzari pe tara si tip dispozitiv";
    XAXIS LABEL="Tara";
    YAXIS LABEL="Valoare totala (EUR)";
RUN;

/* grafic pie - distributia pe regiuni */
PROC GCHART DATA=WORK.vanzari_procesate;
    PIE regiune / SUMVAR=valoare_EUR TYPE=SUM;
    TITLE "Distributia vanzarilor pe regiuni geografice";
RUN;
QUIT;
