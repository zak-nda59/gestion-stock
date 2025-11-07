#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier et générer des codes-barres uniques pour tous les produits
"""

import sqlite3
from datetime import datetime

def get_db_connection():
    """Connexion SQLite locale"""
    conn = sqlite3.connect('boutique_mobile.db')
    conn.row_factory = sqlite3.Row
    return conn

def generer_code_barres_unique(conn):
    """Génère un code-barres unique basé sur le timestamp"""
    cursor = conn.cursor()
    while True:
        code = str(int(datetime.now().timestamp() * 1000000))[-13:]
        cursor.execute('SELECT COUNT(*) as count FROM produits WHERE code_barres = ?', (code,))
        if cursor.fetchone()['count'] == 0:
            return code

def verifier_et_corriger_codes_barres():
    """Vérifie et corrige les codes-barres des produits"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🔍 Vérification des codes-barres...\n")
    
    # Trouver les produits sans code-barres ou avec code-barres vide
    cursor.execute("SELECT * FROM produits WHERE code_barres IS NULL OR code_barres = ''")
    produits_sans_code = cursor.fetchall()
    
    if produits_sans_code:
        print(f"⚠️  {len(produits_sans_code)} produit(s) sans code-barres trouvé(s)")
        for produit in produits_sans_code:
            nouveau_code = generer_code_barres_unique(conn)
            cursor.execute('UPDATE produits SET code_barres = ? WHERE id = ?', 
                         (nouveau_code, produit['id']))
            print(f"   ✅ {produit['nom']}: {nouveau_code}")
        
        conn.commit()
        print(f"\n✅ {len(produits_sans_code)} code(s)-barres généré(s)\n")
    else:
        print("✅ Tous les produits ont déjà un code-barres\n")
    
    # Vérifier les doublons
    cursor.execute("""
        SELECT code_barres, COUNT(*) as count 
        FROM produits 
        GROUP BY code_barres 
        HAVING count > 1
    """)
    doublons = cursor.fetchall()
    
    if doublons:
        print(f"⚠️  {len(doublons)} code(s)-barres en double trouvé(s)")
        for doublon in doublons:
            cursor.execute('SELECT * FROM produits WHERE code_barres = ?', 
                         (doublon['code_barres'],))
            produits = cursor.fetchall()
            
            # Garder le premier, régénérer pour les autres
            for i, produit in enumerate(produits):
                if i > 0:  # Sauter le premier
                    nouveau_code = generer_code_barres_unique(conn)
                    cursor.execute('UPDATE produits SET code_barres = ? WHERE id = ?', 
                                 (nouveau_code, produit['id']))
                    print(f"   ✅ {produit['nom']}: {doublon['code_barres']} → {nouveau_code}")
        
        conn.commit()
        print(f"\n✅ Doublons corrigés\n")
    else:
        print("✅ Aucun doublon détecté\n")
    
    # Afficher le résumé
    cursor.execute('SELECT COUNT(*) as total FROM produits')
    total = cursor.fetchone()['total']
    
    print("=" * 50)
    print(f"📊 RÉSUMÉ")
    print("=" * 50)
    print(f"Total de produits: {total}")
    print(f"Tous les codes-barres sont uniques ✅")
    print("=" * 50)
    
    conn.close()

if __name__ == '__main__':
    try:
        verifier_et_corriger_codes_barres()
        print("\n✅ Vérification terminée avec succès !")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
