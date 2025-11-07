#!/usr/bin/env python3
"""
ðŸš€ BOUTIQUE MOBILE - VERSION COMPLÃˆTE
Application de gestion d'inventaire complÃ¨te - Flask + SQLite
"""

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, make_response
from datetime import datetime
import io
import csv

app = Flask(__name__)

def get_db_connection():
    """Connexion SQLite locale"""
    conn = sqlite3.connect('boutique_mobile.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialise la base de donnÃ©es SQLite"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table catÃ©gories
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            emoji TEXT DEFAULT 'ðŸ“¦',
            description TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table produits
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            code_barres TEXT UNIQUE NOT NULL,
            prix REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            categorie TEXT DEFAULT 'Autre',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # CatÃ©gories par dÃ©faut
    categories_defaut = [
        ('ðŸ“±', 'Ã‰cran', 'Ã‰crans et dalles tactiles'),
        ('ðŸ”‹', 'Batterie', 'Batteries et accumulateurs'),
        ('ðŸ›¡ï¸', 'Coque', 'Coques et Ã©tuis de protection'),
        ('ðŸ“Ž', 'Accessoire', 'Accessoires divers'),
        ('ðŸ”Œ', 'CÃ¢ble', 'CÃ¢bles et chargeurs'),
        ('ðŸ”§', 'Outil', 'Outils de rÃ©paration'),
        ('ðŸ’¾', 'Composant', 'Composants Ã©lectroniques'),
        ('ðŸŽ§', 'Audio', 'Ã‰couteurs et haut-parleurs'),
        ('ðŸ“¦', 'Autre', 'Autres produits')
    ]
    
    for emoji, nom, desc in categories_defaut:
        try:
            cursor.execute(
                'INSERT OR IGNORE INTO categories (emoji, nom, description) VALUES (?, ?, ?)',
                (emoji, nom, desc)
            )
        except:
            pass
    
    # Produits d'exemple (seulement si aucun produit existe)
    cursor.execute('SELECT COUNT(*) as count FROM produits')
    result = cursor.fetchone()
    count = result[0]
    
    if count == 0:
        produits_exemple = [
            ('Ã‰cran iPhone 12', '1234567890123', 45.99, 15, 'Ã‰cran'),
            ('Batterie Samsung S21', '2345678901234', 29.99, 8, 'Batterie'),
            ('Coque iPhone 13 Pro', '3456789012345', 12.99, 25, 'Coque'),
            ('CÃ¢ble USB-C 2m', '4567890123456', 8.99, 30, 'CÃ¢ble'),
            ('Ã‰couteurs Bluetooth', '5678901234567', 19.99, 12, 'Audio'),
            ('Tournevis Kit', '6789012345678', 15.99, 5, 'Outil'),
            ('Chargeur Rapide', '7890123456789', 24.99, 18, 'CÃ¢ble')
        ]
        
        for nom, code, prix, stock, cat in produits_exemple:
            try:
                cursor.execute(
                    'INSERT INTO produits (nom, code_barres, prix, stock, categorie) VALUES (?, ?, ?, ?, ?)',
                    (nom, code, prix, stock, cat)
                )
            except:
                pass
    
    conn.commit()
    conn.close()

def get_categories():
    """RÃ©cupÃ©rer toutes les catÃ©gories"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM categories ORDER BY nom')
        categories = cursor.fetchall()
        conn.close()
        return [dict(cat) for cat in categories]
    except Exception as e:
        return []

def get_all_products():
    """RÃ©cupÃ©rer tous les produits pour la gestion du stock"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits ORDER BY nom')
        produits = cursor.fetchall()
        conn.close()
        return [dict(p) for p in produits]
    except Exception as e:
        return []

@app.route('/')
def index():
    """Page d'accueil avec recherche et aperÃ§u produits"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ParamÃ¨tres de recherche
        recherche = request.args.get('q', '').strip()
        categorie = request.args.get('cat', '').strip()
        
        # Construction de la requÃªte
        query = 'SELECT * FROM produits WHERE 1=1'
        params = []
        
        if recherche:
            query += ' AND (nom LIKE ? OR code_barres LIKE ?)'
            params.extend([f'%{recherche}%', f'%{recherche}%'])
        
        if categorie:
            query += ' AND categorie = ?'
            params.append(categorie)
        
        query += ' ORDER BY nom LIMIT 12'
        
        cursor.execute(query, params)
        produits = cursor.fetchall()
        
        # Stats rapides
        cursor.execute('SELECT COUNT(*) as total FROM produits')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as ruptures FROM produits WHERE stock = 0')
        ruptures = cursor.fetchone()[0]
        
        conn.close()
        
        return render_template('index.html', 
                             produits=[dict(p) for p in produits],
                             categories=get_categories(),
                             recherche=recherche,
                             categorie_filtre=categorie,
                             total=total,
                             ruptures=ruptures)
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/produits')
def voir_produits():
    """Page complÃ¨te des produits avec filtres avancÃ©s"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ParamÃ¨tres de filtrage
        recherche = request.args.get('q', '').strip()
        categorie = request.args.get('cat', '').strip()
        stock_filter = request.args.get('stock', '').strip()
        prix_min = request.args.get('prix_min', '').strip()
        prix_max = request.args.get('prix_max', '').strip()
        tri = request.args.get('sort', 'nom').strip()
        ordre = request.args.get('order', 'asc').strip()
        
        # Construction de la requÃªte
        query = 'SELECT * FROM produits WHERE 1=1'
        params = []
        
        if recherche:
            query += ' AND (nom LIKE ? OR code_barres LIKE ?)'
            params.extend([f'%{recherche}%', f'%{recherche}%'])
        
        if categorie:
            query += ' AND categorie = ?'
            params.append(categorie)
        
        if stock_filter == 'out':
            query += ' AND stock = 0'
        elif stock_filter == 'low':
            query += ' AND stock > 0 AND stock <= 5'
        elif stock_filter == 'ok':
            query += ' AND stock > 5'
        
        if prix_min:
            query += ' AND prix >= ?'
            params.append(float(prix_min))
        
        if prix_max:
            query += ' AND prix <= ?'
            params.append(float(prix_max))
        
        # Tri
        colonnes_tri = {
            'nom': 'nom',
            'prix': 'prix',
            'stock': 'stock',
            'categorie': 'categorie',
            'date': 'date_creation'
        }
        
        colonne_tri = colonnes_tri.get(tri, 'nom')
        ordre_sql = 'DESC' if ordre == 'desc' else 'ASC'
        query += f' ORDER BY {colonne_tri} {ordre_sql}'
        
        cursor.execute(query, params)
        produits = cursor.fetchall()
        
        # Statistiques
        cursor.execute('SELECT COUNT(*) as total FROM produits')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as ruptures FROM produits WHERE stock = 0')
        ruptures = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as stock_faible FROM produits WHERE stock > 0 AND stock <= 5')
        stock_faible = cursor.fetchone()[0]
        
        conn.close()
        
        stats = {
            'total': total,
            'ruptures': ruptures,
            'stock_faible': stock_faible,
            'resultats': len(produits)
        }
        
        return render_template('produits.html', 
                             produits=[dict(p) for p in produits],
                             categories=get_categories(),
                             stats=stats,
                             filtres={
                                 'recherche': recherche,
                                 'categorie': categorie,
                                 'stock_filter': stock_filter,
                                 'prix_min': prix_min,
                                 'prix_max': prix_max,
                                 'tri': tri,
                                 'ordre': ordre
                             })
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/ajouter', methods=['GET', 'POST'])
def ajouter_produit():
    """Ajouter un nouveau produit"""
    if request.method == 'POST':
        try:
            nom = request.form.get('nom', '').strip()
            prix = float(request.form.get('prix', 0))
            stock = int(request.form.get('stock', 0))
            categorie = request.form.get('categorie', 'Autre').strip()
            code_barres = request.form.get('code_barres', '').strip()
            
            if not nom:
                return render_template('ajouter.html', 
                                     categories=get_categories(),
                                     error="Le nom du produit est obligatoire")
            
            # GÃ©nÃ©ration automatique du code-barres si vide
            if not code_barres:
                code_barres = str(int(datetime.now().timestamp() * 1000))[-13:]
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO produits (nom, code_barres, prix, stock, categorie) VALUES (?, ?, ?, ?, ?)',
                (nom, code_barres, prix, stock, categorie)
            )
            conn.commit()
            conn.close()
            
            return redirect(url_for('index'))
            
        except Exception as e:
            return render_template('ajouter.html', 
                                 categories=get_categories(),
                                 error=f"Erreur: {str(e)}")
    
    return render_template('ajouter.html', categories=get_categories())

@app.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier_produit(id):
    """Modifier un produit existant"""
    if request.method == 'POST':
        try:
            nom = request.form.get('nom', '').strip()
            prix = float(request.form.get('prix', 0))
            stock = int(request.form.get('stock', 0))
            categorie = request.form.get('categorie', 'Autre').strip()
            
            if not nom:
                # RÃ©cupÃ©rer le produit pour rÃ©afficher le formulaire
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM produits WHERE id = ?', (id,))
                produit = cursor.fetchone()
                conn.close()
                
                return render_template('modifier.html', 
                                     produit=dict(produit),
                                     categories=get_categories(),
                                     error="Le nom du produit est obligatoire")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            # Mise Ã  jour complÃ¨te avec le stock
            cursor.execute(
                'UPDATE produits SET nom=?, prix=?, stock=?, categorie=? WHERE id=?',
                (nom, prix, stock, categorie, id)
            )
            conn.commit()
            conn.close()
            
            return redirect(url_for('voir_produits'))
            
        except Exception as e:
            # RÃ©cupÃ©rer le produit pour rÃ©afficher le formulaire avec l'erreur
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM produits WHERE id = ?', (id,))
            produit = cursor.fetchone()
            conn.close()
            
            return render_template('modifier.html', 
                                 produit=dict(produit),
                                 categories=get_categories(),
                                 error=f"Erreur: {str(e)}")
    
    # GET - Afficher le formulaire
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits WHERE id = ?', (id,))
        produit = cursor.fetchone()
        conn.close()
        
        if not produit:
            return render_template('error.html', error="Produit non trouvÃ©")
        
        return render_template('modifier.html', 
                             produit=dict(produit),
                             categories=get_categories())
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/supprimer/<int:id>')
def supprimer_produit(id):
    """Supprimer un produit"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM produits WHERE id = ?', (id,))
        conn.commit()
        conn.close()
    except Exception as e:
        pass
    
    return redirect(url_for('voir_produits'))

@app.route('/scanner')
def scanner():
    """Page scanner complet - toutes fonctionnalités"""
    return render_template('scanner.html')

@app.route('/test-scanner')
def test_scanner():
    """Page de test pour le scanner"""
    return render_template('test_scanner.html')

@app.route('/scanner-simple')
def scanner_simple():
    """Scanner simplifié avec diagnostic"""
    return render_template('scanner_simple.html')

@app.route('/code-barres/<int:id>')
def afficher_code_barres(id):
    """Afficher le code-barres d'un produit"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits WHERE id = ?', (id,))
        produit = cursor.fetchone()
        conn.close()
        
        if not produit:
            return render_template('error.html', error="Produit non trouvé")
        
        return render_template('code_barres_produit.html', produit=dict(produit))
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/imprimer-codes-barres')
def imprimer_codes_barres():
    """Page pour imprimer tous les codes-barres"""
    try:
        categorie = request.args.get('categorie', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if categorie:
            cursor.execute('SELECT * FROM produits WHERE categorie = ? ORDER BY nom', (categorie,))
        else:
            cursor.execute('SELECT * FROM produits ORDER BY categorie, nom')
        
        produits = cursor.fetchall()
        conn.close()
        
        from datetime import datetime
        date_aujourd_hui = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        return render_template('imprimer_codes_barres.html', 
                             produits=[dict(p) for p in produits],
                             categories=get_categories(),
                             date=date_aujourd_hui)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/gestion-stock')
def gestion_stock():
    """Page de gestion du stock (quantitÃ©s, rÃ©approvisionnement)"""
    return redirect(url_for('index'))

@app.route('/ajuster-stock', methods=['POST'])
def ajuster_stock():
    """API pour ajuster le stock manuellement"""
    try:
        data = request.get_json()
        produit_id = data.get('produit_id')
        action = data.get('action')  # 'ajouter', 'retirer', 'definir'
        quantite = int(data.get('quantite', 1))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits WHERE id = ?', (produit_id,))
        produit = cursor.fetchone()
        
        if not produit:
            conn.close()
            return jsonify({'success': False, 'message': 'Produit non trouvÃ©'})
        
        produit_dict = dict(produit)
        stock_actuel = produit_dict['stock']
        
        if action == 'ajouter':
            nouveau_stock = stock_actuel + quantite
        elif action == 'retirer':
            if stock_actuel < quantite:
                conn.close()
                return jsonify({
                    'success': False, 
                    'message': f'Stock insuffisant ! Stock actuel: {stock_actuel}, demandÃ©: {quantite}'
                })
            nouveau_stock = stock_actuel - quantite
        elif action == 'definir':
            nouveau_stock = quantite
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Action non valide'})
        
        # Mise Ã  jour du stock
        cursor.execute('UPDATE produits SET stock = ? WHERE id = ?', (nouveau_stock, produit_id))
        conn.commit()
        conn.close()
        
        action_text = {
            'ajouter': f'ajoutÃ© {quantite}',
            'retirer': f'retirÃ© {quantite}',
            'definir': f'dÃ©fini Ã  {quantite}'
        }[action]
        
        return jsonify({
            'success': True,
            'message': f'âœ… {produit_dict["nom"]}: {action_text} unitÃ©(s)',
            'produit': produit_dict['nom'],
            'action': action,
            'quantite': quantite,
            'stock_precedent': stock_actuel,
            'nouveau_stock': nouveau_stock
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/scan', methods=['POST'])
def scan():
    """API de scan - avec choix d'action et quantitÃ©"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        action = data.get('action', '').strip()  # 'retirer', 'ajouter', ou vide pour demander
        quantite = data.get('quantite', 1)
        
        if not code:
            return jsonify({'success': False, 'message': 'Code vide'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits WHERE code_barres = ?', (code,))
        produit = cursor.fetchone()
        
        if not produit:
            conn.close()
            return jsonify({'success': False, 'message': f'Produit non trouvÃ©: {code}'})
        
        produit_dict = dict(produit)
        
        # Si aucune action spÃ©cifiÃ©e, retourner les infos du produit pour demander l'action
        if not action:
            conn.close()
            return jsonify({
                'success': True,
                'ask_action': True,
                'produit': {
                    'id': produit_dict['id'],
                    'nom': produit_dict['nom'],
                    'code_barres': produit_dict['code_barres'],
                    'prix': produit_dict['prix'],
                    'stock': produit_dict['stock'],
                    'categorie': produit_dict['categorie']
                },
                'message': f'Produit trouvÃ©: {produit_dict["nom"]}'
            })
        
        # Traitement de l'action
        stock_actuel = produit_dict['stock']
        
        if action == 'retirer':
            if stock_actuel < quantite:
                conn.close()
                return jsonify({
                    'success': False, 
                    'message': f'âŒ Stock insuffisant ! Stock actuel: {stock_actuel}, demandÃ©: {quantite}'
                })
            nouveau_stock = stock_actuel - quantite
            action_text = f'retirÃ© {quantite}'
        
        elif action == 'ajouter':
            nouveau_stock = stock_actuel + quantite
            action_text = f'ajoutÃ© {quantite}'
        
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Action non valide'})
        
        # Mise Ã  jour du stock
        cursor.execute('UPDATE produits SET stock = ? WHERE id = ?', (nouveau_stock, produit_dict['id']))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'âœ… {produit_dict["nom"]}: {action_text} unitÃ©(s)',
            'produit': produit_dict['nom'],
            'action': action,
            'quantite': quantite,
            'stock_precedent': stock_actuel,
            'nouveau_stock': nouveau_stock
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/statistiques')
def statistiques():
    """Page statistiques"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Stats gÃ©nÃ©rales
        cursor.execute('SELECT COUNT(*) as total FROM produits')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as ruptures FROM produits WHERE stock = 0')
        ruptures = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as stock_faible FROM produits WHERE stock > 0 AND stock <= 5')
        stock_faible = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(stock * prix) as valeur FROM produits')
        result = cursor.fetchone()
        valeur_stock = result[0] or 0
        
        # Top catÃ©gories
        cursor.execute('''
            SELECT categorie, COUNT(*) as count, SUM(stock) as stock_total 
            FROM produits 
            GROUP BY categorie 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        top_categories = cursor.fetchall()
        
        conn.close()
        
        stats = {
            'total_produits': total,
            'ruptures': ruptures,
            'stock_faible': stock_faible,
            'valeur_stock': round(valeur_stock, 2),
            'top_categories': [dict(cat) for cat in top_categories]
        }
        
        return render_template('statistiques.html', stats=stats, categories=get_categories())
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/ruptures')
def ruptures():
    """Produits en rupture"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits WHERE stock = 0 ORDER BY nom')
        produits = cursor.fetchall()
        conn.close()
        
        return render_template('ruptures.html', 
                             produits=[dict(p) for p in produits],
                             categories=get_categories())
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/stock-faible')
def stock_faible():
    """Produits Ã  stock faible"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits WHERE stock > 0 AND stock <= 5 ORDER BY stock ASC')
        produits = cursor.fetchall()
        conn.close()
        
        return render_template('stock_faible.html', 
                             produits=[dict(p) for p in produits],
                             categories=get_categories())
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/codes-barres')
def codes_barres():
    """GÃ©nÃ©rateur de codes-barres"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits ORDER BY nom')
        produits = cursor.fetchall()
        conn.close()
        
        return render_template('codes_barres.html', 
                             produits=[dict(p) for p in produits],
                             categories=get_categories())
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/generer-code/<int:produit_id>')
def generer_code_barres(produit_id):
    """GÃ©nÃ¨re et retourne l'image du code-barres (version simplifiÃ©e)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits WHERE id = ?', (produit_id,))
        produit = cursor.fetchone()
        conn.close()
        
        if not produit:
            return "Produit non trouvÃ©", 404
        
        produit_dict = dict(produit)
        
        # GÃ©nÃ©rer une image SVG simple du code-barres
        code = produit_dict['code_barres']
        
        # SVG simple reprÃ©sentant un code-barres
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="300" height="100" xmlns="http://www.w3.org/2000/svg">
  <rect width="300" height="100" fill="white"/>
  
  <!-- Barres du code-barres (pattern simple) -->
  <rect x="20" y="10" width="2" height="60" fill="black"/>
  <rect x="25" y="10" width="1" height="60" fill="black"/>
  <rect x="29" y="10" width="3" height="60" fill="black"/>
  <rect x="35" y="10" width="1" height="60" fill="black"/>
  <rect x="39" y="10" width="2" height="60" fill="black"/>
  <rect x="44" y="10" width="1" height="60" fill="black"/>
  <rect x="48" y="10" width="1" height="60" fill="black"/>
  <rect x="52" y="10" width="2" height="60" fill="black"/>
  <rect x="57" y="10" width="3" height="60" fill="black"/>
  <rect x="63" y="10" width="1" height="60" fill="black"/>
  <rect x="67" y="10" width="2" height="60" fill="black"/>
  <rect x="72" y="10" width="1" height="60" fill="black"/>
  <rect x="76" y="10" width="1" height="60" fill="black"/>
  <rect x="80" y="10" width="3" height="60" fill="black"/>
  <rect x="86" y="10" width="2" height="60" fill="black"/>
  <rect x="91" y="10" width="1" height="60" fill="black"/>
  <rect x="95" y="10" width="2" height="60" fill="black"/>
  <rect x="100" y="10" width="1" height="60" fill="black"/>
  <rect x="104" y="10" width="3" height="60" fill="black"/>
  <rect x="110" y="10" width="1" height="60" fill="black"/>
  <rect x="114" y="10" width="2" height="60" fill="black"/>
  <rect x="119" y="10" width="1" height="60" fill="black"/>
  <rect x="123" y="10" width="1" height="60" fill="black"/>
  <rect x="127" y="10" width="2" height="60" fill="black"/>
  <rect x="132" y="10" width="3" height="60" fill="black"/>
  <rect x="138" y="10" width="1" height="60" fill="black"/>
  <rect x="142" y="10" width="2" height="60" fill="black"/>
  <rect x="147" y="10" width="1" height="60" fill="black"/>
  <rect x="151" y="10" width="1" height="60" fill="black"/>
  <rect x="155" y="10" width="3" height="60" fill="black"/>
  <rect x="161" y="10" width="2" height="60" fill="black"/>
  <rect x="166" y="10" width="1" height="60" fill="black"/>
  <rect x="170" y="10" width="2" height="60" fill="black"/>
  <rect x="175" y="10" width="1" height="60" fill="black"/>
  <rect x="179" y="10" width="3" height="60" fill="black"/>
  <rect x="185" y="10" width="1" height="60" fill="black"/>
  <rect x="189" y="10" width="2" height="60" fill="black"/>
  <rect x="194" y="10" width="1" height="60" fill="black"/>
  <rect x="198" y="10" width="1" height="60" fill="black"/>
  <rect x="202" y="10" width="2" height="60" fill="black"/>
  <rect x="207" y="10" width="3" height="60" fill="black"/>
  <rect x="213" y="10" width="1" height="60" fill="black"/>
  <rect x="217" y="10" width="2" height="60" fill="black"/>
  <rect x="222" y="10" width="1" height="60" fill="black"/>
  <rect x="226" y="10" width="1" height="60" fill="black"/>
  <rect x="230" y="10" width="3" height="60" fill="black"/>
  <rect x="236" y="10" width="2" height="60" fill="black"/>
  <rect x="241" y="10" width="1" height="60" fill="black"/>
  <rect x="245" y="10" width="2" height="60" fill="black"/>
  <rect x="250" y="10" width="1" height="60" fill="black"/>
  <rect x="254" y="10" width="3" height="60" fill="black"/>
  <rect x="260" y="10" width="1" height="60" fill="black"/>
  <rect x="264" y="10" width="2" height="60" fill="black"/>
  <rect x="269" y="10" width="1" height="60" fill="black"/>
  <rect x="273" y="10" width="1" height="60" fill="black"/>
  <rect x="277" y="10" width="2" height="60" fill="black"/>
  
  <!-- Texte du code-barres -->
  <text x="150" y="85" text-anchor="middle" font-family="monospace" font-size="12" fill="black">{code}</text>
  
  <!-- Nom du produit -->
  <text x="150" y="98" text-anchor="middle" font-family="Arial" font-size="10" fill="black">{produit_dict['nom'][:30]}</text>
</svg>'''
        
        response = make_response(svg_content)
        response.headers['Content-Type'] = 'image/svg+xml'
        return response
        
    except Exception as e:
        return f"Erreur: {str(e)}", 500

@app.route('/export')
def export_csv():
    """Export CSV des produits"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits ORDER BY nom')
        produits = cursor.fetchall()
        conn.close()
        
        if not produits:
            return render_template('error.html', error="Aucun produit Ã  exporter")
        
        # CrÃ©er le CSV en mÃ©moire
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-tÃªtes
        writer.writerow(['ID', 'Nom', 'Code-barres', 'Prix (â‚¬)', 'Stock', 'CatÃ©gorie', 'Date crÃ©ation'])
        
        # DonnÃ©es
        for produit in produits:
            writer.writerow([
                produit['id'],
                produit['nom'],
                produit['code_barres'],
                f"{produit['prix']:.2f}",
                produit['stock'],
                produit['categorie'],
                produit['date_creation']
            ])
        
        # PrÃ©parer la rÃ©ponse
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=produits_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/api/produits')
def api_produits():
    """API JSON des produits"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits ORDER BY nom')
        produits = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(produits),
            'produits': [dict(p) for p in produits]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/produit/<code_barres>')
def api_produit_by_barcode(code_barres):
    """API pour rechercher un produit par code-barres"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits WHERE code_barres = ?', (code_barres,))
        produit = cursor.fetchone()
        conn.close()
        
        if produit:
            return jsonify({
                'success': True,
                'produit': dict(produit)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Produit non trouvé'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def api_stats():
    """API JSON des statistiques"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Stats gÃ©nÃ©rales
        cursor.execute('SELECT COUNT(*) as total FROM produits')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as ruptures FROM produits WHERE stock = 0')
        ruptures = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as stock_faible FROM produits WHERE stock > 0 AND stock <= 5')
        stock_faible = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(stock * prix) as valeur FROM produits')
        result = cursor.fetchone()
        valeur_stock = result[0] or 0
        
        # Top catÃ©gories
        cursor.execute('''
            SELECT categorie, COUNT(*) as count, SUM(stock) as stock_total 
            FROM produits 
            GROUP BY categorie 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        top_categories = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_produits': total,
                'ruptures': ruptures,
                'stock_faible': stock_faible,
                'valeur_stock': round(valeur_stock, 2),
                'top_categories': [dict(cat) for cat in top_categories]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/recherche')
def recherche_avancee():
    """Page de recherche avancÃ©e"""
    return redirect(url_for('voir_produits'))

@app.route('/categories', methods=['GET', 'POST'])
def gerer_categories():
    """GÃ©rer les catÃ©gories"""
    if request.method == 'POST':
        try:
            nom = request.form.get('nom', '').strip()
            emoji = request.form.get('emoji', 'ðŸ“¦').strip()
            description = request.form.get('description', '').strip()
            
            if not nom:
                return render_template('categories.html', 
                                     categories=get_categories(),
                                     error="Le nom de la catÃ©gorie est obligatoire")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO categories (nom, emoji, description) VALUES (?, ?, ?)',
                (nom, emoji, description)
            )
            conn.commit()
            conn.close()
            
            return redirect(url_for('gerer_categories'))
            
        except Exception as e:
            return render_template('categories.html', 
                                 categories=get_categories(),
                                 error=f"Erreur: {str(e)}")
    
    return render_template('categories.html', categories=get_categories())

@app.route('/supprimer-categorie/<int:id>')
def supprimer_categorie(id):
    """Supprimer une catÃ©gorie"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM categories WHERE id = ?', (id,))
        conn.commit()
        conn.close()
    except Exception as e:
        pass
    
    return redirect(url_for('gerer_categories'))

@app.route('/aide')
def aide():
    """Page d'aide"""
    return render_template('aide.html', categories=get_categories())

@app.route('/favicon.ico')
def favicon():
    """Favicon simple"""
    return '', 204

if __name__ == '__main__':
    print("ðŸš€ BOUTIQUE MOBILE - VERSION MINIMALE")
    print("=" * 50)
    
    # Initialisation de la base de donnÃ©es
    try:
        init_database()
        print("âœ… Base de donnÃ©es SQLite initialisÃ©e")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM produits')
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"ðŸ“¦ {count} produits en base")
        
    except Exception as e:
        print(f"âŒ Erreur initialisation: {e}")
    
    print("ðŸŒ Application locale prÃªte")
    print("ðŸ“± AccÃ¨s: http://localhost:5000")
    print("ðŸ”§ FonctionnalitÃ©s disponibles:")
    print("   âœ… Gestion des produits (CRUD)")
    print("   âœ… Scanner codes-barres (camÃ©ra + douchette)")
    print("   âœ… Filtres et tris avancÃ©s")
    print("   âœ… Statistiques avec graphiques")
    print("   âœ… Alertes ruptures/stock faible")
    print("   âœ… GÃ©nÃ©ration de codes-barres (SVG)")
    print("   âœ… Export CSV/Excel")
    print("   âœ… API JSON (produits + stats)")
    print("   âœ… Interface responsive")
    print("   âœ… Base de donnÃ©es persistante")
    
    # Lancement accessible depuis le rÃ©seau
    print("ðŸ“± Pour accÃ©der depuis votre tÃ©lÃ©phone:")
    print("   1. Connectez votre tÃ©lÃ©phone au mÃªme WiFi")
    print("   2. Ouvrez votre navigateur mobile")
    print("   3. Allez sur: http://192.168.0.154:5000")
    print("   (Remplacez l'IP par celle affichÃ©e ci-dessus)")
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=True)


