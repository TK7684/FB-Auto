export const ENV = {
  appId: process.env.VITE_APP_ID ?? "",
  cookieSecret: process.env.JWT_SECRET ?? "",
  databaseUrl: process.env.DATABASE_URL ?? "",
  oAuthServerUrl: process.env.OAUTH_SERVER_URL ?? "",
  ownerOpenId: process.env.OWNER_OPEN_ID ?? "",
  isProduction: process.env.NODE_ENV === "production",
  forgeApiUrl: process.env.BUILT_IN_FORGE_API_URL ?? "",
  forgeApiKey: process.env.BUILT_IN_FORGE_API_KEY ?? "",

  // S3 Storage Configuration
  s3Bucket: process.env.S3_BUCKET ?? "",
  s3Region: process.env.S3_REGION ?? "",
  s3AccessKeyId: process.env.S3_ACCESS_KEY_ID ?? "",
  s3SecretAccessKey: process.env.S3_SECRET_ACCESS_KEY ?? "",

  // Email Service Configuration
  emailServiceApiKey: process.env.EMAIL_SERVICE_API_KEY ?? "",
  emailFromAddress: process.env.EMAIL_FROM_ADDRESS ?? "",

  // SMS Service Configuration
  smsServiceApiKey: process.env.SMS_SERVICE_API_KEY ?? "",

  // Stripe Configuration
  stripeSecretKey: process.env.STRIPE_SECRET_KEY ?? "",
  stripeWebhookSecret: process.env.STRIPE_WEBHOOK_SECRET ?? "",
  stripeMonthlyPriceId: process.env.STRIPE_MONTHLY_PRICE_ID ?? "",
  stripeYearlyPriceId: process.env.STRIPE_YEARLY_PRICE_ID ?? "",
};
