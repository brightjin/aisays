CREATE TABLE `vote` (
  `seq` int DEFAULT NULL,
  `crdt` char(8) DEFAULT NULL,
  `id` varchar(50) DEFAULT NULL,
  `ip` varchar(20) DEFAULT NULL,
  `good` int DEFAULT NULL,
  `bad` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='조회수 및 평가' 