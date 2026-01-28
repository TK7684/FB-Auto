import { int, mysqlEnum, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  stripeCustomerId: varchar("stripeCustomerId", { length: 255 }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * Pet information table
 */
export const pets = mysqlTable("pets", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  name: varchar("name", { length: 100 }).notNull(),
  breed: varchar("breed", { length: 100 }),
  birthDate: timestamp("birthDate"),
  photoUrl: text("photoUrl"),
  gender: mysqlEnum("gender", ["male", "female", "unknown"]).default("unknown"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Pet = typeof pets.$inferSelect;
export type InsertPet = typeof pets.$inferInsert;

/**
 * Health records table - Enhanced with detailed vet visit information
 */
export const healthRecords = mysqlTable("health_records", {
  id: int("id").autoincrement().primaryKey(),
  petId: int("petId").notNull(),
  recordType: varchar("recordType", { length: 50 }).notNull(),
  date: timestamp("date").notNull(),
  // Vet visit details
  symptoms: text("symptoms"),
  diagnosis: text("diagnosis"),
  vetName: varchar("vetName", { length: 200 }),
  clinicName: varchar("clinicName", { length: 200 }),
  cost: int("cost"),
  medications: text("medications"), // JSON string of medications prescribed
  nextAppointment: timestamp("nextAppointment"),
  photoUrls: text("photoUrls"), // JSON array of photo URLs
  notes: text("notes"),
  attachmentUrl: text("attachmentUrl"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type HealthRecord = typeof healthRecords.$inferSelect;
export type InsertHealthRecord = typeof healthRecords.$inferInsert;

/**
 * Vaccinations table
 */
export const vaccinations = mysqlTable("vaccinations", {
  id: int("id").autoincrement().primaryKey(),
  petId: int("petId").notNull(),
  vaccineName: varchar("vaccineName", { length: 100 }).notNull(),
  lastDate: timestamp("lastDate").notNull(),
  nextDate: timestamp("nextDate"),
  reminderEnabled: int("reminderEnabled").default(1).notNull(),
  notes: text("notes"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Vaccination = typeof vaccinations.$inferSelect;
export type InsertVaccination = typeof vaccinations.$inferInsert;

/**
 * Behavior logs table
 */
export const behaviorLogs = mysqlTable("behavior_logs", {
  id: int("id").autoincrement().primaryKey(),
  petId: int("petId").notNull(),
  date: timestamp("date").notNull(),
  behaviorType: varchar("behaviorType", { length: 50 }).notNull(),
  notes: text("notes"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type BehaviorLog = typeof behaviorLogs.$inferSelect;
export type InsertBehaviorLog = typeof behaviorLogs.$inferInsert;

/**
 * Weight records table
 */
export const weightRecords = mysqlTable("weight_records", {
  id: int("id").autoincrement().primaryKey(),
  petId: int("petId").notNull(),
  date: timestamp("date").notNull(),
  weight: int("weight").notNull(),
  unit: varchar("unit", { length: 10 }).default("kg").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type WeightRecord = typeof weightRecords.$inferSelect;
export type InsertWeightRecord = typeof weightRecords.$inferInsert;

/**
 * Expenses table (Premium feature)
 */
export const expenses = mysqlTable("expenses", {
  id: int("id").autoincrement().primaryKey(),
  petId: int("petId").notNull(),
  date: timestamp("date").notNull(),
  category: varchar("category", { length: 50 }).notNull(),
  amount: int("amount").notNull(),
  description: text("description"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Expense = typeof expenses.$inferSelect;
export type InsertExpense = typeof expenses.$inferInsert;

/**
 * Feeding schedules table
 */
export const feedingSchedules = mysqlTable("feeding_schedules", {
  id: int("id").autoincrement().primaryKey(),
  petId: int("petId").notNull(),
  foodType: varchar("foodType", { length: 100 }).notNull(),
  amount: varchar("amount", { length: 50 }).notNull(),
  frequency: varchar("frequency", { length: 50 }).notNull(),
  time: varchar("time", { length: 50 }),
  notes: text("notes"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type FeedingSchedule = typeof feedingSchedules.$inferSelect;
export type InsertFeedingSchedule = typeof feedingSchedules.$inferInsert;

/**
 * Sick care logs table (Premium feature)
 */
export const sickCareLogs = mysqlTable("sick_care_logs", {
  id: int("id").autoincrement().primaryKey(),
  petId: int("petId").notNull(),
  startDate: timestamp("startDate").notNull(),
  endDate: timestamp("endDate"),
  symptoms: text("symptoms").notNull(),
  medications: text("medications"),
  status: mysqlEnum("status", ["ongoing", "recovered", "monitoring"]).default("ongoing").notNull(),
  notes: text("notes"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type SickCareLog = typeof sickCareLogs.$inferSelect;
export type InsertSickCareLog = typeof sickCareLogs.$inferInsert;

/**
 * Subscriptions table for tier management
 */
export const subscriptions = mysqlTable("subscriptions", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull().unique(),
  tier: mysqlEnum("tier", ["free", "premium"]).default("free").notNull(),
  stripeSubscriptionId: varchar("stripeSubscriptionId", { length: 255 }),
  stripePriceId: varchar("stripePriceId", { length: 255 }),
  startDate: timestamp("startDate").defaultNow().notNull(),
  endDate: timestamp("endDate"),
  status: mysqlEnum("status", ["active", "expired", "cancelled"]).default("active").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Subscription = typeof subscriptions.$inferSelect;
export type InsertSubscription = typeof subscriptions.$inferInsert;

/**
 * Medications table - Flea/Tick and Deworming tracking
 */
export const medications = mysqlTable("medications", {
  id: int("id").autoincrement().primaryKey(),
  petId: int("petId").notNull(),
  medicationType: mysqlEnum("medicationType", ["flea_tick", "deworming", "other"]).notNull(),
  medicationName: varchar("medicationName", { length: 200 }).notNull(),
  lastGivenDate: timestamp("lastGivenDate").notNull(),
  nextDueDate: timestamp("nextDueDate"),
  dosage: varchar("dosage", { length: 100 }),
  frequency: varchar("frequency", { length: 100 }),
  reminderEnabled: int("reminderEnabled").default(1).notNull(),
  notes: text("notes"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Medication = typeof medications.$inferSelect;
export type InsertMedication = typeof medications.$inferInsert;

/**
 * Daily activities table with Instagram integration
 */
export const dailyActivities = mysqlTable("daily_activities", {
  id: int("id").autoincrement().primaryKey(),
  petId: int("petId").notNull(),
  date: timestamp("date").notNull(),
  activityType: varchar("activityType", { length: 100 }).notNull(),
  description: text("description"),
  photoUrls: text("photoUrls"), // JSON array of photo URLs
  instagramPostUrl: varchar("instagramPostUrl", { length: 500 }),
  duration: int("duration"), // in minutes
  location: varchar("location", { length: 200 }),
  notes: text("notes"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type DailyActivity = typeof dailyActivities.$inferSelect;
export type InsertDailyActivity = typeof dailyActivities.$inferInsert;