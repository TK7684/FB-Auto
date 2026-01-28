CREATE TABLE `medications` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`medicationType` enum('flea_tick', 'deworming', 'other') NOT NULL,
	`medicationName` varchar(200) NOT NULL,
	`lastGivenDate` timestamp NOT NULL,
	`nextDueDate` timestamp NULL,
	`dosage` varchar(100) NULL,
	`frequency` varchar(100) NULL,
	`reminderEnabled` int DEFAULT 1 NOT NULL,
	`notes` text NULL,
	`createdAt` timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updatedAt` timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `medications_id` PRIMARY KEY(`id`)
);
--> statmt: CREATE TABLE `medications` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`medicationType` enum('flea_tick', 'deworming', 'other') NOT NULL,
	`medicationName` varchar(200) NOT NULL,
	`lastGivenDate` timestamp NOT NULL,
	`nextDueDate` timestamp NULL,
	`dosage` varchar(100) NULL,
	`frequency` varchar(100) NULL,
	`reminderEnabled` int DEFAULT 1 NOT NULL,
	`notes` text NULL,
	`createdAt` timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updatedAt` timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `medications_id` PRIMARY KEY(`id`)
);

CREATE TABLE `daily_activities` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`date` timestamp NOT NULL,
	`activityType` varchar(100) NOT NULL,
	`description` text NOT NULL,
	`photoUrls` text NULL,
	`instagramPostUrl` varchar(500) NULL,
	`duration` int NULL,
	`location` varchar(200) NULL,
	`notes` text NULL,
	`createdAt` timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updatedAt` timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `daily_activities_id` PRIMARY KEY(`id`)
);
--> statmt: CREATE TABLE `daily_activities` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`date` timestamp NOT NULL,
	`activityType` varchar(100) NOT NULL,
	`description` text NOT NULL,
	`photoUrls` text NULL,
	`instagramPostUrl` varchar(500) NULL,
	`duration` int NULL,
	`location` varchar(200) NULL,
	`notes` text NULL,
	`createdAt` timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updatedAt` timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `daily_activities_id` PRIMARY KEY(`id`)
);
