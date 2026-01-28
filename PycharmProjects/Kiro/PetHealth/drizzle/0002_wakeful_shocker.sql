CREATE TABLE `daily_activities` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`date` timestamp NOT NULL,
	`activityType` varchar(100) NOT NULL,
	`description` text,
	`photoUrls` text,
	`instagramPostUrl` varchar(500),
	`duration` int,
	`location` varchar(200),
	`notes` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `daily_activities_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `medications` (
	`id` int AUTO_INCREMENT NOT NULL,
	`petId` int NOT NULL,
	`medicationType` enum('flea_tick','deworming','other') NOT NULL,
	`medicationName` varchar(200) NOT NULL,
	`lastGivenDate` timestamp NOT NULL,
	`nextDueDate` timestamp,
	`dosage` varchar(100),
	`frequency` varchar(100),
	`reminderEnabled` int NOT NULL DEFAULT 1,
	`notes` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `medications_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
ALTER TABLE `health_records` ADD `symptoms` text;--> statement-breakpoint
ALTER TABLE `health_records` ADD `diagnosis` text;--> statement-breakpoint
ALTER TABLE `health_records` ADD `vetName` varchar(200);--> statement-breakpoint
ALTER TABLE `health_records` ADD `clinicName` varchar(200);--> statement-breakpoint
ALTER TABLE `health_records` ADD `cost` int;--> statement-breakpoint
ALTER TABLE `health_records` ADD `medications` text;--> statement-breakpoint
ALTER TABLE `health_records` ADD `nextAppointment` timestamp;--> statement-breakpoint
ALTER TABLE `health_records` ADD `photoUrls` text;--> statement-breakpoint
ALTER TABLE `subscriptions` ADD `stripeSubscriptionId` varchar(255);--> statement-breakpoint
ALTER TABLE `subscriptions` ADD `stripePriceId` varchar(255);--> statement-breakpoint
ALTER TABLE `users` ADD `stripeCustomerId` varchar(255);