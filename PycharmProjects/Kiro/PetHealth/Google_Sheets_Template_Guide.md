# PetHealth - Google Sheets Template Guide

## Overview

This Google Sheets template provides a **free, offline-friendly solution** for dog owners to track their pet's health, vaccinations, behavior, weight, and feeding schedule. This template is perfect for those who want a simple, accessible way to manage pet health records without needing a premium subscription.

---

## How to Use This Template

### Step 1: Make a Copy
1. Open the Google Sheets template link (provided separately)
2. Click **File → Make a copy**
3. Rename your copy to something like "My Dog's Health Tracker"
4. Start entering your pet's information!

### Step 2: Navigate Between Sheets
The template contains multiple sheets (tabs at the bottom):
- **Dashboard** - Overview of your pet's health
- **Pets** - Basic information about your pets
- **Health Records** - Medical history and vet visits
- **Vaccinations** - Vaccine schedule and reminders
- **Behavior Logs** - Track behavioral patterns
- **Weight Tracking** - Monitor weight changes
- **Feeding Schedule** - Daily feeding routine

### Step 3: Enter Data
- Fill in the yellow-highlighted cells with your information
- Blue cells contain formulas - **do not edit these**
- Gray cells are headers and labels

---

## Sheet Descriptions

### 1. Dashboard Sheet
**Purpose:** Quick overview of your pet's health status

**Features:**
- Pet summary (name, breed, age)
- Upcoming vaccination reminders
- Recent weight trend
- Health record count
- Quick stats

**How to use:**
- This sheet updates automatically based on data in other sheets
- Check this daily for important reminders

---

### 2. Pets Sheet
**Purpose:** Store basic information about your pets

**Columns:**
- **Pet ID** - Unique identifier (auto-generated)
- **Name** - Your pet's name
- **Breed** - Dog breed
- **Birth Date** - Date of birth (format: YYYY-MM-DD)
- **Gender** - Male/Female/Unknown
- **Weight (kg)** - Current weight
- **Notes** - Additional information

**Example:**
```
Pet ID | Name  | Breed        | Birth Date  | Gender | Weight | Notes
1      | Max   | Golden Retriever | 2020-05-15 | Male   | 30     | Loves playing fetch
2      | Bella | Poodle       | 2021-03-20 | Female | 8      | Allergic to chicken
```

---

### 3. Health Records Sheet
**Purpose:** Track all medical visits and health events

**Columns:**
- **Date** - Visit date (YYYY-MM-DD)
- **Pet Name** - Which pet
- **Record Type** - Checkup/Treatment/Surgery/Emergency
- **Description** - What happened
- **Vet Name** - Veterinarian's name
- **Cost (฿)** - Treatment cost
- **Next Visit** - Follow-up date
- **Notes** - Additional details

**Tips:**
- Record every vet visit immediately
- Include medication prescriptions in notes
- Track costs for budgeting

---

### 4. Vaccinations Sheet
**Purpose:** Never miss a vaccine with automatic reminders

**Columns:**
- **Pet Name** - Which pet
- **Vaccine Name** - e.g., Rabies, DHPP, Bordetella
- **Last Date** - When last administered
- **Next Date** - When due next
- **Status** - Auto-calculated (Due Soon/Overdue/Up to Date)
- **Reminder** - Days until next dose
- **Notes** - Reactions or special instructions

**Formula Explanation:**
- **Status column** automatically shows:
  - 🔴 **Overdue** - Past due date
  - 🟡 **Due Soon** - Within 30 days
  - 🟢 **Up to Date** - More than 30 days away
- **Reminder column** calculates days remaining

**Example:**
```
Pet Name | Vaccine Name | Last Date   | Next Date   | Status    | Reminder | Notes
Max      | Rabies       | 2024-01-15  | 2025-01-15  | Up to Date| 60 days  | No reactions
Bella    | DHPP         | 2024-10-01  | 2025-01-01  | Due Soon  | 15 days  | Schedule appointment
```

---

### 5. Behavior Logs Sheet
**Purpose:** Track behavioral patterns and changes

**Columns:**
- **Date** - When observed
- **Pet Name** - Which pet
- **Behavior Type** - Aggressive/Anxious/Playful/Calm/Other
- **Trigger** - What caused it
- **Duration** - How long it lasted
- **Severity** - Low/Medium/High
- **Notes** - Detailed description

**Use cases:**
- Identify anxiety triggers
- Track training progress
- Share with behaviorist or trainer
- Monitor changes after medication

---

### 6. Weight Tracking Sheet
**Purpose:** Monitor growth and detect health issues early

**Columns:**
- **Date** - Weigh-in date
- **Pet Name** - Which pet
- **Weight (kg)** - Measured weight
- **Change** - Auto-calculated difference from last weigh-in
- **Trend** - Auto-calculated (Gaining/Losing/Stable)
- **Notes** - Context (after meal, before walk, etc.)

**Formula Explanation:**
- **Change column** shows +/- kg from previous entry
- **Trend column** indicates weight direction

**Tips:**
- Weigh your pet weekly at the same time
- Sudden weight loss/gain may indicate health issues
- Use a chart to visualize trends (see Dashboard)

---

### 7. Feeding Schedule Sheet
**Purpose:** Maintain consistent feeding routine

**Columns:**
- **Pet Name** - Which pet
- **Meal Time** - e.g., Morning, Afternoon, Evening
- **Time** - Specific time (e.g., 7:00 AM)
- **Food Type** - Brand and type
- **Amount** - Cups or grams
- **Frequency** - Daily/Twice daily/etc.
- **Notes** - Special instructions

**Example:**
```
Pet Name | Meal Time | Time    | Food Type           | Amount  | Frequency | Notes
Max      | Morning   | 7:00 AM | Royal Canin Adult   | 2 cups  | Daily     | Add water
Max      | Evening   | 6:00 PM | Royal Canin Adult   | 2 cups  | Daily     | -
Bella    | Morning   | 7:30 AM | Hill's Small Breed  | 1/2 cup | Daily     | No chicken
```

---

## Formulas and Automation

### Automatic Calculations
The template includes built-in formulas for:

1. **Age Calculation** (Pets sheet)
   ```
   =DATEDIF(D2,TODAY(),"Y")&" years "&DATEDIF(D2,TODAY(),"YM")&" months"
   ```

2. **Vaccination Status** (Vaccinations sheet)
   ```
   =IF(E2<TODAY(),"🔴 Overdue",IF(E2<TODAY()+30,"🟡 Due Soon","🟢 Up to Date"))
   ```

3. **Days Until Vaccination** (Vaccinations sheet)
   ```
   =E2-TODAY()&" days"
   ```

4. **Weight Change** (Weight Tracking sheet)
   ```
   =C2-C1
   ```

5. **Weight Trend** (Weight Tracking sheet)
   ```
   =IF(D2>0,"📈 Gaining",IF(D2<0,"📉 Losing","➡️ Stable"))
   ```

### Dashboard Summary Formulas

1. **Total Pets**
   ```
   =COUNTA(Pets!B:B)-1
   ```

2. **Upcoming Vaccinations (Next 30 days)**
   ```
   =COUNTIFS(Vaccinations!E:E,"<="&TODAY()+30,Vaccinations!E:E,">="&TODAY())
   ```

3. **Health Records This Year**
   ```
   =COUNTIFS(HealthRecords!A:A,">="&DATE(YEAR(TODAY()),1,1))
   ```

---

## Tips for Best Results

### Data Entry Best Practices
1. **Use consistent date format** - Always YYYY-MM-DD (e.g., 2024-12-18)
2. **Fill all required fields** - Yellow-highlighted cells should not be empty
3. **Be specific in notes** - Future you will thank you for details
4. **Update regularly** - Set a weekly reminder to update weight and logs

### Backup Your Data
1. **Make regular copies** - File → Make a copy → Rename with date
2. **Download as Excel** - File → Download → Microsoft Excel (.xlsx)
3. **Export to PDF** - File → Download → PDF for sharing with vet

### Customization
Feel free to:
- Add new columns for your specific needs
- Change color schemes (but keep formula cells protected)
- Add conditional formatting for visual alerts
- Create additional charts in Dashboard

---

## Free Tier vs Premium Web App

### What's Included in This Free Template
✅ Unlimited pets
✅ Unlimited health records
✅ Vaccination tracking with reminders
✅ Behavior logging
✅ Weight tracking
✅ Feeding schedule
✅ Offline access
✅ No subscription required

### Premium Web App Benefits (฿350/month)
🌟 **Automatic reminders** - Email/SMS notifications for vaccines
🌟 **Cloud sync** - Access from any device
🌟 **Advanced analytics** - Charts and insights
🌟 **Expense tracking** - Budget management
🌟 **Sick care management** - Treatment tracking
🌟 **Photo uploads** - Store pet photos
🌟 **Multi-user access** - Share with family
🌟 **Mobile app** - iOS/Android support

---

## Troubleshooting

### Problem: Formulas showing #REF! error
**Solution:** Don't delete rows or columns. If you need to remove data, clear the cell content only.

### Problem: Dates not calculating correctly
**Solution:** Ensure dates are in YYYY-MM-DD format. Use the date picker (calendar icon) when entering dates.

### Problem: Dashboard not updating
**Solution:** Check that you're entering data in the correct sheets. Dashboard pulls from other tabs automatically.

### Problem: Can't edit certain cells
**Solution:** Blue cells contain formulas and should not be edited. Only fill in yellow-highlighted cells.

---

## Support

### Need Help?
- **Email:** support@pethealth.example.com
- **Website:** https://pethealth.example.com
- **Upgrade to Premium:** https://pethealth.example.com/subscription

### Share Your Feedback
We'd love to hear how you're using this template! Share your suggestions for improvements.

---

## Version History

- **v1.0** (December 2024) - Initial release
  - Basic pet tracking
  - Health records
  - Vaccination reminders
  - Behavior logs
  - Weight tracking
  - Feeding schedule

---

## License

This template is provided **free of charge** for personal use. You may:
- Make copies for your own pets
- Share the template link with friends
- Customize for your needs

You may **not**:
- Sell or redistribute this template
- Remove attribution
- Use for commercial purposes

---

**Created by PetHealth**
*Helping dog owners provide the best care for their furry friends* 🐾
