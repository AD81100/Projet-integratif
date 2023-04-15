from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import os
import sqlite3
import statistics
import datetime
import requests
import json
from unidecode import unidecode


app = Flask(__name__)


#Connexion à la base de données

def createConnection():
    path = r"C:\Users\arifd\OneDrive\Bureau\site projet flasked\db\db_incendie.db"
    if not os.path.exists(path):
        print(f"Le fichier {path} n'existe pas")
        connection = None
    else:
        try:
            connection = sqlite3.connect(path)
            print("Connection to SQLite réussie")
        except sqlite3.Error as e:
            print(f"The error {e} occured")
    return connection

#Permet d'enlever les accents présent dans le nom des villes, utile pour l'API

def remove_accents(word):
    return unidecode(word)

#Fonction pour récupérer en direct la météo de 2 villes dans un département

def meteo_direct(city1, city2):
    
    #on enlève les accents de la première ville
    
    city1=remove_accents(city1)
    
    #gestion des cas particuliers 
    
    if city1 == "La_Rochelle":
        city1 = "rochelle-17"
    elif city1 == "Aubusson":
        city1 = "aubusson-23"
    elif city1 =="Marmande":
        city1 ="Agen"
    elif city1 =="Lure":
        city1 ="lure-70"    
    elif city1 =="Clamecy":
        city1 ="clamecy-58"   
        
   #on va chercher le JSON sur l'api
        
    api1 = requests.get(f"https://prevision-meteo.ch/services/json/{city1}")
    api_city1 = api1.text
    api_clean_city1 =json.loads(api_city1)
    
    #on récupère la température et l'humidité
    
    temperature_city1 = api_clean_city1 ['current_condition']['tmp']
    humidity_city1 = api_clean_city1['current_condition']['humidity']

    score_city1=0
    
    #gestion des scores pour déterminer la couleur plus tard

    if temperature_city1 >= 35:
        score_city1 += 3
    elif 34 >= temperature_city1 > 25:
        score_city1 += 2
    elif 24 >= temperature_city1 > 19:
        score_city1 += 1
    elif 18 >= temperature_city1> 15:
        score_city1 += 0
    elif 14 >= temperature_city1> 5:
        score_city1 -=1
    else:
        score_city1 -=2

    if humidity_city1 < 20:
        score_city1 += 2
    elif 21 <= humidity_city1< 25:
        score_city1 += 1
    elif 26 <= humidity_city1< 40:
        score_city1 += 0
    elif 27 <= humidity_city1<= 50:
        score_city1 -= 2
    else:
        score_city1 -= 3      
        
    #on fait pareil pour la ville 2
        
    city2=remove_accents(city2)
    
    if city2 == "La_Rochelle":
        city2 = "rochelle-17"
    elif city2 == "Aubusson":
        city2 = "aubusson-23"  
    elif city2 =="Marmande":
        city2 ="Agen"
    elif city2 =="Lure":
        city2 ="lure-70"    
    elif city2 =="Clamecy":
        city2 ="clamecy-58"   
        
    api2 = requests.get(f"https://prevision-meteo.ch/services/json/{city2}")
    api_city2 = api2.text
    api_clean_city2 = json.loads(api_city2)
    temperature_city2 = api_clean_city2['current_condition']['tmp']
    humidity_city2 = api_clean_city2['current_condition']['humidity']

    score_city2 = 0

    if temperature_city2 >= 35:
        score_city2 += 3
    elif 34 >= temperature_city2 > 25:
        score_city2 += 2
    elif 24 >= temperature_city2 > 19:
        score_city2 += 1
    elif 18 >= temperature_city2 > 15:
        score_city2 += 0
    elif 14 >= temperature_city2 > 5:
        score_city2 -= 1
    else:
        score_city2 -= 2

    if humidity_city2 < 20:
        score_city2 += 2
    elif 21 <= humidity_city2 < 25:
        score_city2 += 1
    elif 26 <= humidity_city2 < 40:
        score_city2 += 0
    elif 27 <= humidity_city2 <= 50:
        score_city2 -= 2
    else:
        score_city2 -= 3
        
    #calcul du score moyen en direct pour le département

    score = (score_city1 + score_city2)/2   
        
    return(score)

#Fonction pour éxécuter des requetes SQL

def execute_requete(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
    except sqlite3.Error as e:
        return(f"L'erreur {e} est apparu")
    return(cursor.fetchall())


# Fonction pour la couleur des DFCI en fonction du niveau d'alerte

def get_color(value):
    rounded_value = round(value)
    if 0 <= rounded_value <= 5:
        return "green"
    elif 6 <= rounded_value <= 10:
        return "orange"
    elif 11 <= rounded_value <= 15:
        return "red"
    elif 16 <= rounded_value <= 20:
        return "black"
    else:
        return "unknown"

#Fonction pour arrondir la date à la dizaine de jour la plus proche, utile pour la BDD

def date_plus_proche():
    aujourdhui = datetime.date.today()
    if aujourdhui.day <= 5:
        return f"01/{aujourdhui.month:02d}"
    elif aujourdhui.day <= 15:
        return f"10/{aujourdhui.month:02d}"
    elif aujourdhui.day <= 25:
        return f"20/{aujourdhui.month:02d}"
    else:
        next_month = aujourdhui.month + 1
        if next_month > 12:
            next_month = 1
        return f"01/{next_month:02d}"


#Fonction pour avoir le score moyen des 4 précédentes années

def get_average_alert_level(city, date):
    connection = createConnection()
    c = connection.cursor()

    alerte = []
    for i in range(2018, 2022):
        date_format = f"{date}/{i}"
        query = f"""SELECT e.nivAlerte
                    FROM Etat_DFCI e, DFCI d
                    WHERE e.codeDFCI = d.codeDFCI
                    AND e.dateEtat = '{date_format}'
                    AND d.nomDFCI = '{city}';"""

        c.execute(query)
        results = c.fetchone()

        alerte.append(int(results[0]))

    avg_alert_level = statistics.mean(alerte)


    return avg_alert_level

#Fonction de mise en commun des scores en direct et du score trouvé grâce aux 4 dernières années

def moyenne_departement(city1, city2, date):
    alert_level_city1 = get_average_alert_level(city1, date)
    alert_level_city2 = get_average_alert_level(city2, date)
    average_alert_level = (alert_level_city1 + alert_level_city2) / 2
    direct = meteo_direct(city1, city2)
    moyenne = (average_alert_level + direct) /2
    color = get_color(moyenne)
    return color




date = date_plus_proche()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index.html')
def index_html():
    return redirect(url_for('index'))

@app.route('/france.html')
def france():
    return render_template('france.html')

@app.route('/corse.html')
def corse():
    ajc = moyenne_departement("Ajaccio", "Ajaccio", date)    
    bst = moyenne_departement("Bastia", "Bastia", date)    
    return render_template('corse.html', ajc=ajc, bst=bst)

@app.route('/paca.html')
def paca():
    adhp = moyenne_departement("Castellane", "Barcelonnette", date)
    ha = moyenne_departement("Gap", "Briançon", date)
    am = moyenne_departement("Nice", "Grasse", date)
    bdr = moyenne_departement("Marseille", "Aix-en-Provence", date)
    var = moyenne_departement("Toulon", "Brignoles", date)
    vaucluse = moyenne_departement("Avignon", "Apt", date)
   
    return render_template('paca.html', adhp = adhp,ha=ha,am=am,bdr=bdr,var=var,vaucluse=vaucluse)

@app.route('/aquitaine.html')
def aquitaine():   

    gironde = moyenne_departement("Bordeaux", "Arcachon", date)
    charente = moyenne_departement("Angoulême", "Cognac", date)
    correze = moyenne_departement("Tulle", "Brive-la-Gaillarde", date)
    creuse = moyenne_departement("Gueret", "Aubusson", date)
    dordogne = moyenne_departement("Périgueux", "Bergerac", date)
    landes = moyenne_departement("Mont-de-Marsan", "Dax", date)
    lot_garonne = moyenne_departement("Agen", "Marmande", date)
    charente_maritime = moyenne_departement("La_Rochelle", "Rochefort", date)
    pyr_atlantique = moyenne_departement("Pau", "Bayonne", date)
    deux_sevre = moyenne_departement("Niort", "Bressuire", date)
    vienne = moyenne_departement("Poitiers", "Châtellerault", date)
    h_vienne = moyenne_departement("Limoges", "Bellac", date)

    return render_template('aquitaine.html', h_vienne=h_vienne,vienne=vienne,deux_sevre=deux_sevre,pyr_atlantique=pyr_atlantique, charente_maritime=charente_maritime,lot_garonne=lot_garonne, landes=landes, dordogne = dordogne, creuse = creuse, correze=correze, gironde=gironde, charente=charente)


@app.route('/occitanie.html')
def occitanie():
    
    gard = moyenne_departement("Nîmes", "Alès", date)
    herault = moyenne_departement("Montpellier", "Béziers", date)
    porientale= moyenne_departement("Perpignan", "Céret", date)
    aude = moyenne_departement("Carcassonne", "Limoux", date)
    lozere = moyenne_departement("Mende", "Florac", date)
   
    
    return render_template('occitanie.html', gard=gard, herault=herault, porientale=porientale, aude=aude, lozere=lozere )

@app.route('/bourgogne.html')
def bourgogne():
    coteor = moyenne_departement("Dijon", "Montbard", date)
    doubs = moyenne_departement("Besançon", "Montbéliard", date)
    jura = moyenne_departement("Lons-le-Saunier", "Dole", date)
    nievre = moyenne_departement("Nevers", "Clamecy", date)
    h_saone = moyenne_departement("Vesoul", "Lure", date)
    saoneloire = moyenne_departement("Autun", "Charolles", date)
    yonne = moyenne_departement("Auxerre", "Avallon", date)
    belfort= moyenne_departement("Belfort", "Belfort", date)
    return render_template('bourgogne.html', belfort=belfort, yonne=yonne, saoneloire=saoneloire, coteor = coteor, doubs=doubs, jura=jura, nievre=nievre, h_saone=h_saone )

@app.route('/information.html')
def information():
    return render_template('information.html')

@app.route('/contact.html')

def contact():
    return render_template('contact.html')

@app.route('/confirmation.html', methods=['POST'])
def confirmation():
    prenom = request.form['prenom']
    nom = request.form['nom']
    email = request.form['email']
    telephone = request.form['telephone']
    objet = request.form['objet']
    message = request.form['message']

    return render_template('confirmation.html', prenom=prenom, nom=nom, email=email, telephone=telephone,objet=objet, message=message)




if __name__ == '__main__':
    app.run()
    
    
    

