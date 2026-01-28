import cron from "node-cron";
import { runNotificationJob } from "../notifications";

/**
 * Initialize scheduled jobs
 */
export function initializeScheduler(): void {
  console.log("Initializing scheduler...");

  // Run notification job every day at 9:00 AM
  cron.schedule("0 9 * * *", async () => {
    console.log("Running daily notification job at 9:00 AM");
    await runNotificationJob();
  });

  // Run notification job every day at 6:00 PM as a backup
  cron.schedule("0 18 * * *", async () => {
    console.log("Running daily notification job at 6:00 PM");
    await runNotificationJob();
  });

  console.log("Scheduler initialized with notification jobs");
}

/**
 * Initialize a test job that runs every minute (for development/testing only)
 */
export function initializeTestScheduler(): void {
  if (process.env.NODE_ENV !== "development") {
    console.warn("Test scheduler is only available in development mode");
    return;
  }

  console.log("Initializing test scheduler...");

  // Run notification job every minute for testing
  cron.schedule("* * * * *", async () => {
    console.log("Running test notification job");
    await runNotificationJob();
  });

  console.log("Test scheduler initialized with minute-by-minute notification jobs");
}
