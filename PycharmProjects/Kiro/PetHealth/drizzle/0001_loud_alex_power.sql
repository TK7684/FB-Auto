CREATE TABLE `behavior_logs` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`date` timestamp NOT NULL,
	`behaviorType` varchar(50) NOT NULL,
	`notes` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `behavior_logs_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `expenses` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`date` timestamp NOT NULL,
	`category` varchar(50) NOT NULL,
	`amount` int NOT NULL,
	`description` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `expenses_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `feeding_schedules` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`foodType` varchar(100) NOT NULL,
	`amount` varchar(50) NOT NULL,
	`frequency` varchar(50) NOT NULL,
	`time` varchar(50),
	`notes` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `feeding_schedules_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `health_records` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`recordType` varchar(50) NOT NULL,
	`date` timestamp NOT NULL,
	`notes` text,
	`attachmentUrl` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `health_records_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `pets` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`name` varchar(100) NOT NULL,
	`breed` varchar(100),
	`birthDate` timestamp,
	`photoUrl` text,
	`gender` enum('male','female','unknown') DEFAULT 'unknown',
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `pets_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `sick_care_logs` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`startDate` timestamp NOT NULL,
	`endDate` timestamp,
	`symptoms` text NOT NULL,
	`medications` text,
	`status` enum('ongoing','recovered','monitoring') NOT NULL DEFAULT 'ongoing',
	`notes` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `sick_care_logs_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `subscriptions` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`tier` enum('free','premium') NOT NULL DEFAULT 'free',
	`startDate` timestamp NOT NULL DEFAULT (now()),
	`endDate` timestamp,
	`status` enum('active','expired','cancelled') NOT NULL DEFAULT 'active',
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `subscriptions_id` PRIMARY KEY(`id`),
	CONSTRAINT `subscriptions_userId_unique` UNIQUE(`userId`)
);
--> statement-breakpoint
CREATE TABLE `vaccinations` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`vaccineName` varchar(100) NOT NULL,
	`lastDate` timestamp NOT NULL,
	`nextDate` timestamp,
	`reminderEnabled` int NOT NULL DEFAULT 1,
	`notes` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `vaccinations_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `weight_records` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`date` timestamp NOT NULL,
	`weight` int NOT NULL,
	`unit` varchar(10) NOT NULL DEFAULT 'kg',
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `weight_records_id` PRIMARY KEY(`id`)
);
