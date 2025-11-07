#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour remplir boutique_mobile.db et exporter vers MySQL
"""

import sqlite3
from datetime import datetime

def remplir_base():
    """Remplit la base de données avec des données propres"""
    print("="*60)
    print("  REMPLISSAGE DE LA BASE DE DONNÉES")
    print("="*60)
    print()
    
    conn = sqlite3.connect('boutique_mobile.db')
    cursor = conn.cursor()
    
    # 1. Créer les tables
    print("Création des tables...")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            emoji TEXT DEFAULT '📦',
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
            categorie TEXT DEFAULT 'Autre',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ Tables créées")
    
    # 2. Insérer les catégories
    print("\nAjout des catégories...")
    categories = [
        ('📱', 'Écran', 'Écrans et dalles tactiles'),
        ('🔋', 'Batterie', 'Batteries et accumulateurs'),
        ('🛡️', 'Coque', 'Coques et étuis de protection'),
        ('🔎', 'Accessoire', 'Accessoires divers'),
        ('🔌', 'Câble', 'Câbles et chargeurs'),
        ('🔧', 'Outil', 'Outils de réparation'),
        ('💾', 'Composant', 'Composants électroniques'),
        ('🎧', 'Audio', 'Écouteurs et haut-parleurs'),
        ('📦', 'Autre', 'Autres produits')
    ]
    
    for emoji, nom, desc in categories:
        cursor.execute(
            'INSERT OR IGNORE INTO categories (emoji, nom, description) VALUES (?, ?, ?)',
            (emoji, nom, desc)
        )
    print(f"✓ {len(categories)} catégories ajoutées")
    
    # 3. Insérer les produits
    print("\nAjout des produits...")
    produits = [
        ('Écran iPhone 12', '1234567890123', 45.99, 15, 'Écran'),
        ('Batterie Samsung S21', '2345678901234', 29.99, 8, 'Batterie'),
        ('Coque iPhone 13 Pro', '3456789012345', 12.99, 25, 'Coque'),
        ('Câble USB-C 2m', '4567890123456', 8.99, 30, 'Câble'),
        ('Écouteurs Bluetooth', '5678901234567', 19.99, 12, 'Audio'),
        ('Tournevis Kit', '6789012345678', 15.99, 5, 'Outil'),
        ('Chargeur Rapide', '7890123456789', 24.99, 18, 'Câble'),
        ('Protection Écran Verre', '8901234567890', 9.99, 40, 'Accessoire'),
        ('Carte Mémoire 64GB', '9012345678901', 22.99, 20, 'Composant'),
        ('Haut-parleur Portable', '0123456789012', 34.99, 10, 'Audio')
    ]
    
    for nom, code, prix, stock, cat in produits:
        cursor.execute(
            'INSERT OR IGNORE INTO produits (nom, code_barres, prix, stock, categorie) VALUES (?, ?, ?, ?, ?)',
            (nom, code, prix, stock, cat)
        )
    print(f"✓ {len(produits)} produits ajoutés")
    
    conn.commit()
    conn.close()
    print("\n✓ Base de données remplie avec succès!\n")

def exporter_mysql():
    """Génère un fichier SQL pour phpMyAdmin"""
    print("="*60)
    print("  EXPORT VERS MySQL/phpMyAdmin")
    print("="*60)
    print()
    
    conn = sqlite3.connect('boutique_mobile.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    fichier_sql = 'export_phpmyadmin.sql'
    
    with open(fichier_sql, 'w', encoding='utf-8') as f:
        # En-tête
        f.write("-- ========================================\n")
        f.write("-- BOUTIQUE MOBILE - Export phpMyAdmin\n")
        f.write(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-- ========================================\n\n")
        
        f.write("SET SQL_MODE = \"NO_AUTO_VALUE_ON_ZERO\";\n")
        f.write("START TRANSACTION;\n")
        f.write("SET time_zone = \"+00:00\";\n\n")
        
        # Base de données
        f.write("CREATE DATABASE IF NOT EXISTS `boutique_mobile` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n")
        f.write("USE `boutique_mobile`;\n\n")
        
        # Table categories
        f.write("-- Table: categories\n")
        f.write("DROP TABLE IF EXISTS `categories`;\n")
        f.write("""CREATE TABLE `categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) NOT NULL,
  `emoji` varchar(10) DEFAULT '📦',
  `description` text,
  `date_creation` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nom` (`nom`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n\n""")
        
        # Données categories
        cursor.execute('SELECT * FROM categories')
        categories = cursor.fetchall()
        
        if categories:
            f.write("INSERT INTO `categories` (`id`, `nom`, `emoji`, `description`, `date_creation`) VALUES\n")
            valeurs = []
            for cat in categories:
                emoji = cat['emoji'] or '📦'
                nom = cat['nom'].replace("'", "\\'")
                desc = (cat['description'] or '').replace("'", "\\'")
                date = cat['date_creation'] or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                valeurs.append(f"({cat['id']}, '{nom}', '{emoji}', '{desc}', '{date}')")
            f.write(",\n".join(valeurs) + ";\n\n")
        
        # Table produits
        f.write("-- Table: produits\n")
        f.write("DROP TABLE IF EXISTS `produits`;\n")
        f.write("""CREATE TABLE `produits` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) NOT NULL,
  `code_barres` varchar(50) NOT NULL,
  `prix` decimal(10,2) NOT NULL,
  `stock` int(11) NOT NULL DEFAULT 0,
  `categorie` varchar(100) DEFAULT 'Autre',
  `date_creation` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code_barres` (`code_barres`),
  KEY `categorie` (`categorie`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n\n""")
        
        # Données produits
        cursor.execute('SELECT * FROM produits')
        produits = cursor.fetchall()
        
        if produits:
            f.write("INSERT INTO `produits` (`id`, `nom`, `code_barres`, `prix`, `stock`, `categorie`, `date_creation`) VALUES\n")
            valeurs = []
            for prod in produits:
                nom = prod['nom'].replace("'", "\\'")
                code = prod['code_barres'].replace("'", "\\'")
                categorie = prod['categorie'].replace("'", "\\'")
                date = prod['date_creation'] or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                valeurs.append(f"({prod['id']}, '{nom}', '{code}', {prod['prix']}, {prod['stock']}, '{categorie}', '{date}')")
            f.write(",\n".join(valeurs) + ";\n\n")
        
        f.write("COMMIT;\n")
    
    conn.close()
    
    print(f"✓ Fichier SQL créé: {fichier_sql}")
    print(f"\n📊 Statistiques:")
    print(f"  • {len(categories)} catégories")
    print(f"  • {len(produits)} produits")
    print()

if __name__ == "__main__":
    print("\n🚀 REMPLISSAGE ET EXPORT DE LA BASE DE DONNÉES\n")
    
    # Étape 1: Remplir la base SQLite
    remplir_base()
    
    # Étape 2: Exporter vers MySQL
    exporter_mysql()
    
    print("="*60)
    print("  ✅ TERMINÉ !")
    print("="*60)
    print()
    print("📁 Fichiers générés:")
    print("  • boutique_mobile.db (SQLite)")
    print("  • export_phpmyadmin.sql (MySQL)")
    print()
    print("📤 Import dans phpMyAdmin:")
    print("  1. Ouvrez phpMyAdmin")
    print("  2. Cliquez sur 'Importer'")
    print("  3. Sélectionnez: export_phpmyadmin.sql")
    print("  4. Cliquez sur 'Exécuter'")
    print()