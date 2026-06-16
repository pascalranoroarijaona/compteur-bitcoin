import requests
import json
from datetime import date, datetime
import time

def get_current_block_height():
    """Récupère la hauteur de bloc actuelle du Bitcoin."""
    try:
        response = requests.get("https://blockstream.info/api/blocks/tip/height")
        return int(response.text)
    except Exception as e:
        print(f"Erreur lors de la récupération de la hauteur de bloc : {e}")
        return 916944  # Fallback pour 29/09/2025

def get_btc_price_eur():
    """Récupère le prix actuel du BTC en EUR via CoinGecko API."""
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur")
        return response.json()["bitcoin"]["eur"]
    except Exception as e:
        print(f"Erreur lors de la récupération du prix : {e}")
        return 97304  # Fallback pour 29/09/2025

def get_current_hash_rate_ths():
    """Récupère le hash rate actuel en TH/s via Blockchain.info API."""
    try:
        response = requests.get("https://api.blockchain.info/charts/hash-rate?format=json")
        data = response.json()
        hr_ths = data['values'][-1]['y']
        return hr_ths
    except Exception as e:
        print(f"Erreur lors de la récupération du hash rate : {e}")
        return 600000000  # Fallback approx 600 EH/s = 6e8 TH/s

def days_since_genesis(current_date=None):
    """Calcule les jours depuis la genèse (03/01/2009)."""
    genesis = date(2009, 1, 3)
    if current_date is None:
        current_date = date.today()
    return (current_date - genesis).days

def get_historical_prices(current_date):
    """Récupère les prix historiques BTC en EUR depuis 2018, échantillonné tous les 7 jours pour hebdomadaire."""
    from_ts = 1514764800  # 2018-01-01
    to_ts = int(time.mktime(current_date.timetuple()))
    try:
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range?vs_currency=eur&from={from_ts}&to={to_ts}"
        response = requests.get(url)
        data = response.json()['prices']
        points = []
        for i in range(0, len(data), 7):  # Échantillon tous les 7 jours pour hebdomadaire
            ts_ms, p = data[i]
            dt = datetime.fromtimestamp(ts_ms / 1000).date()
            fractional_year = dt.year + ((dt.timetuple().tm_yday - 1) / 365.25)
            points.append({'x': fractional_year, 'y': p})
        return points
    except Exception as e:
        print(f"Erreur hist: {e}")
        return [{'x': 2018.0, 'y': 10000}, {'x': 2025.0, 'y': 88266}]  # Dummy fallback

def get_power_law_points(current_date, exponent=5.6, years_ahead=5):
    """Génère des points pour la courbe de loi de puissance."""
    current_days = days_since_genesis(current_date)
    price_eur = get_btc_price_eur()
    A = price_eur / (current_days ** exponent)
    
    points = []
    for i in range(0, (years_ahead * 365) + 1, 30):  # Tous les 30 jours pour lisser
        day = current_days + i
        year = 2009 + (day / 365.25)
        price = A * (day ** exponent)
        points.append({'x': year, 'y': price})
    return points, A, exponent

def calculate_mined_btc(start_block, current_block):
    """Calcule le total de BTC minés depuis le bloc de départ jusqu'au bloc actuel."""
    total_btc = 0.0
    
    # Période 1 : Blocs ~499500 à 630000 (récompense 12.5 BTC)
    halving1_end = 630000
    blocks1 = max(0, min(halving1_end, current_block) - max(start_block, 499500))
    total_btc += blocks1 * 12.5
    
    # Période 2 : Blocs 630000 à 840000 (récompense 6.25 BTC)
    halving2_start = 630000
    halving2_end = 840000
    blocks2_start = max(start_block, halving2_start)
    blocks2_end = min(halving2_end, current_block)
    blocks2 = max(0, blocks2_end - blocks2_start)
    total_btc += blocks2 * 6.25
    
    # Période 3 : Blocs 840000 à maintenant (récompense 3.125 BTC)
    halving3_start = 840000
    blocks3_start = max(start_block, halving3_start)
    blocks3_end = current_block
    blocks3 = max(0, blocks3_end - blocks3_start)
    total_btc += blocks3 * 3.125
    
    return total_btc

def calculate_opportunity_cost(share=0.10):  # 10% de part hypothétique
    """Calcule le coût d'opportunité, plus données pour graphique."""
    start_block = 499500  # Hauteur approximative au 1er janvier 2018
    current_block = get_current_block_height()
    price_eur = get_btc_price_eur()
    current_date = date.today()
    
    total_mined_btc = calculate_mined_btc(start_block, current_block)
    btc_past = total_mined_btc * share
    value_eur_past = btc_past * price_eur
    total_euros_past = int(value_eur_past)  # En euros complets
    
    # Données historiques pour le graphique
    hist_points = get_historical_prices(current_date)
    
    initial_blocks = current_block - start_block
    
    # Calcul initial MW/jour total réseau (puissance moyenne)
    hr_ths = get_current_hash_rate_ths()
    eff = 30  # J/TH moyenne
    total_power_w = hr_ths * eff
    total_mw = total_power_w / 1_000_000
    
    # Points pour loi de puissance
    power_points, A, exponent = get_power_law_points(current_date)
    
    return {
        'btc_past': btc_past,
        'total_euros_past': total_euros_past,
        'price_eur': price_eur,
        'share': share,
        'hist_points': hist_points,
        'initial_blocks': initial_blocks,
        'start_block': start_block,
        'initial_current_block': current_block,
        'total_mined_btc': total_mined_btc,
        'initial_total_mw': total_mw,
        'power_points': power_points,
        'A': A,
        'exponent': exponent
    }

def generate_html():
    """Génère le fichier HTML avec mises à jour en temps réel via API."""
    result = calculate_opportunity_cost()
    
    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compteur Bitcoin France</title>
    <link rel="icon" type="image/x-icon" href="https://res.cloudinary.com/daabdiwnt/image/upload/v1760992725/ArticleBTC/Galaxy_mqivqu.ico">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Arial:wght@400;700&display=swap');
        body {{ 
            font-family: 'Arial', sans-serif; 
            background: #000; 
            color: #fff; 
            margin: 0; 
            padding: 0; 
            overflow: auto;
        }}
        .container {{ display: flex; min-height: 100vh; }}
        .left {{ 
            flex: 1; 
            padding: 40px; 
            display: flex; 
            flex-direction: column; 
            background: #000; 
        }}
        .right {{ 
            flex: 1; 
            padding: 40px; 
            background: #111; 
        }}
        h1 {{ 
            font-size: 2.5em; 
            color: #F7931A; 
            margin-bottom: 20px; 
            text-align: center;
        }}
        p {{ color: #ccc; text-align: center; margin-bottom: 40px; }}
        .share-select {{ 
            font-size: 1.2em; 
            color: #F7931A; 
            background: rgba(247, 147, 26, 0.1); 
            border: 2px solid #F7931A; 
            border-radius: 8px; 
            padding: 10px; 
            margin-bottom: 20px; 
            text-align: center;
        }}
        /* Style the button that is used to open and close the collapsible content */
        .collapsible {{
        background-color: #000;
        color: orange;
        cursor: pointer;
        padding: 25px;
        width: 80%;
        border: none;
        text-align: left;
        outline: none;
        font-size: 15px;
        }}

        /* Add a background color to the button if it is clicked on (add the .active class with JS), and when you move the mouse over it (hover) */
        .active, .collapsible:hover {{
        background-color: #000;
        }}

        /* Style the collapsible content. Note: hidden by default */
        .collapsible-content {{
        padding: 0 18px;
        display: none;
        overflow: hidden;
        background-color: #000;
        }}

        .counter {{ 
            font-size: 2.5em; 
            font-weight: 700; 
            margin: 20px 0; 
            padding: 20px; 
            background: rgba(247, 147, 26, 0.1); 
            border: 2px solid #F7931A; 
            border-radius: 8px; 
            box-shadow: 0 0 10px rgba(247, 147, 26, 0.3); 
            color: #fff;
            transition: all 0.3s ease;
        }}
        .label {{ 
            font-size: 1.2em; 
            color: #F7931A; 
            margin-bottom: 10px; 
            text-align: center;
        }}
        h2 {{ color: #F7931A; text-align: center; margin-bottom: 20px; }}
        #powerLawChart {{ 
            max-height: 500px; 
            background: #000; 
            border-radius: 8px; 
            border: 1px solid #F7931A; 
            margin-bottom: 20px;
        }}
        .additional-text {{ 
            color: #ccc; 
            font-size: 0.9em; 
            text-align: left; 
            line-height: 1.6;
        }}
        .additional-text ul {{ 
            list-style-type: none; 
            padding-left: 0; 
        }}
        .additional-text li {{ 
            margin-bottom: 10px; 
            padding-left: 20px; 
            position: relative; 
        }}
        .additional-text li::before {{ 
            content: "•"; 
            color: #F7931A; 
            font-weight: bold; 
            position: absolute; 
            left: 0; 
        }}
        a:link {{
        color: orange;
        background-color: transparent;
        text-decoration: none;
        }}

        a:visited {{
        color: orange;
        background-color: transparent;
        text-decoration: none;
        }}

        a:hover {{
        color: red;
        background-color: transparent;
        text-decoration: underline;
        }}

        a:active {{
        color: orange;
        background-color: transparent;
        text-decoration: underline;
        }}

        table {{ border-collapse: collapse; width: 100%; color: #FFF;}}
        th, td {{ border: 1px solid #FF9900; padding: 8px; text-align: right; }}
        th {{ background-color: #000; text-align: left; }}
        .slider-container {{ margin: 10px 0; display: flex; align-items: center; color: #FF9900;}}
        .slider-container label {{ width: 200px; margin-right: 10px; }}
        .slider-container input {{ flex: 1; }}
        .slider-container span {{ width: 60px; margin-left: 10px; text-align: right; }}
        .wrapper {{
            text-align: center;
        }}
        button {{ padding: 10px; background: #FF9900; color: white; border: none; cursor: pointer; }}

        .updating {{ color: #ccc; font-size: 0.9em; text-align: center; margin-top: 20px; }}
        /* Tooltip Styles - Updated for ? icon */
        .tooltip {{
            position: relative;
            display: inline-block;
            cursor: help;
        }}
        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 350px;
            background-color: #111;
            color: #fff;
            text-align: left;
            border-radius: 6px;
            padding: 10px;
            position: absolute;
            z-index: 1;
            top: 125%;
            left: 50%;
            margin-left: -38px;
            margin-bottom: -45px;
            opacity: 0;
            transition: opacity 0.001s;
            border: 1px solid #F7931A;
            font-size: 0.9em;
            line-height: 1.4;
        }}
        .tooltip .tooltiptext::after {{
            content: "";
            position: absolute;
            bottom: 100%;
            right: 85%;
            margin-left: -5px;
            border-width: 10px;
            border-style: solid;
            border-color: #F7931A transparent transparent transparent;
        }}
        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}

        .tooltip .tooltip-icon {{
            color: #0066cc;
            font-weight: bold;
            font-size: 1em;
            margin-left: 2px;
            vertical-align: super;
        }}
        
        :root {{
        --track-height: 6px;
        --thumb-height: 18px;
        --thumb-width: 18px;
        }}

        input[type="range"] {{
        appearance: none;
        background: transparent;
        width: 15rem;
        cursor: pointer;
        border-radius: 3px;
        }}

        /* Input Track */

        /* Chrome, Safari, Edge (Chromium) */
        input[type="range"]::-webkit-slider-runnable-track {{
        background: linear-gradient(to right, #fff 0%, #ff9900 100%);
        height: var(--track-height);
        border-radius: 3px;
        }}
        
        /* Firefox */
        input[type="range"]::-moz-range-track {{
        background: linear-gradient(to right, #fff 0%, #ff9900 100%);
        height: var(--track-height);
        border-radius: 3px;
        }}

        /* Inpiut Thumb */

        /* Chrome, Safari, Edge (Chromium) */
        input[type="range"]::-webkit-slider-thumb {{
        appearance: none;
        background: #fff;
        border-radius: 50%;
        width: var(--thumb-width);
        height: var(--thumb-height);
        margin-top: calc((var(--track-height) / 2) - (var(--thumb-height) / 2));
        border: 3px solid #ff9900;
        }}

        /* Firefox */
        input[type="range"]::-moz-range-thumb {{
        appearance: none;
        background: #fff;
        border-radius: 0;
        border-radius: 50%;
        border: 3px solid #ff9900;
        }}


    </style>
</head>
<body>
    <div class="container">
        <div class="left">
            <h1>Compteur Bitcoin</h1>
            <p>Coût d'<span class="tooltip">opportunité<span class="tooltip-icon">?</span><span class="tooltiptext">Le coût d'opportunité est un terme économique qui désigne ce que vous perdez en choisissant une option plutôt qu'une autre. Ici, c'est le regret financier : "Et si la France avait dépensé de l'argent/énergie pour miner du Bitcoin au lieu d'autre chose (comme des impôts ou des subventions) ? Combien d'euros aurait-elle gagnés aujourd'hui ?"</span></span> si la France avait miné X% (sélectionnable ci-dessous) de la <span class="tooltip">puissance globale de hachage<span class="tooltip-icon">?</span><span class="tooltiptext">La puissance globale de hachage est la vitesse totale à laquelle tous les mineurs du monde font des calculs (hachages) pour résoudre les puzzles mathématiques du Bitcoin. Mesurée en EH/s (exahashs par seconde), c'est la "force de calcul" qui protège le réseau. Actuellement ~1000 EH/s.</span></span> du <span class="tooltip">réseau Bitcoin<span class="tooltip-icon">?</span><span class="tooltiptext">Le réseau Bitcoin est un système décentralisé mondial : un réseau d'ordinateurs (nœuds) qui valident et stockent la blockchain ensemble, sans banque centrale. Il inclut les mineurs (qui sécurisent), les nœuds (qui vérifient) et les utilisateurs (wallets). Miner X% de sa puissance signifie contribuer X% des calculs totaux pour gagner des récompenses.</span></span> depuis 2018. Mises à jour en temps réel toutes les 10 minutes.</p>
            
            <select id="shareSelect" class="share-select">
                <option value="1">1%</option>
                <option value="2">2%</option>
                <option value="3">3%</option>
                <option value="5">5%</option>
                <option value="10" selected>10%</option>
                <option value="15">15%</option>
            </select>
            
            <div class="label">MW/Jour Nécessaires <span class="tooltip"><span class="tooltip-icon">?</span><span class="tooltiptext">Pour miner, il faut de l'électricité. Ici, il s'agirait, par exemple, de surplus nucléaire et énergies intermittentes bas-carbone disponible chaque jour en France pour optimiser & limiter les gaspillages sur le réseau électrique France (optimisation sous contraintes). Par exemple <a target="_blank" href="https://x.com/i/grok/share/lgsH4qga1fdvgcIIYeSoolj2Z">il est estimé que plus de 3.6 GW sont disponibles chaque jour et non utilisés en raison de la modulation sur le parc nucléaire français.</a></span></span></div>
            <div class="counter" id="mwhCounter">0</div>

            <div class="label">Total Manqués (€) <span class="tooltip"><span class="tooltip-icon">?</span><span class="tooltiptext">Valeur actuelle des BTC manqués (coût d'opportunité total en milliards €). Pour 10% par exemple, ~>= 30 milliards € brut aujourd'hui. Formule (BTC minés × prix actuel).</span></span></div>
            <div class="counter" id="totalEurosCounter">0</div>
            
            <div class="label">BTC Manqués <span class="tooltip"><span class="tooltip-icon">?</span><span class="tooltiptext">Les BTC "manqués" sont les récompenses que la France aurait gagnées en minant. "Miner" n'est pas creuser de l'or, mais un processus informatique : des ordinateurs résolvant des énigmes pour ajouter des blocs à la blockchain et sécuriser les transactions. Le premier mineur qui résout le puzzle gagne ~3.125 BTC/bloc dans le cycle actuel. Les "pools" de minage permettent de distribuer les récompenses aux différents mineurs en fonction de leur part de hachage du réseau.</span></span></div>
            <div class="counter" id="btcCounter">0</div>
            
            <div class="label">Prix BTC Actuel (€) <span class="tooltip"><span class="tooltip-icon">?</span><span class="tooltiptext">Prix de marché actuel du Bitcoin en euros, mis à jour en live via API CoinGecko. Utilisé pour valoriser les BTC manqués (multiplié par le nombre de BTC).</span></span></div>
            <div class="counter" id="priceCounter">0</div>
            
            <div class="label">Blocs Manqués <span class="tooltip"><span class="tooltip-icon">?</span><span class="tooltiptext">Un bloc = une page de transactions ajoutée ~toutes les 10 min. On compte ici le nombre passé de blocs de transactions depuis 2018.</span></span></div>
            <div class="counter" id="blocksCounter">0</div>
            
            
            
            
            <div class="updating" id="updateText">Mise à jour en temps réel.</div>
        </div>
        
        <div class="right">
            <h2>Prix Historique BTC (EUR) & Loi de Puissance (exposant 5.6)</h2>
            <canvas id="powerLawChart"></canvas>
            <p>La loi de puissance modélise la croissance du prix BTC : P(t) = a * t^5.6, où t = jours depuis genèse (2009). Calibrée sur prix actuel, elle projette une hausse ~35-40%/an. Exposant 5.6 est historique (basé sur données 2010-2025).</p>
            <div class="additional-text">
                <ul>
                    <li>Ce manque à gagner n'inclut pas les potentielles retombées économiques de réindustrialiser la France avec une nouvelle industrie novatrice faisant de l'optimisation sous contraintes de réseaux électriques.</li>
                    <li>La création d'emplois dans des régions rurales et là où les containers de minage peuvent s'implémenter. <span class="tooltip"><span class="tooltiptext">Serveurs : ASIC spéciaux (ex. Antminer, ~5k€/unité). Placés en data centers sécurisés (Nord France pour froid/élec pas chère), propriété État/EDF. Investissement ~1-5 Md€, amorti par BTC.</span></span></li>
                    <li>Aide potentielle à l'effort national pour repasser sous les 3% de déficit (sans taxe, ni subvention).</li>
                    <li>La potentielle mise en place de circularité en injectant une partie des profits dans les collectivités locales.</li>
                    <li>Pour maximiser l'utilité du minage de Bitcoin dans la société : une fois une certaine stabilité des dépenses et de la société atteinte, les profits du minage pourraient servir au bien-être des populations, au développement des énergies renouvelables, à l'agroécologie et encore en projetant à plus long-terme : à aider la transition bas-carbone des pays du Sud par exemple.</li>
                    <li><a href="https://x.com/i/grok/share/vxt7T2ufIWKKPaWyWEj0I5Mtl" target="_blank">Le Bitcoin peut devenir un grand allié pour accélérer la transition énergétique</a>. Mais il faut interdire l’utilisation de combustible fossile dans le minage Bitcoin sous peine de lourdes sanctions et réguler le minage pour que l'usage n'empiète pas sur la consommation d'électricité courante (optimisation sous contraintes).</li>
                    <li><a href="https://www.thephysicsofbitcoin.com/" target="_blank">Bitcoin suit une loi de puissance</a> et le rendement futur pourrait être projeté avec un écart type d'erreur.</li>                    
                    <li>📚 En apprendre plus sur Bitcoin avec <b><a href="https://www.thesunstandard.net/blog/nautile-nakamoto.html?lg=FR" target="_blank" style="color: orange;">un 'livre numérique' (format original contenant textes, illustrations et vidéos) accessible gratuitement en ligne et qui lui est dédié</a></b> (vue la densité du sujet, il faut peut-être y consacrer un effort espacé dans le temps). 📚</li>
                </ul>
                <br />
                <button type="button" class="collapsible"><h4>Cliquez ici pour plus d'explications techniques sur le script.</h4></button>
                <div class="collapsible-content">
                    <ul>
                        <li>Ce script calcule le potentiel manqué en milliards d'euros à miner Bitcoin depuis le 1er Janvier 2018. Il suppose que la France aurait pu dédier une part fixe (1,2,3,5,10 ou 15%) de la puissance de hachage globale du réseau Bitcoin depuis janvier 2018 (une hypothèse réaliste avec différents scénarios et basée sur une estimation d'électricité consommé globalement du Bitcoin ~500 TWh cumulés sur la période). Il fetch les données en temps réel (hauteur de bloc actuelle et prix du BTC en EUR) via des API gratuites. Le total est le nombre de BTC minés multiplié par le prix actuel, converti en milliards d'EUR.</li>
                        <li>Récupération en temps réel : Toutes les 10 minutes (600 000 ms), le JS fetch les données via les API (hauteur de bloc via Blockstream et prix via CoinGecko). Les API sont gratuites et CORS-compatibles.</li>
                        <li>Calculs dynamiques : J'ai intégré une fonction JS calculateMinedBtc qui miroite le calcul Python pour déterminer les BTC minés cumulés (en tenant compte des halvings). Le total gaspillage est recalculé comme (BTC # manqués totaux × prix actuel), et les compteurs s'animent vers les nouvelles valeurs.</li>  
                        <li>Ceci est une simulation, <a href="https://colab.research.google.com/drive/1OC5ePgAxMX47JP14uQVTpBktjd2kZq6u?usp=sharing" target="_blank">j'ouvre le code source pour rendre la logique transparente</a>. Cette simulation peut donner une idée de "l'ordre de grandeur" et un rendement total brut sans pour autant prendre en compte CAPEX et autres considérations techniques et implémentations fines.</li>
                    </ul>
                </div>
            </div>
            <br />
            <br />
                <button type="button" class="collapsible"><h4>Effectuer une simulation complète : Minage Bitcoin - France (En Euro)</h4></button>
                <div class="collapsible-content">
                    <p style="color: #FF9900;">Un site dédié a été créé : <b><a target="_blank" href="https://www.simulateur-bitcoin.fr">https://www.simulateur-bitcoin.fr</a></b>.</p>
                    <p style="color: #FF9900;">Cette simulation modélise un déploiement variable sur surplus EDF (2026-2032), avec loi de puissance pour le prix BTC (en USD, convertis en EUR), halving 2028, et croissance du hash global. Glissez les sliders pour ajuster les paramètres et voir les mises à jour en temps réel. <span class="tooltip"><span class="tooltiptext">"La France" = l'État français (gouvernement, via Ministère Économie/Transition Écologique), pas la Banque de France. Initiative publique pour souveraineté numérique, comme un projet d'infrastructure (ex. TGV). Sécurité : Data centers blindés (ANSSI audits), wallets offline multi-sig. Pourquoi 2018 ? Équilibre : post-bulle 2017, maturité tech, inclut 2 halvings ; pas 2015 (trop volatile), pas 2021 (moins de recul).</span></span></p>
                    
                    <div class="slider-container">
                        <label>Nombre de GW : <span class="tooltip"><span class="tooltiptext">Puissance allouée (ex. 1 GW = 1000 MW). Interruptible sur surplus EDF, avec récupération chaleur (chauffage urbain). Pour 1 GW, ~55 EH/s (5.5% global), investissement ~2-3 Md€ (hardware + infra), amorti <6 mois.</span></span></label>
                        <input type="range" id="gwSlider" min="0.15" max="5" step="0.05" value="1">
                        <span id="gwValue">1</span>
                    </div>
                    
                    <div class="slider-container">
                        <label>Exposant loi de puissance : <span class="tooltip"><span class="tooltiptext">Exposant dans P(t) = a * t^exposant. 5.6 est calibré historique ; plus haut = croissance plus agressive.</span></span></label>
                        <input type="range" id="exponentSlider" min="4" max="7" step="0.1" value="5.6">
                        <span id="exponentValue">5.6</span>
                    </div>
                    
                    <div class="slider-container">
                        <label>Croissance hash/an (%): <span class="tooltip"><span class="tooltiptext">Croissance annuelle estimée du hash global (~50%/an historique). Dilue le % français sans upgrade hardware.</span></span></label>
                        <input type="range" id="growthSlider" min="0" max="100" step="5" value="30">
                        <span id="growthValue">30</span>
                    </div>
                    
                    
                    <div id="results-table"></div>
                    
                    <h2>Évolution Projetée du Prix du Bitcoin (USD)</h2>
                    <canvas id="priceChart" width="800" height="400"></canvas>
                    
                    <h2>Revenus Annuels Projetés (M €)</h2>
                    <canvas id="revenueChart" width="800" height="400"></canvas>
                    
                    <h2>Revenus Cumulés Projetés (M €)</h2>
                    <canvas id="cumulativeChart" width="800" height="400"></canvas>
                </div>            
        </div>
    </div>
    
    
    <script>
        
        var coll = document.getElementsByClassName("collapsible");
        var i;

        for (i = 0; i < coll.length; i++) {{
        coll[i].addEventListener("click", function() {{
            this.classList.toggle("active");
            var content = this.nextElementSibling;
            if (content.style.display === "block") {{
            content.style.display = "none";
            }} else {{
            content.style.display = "block";
            }}
        }});
        }}
        // Fonction pour calculer les BTC minés (miroir du Python)
        function calculateMinedBtc(currentBlock) {{
            let totalBtc = 0.0;
            const startBlock = {result['start_block']};
            
            // Période 1 : ~499500 à 630000 (12.5 BTC)
            const halving1End = 630000;
            let blocks1 = Math.max(0, Math.min(halving1End, currentBlock) - Math.max(startBlock, 499500));
            totalBtc += blocks1 * 12.5;
            
            // Période 2 : 630000 à 840000 (6.25 BTC)
            const halving2Start = 630000;
            const halving2End = 840000;
            let blocks2Start = Math.max(startBlock, halving2Start);
            let blocks2End = Math.min(halving2End, currentBlock);
            let blocks2 = Math.max(0, blocks2End - blocks2Start);
            totalBtc += blocks2 * 6.25;
            
            // Période 3 : 840000+ (3.125 BTC)
            const halving3Start = 840000;
            let blocks3Start = Math.max(startBlock, halving3Start);
            let blocks3End = currentBlock;
            let blocks3 = Math.max(0, blocks3End - blocks3Start);
            totalBtc += blocks3 * 3.125;
            
            return totalBtc;
        }}

        // Animation fluide des compteurs
        function animateCounter(id, target, duration = 5000, suffix = '') {{
            const counter = document.getElementById(id);
            const start = parseFloat(counter.textContent.replace(/,/g, '').replace(/[^0-9.-]/g, '')) || 0;
            const range = target - start;
            const increment = range / (duration / 16);
            let current = start;
            const timer = setInterval(() => {{
                current += increment;
                if (current >= target) {{
                    current = target;
                    clearInterval(timer);
                }}
                if (id === 'totalEurosCounter' || id === 'btcCounter' || id === 'blocksCounter' || id === 'mwhCounter') {{
                    counter.textContent = Math.floor(current).toLocaleString() + suffix;
                }} else {{
                    counter.textContent = current.toFixed(2).toLocaleString() + suffix;
                }}
            }}, 16);
        }}

        // Fonction pour mettre à jour tous les compteurs avec le share actuel
        function updateAllCounters(newHeight, newPrice, newBlocks, totalMw) {{
            const share = currentShare / 100;
            const newTotalMined = calculateMinedBtc(newHeight);
            const newTotalBtc = newTotalMined * share;
            const newTotalEuros = Math.floor(newTotalBtc * newPrice);
            const newMw = totalMw * share;
            
            animateCounter('totalEurosCounter', newTotalEuros, 5000, ' €');
            animateCounter('btcCounter', newTotalBtc, 5000, ' BTC');
            animateCounter('priceCounter', newPrice, 5000, ' €');
            animateCounter('blocksCounter', newBlocks, 5000, '');
            animateCounter('mwhCounter', newMw, 5000, ' MW');
        }}

        // Données embeddées initiales
        const initialTotalEuros = {result['total_euros_past']};
        const initialBtc = {result['btc_past']};
        const initialPrice = {result['price_eur']};
        const initialBlocks = {result['initial_blocks']};
        const histData = {json.dumps(result['hist_points'])};
        const powerData = {json.dumps(result['power_points'])};
        const initialTotalMw = {result['initial_total_mw']};
        const startBlock = {result['start_block']};
        const initialCurrentBlock = {result['initial_current_block']};

        let currentShare = 10;
        let lastHeight = initialCurrentBlock;
        let lastPrice = initialPrice;
        let lastTotalMw = initialTotalMw;

        // Événement pour le dropdown
        document.getElementById('shareSelect').onchange = function(e) {{
            currentShare = parseInt(e.target.value);
            // Mise à jour immédiate avec les dernières données connues
            if (lastHeight && lastPrice) {{
                fetch('https://api.blockchain.info/charts/hash-rate?format=json&cors=true')
                .then(r => r.json())
                .then(hashData => {{
                    const hr_ths = hashData.values[hashData.values.length - 1].y;
                    const eff = 30; // J/TH moyenne
                    const total_power_w = hr_ths * eff;
                    const total_mw = total_power_w / 1000000;
                    updateAllCounters(lastHeight, lastPrice, lastHeight - startBlock, total_mw);
                    lastTotalMw = total_mw;
                }})
                .catch(() => {{
                    // Fallback avec valeur initiale
                    updateAllCounters(lastHeight, lastPrice, lastHeight - startBlock, initialTotalMw);
                }});
            }}
        }};

        // Fonction de mise à jour en temps réel
        async function updateData() {{
            try {{
                const heightRes = await fetch('https://blockstream.info/api/blocks/tip/height');
                const heightText = await heightRes.text();
                const newHeight = parseInt(heightText);
                
                const priceRes = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur');
                const priceData = await priceRes.json();
                const newPrice = priceData.bitcoin.eur;
                
                // Fetch hash rate pour MW
                const hrRes = await fetch('https://api.blockchain.info/charts/hash-rate?format=json&cors=true');
                const hashData = await hrRes.json();
                const hr_ths = hashData.values[hashData.values.length - 1].y;
                const eff = 30; // J/TH moyenne réseau
                const total_power_w = hr_ths * eff;
                const total_mw = total_power_w / 1000000;
                
                const newBlocks = newHeight - startBlock;
                
                // Mise à jour avec share actuel
                updateAllCounters(newHeight, newPrice, newBlocks, total_mw);
                
                // Mise à jour du timestamp
                document.getElementById('updateText').textContent = `Dernière mise à jour: ${{new Date().toLocaleString('fr-FR')}}`;
                
                lastHeight = newHeight;
                lastPrice = newPrice;
                lastTotalMw = total_mw;
            }} catch (e) {{
                console.error('Erreur lors de la mise à jour:', e);
                // Fallback
                updateAllCounters(lastHeight, lastPrice, lastHeight - startBlock, lastTotalMw);
            }}
        }}

        // Initialisation
        window.onload = async () => {{
            // 1. Initialiser les compteurs à 0 (pour l'animation)
            document.getElementById('totalEurosCounter').textContent = '0 €';
            document.getElementById('btcCounter').textContent = '0 BTC';
            document.getElementById('priceCounter').textContent = '0 €';
            document.getElementById('blocksCounter').textContent = '0';
            document.getElementById('mwhCounter').textContent = '0 MW';
            
            // 2a. Graphique initial avec données Python
            const ctx = document.getElementById('powerLawChart').getContext('2d');
            window.powerLawChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    datasets: [
                        {{
                            label: 'Prix Historique (EUR)',
                            data: {json.dumps(result['hist_points'])},
                            borderColor: '#F7931A',
                            backgroundColor: 'rgba(247, 147, 26, 0.1)',
                            tension: 0.1,
                            pointRadius: 0,
                            fill: false
                        }},
                        {{
                            label: 'Loi de Puissance (exposant 5.6)',
                            data: {json.dumps(result['power_points'])},
                            borderColor: '#FF6B35',
                            backgroundColor: 'transparent',
                            tension: 0.1,
                            pointRadius: 0,
                            fill: false,
                            borderDash: [5, 5]
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ type: 'linear', ticks: {{ color: '#fff' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }}, title: {{ display: true, text: 'Année', color: '#fff' }} }},
                        y: {{ type: 'linear', ticks: {{ color: '#fff' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }}, title: {{ display: true, text: 'Prix BTC (€)', color: '#fff' }}, beginAtZero: true }}
                    }},
                    plugins: {{ legend: {{ labels: {{ color: '#fff' }} }} }}
                }}
            }});
            // 2b. Tenter une première mise à jour complète (compteurs + graphiques)
            await updateData();
            //animateCounter('totalEurosCounter', {result['total_euros_past']}, 3000, ' €');
            //animateCounter('btcCounter', {result['btc_past']}, 3000, ' BTC');
            //animateCounter('priceCounter', {result['price_eur']}, 2000, ' €');
            //animateCounter('blocksCounter', {result['initial_blocks']}, 2000, '');
            //animateCounter('mwhCounter', initialMw, 2000, ' MW');
            
            // 3. Puis mise à jour toutes les 10 minutes (déjà en place)
            setInterval(updateData, 600000);

            // 4. Initialisation de la simulation (si le panneau est ouvert)
            updateSimulation();
        }};
         // Initialisation
        //window.onload = async () => {{
        //    // 1. Animation initiale avec les données Python (fallback)
        //    const initialShare = 0.10;
        //    const initialMw = {result['initial_total_mw']} * initialShare;
        //    
        //    document.getElementById('totalEurosCounter').textContent = '0';
        //    document.getElementById('btcCounter').textContent = '0';
        //    document.getElementById('priceCounter').textContent = '0';
        //    document.getElementById('blocksCounter').textContent = '0';
        //    document.getElementById('mwhCounter').textContent = '0';
        //    
        //    animateCounter('totalEurosCounter', {result['total_euros_past']}, 3000, ' €');
        //    animateCounter('btcCounter', {result['btc_past']}, 3000, ' BTC');
        //    animateCounter('priceCounter', {result['price_eur']}, 2000, ' €');
        //    animateCounter('blocksCounter', {result['initial_blocks']}, 2000, '');
        //    animateCounter('mwhCounter', initialMw, 2000, ' MW');

        //    // 2. Graphique initial avec données Python
        //    const ctx = document.getElementById('powerLawChart').getContext('2d');
        //    window.powerLawChart = new Chart(ctx, {{
        //        type: 'line',
        //        data: {{
        //            datasets: [
        //                {{
        //                    label: 'Prix Historique (EUR)',
        //                    data: {json.dumps(result['hist_points'])},
        //                    borderColor: '#F7931A',
        //                    backgroundColor: 'rgba(247, 147, 26, 0.1)',
        //                    tension: 0.1,
        //                    pointRadius: 0,
        //                    fill: false
        //                }},
        //                {{
        //                    label: 'Loi de Puissance (exposant 5.6)',
        //                    data: {json.dumps(result['power_points'])},
        //                    borderColor: '#FF6B35',
        //                    backgroundColor: 'transparent',
        //                    tension: 0.1,
        //                    pointRadius: 0,
        //                    fill: false,
        //                    borderDash: [5, 5]
        //                }}
        //             ]
        //         }},
        //         options: {{
        //             responsive: true,
        //             maintainAspectRatio: false,
        //             scales: {{
        //                x: {{ type: 'linear', ticks: {{ color: '#fff' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }}, title: {{ display: true, text: 'Année', color: '#fff' }} }},
        //                y: {{ type: 'linear', ticks: {{ color: '#fff' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }}, title: {{ display: true, text: 'Prix BTC (€)', color: '#fff' }}, beginAtZero: true }}
        //             }},
        //             plugins: {{ legend: {{ labels: {{ color: '#fff' }} }} }}
        //         }}
        //     }});

        //     // 3. MISE À JOUR IMMÉDIATE AU CHARGEMENT
        //     await updateData();  // Rafraîchit tout : bloc, prix, hash rate, graphiques

        //     // 4. Puis mise à jour toutes les 10 minutes
        //     setInterval(updateData, 600000);
        // }};

        // Fonction mise à jour (inchangée, sauf qu'elle met à jour le graphique aussi)
        async function updateData() {{
            try {{
                const [heightRes, priceRes, hrRes] = await Promise.all([
                    fetch('https://blockstream.info/api/blocks/tip/height'),
                    fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur'),
                    fetch('https://api.blockchain.info/charts/hash-rate?format=json&cors=true')
                ]);

                const newHeight = parseInt(await heightRes.text());
                const priceData = await priceRes.json();
                const newPrice = priceData.bitcoin.eur;
                const hashData = await hrRes.json();
                const hr_ths = hashData.values[hashData.values.length - 1].y;
                const eff = 30;
                const total_mw = (hr_ths * eff) / 1000000;
                const newBlocks = newHeight - {result['start_block']};

                // Mise à jour des compteurs
                updateAllCounters(newHeight, newPrice, newBlocks, total_mw);

                // Mise à jour du graphique de loi de puissance
                const currentDays = daysSinceGenesis();
                const A = newPrice / Math.pow(currentDays, {result['exponent']});
                const powerPoints = [];
                for (let i = 0; i <= 5 * 365; i += 30) {{
                    const day = currentDays + i;
                    const year = 2009 + (day / 365.25);
                    const price = A * Math.pow(day, {result['exponent']});
                    powerPoints.push({{x: year, y: price}});
                }}

                // Mettre à jour le dataset
                window.powerLawChart.data.datasets[1].data = powerPoints;
                window.powerLawChart.update('quiet');

                // Mettre à jour la simulation si ouverte
                if (typeof updateSimulation === 'function') {{
                    A_POWER_LAW = newPrice / Math.pow(getDaysFromGenesis(2025), parseFloat(document.getElementById('exponentSlider')?.value || 5.6));
                    updateSimulation();
                }}

                document.getElementById('updateText').textContent = `Dernière mise à jour: ${{new Date().toLocaleString('fr-FR')}}`;

                lastHeight = newHeight;
                lastPrice = newPrice;
                lastTotalMw = total_mw;

            }} catch (e) {{
                console.error('Erreur mise à jour:', e);
            }}
        }}
        
        // Fonction pour calculer les jours depuis genèse
        function daysSinceGenesis() {{
            const genesis = new Date(2009, 0, 3);
            const now = new Date();
            return Math.floor((now - genesis) / (1000 * 60 * 60 * 24));
        }}
        
        document.querySelectorAll('.tooltip').forEach(function(tooltip) {{
            const tooltipText = tooltip.querySelector('.tooltiptext');
            let timeout;

            tooltip.addEventListener('mouseenter', function() {{
                // Clear any existing timeout to prevent premature hide
                if (timeout) clearTimeout(timeout);
                // Show the tooltip
                tooltipText.classList.add('visible');
            }});

            tooltip.addEventListener('mouseleave', function() {{
                // Set a timeout to hide after 5 seconds (adjust as needed)
                timeout = setTimeout(function() {{
                    tooltipText.classList.remove('visible');
                }}, 5000);
            }});
        }});
        // Paramètres de simulation
        const GENESIS_DATE = new Date(2009, 0, 3);  // 3 janv 2009
        const CURRENT_HASH_EH_S = 1000;  // Hash global actuel (EH/s)
        const BASE_FRENCH_HASH_EH_S = 55.6;   // Pour 1 GW à 18 J/TH
        const BLOCKS_PER_DAY = 144;
        const DAYS_PER_YEAR = 365.25;
        const FEES_PER_BLOCK = 0.022;
        let A_POWER_LAW = {result['A']};  // Calibré initialement
        let ANNUAL_GROWTH_RATE = 1.5;  // 50% initial
        let FRENCH_HASH_EH_S = BASE_FRENCH_HASH_EH_S * 1;  // Initial pour 1 GW
        
        let priceChart, revenueChart, cumulativeChart;
        
        // Halving approx avril 2028 (jour 121 de l'année)
        function getAverageReward(year) {{
            if (year < 2028) {{
                return 3.125 + FEES_PER_BLOCK;
            }} else if (year < 2032) {{
                if (year === 2028) {{
                    // Moyenne 2028 : ~121 jours à 3.125, reste à 1.5625
                    const full_reward_days = 121 / DAYS_PER_YEAR;
                    return (3.125 * full_reward_days + 1.5625 * (1 - full_reward_days)) + FEES_PER_BLOCK;
                }}
                return 1.5625 + FEES_PER_BLOCK;
            }}
            return 0.78125 + FEES_PER_BLOCK;  // Post-2032
        }}
        
        function getDaysFromGenesis(year) {{
            const midDate = new Date(year, 6, 1);  // 1er juillet
            const diffTime = midDate - GENESIS_DATE;
            return Math.floor(diffTime / (1000 * 60 * 60 * 24));
        }}
        
        function getBTCPrice(days, exponent) {{
            return A_POWER_LAW * Math.pow(days, exponent);
        }}
        
        // Mise à jour des sliders avec appel dynamique à updateSimulation
        document.getElementById('gwSlider').oninput = function() {{
            document.getElementById('gwValue').textContent = this.value;
            updateSimulation();
        }};
        document.getElementById('exponentSlider').oninput = function() {{
            document.getElementById('exponentValue').textContent = this.value;
            updateSimulation();
        }};
        document.getElementById('growthSlider').oninput = function() {{
            document.getElementById('growthValue').textContent = this.value;
            updateSimulation();
        }};

        
        function updateSimulation() {{
            const gw = parseFloat(document.getElementById('gwSlider').value);
            const exponent = parseFloat(document.getElementById('exponentSlider').value);
            ANNUAL_GROWTH_RATE = 1 + (parseFloat(document.getElementById('growthSlider').value) / 100);
            FRENCH_HASH_EH_S = BASE_FRENCH_HASH_EH_S * gw;
            
            // Recalculer A si exposant change (calibré sur prix actuel ~123000 USD)
            const currentDays = getDaysFromGenesis(2025);
            const currentPrice = {result['price_eur']};
            A_POWER_LAW = currentPrice / Math.pow(currentDays, exponent);
            
            // Calcul des données
            const years = [2026, 2027, 2028, 2029, 2030, 2031, 2032];
            let simulationData = [];
            let cumulativeRevenueEur = 0;
            
            years.forEach(year => {{
                const days = getDaysFromGenesis(year);
                const priceEur = getBTCPrice(days, exponent);
                const hashYear = CURRENT_HASH_EH_S * Math.pow(ANNUAL_GROWTH_RATE, year - 2026);
                const hashPct = (FRENCH_HASH_EH_S / hashYear) * 100;
                const avgReward = getAverageReward(year);
                const totalBTCEmittedYear = avgReward * BLOCKS_PER_DAY * DAYS_PER_YEAR;
                const btcMined = (hashPct / 100) * totalBTCEmittedYear;
                const revenueEur = btcMined * priceEur;
                
                cumulativeRevenueEur += revenueEur;
                
                simulationData.push({{
                    year: year,
                    priceEur: priceEur,
                    hashPct: hashPct,
                    btcMined: btcMined,
                    revenueEur: revenueEur,
                    cumulativeEur: cumulativeRevenueEur
                }});
            }});
            
            // Génération du tableau
            let tableHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Année</th>
                            <th>Prix BTC (€)</th>
                            <th>% Hash FR</th>
                            <th>BTC Minés</th>
                            <th>Revenus Annuels (M €)</th>
                            <th>Revenus Cumulés (M €)</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            simulationData.forEach(row => {{
                tableHTML += `
                    <tr>
                        <td>${{row.year}}</td>
                        <td>${{Math.round(row.priceEur).toLocaleString()}}</td>
                        <td>${{row.hashPct.toFixed(3)}} %</td>
                        <td>${{Math.round(row.btcMined).toLocaleString()}}</td>
                        <td>${{Math.round(row.revenueEur).toLocaleString()}}</td>
                        <td>${{Math.round(row.cumulativeEur).toLocaleString()}}</td>
                    </tr>
                `;
            }});
            tableHTML += `
                    </tbody>
                    <tfoot>
                        <tr style="font-weight: bold;">
                            <td>Total</td>
                            <td colspan="2"></td>
                            <td>${{Math.round(simulationData.reduce((sum, r) => sum + r.btcMined, 0)).toLocaleString()}} BTC</td>
                            <td colspan="2">${{Math.round(simulationData[simulationData.length - 1].cumulativeEur).toLocaleString()}} M €</td>
                        </tr>
                    </tfoot>
                </table>
            `;
            document.getElementById('results-table').innerHTML = tableHTML;
            
            // Mise à jour des graphiques
            if (priceChart) priceChart.destroy();
            if (revenueChart) revenueChart.destroy();
            if (cumulativeChart) cumulativeChart.destroy();
            
            // Graphique 1: Prix BTC (€)
            const priceCtx = document.getElementById('priceChart').getContext('2d');
            priceChart = new Chart(priceCtx, {{
                type: 'line',
                data: {{
                    labels: years.map(y => y.toString()),
                    datasets: [{{
                        label: 'Prix BTC (€)',
                        data: simulationData.map(d => d.priceEur),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{ beginAtZero: false, title: {{ display: true, text: 'Prix (USD)' }} }},
                        x: {{ title: {{ display: true, text: 'Année' }} }}
                    }},
                    plugins: {{ title: {{ display: true, text: 'Projection du Prix du Bitcoin (Loi de Puissance)' }} }}
                }}
            }});
            
            // Graphique 2: Revenus Annuels (M €)
            const revenueCtx = document.getElementById('revenueChart').getContext('2d');
            revenueChart = new Chart(revenueCtx, {{
                type: 'bar',
                data: {{
                    labels: years.map(y => y.toString()),
                    datasets: [{{
                        label: 'Revenus (M €)',
                        data: simulationData.map(d => d.revenueEur),
                        backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{ beginAtZero: true, title: {{ display: true, text: 'Revenus (M €)' }} }},
                        x: {{ title: {{ display: true, text: 'Année' }} }}
                    }},
                    plugins: {{ title: {{ display: true, text: 'Revenus Annuels Projetés' }} }}
                }}
            }});
            
            // Graphique 3: Revenus Cumulés (M €)
            const cumulativeCtx = document.getElementById('cumulativeChart').getContext('2d');
            cumulativeChart = new Chart(cumulativeCtx, {{
                type: 'line',
                data: {{
                    labels: years.map(y => y.toString()),
                    datasets: [{{
                        label: 'Revenus Cumulés (M €)',
                        data: simulationData.map(d => d.cumulativeEur),
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.2)',
                        fill: true,
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{ beginAtZero: true, title: {{ display: true, text: 'Revenus Cumulés (M €)' }} }},
                        x: {{ title: {{ display: true, text: 'Année' }} }}
                    }},
                    plugins: {{ title: {{ display: true, text: 'Projection des Revenus Cumulés' }} }}
                }}
            }});
        }}
        
        // Initialisation
        updateSimulation();
    
    </script>
</body>
</html>
    """
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Fichier index.html généré")

if __name__ == "__main__":
    generate_html()
