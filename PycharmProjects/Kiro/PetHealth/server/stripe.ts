import Stripe from "stripe";
import { ENV } from "./_core/env";
import * as db from "./db";

// Initialize Stripe with the secret key
export const stripe = new Stripe(ENV.stripeSecretKey || "", {
  apiVersion: "2024-06-20",
});

// Price IDs for subscription tiers (in production, these would be created in Stripe Dashboard)
export const PRICE_IDS = {
  // Monthly subscription (฿350/month)
  monthly: process.env.STRIPE_MONTHLY_PRICE_ID || "price_monthly_premium_350",
  // Yearly subscription (฿3500/year - 2 months free)
  yearly: process.env.STRIPE_YEARLY_PRICE_ID || "price_yearly_premium_3500",
};

// Create a checkout session for Premium subscription
export async function createCheckoutSession(
  userId: number,
  priceId: string,
  successUrl: string,
  cancelUrl: string
): Promise<{ sessionId: string; url: string }> {
  const user = await db.getUserByOpenId(userId.toString());
  if (!user) {
    throw new Error("User not found");
  }

  // Check if user already has an active subscription
  const existingSubscription = await db.getUserSubscription(userId);
  if (existingSubscription && existingSubscription.tier === "premium") {
    throw new Error("User already has an active Premium subscription");
  }

  // Create a Stripe customer if not exists
  let customerId = user.stripeCustomerId;
  if (!customerId) {
    const customer = await stripe.customers.create({
      email: user.email || undefined,
      metadata: {
        userId: userId.toString(),
      },
    });
    customerId = customer.id;

    // Update user with Stripe customer ID
    await db.updateUser(userId, { stripeCustomerId: customerId });
  }

  // Create a checkout session
  const session = await stripe.checkout.sessions.create({
    customer: customerId,
    payment_method_types: ["card"],
    line_items: [
      {
        price: priceId,
        quantity: 1,
      },
    ],
    mode: "subscription",
    success_url: successUrl,
    cancel_url: cancelUrl,
    metadata: {
      userId: userId.toString(),
    },
    subscription_data: {
      metadata: {
        userId: userId.toString(),
      },
    },
  });

  return {
    sessionId: session.id,
    url: session.url || "",
  };
}

// Create a customer portal session for managing subscription
export async function createCustomerPortalSession(
  userId: number,
  returnUrl: string
): Promise<{ url: string }> {
  const user = await db.getUserByOpenId(userId.toString());
  if (!user || !user.stripeCustomerId) {
    throw new Error("User not found or no Stripe customer ID");
  }

  const session = await stripe.billingPortal.sessions.create({
    customer: user.stripeCustomerId,
    return_url: returnUrl,
  });

  return { url: session.url };
}

// Webhook handler for Stripe events
export async function handleStripeWebhook(
  payload: string,
  signature: string
): Promise<void> {
  try {
    const event = stripe.webhooks.constructEvent(
      payload,
      signature,
      ENV.stripeWebhookSecret || ""
    );
  } catch (err) {
    console.error(`Webhook signature verification failed:`, err);
    throw new Error("Invalid signature");
  }

  // Handle the event
  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object as Stripe.Checkout.Session;
      await handleCheckoutSessionCompleted(session);
      break;
    }
    case "invoice.payment_succeeded": {
      const invoice = event.data.object as Stripe.Invoice;
      await handleInvoicePaymentSucceeded(invoice);
      break;
    }
    case "invoice.payment_failed": {
      const invoice = event.data.object as Stripe.Invoice;
      await handleInvoicePaymentFailed(invoice);
      break;
    }
    case "customer.subscription.updated": {
      const subscription = event.data.object as Stripe.Subscription;
      await handleSubscriptionUpdated(subscription);
      break;
    }
    case "customer.subscription.deleted": {
      const subscription = event.data.object as Stripe.Subscription;
      await handleSubscriptionDeleted(subscription);
      break;
    }
    default:
      // Unexpected event type
      console.log(`Unhandled event type ${event.type}`);
  }
}

// Handle checkout session completion
async function handleCheckoutSessionCompleted(
  session: Stripe.Checkout.Session
): Promise<void> {
  const userId = session.metadata?.userId;
  if (!userId) {
    console.error("No userId in checkout session metadata");
    return;
  }

  const userIdNum = parseInt(userId);
  const user = await db.getUserByOpenId(userIdNum.toString());
  if (!user) return;

  // Get or create subscription record
  let subscription = await db.getUserSubscription(userIdNum);

  if (!subscription) {
    // Create new subscription record
    await db.createSubscription({
      userId: userIdNum,
      tier: "premium",
      stripeSubscriptionId: session.subscription as string,
      stripePriceId: session.display_items?.[0]?.price?.id || "",
      startDate: new Date(),
      status: "active",
    });
  } else {
    // Update existing subscription record
    await db.updateSubscription(userIdNum, {
      tier: "premium",
      stripeSubscriptionId: session.subscription as string,
      stripePriceId: session.display_items?.[0]?.price?.id || "",
      status: "active",
    });
  }

  console.log(`User ${userIdNum} subscribed to Premium`);
}

// Handle invoice payment succeeded
async function handleInvoicePaymentSucceeded(
  invoice: Stripe.Invoice
): Promise<void> {
  if (invoice.subscription) {
    // This is a subscription invoice
    const subscription = await stripe.subscriptions.retrieve(
      invoice.subscription as string
    );
    const userId = subscription.metadata?.userId;

    if (userId) {
      const userIdNum = parseInt(userId);

      // Update subscription status to active
      await db.updateSubscription(userIdNum, {
        status: "active",
        endDate: subscription.current_period_end
          ? new Date(subscription.current_period_end * 1000)
          : undefined,
      });
    }
  }
}

// Handle invoice payment failed
async function handleInvoicePaymentFailed(
  invoice: Stripe.Invoice
): Promise<void> {
  if (invoice.subscription) {
    // This is a subscription invoice
    const subscription = await stripe.subscriptions.retrieve(
      invoice.subscription as string
    );
    const userId = subscription.metadata?.userId;

    if (userId) {
      const userIdNum = parseInt(userId);

      // Update subscription status to indicate payment issue
      await db.updateSubscription(userIdNum, {
        status: "active", // Still active but with payment issue
      });
    }
  }
}

// Handle subscription update
async function handleSubscriptionUpdated(
  subscription: Stripe.Subscription
): Promise<void> {
  const userId = subscription.metadata?.userId;

  if (userId) {
    const userIdNum = parseInt(userId);

    // Update subscription details
    await db.updateSubscription(userIdNum, {
      stripePriceId: subscription.items.data[0]?.price?.id || "",
      status: subscription.status as any,
      endDate: subscription.current_period_end
        ? new Date(subscription.current_period_end * 1000)
        : undefined,
    });
  }
}

// Handle subscription deletion
async function handleSubscriptionDeleted(
  subscription: Stripe.Subscription
): Promise<void> {
  const userId = subscription.metadata?.userId;

  if (userId) {
    const userIdNum = parseInt(userId);

    // Update subscription status to expired
    await db.updateSubscription(userIdNum, {
      status: "expired",
      endDate: new Date(),
    });
  }
}
