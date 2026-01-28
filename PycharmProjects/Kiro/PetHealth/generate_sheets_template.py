import csv
from datetime import datetime, timedelta

# Create Pets sheet
pets_data = [
    ["Pet ID", "Name", "Breed", "Birth Date", "Gender", "Weight (kg)", "Notes"],
    ["1", "Max", "Golden Retriever", "2020-05-15", "Male", "30", "Loves playing fetch"],
    ["2", "Bella", "Poodle", "2021-03-20", "Female", "8", "Allergic to chicken"],
    ["", "", "", "", "", "", "Add your pets here..."],
]

with open("/home/ubuntu/PetHealth/PetHealth_Template_Pets.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(pets_data)

# Create Health Records sheet
health_records_data = [
    ["Date", "Pet Name", "Record Type", "Description", "Vet Name", "Cost (฿)", "Next Visit", "Notes"],
    ["2024-01-15", "Max", "Checkup", "Annual health checkup", "Dr. Smith", "1500", "2025-01-15", "All clear"],
    ["2024-03-20", "Bella", "Treatment", "Skin allergy treatment", "Dr. Johnson", "800", "2024-04-20", "Prescribed medication"],
    ["", "", "", "", "", "", "", "Add health records here..."],
]

with open("/home/ubuntu/PetHealth/PetHealth_Template_HealthRecords.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(health_records_data)

# Create Vaccinations sheet
today = datetime.now()
next_month = today + timedelta(days=30)
next_year = today + timedelta(days=365)

vaccinations_data = [
    ["Pet Name", "Vaccine Name", "Last Date", "Next Date", "Notes"],
    ["Max", "Rabies", "2024-01-15", next_year.strftime("%Y-%m-%d"), "No reactions"],
    ["Max", "DHPP", "2024-01-15", next_year.strftime("%Y-%m-%d"), "Annual booster"],
    ["Bella", "Rabies", "2024-03-20", (today + timedelta(days=350)).strftime("%Y-%m-%d"), "No reactions"],
    ["Bella", "Bordetella", "2024-10-01", next_month.strftime("%Y-%m-%d"), "Due soon - schedule appointment"],
    ["", "", "", "", "Add vaccinations here..."],
]

with open("/home/ubuntu/PetHealth/PetHealth_Template_Vaccinations.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(vaccinations_data)

# Create Behavior Logs sheet
behavior_logs_data = [
    ["Date", "Pet Name", "Behavior Type", "Trigger", "Duration (min)", "Severity", "Notes"],
    ["2024-12-01", "Max", "Anxious", "Thunderstorm", "45", "Medium", "Hid under bed, panting"],
    ["2024-12-05", "Bella", "Playful", "New toy", "30", "Low", "Very excited, running around"],
    ["2024-12-10", "Max", "Aggressive", "Stranger at door", "10", "Medium", "Barking loudly, need training"],
    ["", "", "", "", "", "", "Add behavior logs here..."],
]

with open("/home/ubuntu/PetHealth/PetHealth_Template_BehaviorLogs.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(behavior_logs_data)

# Create Weight Tracking sheet
weight_tracking_data = [
    ["Date", "Pet Name", "Weight (kg)", "Notes"],
    ["2024-01-01", "Max", "28", "Starting weight"],
    ["2024-02-01", "Max", "28.5", "Slight increase"],
    ["2024-03-01", "Max", "29", "Healthy gain"],
    ["2024-04-01", "Max", "30", "Target weight reached"],
    ["2024-01-01", "Bella", "7.5", "Starting weight"],
    ["2024-02-01", "Bella", "7.8", "Good progress"],
    ["2024-03-01", "Bella", "8", "Target weight reached"],
    ["", "", "", "Add weight records here..."],
]

with open("/home/ubuntu/PetHealth/PetHealth_Template_WeightTracking.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(weight_tracking_data)

# Create Feeding Schedule sheet
feeding_schedule_data = [
    ["Pet Name", "Meal Time", "Time", "Food Type", "Amount", "Frequency", "Notes"],
    ["Max", "Morning", "7:00 AM", "Royal Canin Adult", "2 cups", "Daily", "Add water to soften"],
    ["Max", "Evening", "6:00 PM", "Royal Canin Adult", "2 cups", "Daily", ""],
    ["Bella", "Morning", "7:30 AM", "Hill's Small Breed", "1/2 cup", "Daily", "No chicken formula"],
    ["Bella", "Evening", "6:30 PM", "Hill's Small Breed", "1/2 cup", "Daily", ""],
    ["", "", "", "", "", "", "Add feeding schedule here..."],
]

with open("/home/ubuntu/PetHealth/PetHealth_Template_FeedingSchedule.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(feeding_schedule_data)

# Create Dashboard sheet
dashboard_data = [
    ["PetHealth Dashboard", "", "", ""],
    ["", "", "", ""],
    ["Quick Stats", "", "", ""],
    ["Total Pets", "2", "", ""],
    ["Health Records This Year", "2", "", ""],
    ["Upcoming Vaccinations (30 days)", "1", "", ""],
    ["", "", "", ""],
    ["Recent Activity", "", "", ""],
    ["Last Health Record", "2024-03-20", "Bella - Skin allergy treatment", ""],
    ["Next Vaccination Due", next_month.strftime("%Y-%m-%d"), "Bella - Bordetella", ""],
    ["", "", "", ""],
    ["Instructions:", "", "", ""],
    ["1. This dashboard summarizes data from other sheets", "", "", ""],
    ["2. Update other sheets to see changes here", "", "", ""],
    ["3. Check this daily for important reminders", "", "", ""],
]

with open("/home/ubuntu/PetHealth/PetHealth_Template_Dashboard.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(dashboard_data)

print("✅ All CSV files generated successfully!")
print("\nGenerated files:")
print("- PetHealth_Template_Pets.csv")
print("- PetHealth_Template_HealthRecords.csv")
print("- PetHealth_Template_Vaccinations.csv")
print("- PetHealth_Template_BehaviorLogs.csv")
print("- PetHealth_Template_WeightTracking.csv")
print("- PetHealth_Template_FeedingSchedule.csv")
print("- PetHealth_Template_Dashboard.csv")
