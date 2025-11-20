#!/usr/bin/env python3
"""
🚀 BOUTIQUE MOBILE - VERSION COMPLÈTE
Application de gestion d'inventaire complète - Flask + SQLite/PostgreSQL
"""

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, make_response
from datetime import datetime
import io
import csv

app = Flask(__name__)

# Détection automatique : PostgreSQL (production) ou SQLite (local)
DATABASE_URL = os.environ.get('DATABASE_URL', '')
USE_POSTGRES = DATABASE_URL.startswith('postgres')

if USE_POSTGRES:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        # Fix pour Render (postgres:// → postgresql://)
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        # Debug: afficher l'hostname utilisé
        import re
        hostname_match = re.search(r'@([^/]+)/', DATABASE_URL)
        if hostname_match:
            print(f"🔍 Tentative connexion PostgreSQL: {hostname_match.group(1)}")
    except ImportError:
        # Si psycopg2 n'est pas disponible, utiliser SQLite
        print("⚠️ psycopg2 non disponible, utilisation de SQLite")
        USE_POSTGRES = False

def get_db_connection():
    """Connexion universelle SQLite (local) ou PostgreSQL (production)"""
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect('boutique_mobile.db')
        conn.row_factory = sqlite3.Row
        return conn

def get_cursor(conn):
    """Crée un cursor approprié selon le type de base de données"""
    if USE_POSTGRES:
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()

def init_database():
    """Initialise la base de données (PostgreSQL ou SQLite)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Syntaxe SQL adaptée selon la base
    if USE_POSTGRES:
        # PostgreSQL
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                nom TEXT NOT NULL UNIQUE,
                emoji TEXT DEFAULT '\ud83d\udce6',
                description TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produits (
                id SERIAL PRIMARY KEY,
                nom TEXT NOT NULL,
                code_barres TEXT UNIQUE NOT NULL,
                prix REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                categorie TEXT DEFAULT 'Other',
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        placeholder = '%s'
        insert_ignore = 'INSERT INTO categories (emoji, nom, description) VALUES (%s, %s, %s) ON CONFLICT (nom) DO NOTHING'
    else:
        # SQLite
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL UNIQUE,
                emoji TEXT DEFAULT '\ud83d\udce6',
                description TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                code_barres TEXT UNIQUE NOT NULL,
                prix REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                categorie TEXT DEFAULT 'Other',
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        placeholder = '?'
        insert_ignore = 'INSERT OR IGNORE INTO categories (emoji, nom, description) VALUES (?, ?, ?)'
    
    # Default categories (ONLY if no category exists)
    cursor.execute('SELECT COUNT(*) FROM categories')
    result = cursor.fetchone()
    count_categories = result[0]
    
    if count_categories == 0:
        default_categories = [
            ('\ud83d\udcf1', 'Screen', 'Screens and touch panels'),
            ('\ud83d\udd0b', 'Battery', 'Batteries and accumulators'),
            ('\ud83d\udee1\ufe0f', 'Case', 'Protective cases and covers'),
            ('\ud83d\udd0d', 'Accessory', 'Various accessories'),
            ('\ud83d\udd0c', 'Cable', 'Cables and chargers'),
            ('\ud83d\udd27', 'Tool', 'Repair tools'),
            ('\ud83d\udcbe', 'Component', 'Electronic components'),
            ('\ud83c\udfa7', 'Audio', 'Earphones and speakers'),
            ('\ud83d\udce6', 'Other', 'Other products')
        ]
        
        for emoji, name, desc in default_categories:
            try:
                cursor.execute(insert_ignore, (emoji, name, desc))
            except:
                pass
    
    # Example products (only if no product exists)
    cursor.execute('SELECT COUNT(*) FROM produits')
    result = cursor.fetchone()
    count_produits = result[0]
    
    if count_produits == 0:
        produits_exemple = [
            ('iPhone 12 Screen', '1234567890123', 45.99, 15, 'Screen'),
            ('Samsung S21 Battery', '2345678901234', 29.99, 8, 'Battery'),
            ('iPhone 13 Pro Case', '3456789012345', 12.99, 25, 'Case'),
            ('USB-C Cable 2m', '4567890123456', 8.99, 30, 'Cable'),
            ('Bluetooth Earphones', '5678901234567', 19.99, 12, 'Audio'),
            ('Screwdriver Kit', '6789012345678', 15.99, 5, 'Tool'),
            ('Fast Charger', '7890123456789', 24.99, 18, 'Cable')
        ]
        
        insert_produit = f'INSERT INTO produits (nom, code_barres, prix, stock, categorie) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})'
        
        for nom, code, prix, stock, cat in produits_exemple:
            try:
                cursor.execute(insert_produit, (nom, code, prix, stock, cat))
            except:
                pass
    
    conn.commit()
    conn.close()

def adapt_query(query):
    """Adapte les placeholders SQL selon la base de données (? → %s pour PostgreSQL)"""
    if USE_POSTGRES:
        return query.replace('?', '%s')
    return query

def row_to_dict(row):
    """Convertit une ligne de résultat en dictionnaire (compatible PostgreSQL et SQLite)"""
    if USE_POSTGRES:
        # Avec RealDictCursor, row est déjà un dict, on le retourne tel quel
        return row
    else:
        # SQLite avec row_factory = sqlite3.Row
        return dict(row)

def rows_to_list(rows):
    """Convertit une liste de rows en liste de dictionnaires"""
    if USE_POSTGRES:
        # Avec RealDictCursor, les rows sont déjà des dicts
        return rows
    else:
        # SQLite avec row_factory = sqlite3.Row
        return [dict(row) for row in rows]

def get_categories():
    """Récupérer toutes les catégories"""
    try:
        conn = get_db_connection()
        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = conn.cursor()
        cursor.execute('SELECT * FROM categories ORDER BY nom')
        categories = cursor.fetchall()
        conn.close()
        return rows_to_list(categories)
    except Exception as e:
        return []

def get_all_products():
    """Récupérer tous les produits pour la gestion du stock"""
    try:
        conn = get_db_connection()
        if USE_POSTGRES:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits ORDER BY nom')
        produits = cursor.fetchall()
        conn.close()
        return rows_to_list(produits)
    except Exception as e:
        return []

@app.route('/')
def index():
    """Page d'accueil avec recherche et aperÃ§u produits"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        
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
        
        query = adapt_query(query)
        cursor.execute(query, params)
        produits = cursor.fetchall()
        
        # Stats rapides
        cursor.execute('SELECT COUNT(*) as total FROM produits')
        result = cursor.fetchone()
        total = result['total'] if USE_POSTGRES else result[0]
        
        cursor.execute('SELECT COUNT(*) as ruptures FROM produits WHERE stock = 0')
        result = cursor.fetchone()
        ruptures = result['ruptures'] if USE_POSTGRES else result[0]
        
        conn.close()
        
        return render_template('index.html', 
                             produits=rows_to_list(produits),
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
        cursor = get_cursor(conn)
        
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
        
        query = adapt_query(query)
        cursor.execute(query, params)
        produits = cursor.fetchall()
        
        # Statistiques
        cursor.execute('SELECT COUNT(*) as total FROM produits')
        result = cursor.fetchone()
        total = result['total'] if USE_POSTGRES else result[0]
        
        cursor.execute('SELECT COUNT(*) as ruptures FROM produits WHERE stock = 0')
        result = cursor.fetchone()
        ruptures = result['ruptures'] if USE_POSTGRES else result[0]
        
        cursor.execute('SELECT COUNT(*) as stock_faible FROM produits WHERE stock > 0 AND stock <= 5')
        result = cursor.fetchone()
        stock_faible = result['stock_faible'] if USE_POSTGRES else result[0]
        
        conn.close()
        
        stats = {
            'total': total,
            'ruptures': ruptures,
            'stock_faible': stock_faible,
            'resultats': len(produits)
        }
        
        return render_template('products.html', 
                             produits=rows_to_list(produits),
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
            categorie = request.form.get('categorie', 'Other').strip()
            code_barres = request.form.get('code_barres', '').strip()
            
            if not nom:
                return render_template('add_product.html', 
                                     categories=get_categories(),
                                     error="Product name is required")
            
            # GÃ©nÃ©ration automatique du code-barres si vide
            if not code_barres:
                code_barres = str(int(datetime.now().timestamp() * 1000))[-13:]
            
            conn = get_db_connection()
            cursor = get_cursor(conn)
            query = adapt_query('INSERT INTO produits (nom, code_barres, prix, stock, categorie) VALUES (?, ?, ?, ?, ?)')
            cursor.execute(query, (nom, code_barres, prix, stock, categorie))
            conn.commit()
            conn.close()
            
            return redirect(url_for('index'))
            
        except Exception as e:
            return render_template('add_product.html', 
                                 categories=get_categories(),
                                 error=f"Error: {str(e)}")
    
    return render_template('add_product.html', categories=get_categories())

@app.route('/modifier/<int:id>', methods=['GET', 'POST'])
def modifier_produit(id):
    """Modifier un produit existant"""
    if request.method == 'POST':
        try:
            nom = request.form.get('nom', '').strip()
            prix = float(request.form.get('prix', 0))
            stock = int(request.form.get('stock', 0))
            categorie = request.form.get('categorie', 'Other').strip()
            
            if not nom:
                # Récupérer le produit pour réafficher le formulaire
                conn = get_db_connection()
                cursor = get_cursor(conn)
                query = adapt_query('SELECT * FROM produits WHERE id = ?')
                cursor.execute(query, (id,))
                produit = cursor.fetchone()
                conn.close()
                
                return render_template('edit_product.html', 
                                     produit=row_to_dict(produit),
                                     categories=get_categories(),
                                     error="Product name is required")
            
            conn = get_db_connection()
            cursor = get_cursor(conn)
            query = adapt_query('UPDATE produits SET nom=?, prix=?, stock=?, categorie=? WHERE id=?')
            cursor.execute(query, (nom, prix, stock, categorie, id))
            conn.commit()
            conn.close()
            
            return redirect(url_for('voir_produits'))
            
        except Exception as e:
            # Récupérer le produit pour réafficher le formulaire avec l'erreur
            conn = get_db_connection()
            cursor = get_cursor(conn)
            query = adapt_query('SELECT * FROM produits WHERE id = ?')
            cursor.execute(query, (id,))
            produit = cursor.fetchone()
            conn.close()
            
            return render_template('edit_product.html', 
                                 produit=row_to_dict(produit),
                                 categories=get_categories(),
                                 error=f"Error: {str(e)}")
    
    # GET - Afficher le formulaire
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        query = adapt_query('SELECT * FROM produits WHERE id = ?')
        cursor.execute(query, (id,))
        produit = cursor.fetchone()
        conn.close()
        
        if not produit:
            return render_template('error.html', error="Product not found")
        
        return render_template('edit_product.html', 
                             produit=row_to_dict(produit),
                             categories=get_categories())
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/supprimer/<int:id>')
def supprimer_produit(id):
    """Supprimer un produit"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        query = adapt_query('DELETE FROM produits WHERE id = ?')
        cursor.execute(query, (id,))
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
    return render_template('scanner_test.html')

@app.route('/scanner-simple')
def scanner_simple():
    """Scanner simplifié avec diagnostic"""
    return render_template('simple_scanner.html')

@app.route('/code-barres/<int:id>')
def afficher_code_barres(id):
    """Afficher le code-barres d'un produit"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        query = adapt_query('SELECT * FROM produits WHERE id = ?')
        cursor.execute(query, (id,))
        produit = cursor.fetchone()
        conn.close()
        
        if not produit:
            return render_template('error.html', error="Product not found")
        
        return render_template('product_barcode.html', produit=row_to_dict(produit))
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/imprimer-codes-barres')
def imprimer_codes_barres():
    """Page pour imprimer tous les codes-barres"""
    try:
        categorie = request.args.get('categorie', '')
        
        conn = get_db_connection()
        cursor = get_cursor(conn)
        
        if categorie:
            query = adapt_query('SELECT * FROM produits WHERE categorie = ? ORDER BY nom')
            cursor.execute(query, (categorie,))
        else:
            cursor.execute('SELECT * FROM produits ORDER BY categorie, nom')
        
        produits = cursor.fetchall()
        conn.close()
        
        from datetime import datetime
        date_aujourd_hui = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        return render_template('print_barcodes.html', 
                             produits=rows_to_list(produits),
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
        cursor = get_cursor(conn)
        query = adapt_query('SELECT * FROM produits WHERE id = ?')
        cursor.execute(query, (produit_id,))
        produit = cursor.fetchone()
        
        if not produit:
            conn.close()
            return jsonify({'success': False, 'message': 'Product not found'})
        
        produit_dict = row_to_dict(produit)
        stock_actuel = produit_dict['stock']
        
        if action == 'ajouter':
            nouveau_stock = stock_actuel + quantite
            action_text = f'added {quantite}'
        elif action == 'retirer':
            if stock_actuel < quantite:
                conn.close()
                return jsonify({
                    'success': False, 
                    'message': f'Not enough stock! Current stock: {stock_actuel}, requested: {quantite}'
                })
            nouveau_stock = stock_actuel - quantite
            action_text = f'removed {quantite}'
        elif action == 'definir':
            nouveau_stock = quantite
            action_text = f'set to {quantite}'
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid action'})
        
        # Mise à jour du stock
        query = adapt_query('UPDATE produits SET stock = ? WHERE id = ?')
        cursor.execute(query, (nouveau_stock, produit_id))
        conn.commit()
        conn.close()
        
        action_text = {
            'ajouter': f'added {quantite}',
            'retirer': f'removed {quantite}',
            'definir': f'set to {quantite}'
        }[action]
        
        return jsonify({
            'success': True,
            'message': f'✅ {produit_dict["nom"]}: {action_text} unit(s)',
            'produit': produit_dict['nom'],
            'action': action,
            'quantite': quantite,
            'stock_precedent': stock_actuel,
            'nouveau_stock': nouveau_stock
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/scan', methods=['POST'])
def scan():
    """API de scan - avec choix d'action et quantitÃ©"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        action = data.get('action', '').strip()  # 'retirer', 'ajouter', ou vide pour demander
        quantite = data.get('quantite', 1)
        
        if not code:
            return jsonify({'success': False, 'message': 'Empty code'})
        
        conn = get_db_connection()
        cursor = get_cursor(conn)
        query = adapt_query('SELECT * FROM produits WHERE code_barres = ?')
        cursor.execute(query, (code,))
        produit = cursor.fetchone()
        
        if not produit:
            conn.close()
            return jsonify({'success': False, 'message': f'Product not found: {code}'})
        
        produit_dict = row_to_dict(produit)
        
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
                'message': f'Product found: {produit_dict["nom"]}'
            })
        
        # Traitement de l'action
        stock_actuel = produit_dict['stock']
        
        if action == 'retirer':
            if stock_actuel < quantite:
                conn.close()
                return jsonify({
                    'success': False, 
                    'message': f'❌ Not enough stock! Current stock: {stock_actuel}, requested: {quantite}'
                })
            nouveau_stock = stock_actuel - quantite
            action_text = f'removed {quantite}'
        
        elif action == 'ajouter':
            nouveau_stock = stock_actuel + quantite
            action_text = f'added {quantite}'
        
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Action non valide'})
        
        # Mise Ã  jour du stock
        query = adapt_query('UPDATE produits SET stock = ? WHERE id = ?')
        cursor.execute(query, (nouveau_stock, produit_dict['id']))
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
        cursor = get_cursor(conn)
        
        # Stats gÃ©nÃ©rales
        cursor.execute('SELECT COUNT(*) as total FROM produits')
        result = cursor.fetchone()
        total = result['total'] if USE_POSTGRES else result[0]
        
        cursor.execute('SELECT COUNT(*) as ruptures FROM produits WHERE stock = 0')
        result = cursor.fetchone()
        ruptures = result['ruptures'] if USE_POSTGRES else result[0]
        
        cursor.execute('SELECT COUNT(*) as stock_faible FROM produits WHERE stock > 0 AND stock <= 5')
        result = cursor.fetchone()
        stock_faible = result['stock_faible'] if USE_POSTGRES else result[0]
        
        cursor.execute('SELECT SUM(stock * prix) as valeur FROM produits')
        result = cursor.fetchone()
        valeur_stock = (result['valeur'] if USE_POSTGRES else result[0]) or 0
        
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
            'top_categories': rows_to_list(top_categories)
        }
        
        return render_template('statistics.html', stats=stats, categories=get_categories())
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/ruptures')
def ruptures():
    """Produits en rupture"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        cursor.execute('SELECT * FROM produits WHERE stock = 0 ORDER BY nom')
        produits = cursor.fetchall()
        conn.close()
        
        return render_template('ruptures.html', 
                             produits=rows_to_list(produits),
                             categories=get_categories())
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/stock-faible')
def stock_faible():
    """Produits Ã  stock faible"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        cursor.execute('SELECT * FROM produits WHERE stock > 0 AND stock <= 5 ORDER BY stock ASC')
        produits = cursor.fetchall()
        conn.close()
        
        return render_template('stock_faible.html', 
                             produits=rows_to_list(produits),
                             categories=get_categories())
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/codes-barres')
def codes_barres():
    """GÃ©nÃ©rateur de codes-barres"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        cursor.execute('SELECT * FROM produits ORDER BY nom')
        produits = cursor.fetchall()
        conn.close()
        
        return render_template('barcodes.html', 
                             produits=rows_to_list(produits),
                             categories=get_categories())
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/generer-code/<int:produit_id>')
def generer_code_barres(produit_id):
    """GÃ©nÃ¨re et retourne l'image du code-barres (version simplifiÃ©e)"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        query = adapt_query('SELECT * FROM produits WHERE id = ?')
        cursor.execute(query, (produit_id,))
        produit = cursor.fetchone()
        conn.close()
        
        if not produit:
            return "Product not found", 404
        
        produit_dict = row_to_dict(produit)
        
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
        return f"Error: {str(e)}", 500

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
            return render_template('error.html', error="No product to export")
        
        # CrÃ©er le CSV en mÃ©moire
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['ID', 'Name', 'Barcode', 'Price ($)', 'Stock', 'Category', 'Created at'])
        
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
        cursor = get_cursor(conn)
        cursor.execute('SELECT * FROM produits ORDER BY nom')
        produits = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(produits),
            'produits': rows_to_list(produits)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/produit/<code_barres>')
def api_produit_by_barcode(code_barres):
    """API pour rechercher un produit par code-barres"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        query = adapt_query('SELECT * FROM produits WHERE code_barres = ?')
        cursor.execute(query, (code_barres,))
        produit = cursor.fetchone()
        conn.close()
        
        if produit:
            return jsonify({
                'success': True,
                'produit': row_to_dict(produit)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Product not found'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def api_stats():
    """API JSON des statistiques"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        
        # Stats gÃ©nÃ©rales
        cursor.execute('SELECT COUNT(*) as total FROM produits')
        result = cursor.fetchone()
        total = result['total'] if USE_POSTGRES else result[0]
        
        cursor.execute('SELECT COUNT(*) as ruptures FROM produits WHERE stock = 0')
        result = cursor.fetchone()
        ruptures = result['ruptures'] if USE_POSTGRES else result[0]
        
        cursor.execute('SELECT COUNT(*) as stock_faible FROM produits WHERE stock > 0 AND stock <= 5')
        result = cursor.fetchone()
        stock_faible = result['stock_faible'] if USE_POSTGRES else result[0]
        
        cursor.execute('SELECT SUM(stock * prix) as valeur FROM produits')
        result = cursor.fetchone()
        valeur_stock = (result['valeur'] if USE_POSTGRES else result[0]) or 0
        
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
                'top_categories': rows_to_list(top_categories)
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
                                     error="Category name is required")
            
            conn = get_db_connection()
            cursor = get_cursor(conn)
            query = adapt_query('INSERT INTO categories (nom, emoji, description) VALUES (?, ?, ?)')
            cursor.execute(query, (nom, emoji, description))
            conn.commit()
            conn.close()
            
            return redirect(url_for('gerer_categories'))
            
        except Exception as e:
            return render_template('categories.html', 
                                 categories=get_categories(),
                                 error=f"Error: {str(e)}")
    
    return render_template('categories.html', categories=get_categories())

@app.route('/supprimer-categorie/<int:id>')
def supprimer_categorie(id):
    """Supprimer une catÃ©gorie"""
    try:
        conn = get_db_connection()
        cursor = get_cursor(conn)
        query = adapt_query('DELETE FROM categories WHERE id = ?')
        cursor.execute(query, (id,))
        conn.commit()
        conn.close()
    except Exception as e:
        pass
    
    return redirect(url_for('gerer_categories'))

@app.route('/aide')
def aide():
    """Help page"""
    return render_template('help.html', categories=get_categories())

@app.route('/favicon.ico')
def favicon():
    """Favicon simple"""
    return '', 204

# Initialisation de la base de données au démarrage de l'application
try:
    init_database()
    db_type = "PostgreSQL" if USE_POSTGRES else "SQLite"
    print(f"✅ Database {db_type} initialized")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM produits')
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"📦 {count} products in database")
    print(f"🗄️ Database type: {db_type}")
    if USE_POSTGRES:
        print(f"🔗 PostgreSQL connection active")
    
except Exception as e:
    print(f"⚠️ Database initialization error: {e}")
    print(f"⚠️ Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    print("Database will be created on first request")

if __name__ == '__main__':
    print("🚀 SMART INVENTORY & BARCODE SCANNER - MINIMAL VERSION")
    print("=" * 50)
    
    print("🌐 Local application ready")
    print("📱 Access: http://localhost:5000")
    print("🔧 Available features:")
    print("   ✅ Product management (CRUD)")
    print("   ✅ Barcode scanning (camera + handheld scanner)")
    print("   ✅ Advanced filters and sorting")
    print("   ✅ Statistics with charts")
    print("   ✅ Out-of-stock / low stock alerts")
    print("   ✅ Barcode generation (SVG)")
    print("   ✅ CSV/Excel export")
    print("   ✅ JSON API (products + stats)")
    print("   ✅ Responsive interface")
    print("   ✅ Persistent database")
    
    # Launch accessible from the network
    print("📱 To access from your phone:")
    print("   1. Connect your phone to the same WiFi network")
    print("   2. Open your mobile browser")
    print("   3. Go to: http://192.168.0.154:5000")
    print("   (Replace the IP with the one shown above)")
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
