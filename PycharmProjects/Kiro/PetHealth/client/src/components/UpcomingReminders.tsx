import { useQuery } from "@tanstack/react-query";
import { Bell, Calendar, Clock, Pill, Syringe } from "lucide-react";
import { format, isAfter, addDays } from "date-fns";
import { th } from "date-fns/locale";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { trpc } from "@/lib/trpc";

interface UpcomingRemindersProps {
  petId?: number;
  limit?: number;
}

export function UpcomingReminders({ petId, limit = 5 }: UpcomingRemindersProps) {
  const { data: pets, isLoading: petsLoading } = trpc.pets.list.useQuery();
  const { data: vaccinations, isLoading: vaccinationsLoading } = trpc.vaccinations.list.useQuery(
    { petId: petId || 0 },
    { enabled: !!petId }
  );
  const { data: medications, isLoading: medicationsLoading } = trpc.medications.list.useQuery(
    { petId: petId || 0 },
    { enabled: !!petId }
  );

  // If petId is not provided, get all reminders for all pets
  const getAllReminders = () => {
    if (petId) return [];

    const allReminders: any[] = [];

    pets?.forEach(pet => {
      // This would ideally be done with a single API call
      // For now, we'll just return a placeholder
    });

    return allReminders;
  };

  // Get reminders for a specific pet
  const getPetReminders = () => {
    if (!petId) return [];

    const reminders: any[] = [];
    const now = new Date();

    // Add vaccination reminders
    vaccinations?.forEach(vaccination => {
      if (vaccination.nextDate && vaccination.reminderEnabled) {
        const nextDate = new Date(vaccination.nextDate);
        const isOverdue = !isAfter(nextDate, now);
        const isUpcoming = isAfter(addDays(now, 14), nextDate); // Within 14 days

        if (isOverdue || isUpcoming) {
          reminders.push({
            id: `vaccination-${vaccination.id}`,
            type: 'vaccination',
            title: `วัคซีน ${vaccination.vaccineName}`,
            dueDate: nextDate,
            isOverdue,
            petId: vaccination.petId,
          });
        }
      }
    });

    // Add medication reminders
    medications?.forEach(medication => {
      if (medication.nextDueDate && medication.reminderEnabled) {
        const nextDate = new Date(medication.nextDueDate);
        const isOverdue = !isAfter(nextDate, now);
        const isUpcoming = isAfter(addDays(now, 7), nextDate); // Within 7 days

        if (isOverdue || isUpcoming) {
          reminders.push({
            id: `medication-${medication.id}`,
            type: 'medication',
            title: `ยา ${medication.medicationName}`,
            dueDate: nextDate,
            isOverdue,
            petId: medication.petId,
          });
        }
      }
    });

    // Sort by date (closest first)
    reminders.sort((a, b) => a.dueDate.getTime() - b.dueDate.getTime());

    return reminders.slice(0, limit);
  };

  const reminders = petId ? getPetReminders() : getAllReminders();
  const isLoading = petsLoading || (petId ? (vaccinationsLoading || medicationsLoading) : false);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            การแจ้งเตือนที่ใกล้ถึง
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="space-y-1 flex-1">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (reminders.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            การแจ้งเตือนที่ใกล้ถึง
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4 text-muted-foreground">
            ไม่มีการแจ้งเตือนที่ใกล้ถึง
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          การแจ้งเตือนที่ใกล้ถึง
        </CardTitle>
        <CardDescription>
          วัคซีนและยาที่ต้องให้ในเร็วๆ นี้
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {reminders.map((reminder) => {
            const pet = pets?.find(p => p.id === reminder.petId);

            return (
              <div key={reminder.id} className="flex items-start gap-3">
                <div className={`p-2 rounded-full ${
                  reminder.isOverdue
                    ? 'bg-red-100 text-red-600'
                    : 'bg-amber-100 text-amber-600'
                }`}>
                  {reminder.type === 'vaccination' ? (
                    <Syringe className="h-4 w-4" />
                  ) : (
                    <Pill className="h-4 w-4" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium truncate">{reminder.title}</p>
                    {reminder.isOverdue && (
                      <Badge variant="destructive" className="text-xs">
                        ล่าช้าแล้ว
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="h-3 w-3" />
                    <span>
                      {format(reminder.dueDate, "d MMMM yyyy", { locale: th })}
                    </span>
                  </div>
                  {pet && (
                    <div className="text-sm text-muted-foreground">
                      สำหรับ: {pet.name}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
