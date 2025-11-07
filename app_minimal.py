#!/usr/bin/env python3
"""
🚀 BOUTIQUE MOBILE - VERSION MINIMALE
Application de gestion d'inventaire - Flask + SQLite uniquement
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
    """Initialise la base de données SQLite"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table catégories
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            emoji TEXT DEFAULT '📦',
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
    
    # Catégories par défaut
    categories_defaut = [
        ('📱', 'Écran', 'Écrans et dalles tactiles'),
        ('🔋', 'Batterie', 'Batteries et accumulateurs'),
        ('🛡️', 'Coque', 'Coques et étuis de protection'),
        ('📎', 'Accessoire', 'Accessoires divers'),
        ('🔌', 'Câble', 'Câbles et chargeurs'),
        ('🔧', 'Outil', 'Outils de réparation'),
        ('💾', 'Composant', 'Composants électroniques'),
        ('🎧', 'Audio', 'Écouteurs et haut-parleurs'),
        ('📦', 'Autre', 'Autres produits')
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
            ('Écran iPhone 12', '1234567890123', 45.99, 15, 'Écran'),
            ('Batterie Samsung S21', '2345678901234', 29.99, 8, 'Batterie'),
            ('Coque iPhone 13 Pro', '3456789012345', 12.99, 25, 'Coque'),
            ('Câble USB-C 2m', '4567890123456', 8.99, 30, 'Câble'),
            ('Écouteurs Bluetooth', '5678901234567', 19.99, 12, 'Audio'),
            ('Tournevis Kit', '6789012345678', 15.99, 5, 'Outil'),
            ('Chargeur Rapide', '7890123456789', 24.99, 18, 'Câble')
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
    """Récupérer toutes les catégories"""
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
    """Récupérer tous les produits pour la gestion du stock"""
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
    """Page d'accueil avec recherche et aperçu produits"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Paramètres de recherche
        recherche = request.args.get('q', '').strip()
        categorie = request.args.get('cat', '').strip()
        
        # Construction de la requête
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
    """Page complète des produits avec filtres avancés"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Paramètres de filtrage
        recherche = request.args.get('q', '').strip()
        categorie = request.args.get('cat', '').strip()
        stock_filter = request.args.get('stock', '').strip()
        prix_min = request.args.get('prix_min', '').strip()
        prix_max = request.args.get('prix_max', '').strip()
        tri = request.args.get('sort', 'nom').strip()
        ordre = request.args.get('order', 'asc').strip()
        
        # Construction de la requête
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
        
        return render_template('produits_simple.html', 
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
            
            # Génération automatique du code-barres si vide
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
    """Modifier un produit existant (sans gestion du stock)"""
    if request.method == 'POST':
        try:
            nom = request.form.get('nom', '').strip()
            prix = float(request.form.get('prix', 0))
            categorie = request.form.get('categorie', 'Autre').strip()
            
            if not nom:
                # Récupérer le produit pour réafficher le formulaire
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM produits WHERE id = ?', (id,))
                produit = cursor.fetchone()
                conn.close()
                
                return render_template('modifier_simple.html', 
                                     produit=dict(produit),
                                     categories=get_categories(),
                                     error="Le nom du produit est obligatoire")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            # Mise à jour SANS le stock - le stock ne se gère que par scanner
            cursor.execute(
                'UPDATE produits SET nom=?, prix=?, categorie=? WHERE id=?',
                (nom, prix, categorie, id)
            )
            conn.commit()
            conn.close()
            
            return redirect(url_for('voir_produits'))
            
        except Exception as e:
            # Récupérer le produit pour réafficher le formulaire avec l'erreur
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM produits WHERE id = ?', (id,))
            produit = cursor.fetchone()
            conn.close()
            
            return render_template('modifier_simple.html', 
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
            return render_template('error.html', error="Produit non trouvé")
        
        return render_template('modifier_simple.html', 
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
    """Page scanner parfait - simple et fonctionnel"""
    return render_template('scanner_parfait.html')

@app.route('/gestion-stock')
def gestion_stock():
    """Page de gestion du stock (quantités, réapprovisionnement)"""
    return render_template('gestion_stock.html', produits=get_all_products(), categories=get_categories())

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
            return jsonify({'success': False, 'message': 'Produit non trouvé'})
        
        produit_dict = dict(produit)
        stock_actuel = produit_dict['stock']
        
        if action == 'ajouter':
            nouveau_stock = stock_actuel + quantite
        elif action == 'retirer':
            if stock_actuel < quantite:
                conn.close()
                return jsonify({
                    'success': False, 
                    'message': f'Stock insuffisant ! Stock actuel: {stock_actuel}, demandé: {quantite}'
                })
            nouveau_stock = stock_actuel - quantite
        elif action == 'definir':
            nouveau_stock = quantite
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Action non valide'})
        
        # Mise à jour du stock
        cursor.execute('UPDATE produits SET stock = ? WHERE id = ?', (nouveau_stock, produit_id))
        conn.commit()
        conn.close()
        
        action_text = {
            'ajouter': f'ajouté {quantite}',
            'retirer': f'retiré {quantite}',
            'definir': f'défini à {quantite}'
        }[action]
        
        return jsonify({
            'success': True,
            'message': f'✅ {produit_dict["nom"]}: {action_text} unité(s)',
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
    """API de scan - avec choix d'action et quantité"""
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
            return jsonify({'success': False, 'message': f'Produit non trouvé: {code}'})
        
        produit_dict = dict(produit)
        
        # Si aucune action spécifiée, retourner les infos du produit pour demander l'action
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
                'message': f'Produit trouvé: {produit_dict["nom"]}'
            })
        
        # Traitement de l'action
        stock_actuel = produit_dict['stock']
        
        if action == 'retirer':
            if stock_actuel < quantite:
                conn.close()
                return jsonify({
                    'success': False, 
                    'message': f'❌ Stock insuffisant ! Stock actuel: {stock_actuel}, demandé: {quantite}'
                })
            nouveau_stock = stock_actuel - quantite
            action_text = f'retiré {quantite}'
        
        elif action == 'ajouter':
            nouveau_stock = stock_actuel + quantite
            action_text = f'ajouté {quantite}'
        
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Action non valide'})
        
        # Mise à jour du stock
        cursor.execute('UPDATE produits SET stock = ? WHERE id = ?', (nouveau_stock, produit_dict['id']))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'✅ {produit_dict["nom"]}: {action_text} unité(s)',
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
        
        # Stats générales
        cursor.execute('SELECT COUNT(*) as total FROM produits')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as ruptures FROM produits WHERE stock = 0')
        ruptures = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as stock_faible FROM produits WHERE stock > 0 AND stock <= 5')
        stock_faible = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(stock * prix) as valeur FROM produits')
        result = cursor.fetchone()
        valeur_stock = result[0] or 0
        
        # Top catégories
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
    """Produits à stock faible"""
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
    """Générateur de codes-barres"""
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
    """Génère et retourne l'image du code-barres (version simplifiée)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits WHERE id = ?', (produit_id,))
        produit = cursor.fetchone()
        conn.close()
        
        if not produit:
            return "Produit non trouvé", 404
        
        produit_dict = dict(produit)
        
        # Générer une image SVG simple du code-barres
        code = produit_dict['code_barres']
        
        # SVG simple représentant un code-barres
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
            return render_template('error.html', error="Aucun produit à exporter")
        
        # Créer le CSV en mémoire
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        writer.writerow(['ID', 'Nom', 'Code-barres', 'Prix (€)', 'Stock', 'Catégorie', 'Date création'])
        
        # Données
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
        
        # Préparer la réponse
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

@app.route('/api/stats')
def api_stats():
    """API JSON des statistiques"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Stats générales
        cursor.execute('SELECT COUNT(*) as total FROM produits')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as ruptures FROM produits WHERE stock = 0')
        ruptures = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as stock_faible FROM produits WHERE stock > 0 AND stock <= 5')
        stock_faible = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(stock * prix) as valeur FROM produits')
        result = cursor.fetchone()
        valeur_stock = result[0] or 0
        
        # Top catégories
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
    """Page de recherche avancée"""
    return redirect(url_for('voir_produits'))

@app.route('/categories', methods=['GET', 'POST'])
def gerer_categories():
    """Gérer les catégories"""
    if request.method == 'POST':
        try:
            nom = request.form.get('nom', '').strip()
            emoji = request.form.get('emoji', '📦').strip()
            description = request.form.get('description', '').strip()
            
            if not nom:
                return render_template('categories.html', 
                                     categories=get_categories(),
                                     error="Le nom de la catégorie est obligatoire")
            
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
    """Supprimer une catégorie"""
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
    print("🚀 BOUTIQUE MOBILE - VERSION MINIMALE")
    print("=" * 50)
    
    # Initialisation de la base de données
    try:
        init_database()
        print("✅ Base de données SQLite initialisée")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM produits')
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"📦 {count} produits en base")
        
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
    
    print("🌐 Application locale prête")
    print("📱 Accès: http://localhost:5000")
    print("🔧 Fonctionnalités disponibles:")
    print("   ✅ Gestion des produits (CRUD)")
    print("   ✅ Scanner codes-barres (caméra + douchette)")
    print("   ✅ Filtres et tris avancés")
    print("   ✅ Statistiques avec graphiques")
    print("   ✅ Alertes ruptures/stock faible")
    print("   ✅ Génération de codes-barres (SVG)")
    print("   ✅ Export CSV/Excel")
    print("   ✅ API JSON (produits + stats)")
    print("   ✅ Interface responsive")
    print("   ✅ Base de données persistante")
    
    # Lancement
    app.run(host='0.0.0.0', port=5000, debug=True)
