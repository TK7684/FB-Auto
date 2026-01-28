import { eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { InsertUser, users } from "../drizzle/schema";
import { ENV } from "./_core/env";

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = "admin";
      updateSet.role = "admin";
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db
    .select()
    .from(users)
    .where(eq(users.openId, openId))
    .limit(1);

  return result.length > 0 ? result[0] : undefined;
}

// ========== Pet Queries ==========
import {
  pets,
  Pet,
  InsertPet,
  healthRecords,
  HealthRecord,
  InsertHealthRecord,
  vaccinations,
  Vaccination,
  InsertVaccination,
  behaviorLogs,
  BehaviorLog,
  InsertBehaviorLog,
  weightRecords,
  WeightRecord,
  InsertWeightRecord,
  expenses,
  Expense,
  InsertExpense,
  feedingSchedules,
  FeedingSchedule,
  InsertFeedingSchedule,
  sickCareLogs,
  SickCareLog,
  InsertSickCareLog,
  subscriptions,
  Subscription,
  InsertSubscription,
  medications,
  Medication,
  InsertMedication,
  dailyActivities,
  DailyActivity,
  InsertDailyActivity,
} from "../drizzle/schema";
import { and, desc } from "drizzle-orm";

export async function getUserPets(userId: number): Promise<Pet[]> {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(pets)
    .where(eq(pets.userId, userId))
    .orderBy(desc(pets.createdAt));
}

export async function getPetById(
  petId: number,
  userId: number
): Promise<Pet | undefined> {
  const db = await getDb();
  if (!db) return undefined;
  const result = await db
    .select()
    .from(pets)
    .where(and(eq(pets.id, petId), eq(pets.userId, userId)))
    .limit(1);
  return result[0];
}

export async function createPet(pet: InsertPet): Promise<Pet> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const result = await db.insert(pets).values(pet);
  const newPet = await db
    .select()
    .from(pets)
    .where(eq(pets.id, Number(result[0].insertId)))
    .limit(1);
  return newPet[0]!;
}

export async function updatePet(
  petId: number,
  userId: number,
  data: Partial<InsertPet>
): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db
    .update(pets)
    .set(data)
    .where(and(eq(pets.id, petId), eq(pets.userId, userId)));
}

export async function deletePet(petId: number, userId: number): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.delete(pets).where(and(eq(pets.id, petId), eq(pets.userId, userId)));
}

// ========== Health Record Queries ==========

export async function getHealthRecords(petId: number): Promise<HealthRecord[]> {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(healthRecords)
    .where(eq(healthRecords.petId, petId))
    .orderBy(desc(healthRecords.date));
}

export async function createHealthRecord(
  record: InsertHealthRecord
): Promise<HealthRecord> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const result = await db.insert(healthRecords).values(record);
  const newRecord = await db
    .select()
    .from(healthRecords)
    .where(eq(healthRecords.id, Number(result[0].insertId)))
    .limit(1);
  return newRecord[0]!;
}

export async function deleteHealthRecord(recordId: number): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.delete(healthRecords).where(eq(healthRecords.id, recordId));
}

export async function countHealthRecordsThisMonth(
  petId: number
): Promise<number> {
  const db = await getDb();
  if (!db) return 0;
  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const result = await db
    .select()
    .from(healthRecords)
    .where(and(eq(healthRecords.petId, petId), desc(healthRecords.createdAt)));
  return result.filter(r => new Date(r.createdAt) >= startOfMonth).length;
}

// ========== Vaccination Queries ==========

export async function getVaccinations(petId: number): Promise<Vaccination[]> {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(vaccinations)
    .where(eq(vaccinations.petId, petId))
    .orderBy(desc(vaccinations.lastDate));
}

export async function createVaccination(
  vaccination: InsertVaccination
): Promise<Vaccination> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const result = await db.insert(vaccinations).values(vaccination);
  const newVaccination = await db
    .select()
    .from(vaccinations)
    .where(eq(vaccinations.id, Number(result[0].insertId)))
    .limit(1);
  return newVaccination[0]!;
}

export async function updateVaccination(
  vaccinationId: number,
  data: Partial<InsertVaccination>
): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db
    .update(vaccinations)
    .set(data)
    .where(eq(vaccinations.id, vaccinationId));
}

export async function deleteVaccination(vaccinationId: number): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.delete(vaccinations).where(eq(vaccinations.id, vaccinationId));
}

// ========== Behavior Log Queries ==========

export async function getBehaviorLogs(petId: number): Promise<BehaviorLog[]> {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(behaviorLogs)
    .where(eq(behaviorLogs.petId, petId))
    .orderBy(desc(behaviorLogs.date));
}

export async function createBehaviorLog(
  log: InsertBehaviorLog
): Promise<BehaviorLog> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const result = await db.insert(behaviorLogs).values(log);
  const newLog = await db
    .select()
    .from(behaviorLogs)
    .where(eq(behaviorLogs.id, Number(result[0].insertId)))
    .limit(1);
  return newLog[0]!;
}

export async function deleteBehaviorLog(logId: number): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.delete(behaviorLogs).where(eq(behaviorLogs.id, logId));
}

export async function countBehaviorLogsThisMonth(
  petId: number
): Promise<number> {
  const db = await getDb();
  if (!db) return 0;
  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const result = await db
    .select()
    .from(behaviorLogs)
    .where(and(eq(behaviorLogs.petId, petId), desc(behaviorLogs.createdAt)));
  return result.filter(r => new Date(r.createdAt) >= startOfMonth).length;
}

// ========== Weight Record Queries ==========

export async function getWeightRecords(petId: number): Promise<WeightRecord[]> {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(weightRecords)
    .where(eq(weightRecords.petId, petId))
    .orderBy(desc(weightRecords.date));
}

export async function createWeightRecord(
  record: InsertWeightRecord
): Promise<WeightRecord> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const result = await db.insert(weightRecords).values(record);
  const newRecord = await db
    .select()
    .from(weightRecords)
    .where(eq(weightRecords.id, Number(result[0].insertId)))
    .limit(1);
  return newRecord[0]!;
}

export async function deleteWeightRecord(recordId: number): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.delete(weightRecords).where(eq(weightRecords.id, recordId));
}

// ========== Expense Queries (Premium) ==========

export async function getExpenses(petId: number): Promise<Expense[]> {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(expenses)
    .where(eq(expenses.petId, petId))
    .orderBy(desc(expenses.date));
}

export async function createExpense(expense: InsertExpense): Promise<Expense> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const result = await db.insert(expenses).values(expense);
  const newExpense = await db
    .select()
    .from(expenses)
    .where(eq(expenses.id, Number(result[0].insertId)))
    .limit(1);
  return newExpense[0]!;
}

export async function deleteExpense(expenseId: number): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.delete(expenses).where(eq(expenses.id, expenseId));
}

// ========== Feeding Schedule Queries ==========

export async function getFeedingSchedules(
  petId: number
): Promise<FeedingSchedule[]> {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(feedingSchedules)
    .where(eq(feedingSchedules.petId, petId))
    .orderBy(desc(feedingSchedules.createdAt));
}

export async function createFeedingSchedule(
  schedule: InsertFeedingSchedule
): Promise<FeedingSchedule> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const result = await db.insert(feedingSchedules).values(schedule);
  const newSchedule = await db
    .select()
    .from(feedingSchedules)
    .where(eq(feedingSchedules.id, Number(result[0].insertId)))
    .limit(1);
  return newSchedule[0]!;
}

export async function updateFeedingSchedule(
  scheduleId: number,
  data: Partial<InsertFeedingSchedule>
): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db
    .update(feedingSchedules)
    .set(data)
    .where(eq(feedingSchedules.id, scheduleId));
}

export async function deleteFeedingSchedule(scheduleId: number): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.delete(feedingSchedules).where(eq(feedingSchedules.id, scheduleId));
}

// ========== Sick Care Log Queries (Premium) ==========

export async function getSickCareLogs(petId: number): Promise<SickCareLog[]> {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(sickCareLogs)
    .where(eq(sickCareLogs.petId, petId))
    .orderBy(desc(sickCareLogs.startDate));
}

export async function createSickCareLog(
  log: InsertSickCareLog
): Promise<SickCareLog> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const result = await db.insert(sickCareLogs).values(log);
  const newLog = await db
    .select()
    .from(sickCareLogs)
    .where(eq(sickCareLogs.id, Number(result[0].insertId)))
    .limit(1);
  return newLog[0]!;
}

export async function updateSickCareLog(
  logId: number,
  data: Partial<InsertSickCareLog>
): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.update(sickCareLogs).set(data).where(eq(sickCareLogs.id, logId));
}

export async function deleteSickCareLog(logId: number): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.delete(sickCareLogs).where(eq(sickCareLogs.id, logId));
}

// ========== Subscription Queries ==========

export async function getUserSubscription(
  userId: number
): Promise<Subscription | undefined> {
  const db = await getDb();
  if (!db) return undefined;
  const result = await db
    .select()
    .from(subscriptions)
    .where(eq(subscriptions.userId, userId))
    .limit(1);
  return result[0];
}

export async function createSubscription(
  subscription: InsertSubscription
): Promise<Subscription> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const result = await db.insert(subscriptions).values(subscription);
  const newSubscription = await db
    .select()
    .from(subscriptions)
    .where(eq(subscriptions.id, Number(result[0].insertId)))
    .limit(1);
  return newSubscription[0]!;
}

export async function updateSubscription(
  userId: number,
  data: Partial<InsertSubscription>
): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db
    .update(subscriptions)
    .set(data)
    .where(eq(subscriptions.userId, userId));
}

// ========== Medication Queries ==========

export async function getMedications(petId: number): Promise<Medication[]> {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(medications)
    .where(eq(medications.petId, petId))
    .orderBy(desc(medications.lastGivenDate));
}

export async function createMedication(
  medication: InsertMedication
): Promise<Medication> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const result = await db.insert(medications).values(medication);
  const newMedication = await db
    .select()
    .from(medications)
    .where(eq(medications.id, Number(result[0].insertId)))
    .limit(1);
  return newMedication[0]!;
}

export async function getMedicationById(
  medicationId: number
): Promise<Medication | undefined> {
  const db = await getDb();
  if (!db) return undefined;
  const result = await db
    .select()
    .from(medications)
    .where(eq(medications.id, medicationId))
    .limit(1);
  return result[0];
}

export async function updateMedication(
  medicationId: number,
  data: Partial<InsertMedication>
): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db
    .update(medications)
    .set(data)
    .where(eq(medications.id, medicationId));
}

export async function deleteMedication(medicationId: number): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.delete(medications).where(eq(medications.id, medicationId));
}

// ========== Daily Activity Queries ==========

export async function getDailyActivities(
  petId: number
): Promise<DailyActivity[]> {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(dailyActivities)
    .where(eq(dailyActivities.petId, petId))
    .orderBy(desc(dailyActivities.date));
}

export async function createDailyActivity(
  activity: InsertDailyActivity
): Promise<DailyActivity> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  const result = await db.insert(dailyActivities).values(activity);
  const newActivity = await db
    .select()
    .from(dailyActivities)
    .where(eq(dailyActivities.id, Number(result[0].insertId)))
    .limit(1);
  return newActivity[0]!;
}

export async function getDailyActivityById(
  activityId: number
): Promise<DailyActivity | undefined> {
  const db = await getDb();
  if (!db) return undefined;
  const result = await db
    .select()
    .from(dailyActivities)
    .where(eq(dailyActivities.id, activityId))
    .limit(1);
  return result[0];
}

export async function updateDailyActivity(
  activityId: number,
  data: Partial<InsertDailyActivity>
): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db
    .update(dailyActivities)
    .set(data)
    .where(eq(dailyActivities.id, activityId));
}

export async function deleteDailyActivity(activityId: number): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  await db.delete(dailyActivities).where(eq(dailyActivities.id, activityId));
}

// ========== Storage Queries ==========

export async function getUploadUrl(
  fileName: string,
  fileType: string
): Promise<{ uploadUrl: string; fileUrl: string }> {
  // Import storage module
  const storage = await import("./storage");
  return storage.getUploadUrl(fileName, fileType);
}
