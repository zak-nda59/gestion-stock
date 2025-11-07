# 📱 Boutique Mobile - Gestion d'Inventaire

Application web complète de gestion d'inventaire avec scanner de codes-barres, spécialement conçue pour les boutiques de réparation mobile.

## 🚀 Fonctionnalités

### ✨ Gestion Complète des Produits
- **CRUD complet** : Ajouter, modifier, supprimer des produits
- **Catégories personnalisables** avec emojis
- **Codes-barres automatiques** ou manuels
- **Gestion du stock** en temps réel

### 📱 Scanner Intelligent
- **Scanner caméra** intégré (QuaggaJS)
- **Support douchette** USB/Bluetooth
- **Décrément automatique** du stock lors des scans
- **Prévention des doublons**

### 🔍 Recherche et Filtres Avancés
- **Recherche instantanée** par nom ou code-barres
- **Filtres multiples** : catégorie, stock, prix
- **Tris personnalisés** : prix, stock, nom, date
- **Boutons de tri rapide**

### 📊 Statistiques et Analyses
- **Dashboard complet** avec métriques
- **Graphiques interactifs** (Chart.js)
- **Alertes automatiques** (ruptures, stock faible)
- **Valeur totale du stock**

### 🎨 Interface Moderne
- **Design responsive** mobile-first
- **Animations fluides** et transitions
- **Thèmes colorés** par section
- **Interface intuitive** et simple

### 💾 Export et Impression
- **Export CSV/Excel** complet
- **Génération de codes-barres** (PNG)
- **Impression d'étiquettes**

## 🛠️ Technologies

- **Backend** : Python 3.10 + Flask
- **Base de données** : PostgreSQL (Render) / SQLite (local)
- **Frontend** : HTML5 + CSS3 + Bootstrap 5 + JavaScript
- **Scanner** : QuaggaJS pour caméra
- **Graphiques** : Chart.js
- **Codes-barres** : python-barcode + Pillow
- **Export** : Pandas

## 🌐 Déploiement sur Render

### Prérequis
1. Compte GitHub
2. Compte Render.com

### Étapes de déploiement

1. **Créer un repository GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Boutique Mobile"
   git branch -M main
   git remote add origin https://github.com/VOTRE_USERNAME/boutique-mobile.git
   git push -u origin main
   ```

2. **Déployer sur Render**
   - Connectez-vous sur [render.com](https://render.com)
   - Cliquez "New +" → "Web Service"
   - Connectez votre repository GitHub
   - Configurez :
     - **Name** : `boutique-mobile`
     - **Environment** : `Python 3`
     - **Build Command** : `pip install -r requirements.txt`
     - **Start Command** : `gunicorn app:app`

3. **Créer la base de données PostgreSQL**
   - Dans Render, cliquez "New +" → "PostgreSQL"
   - **Name** : `boutique-mobile-db`
   - Copiez l'URL de connexion

4. **Configurer les variables d'environnement**
   - Dans votre Web Service, allez dans "Environment"
   - Ajoutez : `DATABASE_URL` = URL de votre base PostgreSQL

5. **Déployer**
   - Render déploiera automatiquement votre application
   - Votre app sera accessible sur : `https://boutique-mobile-XXXX.onrender.com`

## 🏃‍♂️ Lancement Local

```bash
# Cloner le projet
git clone https://github.com/VOTRE_USERNAME/boutique-mobile.git
cd boutique-mobile

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python app.py

# Accéder à l'application
# http://localhost:5000
```

## 📋 Routes Disponibles

### Pages Principales
- `/` - Accueil avec recherche et aperçu
- `/produits` - Tous les produits avec filtres avancés
- `/ajouter` - Ajouter un nouveau produit
- `/modifier/<id>` - Modifier un produit
- `/supprimer/<id>` - Supprimer un produit

### Scanner et Codes-barres
- `/scanner` - Interface de scan (caméra + douchette)
- `/codes-barres` - Générateur de codes-barres
- `/generer-code/<id>` - Générer l'image du code-barres

### Analyses et Alertes
- `/statistiques` - Dashboard avec graphiques
- `/ruptures` - Produits en rupture de stock
- `/stock-faible` - Produits à stock faible
- `/export` - Export CSV des produits

### API
- `POST /scan` - Scanner un code-barres (JSON)

## 🎯 Utilisation

### Ajouter des Produits
1. Cliquez "Ajouter un Produit"
2. Remplissez les informations
3. Le code-barres est généré automatiquement
4. Sauvegardez

### Scanner des Produits
1. Allez dans "Scanner"
2. **Douchette** : Connectez et scannez directement
3. **Caméra** : Cliquez "Démarrer" et pointez vers le code
4. Le stock est automatiquement décrémenté

### Filtrer et Trier
1. Allez dans "Voir tous les produits"
2. Utilisez les filtres : recherche, catégorie, stock
3. Triez par : prix, stock, nom, date
4. Utilisez les boutons de tri rapide

### Suivre les Statistiques
1. Consultez le dashboard pour les métriques
2. Surveillez les alertes de rupture
3. Analysez la répartition par catégories

## 🔧 Configuration

### Variables d'Environnement
- `DATABASE_URL` : URL de connexion PostgreSQL (Render)
- `PORT` : Port d'écoute (défaut: 5000)

### Base de Données
L'application s'adapte automatiquement :
- **PostgreSQL** sur Render (production)
- **SQLite** en local (développement)

## 📱 Compatibilité

- ✅ **Desktop** : Chrome, Firefox, Safari, Edge
- ✅ **Mobile** : iOS Safari, Android Chrome
- ✅ **Tablette** : iPad, Android tablets
- ✅ **Scanner** : Douchettes USB/Bluetooth
- ✅ **Caméra** : Tous navigateurs modernes

## 🆘 Support

### Problèmes Courants

**Scanner caméra ne fonctionne pas**
- Autorisez l'accès à la caméra
- Utilisez HTTPS (obligatoire pour la caméra)
- Vérifiez la compatibilité du navigateur

**Douchette ne scanne pas**
- Vérifiez la connexion USB/Bluetooth
- Cliquez dans le champ de saisie
- Testez avec un autre code-barres

**Erreur de déploiement**
- Vérifiez les versions dans `requirements.txt`
- Consultez les logs Render
- Vérifiez la configuration de la base de données

## 📄 Licence

MIT License - Libre d'utilisation pour projets personnels et commerciaux.

## 🎉 Crédits

Développé avec ❤️ pour les boutiques de réparation mobile.

---

**🚀 Votre boutique mobile est maintenant en ligne et accessible partout !**
