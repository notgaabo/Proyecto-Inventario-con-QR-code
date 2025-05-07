CREATE DATABASE  IF NOT EXISTS `final_project` 
USE `final_project`;
--
-- Table structure for table `companies`
--

DROP TABLE IF EXISTS `companies`;

CREATE TABLE `companies` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `industry` varchar(255) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`)
) 
--
-- Table structure for table `company_roles`
--

DROP TABLE IF EXISTS `company_roles`;

CREATE TABLE `company_roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_name` varchar(50) DEFAULT NULL,
  `permissions` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) 

--
-- Table structure for table `order_items`
--

DROP TABLE IF EXISTS `order_items`;

CREATE TABLE `order_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `product_id` int NOT NULL,
  `quantity` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `order_id` (`order_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `order_items_chk_1` CHECK ((`quantity` > 0))
) 
--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;

CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `supplier_id` int NOT NULL,
  `order_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('pending','in_transit','delivered') DEFAULT 'pending',
  `created_by` int NOT NULL,
  `delivered_at` timestamp NULL DEFAULT NULL,
  `is_printed` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `company_id` (`company_id`),
  KEY `supplier_id` (`supplier_id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `orders_ibfk_2` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `orders_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE RESTRICT
)
--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;

CREATE TABLE `products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `category` varchar(255) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `stock` int NOT NULL,
  `cost_price` decimal(10,2) DEFAULT NULL,
  `image` varchar(255) DEFAULT NULL,
  `supplier_id` int DEFAULT NULL,
  `company_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_supplier` (`supplier_id`),
  KEY `fk_company_id` (`company_id`),
  CONSTRAINT `fk_company_id` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL
) 
--
-- Table structure for table `returns`
--

DROP TABLE IF EXISTS `returns`;

CREATE TABLE `returns` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `quantity` int NOT NULL,
  `reason` varchar(255) NOT NULL,
  `company_id` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `sale_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `product_id` (`product_id`),
  KEY `company_id` (`company_id`),
  KEY `sale_id` (`sale_id`),
  CONSTRAINT `returns_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `returns_ibfk_2` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`),
  CONSTRAINT `returns_ibfk_3` FOREIGN KEY (`sale_id`) REFERENCES `sales` (`id`)
) 
--
-- Table structure for table `sales`
--

DROP TABLE IF EXISTS `sales`;

CREATE TABLE `sales` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `product_id` int NOT NULL,
  `user_id` int NOT NULL,
  `quantity` int NOT NULL,
  `sale_price` decimal(10,2) NOT NULL,
  `sale_date` datetime NOT NULL,
  `profit` decimal(10,2) DEFAULT NULL,
  `payment_method` enum('cash','transfer','stripe') NOT NULL DEFAULT 'cash',
  `stripe_payment_id` varchar(100) DEFAULT NULL,
  `sale_group_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_product_id` (`product_id`),
  KEY `fk_sales_company_id` (`company_id`),
  KEY `fk_sales_user_id` (`user_id`),
  CONSTRAINT `fk_product_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_sales_company_id` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`),
  CONSTRAINT `fk_sales_product_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `fk_sales_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `sales_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) 
--
-- Table structure for table `suppliers`
--

DROP TABLE IF EXISTS `suppliers`;

CREATE TABLE `suppliers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `contact_info` varchar(255) DEFAULT NULL,
  `company_id` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `company_id` (`company_id`),
  CONSTRAINT `suppliers_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE
) 
--
-- Table structure for table `transfer_details`
--

DROP TABLE IF EXISTS `transfer_details`;

CREATE TABLE `transfer_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sale_id` int NOT NULL,
  `account_number` varchar(50) NOT NULL,
  `bank_name` varchar(100) NOT NULL,
  `transfer_date` date NOT NULL,
  `reference_number` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_transfer_details_sale_id` (`sale_id`),
  CONSTRAINT `fk_transfer_details_sale_id` FOREIGN KEY (`sale_id`) REFERENCES `sales` (`id`),
  CONSTRAINT `transfer_details_ibfk_1` FOREIGN KEY (`sale_id`) REFERENCES `sales` (`id`)
) 
--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int DEFAULT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(50) NOT NULL,
  `role_id` int DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  KEY `role_id` (`role_id`),
  KEY `fk_users_company_id` (`company_id`),
  CONSTRAINT `fk_users_company_id` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`)
) 

-- Dump completed on 2025-05-06 15:03:06
