CREATE TABLE `tags` (
  `seq` int DEFAULT NULL,
  `crdt` char(8) DEFAULT NULL,
  `tag` varchar(255) DEFAULT NULL,
  UNIQUE KEY `seq` (`seq`,`tag`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci