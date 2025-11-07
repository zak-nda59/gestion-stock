-- ========================================
-- BOUTIQUE MOBILE - Export phpMyAdmin
-- Date: 2025-11-07 18:42:44
-- ========================================

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

CREATE DATABASE IF NOT EXISTS `boutique_mobile` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `boutique_mobile`;

-- Table: categories
DROP TABLE IF EXISTS `categories`;
CREATE TABLE `categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) NOT NULL,
  `emoji` varchar(10) DEFAULT '📦',
  `description` text,
  `date_creation` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nom` (`nom`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `categories` (`id`, `nom`, `emoji`, `description`, `date_creation`) VALUES
(1, 'Écran', '📱', 'Écrans et dalles tactiles', '2025-11-07 17:42:44'),
(2, 'Batterie', '🔋', 'Batteries et accumulateurs', '2025-11-07 17:42:44'),
(3, 'Coque', '🛡️', 'Coques et étuis de protection', '2025-11-07 17:42:44'),
(4, 'Accessoire', '🔎', 'Accessoires divers', '2025-11-07 17:42:44'),
(5, 'Câble', '🔌', 'Câbles et chargeurs', '2025-11-07 17:42:44'),
(6, 'Outil', '🔧', 'Outils de réparation', '2025-11-07 17:42:44'),
(7, 'Composant', '💾', 'Composants électroniques', '2025-11-07 17:42:44'),
(8, 'Audio', '🎧', 'Écouteurs et haut-parleurs', '2025-11-07 17:42:44'),
(9, 'Autre', '📦', 'Autres produits', '2025-11-07 17:42:44');

-- Table: produits
DROP TABLE IF EXISTS `produits`;
CREATE TABLE `produits` (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `produits` (`id`, `nom`, `code_barres`, `prix`, `stock`, `categorie`, `date_creation`) VALUES
(1, 'Écran iPhone 12', '1234567890123', 45.99, 15, 'Écran', '2025-11-07 17:42:44'),
(2, 'Batterie Samsung S21', '2345678901234', 29.99, 8, 'Batterie', '2025-11-07 17:42:44'),
(3, 'Coque iPhone 13 Pro', '3456789012345', 12.99, 25, 'Coque', '2025-11-07 17:42:44'),
(4, 'Câble USB-C 2m', '4567890123456', 8.99, 30, 'Câble', '2025-11-07 17:42:44'),
(5, 'Écouteurs Bluetooth', '5678901234567', 19.99, 12, 'Audio', '2025-11-07 17:42:44'),
(6, 'Tournevis Kit', '6789012345678', 15.99, 5, 'Outil', '2025-11-07 17:42:44'),
(7, 'Chargeur Rapide', '7890123456789', 24.99, 18, 'Câble', '2025-11-07 17:42:44'),
(8, 'Protection Écran Verre', '8901234567890', 9.99, 40, 'Accessoire', '2025-11-07 17:42:44'),
(9, 'Carte Mémoire 64GB', '9012345678901', 22.99, 20, 'Composant', '2025-11-07 17:42:44'),
(10, 'Haut-parleur Portable', '0123456789012', 34.99, 10, 'Audio', '2025-11-07 17:42:44');

COMMIT;
