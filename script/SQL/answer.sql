 CREATE TABLE `answer` (
  `seq` int DEFAULT NULL,
  `crdt` char(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `choice` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `object` tinyint DEFAULT NULL,
  `created` int DEFAULT NULL,
  `model` varchar(50) DEFAULT NULL,
  `usage_prompt_tokens` int DEFAULT NULL,
  `usage_completion_tokens` int DEFAULT NULL,
  `usage_total_tokens` int DEFAULT NULL,
  KEY `seq` (`seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='답변 테이블' 