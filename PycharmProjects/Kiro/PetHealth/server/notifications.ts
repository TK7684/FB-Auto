import { eq, and, lt, or } from "drizzle-orm";
import { db, getDb } from "./db";
import {
  vaccinations,
  medications,
  users,
  subscriptions,
} from "../drizzle/schema";
import { addDays, isAfter, subDays } from "date-fns";
import { ENV } from "./_core/env";

// Types for notification
export interface NotificationTemplate {
  subject: string;
  message: string;
  type: "email" | "sms";
}

// Email notification service
export class EmailService {
  static async send(
    to: string,
    subject: string,
    message: string
  ): Promise<boolean> {
    try {
      // In a real implementation, you would use a service like AWS SES, SendGrid, or Nodemailer
      // For this example, we'll just log the notification
      console.log(`[EMAIL] To: ${to}, Subject: ${subject}`);
      console.log(`[EMAIL] Message: ${message}`);

      // If you have an email service configured, uncomment and adapt the code below:
      if (ENV.emailServiceApiKey && ENV.emailFromAddress) {
        const response = await fetch("https://api.emailservice.com/send", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${ENV.emailServiceApiKey}`,
          },
          body: JSON.stringify({
            from: ENV.emailFromAddress,
            to,
            subject,
            message,
          }),
        });

        return response.ok;
      }

      return true;
    } catch (error) {
      console.error("Failed to send email:", error);
      return false;
    }
  }
}

// SMS notification service
export class SMSService {
  static async send(to: string, message: string): Promise<boolean> {
    try {
      // In a real implementation, you would use a service like Twilio, AWS SNS, etc.
      // For this example, we'll just log the notification
      console.log(`[SMS] To: ${to}`);
      console.log(`[SMS] Message: ${message}`);

      // If you have an SMS service configured, uncomment and adapt the code below:
      if (ENV.smsServiceApiKey) {
        const response = await fetch("https://api.smsservice.com/send", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${ENV.smsServiceApiKey}`,
          },
          body: JSON.stringify({
            to,
            message,
          }),
        });

        return response.ok;
      }

      return true;
    } catch (error) {
      console.error("Failed to send SMS:", error);
      return false;
    }
  }
}

// Notification templates
export const NotificationTemplates = {
  vaccinationReminder: (
    petName: string,
    vaccineName: string,
    dueDate: Date
  ): NotificationTemplate => ({
    subject: `แจ้งเตือน: ถึงวันฉีดวัคซีน ${vaccineName} ของ ${petName}`,
    message: `
      เรียน คุณเจ้าของน้อง${petName},

      นี่คือการแจ้งเตือนว่าใกล้ถึงวันที่ต้องฉีดวัคซีน ${vaccineName} แล้ว
      วันที่ครบกำหนด: ${dueDate.toLocaleDateString("th-TH")}

      กรุณานัดหมายกับสัตวแพทย์เพื่อทำการฉีดวัคซีนให้น้อง${petName}

      ขอบคุณที่ใช้บริการ PetHealth

      หมายเหตุ: คุณสามารถปิดการแจ้งเตือนนี้ได้ในหน้าจัดการวัคซีนของสัตว์เลี้ยง
    `,
    type: "email",
  }),

  medicationReminder: (
    petName: string,
    medicationName: string,
    dueDate: Date
  ): NotificationTemplate => ({
    subject: `แจ้งเตือน: ถึงวันที่ต้องให้ยา ${medicationName} แก่ ${petName}`,
    message: `
      เรียน คุณเจ้าของน้อง${petName},

      นี่คือการแจ้งเตือนว่าใกล้ถึงวันที่ต้องให้ยา ${medicationName} แล้ว
      วันที่ครบกำหนด: ${dueDate.toLocaleDateString("th-TH")}

      กรุณาเตรียมยาให้พร้อมสำหรับน้อง${petName}

      ขอบคุณที่ใช้บริการ PetHealth

      หมายเหตุ: คุณสามารถปิดการแจ้งเตือนนี้ได้ในหน้าจัดการยาของสัตว์เลี้ยง
    `,
    type: "email",
  }),

  vaccinationOverdue: (
    petName: string,
    vaccineName: string,
    dueDate: Date
  ): NotificationTemplate => ({
    subject: `แจ้งเตือนฉุกเฉิน: ${vaccineName} ของ ${petName} ล่าช้าแล้ว!`,
    message: `
      เรียน คุณเจ้าของน้อง${petName},

      นี่คือการแจ้งเตือนฉุกเฉินว่า ${vaccineName} ของน้อง${petName} ล่าช้าแล้ว!
      วันที่ครบกำหนด: ${dueDate.toLocaleDateString("th-TH")}
      ปัจจุบัน: ${new Date().toLocaleDateString("th-TH")}

      กรุณานัดหมายกับสัตวแพทย์ทันทีเพื่อทำการฉีดวัคซีนให้น้อง${petName}

      ขอบคุณที่ใช้บริการ PetHealth
    `,
    type: "email",
  }),

  medicationOverdue: (
    petName: string,
    medicationName: string,
    dueDate: Date
  ): NotificationTemplate => ({
    subject: `แจ้งเตือนฉุกเฉิน: การให้ยา ${medicationName} แก่ ${petName} ล่าช้าแล้ว!`,
    message: `
      เรียน คุณเจ้าของน้อง${petName},

      นี่คือการแจ้งเตือนฉุกเฉินว่าการให้ยา ${medicationName} แก่น้อง${petName} ล่าช้าแล้ว!
      วันที่ครบกำหนด: ${dueDate.toLocaleDateString("th-TH")}
      ปัจจุบัน: ${new Date().toLocaleDateString("th-TH")}

      กรุณาให้ยาน้อง${petName}โดยเร็วที่สุดและปรึกษาสัตวแพทย์หากจำเป็น

      ขอบคุณที่ใช้บริการ PetHealth
    `,
    type: "email",
  }),
};

// Main notification service
export class NotificationService {
  /**
   * Process all pending notifications for vaccinations and medications
   * This function should be called periodically (e.g., daily via a cron job)
   */
  static async processAllNotifications(): Promise<void> {
    console.log("Processing notifications...");

    try {
      await this.processVaccinationNotifications();
      await this.processMedicationNotifications();
      console.log("All notifications processed successfully");
    } catch (error) {
      console.error("Error processing notifications:", error);
    }
  }

  /**
   * Process vaccination reminders and overdue notifications
   */
  static async processVaccinationNotifications(): Promise<void> {
    const db = await getDb();
    if (!db) {
      console.warn("Database not available for vaccination notifications");
      return;
    }

    // Get all users with active subscriptions
    const usersWithSubscriptions = await db
      .select({
        user: users,
        subscription: subscriptions,
      })
      .from(users)
      .leftJoin(subscriptions, eq(users.id, subscriptions.userId))
      .where(eq(subscriptions.status, "active"));

    for (const { user, subscription } of usersWithSubscriptions) {
      if (!user.email) continue;

      // Get all pets for this user
      const pets = await db.getUserPets(user.id);

      for (const pet of pets) {
        // Get all vaccinations for this pet with reminders enabled
        const petVaccinations = await db
          .select()
          .from(vaccinations)
          .where(
            and(
              eq(vaccinations.petId, pet.id),
              eq(vaccinations.reminderEnabled, 1),
              // Only include vaccinations with a next due date
              // that is either 7 days from now or already past due
              or(
                // Notifications for upcoming vaccinations (7 days before)
                and(
                  eq(vaccinations.reminderEnabled, 1)
                  // nextDate is within the next 7 days
                  // Note: We're using raw SQL here for complex date comparisons
                  // In a production app, you might want to use a more robust approach
                ),
                // Notifications for overdue vaccinations
                and(
                  eq(vaccinations.reminderEnabled, 1)
                  // nextDate is before today
                  // Note: We're using raw SQL here for complex date comparisons
                )
              )
            )
          );

        for (const vaccination of petVaccinations) {
          if (!vaccination.nextDate) continue;

          const today = new Date();
          const dueDate = new Date(vaccination.nextDate);

          // Check if vaccination is overdue (due date is in the past)
          if (dueDate < today) {
            const template = NotificationTemplates.vaccinationOverdue(
              pet.name,
              vaccination.vaccineName,
              dueDate
            );

            // Send email notification
            await EmailService.send(
              user.email,
              template.subject,
              template.message
            );

            console.log(
              `Sent overdue vaccination notification to ${user.email} for ${pet.name}'s ${vaccination.vaccineName}`
            );
          }
          // Check if vaccination is due within the next 7 days
          else if (dueDate <= addDays(today, 7)) {
            const template = NotificationTemplates.vaccinationReminder(
              pet.name,
              vaccination.vaccineName,
              dueDate
            );

            // Send email notification
            await EmailService.send(
              user.email,
              template.subject,
              template.message
            );

            console.log(
              `Sent vaccination reminder to ${user.email} for ${pet.name}'s ${vaccination.vaccineName}`
            );
          }
        }
      }
    }
  }

  /**
   * Process medication reminders and overdue notifications
   */
  static async processMedicationNotifications(): Promise<void> {
    const db = await getDb();
    if (!db) {
      console.warn("Database not available for medication notifications");
      return;
    }

    // Get all users with active subscriptions
    const usersWithSubscriptions = await db
      .select({
        user: users,
        subscription: subscriptions,
      })
      .from(users)
      .leftJoin(subscriptions, eq(users.id, subscriptions.userId))
      .where(eq(subscriptions.status, "active"));

    for (const { user, subscription } of usersWithSubscriptions) {
      if (!user.email) continue;

      // Get all pets for this user
      const pets = await db.getUserPets(user.id);

      for (const pet of pets) {
        // Get all medications for this pet with reminders enabled
        const petMedications = await db
          .select()
          .from(medications)
          .where(
            and(
              eq(medications.petId, pet.id),
              eq(medications.reminderEnabled, 1)
            )
          );

        for (const medication of petMedications) {
          if (!medication.nextDueDate) continue;

          const today = new Date();
          const dueDate = new Date(medication.nextDueDate);

          // Check if medication is overdue (due date is in the past)
          if (dueDate < today) {
            const template = NotificationTemplates.medicationOverdue(
              pet.name,
              medication.medicationName,
              dueDate
            );

            // Send email notification
            await EmailService.send(
              user.email,
              template.subject,
              template.message
            );

            console.log(
              `Sent overdue medication notification to ${user.email} for ${pet.name}'s ${medication.medicationName}`
            );
          }
          // Check if medication is due within the next 3 days
          else if (dueDate <= addDays(today, 3)) {
            const template = NotificationTemplates.medicationReminder(
              pet.name,
              medication.medicationName,
              dueDate
            );

            // Send email notification
            await EmailService.send(
              user.email,
              template.subject,
              template.message
            );

            console.log(
              `Sent medication reminder to ${user.email} for ${pet.name}'s ${medication.medicationName}`
            );
          }
        }
      }
    }
  }

  /**
   * Send a custom notification to a user
   */
  static async sendCustomNotification(
    userId: number,
    template: NotificationTemplate
  ): Promise<boolean> {
    const db = await getDb();
    if (!db) return false;

    const user = await db.getUserByOpenId(userId.toString());
    if (!user || !user.email) return false;

    let success = false;

    if (template.type === "email") {
      success = await EmailService.send(
        user.email,
        template.subject,
        template.message
      );
    } else if (template.type === "sms" && user.phone) {
      success = await SMSService.send(user.phone, template.message);
    }

    return success;
  }
}

// Export a function that can be called by a scheduled job
export async function runNotificationJob(): Promise<void> {
  console.log("Starting notification job...");
  await NotificationService.processAllNotifications();
  console.log("Notification job completed");
}
