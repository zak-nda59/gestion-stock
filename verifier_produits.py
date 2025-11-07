#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple pour vérifier les codes-barres des produits
"""

import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('boutique_mobile.db')
    conn.row_factory = sqlite3.Row
    return conn

def verifier_produits():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print(" VERIFICATION DES CODES-BARRES ".center(70))
    print("="*70 + "\n")
    
    # Récupérer tous les produits
    cursor.execute('SELECT * FROM produits ORDER BY id')
    produits = cursor.fetchall()
    
    print(f"Total de produits: {len(produits)}\n")
    
    produits_sans_code = 0
    codes_barres = []
    
    for produit in produits:
        p = dict(produit)
        code = p.get('code_barres', '')
        
        print(f"ID: {p['id']:2d} | {p['nom']:25s} | Code: ", end="")
        
        if not code or code == '':
            print("❌ MANQUANT")
            produits_sans_code += 1
        else:
            print(f"✅ {code}")
            codes_barres.append(code)
    
    # Vérifier les doublons
    print("\n" + "-"*70)
    
    if produits_sans_code > 0:
        print(f"\n⚠️  {produits_sans_code} produit(s) SANS code-barres !")
        print("   → Exécutez: python generer_codes_barres.py")
    else:
        print("\n✅ Tous les produits ont un code-barres")
    
    # Vérifier unicité
    doublons = len(codes_barres) - len(set(codes_barres))
    if doublons > 0:
        print(f"⚠️  {doublons} code(s)-barres en double détecté(s)")
    else:
        print("✅ Tous les codes-barres sont uniques")
    
    print("\n" + "="*70 + "\n")
    
    conn.close()

if __name__ == '__main__':
    verifier_produits()
