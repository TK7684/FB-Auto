import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { protectedProcedure, publicProcedure, router } from "./_core/trpc";
import { z } from "zod";
import * as db from "./db";
import { TRPCError } from "@trpc/server";
import { NotificationService } from "./notifications";

export const appRouter = router({
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  // Pet management procedures
  pets: router({
    list: protectedProcedure.query(async ({ ctx }) => {
      return db.getUserPets(ctx.user.id);
    }),

    getById: protectedProcedure
      .input(z.object({ petId: z.number() }))
      .query(async ({ ctx, input }) => {
        const pet = await db.getPetById(input.petId, ctx.user.id);
        if (!pet) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Pet not found" });
        }
        return pet;
      }),

    create: protectedProcedure
      .input(
        z.object({
          name: z.string().min(1),
          breed: z.string().optional(),
          birthDate: z.string().optional(),
          photoUrl: z.string().optional(),
          gender: z.enum(["male", "female", "unknown"]).optional(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        // Check tier limits
        const subscription = await db.getUserSubscription(ctx.user.id);
        const tier = subscription?.tier || "free";

        if (tier === "free") {
          const existingPets = await db.getUserPets(ctx.user.id);
          if (existingPets.length >= 1) {
            throw new TRPCError({
              code: "FORBIDDEN",
              message:
                "Free tier allows only 1 pet. Upgrade to Premium for unlimited pets.",
            });
          }
        }

        return db.createPet({
          userId: ctx.user.id,
          name: input.name,
          breed: input.breed || null,
          birthDate: input.birthDate ? new Date(input.birthDate) : null,
          photoUrl: input.photoUrl || null,
          gender: input.gender || "unknown",
        });
      }),

    update: protectedProcedure
      .input(
        z.object({
          petId: z.number(),
          name: z.string().min(1).optional(),
          breed: z.string().optional(),
          birthDate: z.string().optional(),
          photoUrl: z.string().optional(),
          gender: z.enum(["male", "female", "unknown"]).optional(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        const { petId, ...data } = input;
        const updateData: any = {};
        if (data.name) updateData.name = data.name;
        if (data.breed !== undefined) updateData.breed = data.breed || null;
        if (data.birthDate !== undefined)
          updateData.birthDate = data.birthDate
            ? new Date(data.birthDate)
            : null;
        if (data.photoUrl !== undefined)
          updateData.photoUrl = data.photoUrl || null;
        if (data.gender) updateData.gender = data.gender;

        await db.updatePet(petId, ctx.user.id, updateData);
        return { success: true };
      }),

    delete: protectedProcedure
      .input(z.object({ petId: z.number() }))
      .mutation(async ({ ctx, input }) => {
        await db.deletePet(input.petId, ctx.user.id);
        return { success: true };
      }),
  }),

  // Health records procedures
  healthRecords: router({
    list: protectedProcedure
      .input(z.object({ petId: z.number() }))
      .query(async ({ input }) => {
        return db.getHealthRecords(input.petId);
      }),

    create: protectedProcedure
      .input(
        z.object({
          petId: z.number(),
          recordType: z.string(),
          date: z.string(),
          notes: z.string().optional(),
          attachmentUrl: z.string().optional(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        // Check tier limits
        const subscription = await db.getUserSubscription(ctx.user.id);
        const tier = subscription?.tier || "free";

        if (tier === "free") {
          const count = await db.countHealthRecordsThisMonth(input.petId);
          if (count >= 10) {
            throw new TRPCError({
              code: "FORBIDDEN",
              message:
                "Free tier allows 10 health records per month. Upgrade to Premium for unlimited records.",
            });
          }
        }

        return db.createHealthRecord({
          petId: input.petId,
          recordType: input.recordType,
          date: new Date(input.date),
          notes: input.notes || null,
          attachmentUrl: input.attachmentUrl || null,
        });
      }),

    delete: protectedProcedure
      .input(z.object({ recordId: z.number() }))
      .mutation(async ({ input }) => {
        await db.deleteHealthRecord(input.recordId);
        return { success: true };
      }),
  }),

  // Vaccination procedures
  vaccinations: router({
    list: protectedProcedure
      .input(z.object({ petId: z.number() }))
      .query(async ({ input }) => {
        return db.getVaccinations(input.petId);
      }),

    create: protectedProcedure
      .input(
        z.object({
          petId: z.number(),
          vaccineName: z.string(),
          lastDate: z.string(),
          nextDate: z.string().optional(),
          reminderEnabled: z.number().optional(),
          notes: z.string().optional(),
        })
      )
      .mutation(async ({ input }) => {
        return db.createVaccination({
          petId: input.petId,
          vaccineName: input.vaccineName,
          lastDate: new Date(input.lastDate),
          nextDate: input.nextDate ? new Date(input.nextDate) : null,
          reminderEnabled: input.reminderEnabled ?? 1,
          notes: input.notes || null,
        });
      }),

    update: protectedProcedure
      .input(
        z.object({
          vaccinationId: z.number(),
          vaccineName: z.string().optional(),
          lastDate: z.string().optional(),
          nextDate: z.string().optional(),
          reminderEnabled: z.number().optional(),
          notes: z.string().optional(),
        })
      )
      .mutation(async ({ input }) => {
        const { vaccinationId, ...data } = input;
        const updateData: any = {};
        if (data.vaccineName) updateData.vaccineName = data.vaccineName;
        if (data.lastDate) updateData.lastDate = new Date(data.lastDate);
        if (data.nextDate !== undefined)
          updateData.nextDate = data.nextDate ? new Date(data.nextDate) : null;
        if (data.reminderEnabled !== undefined)
          updateData.reminderEnabled = data.reminderEnabled;
        if (data.notes !== undefined) updateData.notes = data.notes || null;

        await db.updateVaccination(vaccinationId, updateData);
        return { success: true };
      }),

    delete: protectedProcedure
      .input(z.object({ vaccinationId: z.number() }))
      .mutation(async ({ input }) => {
        await db.deleteVaccination(input.vaccinationId);
        return { success: true };
      }),
  }),

  // Behavior logs procedures
  behaviorLogs: router({
    list: protectedProcedure
      .input(z.object({ petId: z.number() }))
      .query(async ({ input }) => {
        return db.getBehaviorLogs(input.petId);
      }),

    create: protectedProcedure
      .input(
        z.object({
          petId: z.number(),
          date: z.string(),
          behaviorType: z.string(),
          notes: z.string().optional(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        // Check tier limits
        const subscription = await db.getUserSubscription(ctx.user.id);
        const tier = subscription?.tier || "free";

        if (tier === "free") {
          const count = await db.countBehaviorLogsThisMonth(input.petId);
          if (count >= 5) {
            throw new TRPCError({
              code: "FORBIDDEN",
              message:
                "Free tier allows 5 behavior logs per month. Upgrade to Premium for unlimited logs.",
            });
          }
        }

        return db.createBehaviorLog({
          petId: input.petId,
          date: new Date(input.date),
          behaviorType: input.behaviorType,
          notes: input.notes || null,
        });
      }),

    delete: protectedProcedure
      .input(z.object({ logId: z.number() }))
      .mutation(async ({ input }) => {
        await db.deleteBehaviorLog(input.logId);
        return { success: true };
      }),
  }),

  // Weight records procedures
  weightRecords: router({
    list: protectedProcedure
      .input(z.object({ petId: z.number() }))
      .query(async ({ input }) => {
        return db.getWeightRecords(input.petId);
      }),

    create: protectedProcedure
      .input(
        z.object({
          petId: z.number(),
          date: z.string(),
          weight: z.number(),
          unit: z.string().optional(),
        })
      )
      .mutation(async ({ input }) => {
        return db.createWeightRecord({
          petId: input.petId,
          date: new Date(input.date),
          weight: input.weight,
          unit: input.unit || "kg",
        });
      }),

    delete: protectedProcedure
      .input(z.object({ recordId: z.number() }))
      .mutation(async ({ input }) => {
        await db.deleteWeightRecord(input.recordId);
        return { success: true };
      }),
  }),

  // Expenses procedures (Premium feature)
  expenses: router({
    list: protectedProcedure
      .input(z.object({ petId: z.number() }))
      .query(async ({ ctx, input }) => {
        const subscription = await db.getUserSubscription(ctx.user.id);
        const tier = subscription?.tier || "free";

        if (tier === "free") {
          throw new TRPCError({
            code: "FORBIDDEN",
            message:
              "Expense tracking is a Premium feature. Please upgrade to access this feature.",
          });
        }

        return db.getExpenses(input.petId);
      }),

    create: protectedProcedure
      .input(
        z.object({
          petId: z.number(),
          date: z.string(),
          category: z.string(),
          amount: z.number(),
          description: z.string().optional(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        const subscription = await db.getUserSubscription(ctx.user.id);
        const tier = subscription?.tier || "free";

        if (tier === "free") {
          throw new TRPCError({
            code: "FORBIDDEN",
            message:
              "Expense tracking is a Premium feature. Please upgrade to access this feature.",
          });
        }

        return db.createExpense({
          petId: input.petId,
          date: new Date(input.date),
          category: input.category,
          amount: input.amount,
          description: input.description || null,
        });
      }),

    delete: protectedProcedure
      .input(z.object({ expenseId: z.number() }))
      .mutation(async ({ ctx, input }) => {
        const subscription = await db.getUserSubscription(ctx.user.id);
        const tier = subscription?.tier || "free";

        if (tier === "free") {
          throw new TRPCError({
            code: "FORBIDDEN",
            message:
              "Expense tracking is a Premium feature. Please upgrade to access this feature.",
          });
        }

        await db.deleteExpense(input.expenseId);
        return { success: true };
      }),
  }),

  // Feeding schedules procedures
  feedingSchedules: router({
    list: protectedProcedure
      .input(z.object({ petId: z.number() }))
      .query(async ({ input }) => {
        return db.getFeedingSchedules(input.petId);
      }),

    create: protectedProcedure
      .input(
        z.object({
          petId: z.number(),
          foodType: z.string(),
          amount: z.string(),
          frequency: z.string(),
          time: z.string().optional(),
          notes: z.string().optional(),
        })
      )
      .mutation(async ({ input }) => {
        return db.createFeedingSchedule({
          petId: input.petId,
          foodType: input.foodType,
          amount: input.amount,
          frequency: input.frequency,
          time: input.time || null,
          notes: input.notes || null,
        });
      }),

    update: protectedProcedure
      .input(
        z.object({
          scheduleId: z.number(),
          foodType: z.string().optional(),
          amount: z.string().optional(),
          frequency: z.string().optional(),
          time: z.string().optional(),
          notes: z.string().optional(),
        })
      )
      .mutation(async ({ input }) => {
        const { scheduleId, ...data } = input;
        const updateData: any = {};
        if (data.foodType) updateData.foodType = data.foodType;
        if (data.amount) updateData.amount = data.amount;
        if (data.frequency) updateData.frequency = data.frequency;
        if (data.time !== undefined) updateData.time = data.time || null;
        if (data.notes !== undefined) updateData.notes = data.notes || null;

        await db.updateFeedingSchedule(scheduleId, updateData);
        return { success: true };
      }),

    delete: protectedProcedure
      .input(z.object({ scheduleId: z.number() }))
      .mutation(async ({ input }) => {
        await db.deleteFeedingSchedule(input.scheduleId);
        return { success: true };
      }),
  }),

  // Sick care logs procedures (Premium feature)
  sickCareLogs: router({
    list: protectedProcedure
      .input(z.object({ petId: z.number() }))
      .query(async ({ ctx, input }) => {
        const subscription = await db.getUserSubscription(ctx.user.id);
        const tier = subscription?.tier || "free";

        if (tier === "free") {
          throw new TRPCError({
            code: "FORBIDDEN",
            message:
              "Sick care management is a Premium feature. Please upgrade to access this feature.",
          });
        }

        return db.getSickCareLogs(input.petId);
      }),

    create: protectedProcedure
      .input(
        z.object({
          petId: z.number(),
          startDate: z.string(),
          endDate: z.string().optional(),
          symptoms: z.string(),
          medications: z.string().optional(),
          status: z.enum(["ongoing", "recovered", "monitoring"]).optional(),
          notes: z.string().optional(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        const subscription = await db.getUserSubscription(ctx.user.id);
        const tier = subscription?.tier || "free";

        if (tier === "free") {
          throw new TRPCError({
            code: "FORBIDDEN",
            message:
              "Sick care management is a Premium feature. Please upgrade to access this feature.",
          });
        }

        return db.createSickCareLog({
          petId: input.petId,
          startDate: new Date(input.startDate),
          endDate: input.endDate ? new Date(input.endDate) : null,
          symptoms: input.symptoms,
          medications: input.medications || null,
          status: input.status || "ongoing",
          notes: input.notes || null,
        });
      }),

    update: protectedProcedure
      .input(
        z.object({
          logId: z.number(),
          endDate: z.string().optional(),
          symptoms: z.string().optional(),
          medications: z.string().optional(),
          status: z.enum(["ongoing", "recovered", "monitoring"]).optional(),
          notes: z.string().optional(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        const subscription = await db.getUserSubscription(ctx.user.id);
        const tier = subscription?.tier || "free";

        if (tier === "free") {
          throw new TRPCError({
            code: "FORBIDDEN",
            message:
              "Sick care management is a Premium feature. Please upgrade to access this feature.",
          });
        }

        const { logId, ...data } = input;
        const updateData: any = {};
        if (data.endDate !== undefined)
          updateData.endDate = data.endDate ? new Date(data.endDate) : null;
        if (data.symptoms) updateData.symptoms = data.symptoms;
        if (data.medications !== undefined)
          updateData.medications = data.medications || null;
        if (data.status) updateData.status = data.status;
        if (data.notes !== undefined) updateData.notes = data.notes || null;

        await db.updateSickCareLog(logId, updateData);
        return { success: true };
      }),

    delete: protectedProcedure
      .input(z.object({ logId: z.number() }))
      .mutation(async ({ ctx, input }) => {
        const subscription = await db.getUserSubscription(ctx.user.id);
        const tier = subscription?.tier || "free";

        if (tier === "free") {
          throw new TRPCError({
            code: "FORBIDDEN",
            message:
              "Sick care management is a Premium feature. Please upgrade to access this feature.",
          });
        }

        await db.deleteSickCareLog(input.logId);
        return { success: true };
      }),
  }),

  // Subscription procedures
  subscription: router({
    get: protectedProcedure.query(async ({ ctx }) => {
      let subscription = await db.getUserSubscription(ctx.user.id);

      // Create default free subscription if not exists
      if (!subscription) {
        subscription = await db.createSubscription({
          userId: ctx.user.id,
          tier: "free",
          status: "active",
        });
      }

      return subscription;
    }),

    upgrade: protectedProcedure.mutation(async ({ ctx }) => {
      const subscription = await db.getUserSubscription(ctx.user.id);

      if (subscription) {
        await db.updateSubscription(ctx.user.id, {
          tier: "premium",
          status: "active",
          endDate: null,
        });
      } else {
        await db.createSubscription({
          userId: ctx.user.id,
          tier: "premium",
          status: "active",
        });
      }

      return { success: true, message: "Successfully upgraded to Premium!" };
    }),

    createCheckoutSession: protectedProcedure
      .input(
        z.object({
          priceId: z.string(),
          successUrl: z.string(),
          cancelUrl: z.string(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        const { createCheckoutSession } = await import("../stripe");
        const { sessionId, url } = await createCheckoutSession(
          ctx.user.id,
          input.priceId,
          input.successUrl,
          input.cancelUrl
        );
        return { sessionId, url };
      }),

    createCustomerPortalSession: protectedProcedure
      .input(z.object({ returnUrl: z.string() }))
      .mutation(async ({ ctx, input }) => {
        const { createCustomerPortalSession } = await import("../stripe");
        const { url } = await createCustomerPortalSession(
          ctx.user.id,
          input.returnUrl
        );
        return { url };
      }),
  }),

  // Medications management procedures
  medications: router({
    list: protectedProcedure.query(async ({ ctx }) => {
      const pets = await db.getUserPets(ctx.user.id);
      const petIds = pets.map(pet => pet.id);

      const allMedications = [];
      for (const petId of petIds) {
        const medications = await db.getMedications(petId);
        allMedications.push(...medications);
      }

      return allMedications;
    }),

    create: protectedProcedure
      .input(
        z.object({
          petId: z.number(),
          medicationType: z.enum(["flea_tick", "deworming", "other"]),
          medicationName: z.string().min(1),
          lastGivenDate: z.date(),
          nextDueDate: z.date().optional(),
          dosage: z.string().optional(),
          frequency: z.string().optional(),
          reminderEnabled: z.boolean().default(true),
          notes: z.string().optional(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        // Verify user owns the pet
        const pet = await db.getPetById(input.petId, ctx.user.id);
        if (!pet) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Pet not found" });
        }

        return db.createMedication(input);
      }),

    update: protectedProcedure
      .input(
        z.object({
          medicationId: z.number(),
          petId: z.number(),
          medicationType: z.enum(["flea_tick", "deworming", "other"]),
          medicationName: z.string().min(1),
          lastGivenDate: z.date(),
          nextDueDate: z.date().optional(),
          dosage: z.string().optional(),
          frequency: z.string().optional(),
          reminderEnabled: z.boolean(),
          notes: z.string().optional(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        // Verify user owns the pet
        const pet = await db.getPetById(input.petId, ctx.user.id);
        if (!pet) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Pet not found" });
        }

        const { medicationId, ...data } = input;
        await db.updateMedication(medicationId, data);
        return { success: true };
      }),

    delete: protectedProcedure
      .input(z.object({ medicationId: z.number() }))
      .mutation(async ({ ctx, input }) => {
        // Verify medication belongs to user's pet
        const medication = await db.getMedicationById(input.medicationId);
        if (!medication) {
          throw new TRPCError({
            code: "NOT_FOUND",
            message: "Medication not found",
          });
        }

        const pet = await db.getPetById(medication.petId, ctx.user.id);
        if (!pet) {
          throw new TRPCError({
            code: "FORBIDDEN",
            message: "You don't have permission to delete this medication",
          });
        }

        await db.deleteMedication(input.medicationId);
        return { success: true };
      }),
  }),

  // Daily activities management procedures
  dailyActivities: router({
    list: protectedProcedure.query(async ({ ctx }) => {
      const pets = await db.getUserPets(ctx.user.id);
      const petIds = pets.map(pet => pet.id);

      const allActivities = [];
      for (const petId of petIds) {
        const activities = await db.getDailyActivities(petId);
        allActivities.push(...activities);
      }

      return allActivities.sort(
        (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
      );
    }),

    create: protectedProcedure
      .input(
        z.object({
          petId: z.number(),
          date: z.date(),
          activityType: z.string(),
          description: z.string().min(1),
          photoUrls: z.string().optional(),
          instagramPostUrl: z.string().optional(),
          duration: z.number().optional(),
          location: z.string().optional(),
          notes: z.string().optional(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        // Verify user owns the pet
        const pet = await db.getPetById(input.petId, ctx.user.id);
        if (!pet) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Pet not found" });
        }

        return db.createDailyActivity(input);
      }),

    update: protectedProcedure
      .input(
        z.object({
          activityId: z.number(),
          petId: z.number(),
          date: z.date(),
          activityType: z.string(),
          description: z.string().min(1),
          photoUrls: z.string().optional(),
          instagramPostUrl: z.string().optional(),
          duration: z.number().optional(),
          location: z.string().optional(),
          notes: z.string().optional(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        // Verify user owns the pet
        const pet = await db.getPetById(input.petId, ctx.user.id);
        if (!pet) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Pet not found" });
        }

        const { activityId, ...data } = input;
        await db.updateDailyActivity(activityId, data);
        return { success: true };
      }),

    delete: protectedProcedure
      .input(z.object({ activityId: z.number() }))
      .mutation(async ({ ctx, input }) => {
        // Verify activity belongs to user's pet
        const activity = await db.getDailyActivityById(input.activityId);
        if (!activity) {
          throw new TRPCError({
            code: "NOT_FOUND",
            message: "Activity not found",
          });
        }

        const pet = await db.getPetById(activity.petId, ctx.user.id);
        if (!pet) {
          throw new TRPCError({
            code: "FORBIDDEN",
            message: "You don't have permission to delete this activity",
          });
        }

        await db.deleteDailyActivity(input.activityId);
        return { success: true };
      }),
  }),

  // Storage procedures
  storage: router({
    getUploadUrl: protectedProcedure
      .input(
        z.object({
          fileName: z.string(),
          fileType: z.string(),
          folder: z.string().optional(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        // Generate a unique file name
        const timestamp = Date.now();
        const randomString = Math.random().toString(36).substring(2, 15);
        const extension = input.fileName.split(".").pop();
        const uniqueFileName = `${input.folder || "uploads"}/${timestamp}-${randomString}.${extension}`;

        // Get upload URL from S3 storage
        const { uploadUrl, fileUrl } = await db.getUploadUrl(
          uniqueFileName,
          input.fileType
        );

        return { uploadUrl, fileUrl };
      }),
  }),

  // Notification management procedures
  notifications: router({
    sendTest: protectedProcedure
      .input(
        z.object({
          type: z.enum(["vaccination", "medication"]),
          userId: z.number(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        if (ctx.user.role !== "admin") {
          throw new TRPCError({
            code: "FORBIDDEN",
            message: "Only admins can send test notifications",
          });
        }

        try {
          // For testing, just process all notifications
          await NotificationService.processAllNotifications();
          return { success: true, message: "Test notifications sent" };
        } catch (error) {
          console.error("Failed to send test notifications:", error);
          throw new TRPCError({
            code: "INTERNAL_SERVER_ERROR",
            message: "Failed to send test notifications",
          });
        }
      }),
  }),
});

export type AppRouter = typeof appRouter;
