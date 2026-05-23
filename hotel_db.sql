-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 22, 2026 at 10:38 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `hotel_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `damages`
--

CREATE TABLE `damages` (
  `id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `purchase_id` int(11) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `quantity` int(11) NOT NULL,
  `reason` text DEFAULT NULL,
  `status` varchar(50) DEFAULT 'reported',
  `created_by` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `damages`
--

INSERT INTO `damages` (`id`, `item_id`, `purchase_id`, `category`, `quantity`, `reason`, `status`, `created_by`, `created_at`) VALUES
(1, 13, NULL, 'asasd', 1, 'asdd', 'reported', 'Purchase Admin', '2026-05-04 18:16:57'),
(2, 13, 2, 'Supplier Damage', 1, 'broken', 'reported', 'Purchase Admin', '2026-05-19 18:33:10'),
(3, 2, 3, 'Supplier Damage', 1, 'teared', 'reported', 'Purchase Admin', '2026-05-19 18:34:49'),
(4, 13, 6, 'Supplier Damage', 1, 'lorem', 'reported', 'Purchase Admin', '2026-05-21 10:23:19');

-- --------------------------------------------------------

--
-- Table structure for table `inventory_history`
--

CREATE TABLE `inventory_history` (
  `id` int(11) NOT NULL,
  `item_name` varchar(255) NOT NULL,
  `movement_type` varchar(50) NOT NULL COMMENT 'stock_in | distributed | adjustment | damage',
  `quantity` int(11) NOT NULL,
  `user_name` varchar(100) NOT NULL,
  `notes` text DEFAULT NULL,
  `department` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `inventory_history`
--

INSERT INTO `inventory_history` (`id`, `item_name`, `movement_type`, `quantity`, `user_name`, `notes`, `department`, `created_at`) VALUES
(1, 'ABC', 'stock_in', 79, 'Purchase Admin', 'Initial stock entry', NULL, '2026-05-04 18:02:03'),
(2, 'Bath Towels', 'stock_in', 10, 'Purchase Admin', 'Purchase #1', NULL, '2026-05-04 18:14:48'),
(3, 'Bed Sheets', 'stock_in', 10, 'Purchase Admin', 'Purchase #1', NULL, '2026-05-04 18:14:48'),
(4, 'Cleaning Rags', 'stock_in', 8, 'Purchase Admin', 'Purchase #1', NULL, '2026-05-04 18:14:48'),
(5, 'ABC', 'damage', 1, 'Purchase Admin', 'asdd', NULL, '2026-05-04 18:16:57'),
(6, 'ABC', 'stock_in', 1, 'Purchase Admin', 'Purchase #2', NULL, '2026-05-04 18:26:47'),
(7, 'ABC', 'damage', 1, 'Purchase Admin', 'Damage report — PO #2: broken', NULL, '2026-05-19 18:33:10'),
(8, 'Bed Sheets', 'stock_in', 2, 'Purchase Admin', 'Purchase #3', NULL, '2026-05-19 18:34:01'),
(9, 'Bed Sheets', 'damage', 1, 'Purchase Admin', 'Damage report — PO #3: teared', NULL, '2026-05-19 18:34:49'),
(10, 'Bath Towels', 'distributed', 2, 'Housekeeping Manager', '201', 'Housekeeping', '2026-05-19 20:31:03'),
(11, 'ABC', 'stock_in', 1, 'Purchase Admin', 'Purchase #4', NULL, '2026-05-20 10:24:12'),
(12, 'Hose', 'stock_in', 1, 'Purchase Admin', 'Purchase #5', NULL, '2026-05-20 11:09:48'),
(13, 'Hose', 'stock_in', 1, 'Purchase Admin', 'Purchase #5', NULL, '2026-05-20 11:09:48'),
(14, 'ABC', 'stock_in', 1, 'Purchase Admin', 'Purchase #6', NULL, '2026-05-21 10:21:09'),
(15, 'Bath Towels', 'stock_in', 1, 'Purchase Admin', 'Purchase #6', NULL, '2026-05-21 10:21:09'),
(16, 'ABC', 'damage', 1, 'Purchase Admin', 'Damage report — PO #6: lorem', NULL, '2026-05-21 10:23:19'),
(17, 'ABC', 'stock_in', 1, 'Purchase Admin', 'Purchase #7', NULL, '2026-05-21 20:49:49');

-- --------------------------------------------------------

--
-- Table structure for table `items`
--

CREATE TABLE `items` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `sku` varchar(100) DEFAULT NULL,
  `unit` varchar(50) DEFAULT NULL,
  `unit_cost` decimal(12,2) DEFAULT 0.00,
  `stock_qty` int(11) DEFAULT 0,
  `min_stock` int(11) DEFAULT 10,
  `category` varchar(100) DEFAULT 'General',
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `items`
--

INSERT INTO `items` (`id`, `name`, `sku`, `unit`, `unit_cost`, `stock_qty`, `min_stock`, `category`, `created_at`, `updated_at`) VALUES
(1, 'Bath Towels', 'HK-001', 'pcs', 250.00, 109, 20, 'Housekeeping', '2026-05-04 17:55:57', '2026-05-21 10:21:09'),
(2, 'Bed Sheets', 'HK-002', 'sets', 450.00, 91, 15, 'Housekeeping', '2026-05-04 17:55:57', '2026-05-19 18:34:49'),
(3, 'Shampoo (50ml)', 'HK-003', 'pcs', 35.00, 200, 50, 'Housekeeping', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(4, 'Soap Bar', 'HK-004', 'pcs', 18.00, 300, 60, 'Housekeeping', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(5, 'Toilet Paper', 'HK-005', 'rolls', 12.00, 400, 80, 'Housekeeping', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(6, 'Rice (50kg sack)', 'DI-001', 'sacks', 2400.00, 10, 3, 'Dining', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(7, 'Cooking Oil (5L)', 'DI-002', 'btls', 420.00, 20, 5, 'Dining', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(8, 'Table Napkins', 'DI-003', 'packs', 60.00, 50, 10, 'Dining', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(9, 'Dishwashing Liquid', 'DI-004', 'btls', 85.00, 30, 8, 'Dining', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(10, 'Gloves (box)', 'MT-001', 'boxes', 150.00, 15, 5, 'Maintenance', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(11, 'Light Bulbs (LED)', 'MT-002', 'pcs', 120.00, 40, 10, 'Maintenance', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(12, 'Cleaning Rags', 'MT-003', 'pcs', 25.00, 68, 10, 'Maintenance', '2026-05-04 17:55:57', '2026-05-04 18:14:48'),
(13, 'ABC', 'G-001', 'pcs', 110.00, 80, 11, 'General', '2026-05-04 18:02:03', '2026-05-21 20:49:49'),
(14, 'Hose', 'HK-006', 'pcs', 1220.00, 2, 2, 'Housekeeping', '2026-05-20 11:09:00', '2026-05-20 11:09:48');

-- --------------------------------------------------------

--
-- Table structure for table `messages`
--

CREATE TABLE `messages` (
  `id` int(11) NOT NULL,
  `sender_id` int(11) NOT NULL,
  `recipient_id` int(11) NOT NULL,
  `category` varchar(64) DEFAULT 'General',
  `title` varchar(255) DEFAULT NULL,
  `body` text DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `messages`
--

INSERT INTO `messages` (`id`, `sender_id`, `recipient_id`, `category`, `title`, `body`, `is_read`, `created_at`, `updated_at`) VALUES
(1, 1, 4, 'General', 'Hello', 'hi', 1, '2026-05-04 18:03:49', '2026-05-04 18:12:57'),
(2, 2, 1, 'Purchase', 'Hi', 'hello', 0, '2026-05-04 18:06:33', '2026-05-04 18:06:33'),
(3, 3, 1, 'Urgent', 'Helo', 'a sadasff asas', 1, '2026-05-04 18:07:36', '2026-05-05 07:56:38'),
(4, 1, 3, 'Urgent', 'Re: Helo', 'hehe', 1, '2026-05-05 07:56:48', '2026-05-05 07:58:32'),
(5, 1, 3, 'General', 'ssd', 'sss', 1, '2026-05-19 20:28:25', '2026-05-19 20:30:33'),
(6, 1, 3, 'Inventory', 'test', 'test', 0, '2026-05-21 10:27:28', '2026-05-21 10:27:28');

-- --------------------------------------------------------

--
-- Table structure for table `purchases`
--

CREATE TABLE `purchases` (
  `id` int(11) NOT NULL,
  `supplier_id` int(11) DEFAULT NULL,
  `expected_date` date DEFAULT NULL,
  `total_amount` decimal(12,2) DEFAULT 0.00,
  `status` varchar(32) DEFAULT 'pending',
  `created_by` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `purchases`
--

INSERT INTO `purchases` (`id`, `supplier_id`, `expected_date`, `total_amount`, `status`, `created_by`, `created_at`, `updated_at`) VALUES
(1, 1, '2026-02-25', 7200.00, 'approved', 'Purchase Admin', '2026-05-04 18:00:00', '2026-05-04 18:14:48'),
(2, 1, '2026-05-04', 110.00, 'approved', 'Purchase Admin', '2026-05-04 18:26:39', '2026-05-04 18:26:47'),
(3, 1, '2026-05-20', 900.00, 'approved', 'Purchase Admin', '2026-05-19 18:33:49', '2026-05-19 18:34:01'),
(4, 1, '2026-05-20', 110.00, 'delivered', 'Purchase Admin', '2026-05-20 10:24:05', '2026-05-20 10:24:12'),
(5, 1, '2026-05-20', 2440.00, 'delivered', 'Purchase Admin', '2026-05-20 11:09:41', '2026-05-20 11:09:48'),
(6, 3, '2026-05-21', 250.00, 'delivered', 'Purchase Admin', '2026-05-21 10:20:38', '2026-05-21 10:21:09'),
(7, 1, '2026-05-21', 110.00, 'delivered', 'Purchase Admin', '2026-05-21 20:49:45', '2026-05-21 20:49:49');

-- --------------------------------------------------------

--
-- Table structure for table `purchase_items`
--

CREATE TABLE `purchase_items` (
  `id` int(11) NOT NULL,
  `purchase_id` int(11) NOT NULL,
  `item_name` varchar(255) DEFAULT NULL,
  `item_id` int(11) DEFAULT NULL,
  `quantity` int(11) NOT NULL,
  `unit_price` decimal(12,2) NOT NULL,
  `total` decimal(12,2) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `in_inventory` tinyint(4) DEFAULT 0,
  `qty_added_to_inventory` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `purchase_items`
--

INSERT INTO `purchase_items` (`id`, `purchase_id`, `item_name`, `item_id`, `quantity`, `unit_price`, `total`, `created_at`, `in_inventory`, `qty_added_to_inventory`) VALUES
(1, 1, 'Bath Towels', 1, 10, 250.00, 2500.00, '2026-05-04 18:00:00', 1, 10),
(2, 1, 'Bed Sheets', 2, 10, 450.00, 4500.00, '2026-05-04 18:00:00', 1, 10),
(3, 1, 'Cleaning Rags', 12, 8, 25.00, 200.00, '2026-05-04 18:00:00', 1, 8),
(4, 2, 'ABC', 13, 1, 110.00, 110.00, '2026-05-04 18:26:39', 1, 1),
(5, 3, 'Bed Sheets', 2, 2, 450.00, 900.00, '2026-05-19 18:33:49', 1, 2),
(6, 4, 'ABC', 13, 1, 110.00, 110.00, '2026-05-20 10:24:05', 1, 1),
(7, 5, 'Hose', 14, 1, 1220.00, 1220.00, '2026-05-20 11:09:41', 1, 1),
(8, 5, 'Hose', 14, 1, 1220.00, 1220.00, '2026-05-20 11:09:41', 1, 1),
(9, 6, 'ABC', 13, 1, 0.00, 0.00, '2026-05-21 10:20:38', 1, 1),
(10, 6, 'Bath Towels', 1, 1, 250.00, 250.00, '2026-05-21 10:20:38', 1, 1),
(11, 7, 'ABC', 13, 1, 110.00, 110.00, '2026-05-21 20:49:45', 1, 1);

-- --------------------------------------------------------

--
-- Table structure for table `requests`
--

CREATE TABLE `requests` (
  `id` int(11) NOT NULL,
  `department` varchar(50) NOT NULL,
  `requested_by` varchar(100) NOT NULL,
  `item_name` varchar(255) NOT NULL,
  `quantity` int(11) NOT NULL,
  `unit` varchar(50) DEFAULT NULL,
  `reason` text DEFAULT NULL,
  `status` varchar(20) DEFAULT 'Pending',
  `notes` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `requests`
--

INSERT INTO `requests` (`id`, `department`, `requested_by`, `item_name`, `quantity`, `unit`, `reason`, `status`, `notes`, `created_at`, `updated_at`) VALUES
(1, 'Housekeeping', 'Housekeeping Manager', 'Vacuum', 1, 'pcs', 'to easy the cleaning process', 'Approved', 'Approved by Purchase Admin', '2026-05-04 18:08:57', '2026-05-19 19:02:32'),
(2, 'Housekeeping', 'Housekeeping Manager', 'Vacuum', 1, 'pcs', 'g', 'Approved', 'Approved by Purchase Admin', '2026-05-19 20:10:50', '2026-05-19 20:11:09'),
(3, 'Housekeeping', 'Housekeeping Manager', 'ABC', 1, 'pcs', '', 'Approved', 'Approved by Purchase Admin', '2026-05-20 10:23:13', '2026-05-20 10:23:31'),
(4, 'Housekeeping', 'Housekeeping Manager', 'Vacuum', 1, 'pcs', 'help', 'Approved', 'Approved by Purchase Admin', '2026-05-20 10:54:22', '2026-05-20 10:54:38'),
(5, 'Housekeeping', 'Housekeeping Manager', 'Hose', 1, 'pcs', 'belp', 'Approved', 'Approved by Purchase Admin', '2026-05-20 10:59:08', '2026-05-20 11:08:22');

-- --------------------------------------------------------

--
-- Table structure for table `suppliers`
--

CREATE TABLE `suppliers` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `contact_name` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `phone` varchar(64) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `suppliers`
--

INSERT INTO `suppliers` (`id`, `name`, `contact_name`, `email`, `phone`, `address`, `created_at`, `updated_at`) VALUES
(1, 'ABC Suppliers Inc.', 'Juan dela Cruz', 'abc@suppliers.com', '+63 912 000 0001', 'Davao City', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(2, 'XYZ Supplies Co.', 'Maria Santos', 'xyz@supplies.com', '+63 912 000 0002', 'Makati City', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(3, 'Hotel Depot PH', 'Pedro Reyes', 'depot@hoteldph.com', '+63 912 000 0003', 'Cebu City', '2026-05-04 17:55:57', '2026-05-04 17:55:57');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL COMMENT 'SHA-256 hash via hashlib',
  `full_name` varchar(255) NOT NULL,
  `role` varchar(50) NOT NULL COMMENT 'admin | owner | department',
  `department` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `email`, `password`, `full_name`, `role`, `department`, `created_at`, `updated_at`) VALUES
(1, 'admin@hotel.com', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'Purchase Admin', 'admin', NULL, '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(2, 'owner@hotel.com', '43a0d17178a9d26c9e0fe9a74b0b45e38d32f27aed887a008a54bf6e033bf7b9', 'Hotel Owner', 'owner', NULL, '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(3, 'housekeeping@hotel.com', '245b342eb00576ef2efc99304125cffdd9bd6c27e0ac63812cd4211915606dd2', 'Housekeeping Manager', 'department', 'Housekeeping', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(4, 'dining@hotel.com', '245b342eb00576ef2efc99304125cffdd9bd6c27e0ac63812cd4211915606dd2', 'Dining Manager', 'department', 'Dining', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(5, 'maintenance@hotel.com', '245b342eb00576ef2efc99304125cffdd9bd6c27e0ac63812cd4211915606dd2', 'Maintenance Manager', 'department', 'Maintenance', '2026-05-04 17:55:57', '2026-05-04 17:55:57'),
(7, 'test', '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08', 'test', 'admin', NULL, '2026-05-21 10:28:27', '2026-05-21 10:28:27');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `damages`
--
ALTER TABLE `damages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_item` (`item_id`),
  ADD KEY `idx_created` (`created_at`);

--
-- Indexes for table `inventory_history`
--
ALTER TABLE `inventory_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_item_name` (`item_name`),
  ADD KEY `idx_movement_type` (`movement_type`),
  ADD KEY `idx_created` (`created_at`);

--
-- Indexes for table `items`
--
ALTER TABLE `items`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_name` (`name`),
  ADD KEY `idx_category` (`category`),
  ADD KEY `idx_stock` (`stock_qty`);

--
-- Indexes for table `messages`
--
ALTER TABLE `messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_sender` (`sender_id`),
  ADD KEY `idx_recipient` (`recipient_id`),
  ADD KEY `idx_is_read` (`is_read`),
  ADD KEY `idx_created` (`created_at`);

--
-- Indexes for table `purchases`
--
ALTER TABLE `purchases`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_supplier` (`supplier_id`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_created` (`created_at`);

--
-- Indexes for table `purchase_items`
--
ALTER TABLE `purchase_items`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_purchase` (`purchase_id`),
  ADD KEY `idx_item` (`item_id`);

--
-- Indexes for table `requests`
--
ALTER TABLE `requests`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_dept` (`department`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_created` (`created_at`);

--
-- Indexes for table `suppliers`
--
ALTER TABLE `suppliers`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_name` (`name`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_email` (`email`),
  ADD KEY `idx_role` (`role`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `damages`
--
ALTER TABLE `damages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `inventory_history`
--
ALTER TABLE `inventory_history`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT for table `items`
--
ALTER TABLE `items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `messages`
--
ALTER TABLE `messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `purchases`
--
ALTER TABLE `purchases`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `purchase_items`
--
ALTER TABLE `purchase_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `requests`
--
ALTER TABLE `requests`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `suppliers`
--
ALTER TABLE `suppliers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `damages`
--
ALTER TABLE `damages`
  ADD CONSTRAINT `damages_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `messages`
--
ALTER TABLE `messages`
  ADD CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`recipient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `purchases`
--
ALTER TABLE `purchases`
  ADD CONSTRAINT `purchases_ibfk_1` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `purchase_items`
--
ALTER TABLE `purchase_items`
  ADD CONSTRAINT `purchase_items_ibfk_1` FOREIGN KEY (`purchase_id`) REFERENCES `purchases` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `purchase_items_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
