import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "wouter";
import { useAuth } from "@_core/hooks/useAuth";
import DashboardLayout from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Heart,
  Syringe,
  Activity,
  TrendingUp,
  DollarSign,
  Utensils,
  Stethoscope,
  Pill,
  Calendar,
  ChevronRight,
  MapPin,
  Baby,
} from "lucide-react";
import { format } from "date-fns";
import { th } from "date-fns/locale";
import { trpc } from "@/lib/trpc";

interface PetProfileProps {
  params: { id: string };
}

export default function PetProfile({ params }: PetProfileProps) {
  const { id } = useParams<{ id: string }>();
  const petId = parseInt(id || "0");
  const { user } = useAuth();

  const { data: pet, isLoading: petLoading } = trpc.pets.getById.useQuery({
    petId,
  });

  const { data: healthRecords } = trpc.healthRecords.list.useQuery(
    { petId },
    { enabled: !!petId }
  );

  const { data: vaccinations } = trpc.vaccinations.list.useQuery(
    { petId },
    { enabled: !!petId }
  );

  const { data: medications } = trpc.medications.list.useQuery(
    { petId },
    { enabled: !!petId }
  );

  if (petLoading) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <div className="animate-pulse space-y-6">
            <div className="h-32 w-32 bg-gray-200 rounded-full"></div>
            <div className="h-8 w-64 bg-gray-200 rounded"></div>
            <div className="h-4 w-96 bg-gray-200 rounded"></div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!pet) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <h1 className="text-3xl font-bold">ไม่พบข้อมูลสัตว์เลี้ยง</h1>
          <p className="text-muted-foreground mt-2">
            ไม่พบข้อมูลสัตว์เลี้ยงที่คุณกำลังมองหา
          </p>
          <Link href="/pets">
            <Button className="mt-4">กลับไปหน้าสัตว์เลี้ยง</Button>
          </Link>
        </div>
      </DashboardLayout>
    );
  }

  const age = pet.birthDate
    ? Math.floor(
        (Date.now() - new Date(pet.birthDate).getTime()) /
          (1000 * 60 * 60 * 24 * 365)
      )
    : null;

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Pet Info Header */}
        <div className="flex flex-col md:flex-row gap-6 items-start md:items-center">
          {pet.photoUrl ? (
            <img
              src={pet.photoUrl}
              alt={pet.name}
              className="w-32 h-32 rounded-full object-cover border-4 border-white shadow-lg"
            />
          ) : (
            <div className="w-32 h-32 rounded-full bg-primary/10 flex items-center justify-center border-4 border-white shadow-lg">
              <div className="text-center">
                <div className="text-4xl">🐾</div>
              </div>
            </div>
          )}

          <div className="flex-1">
            <h1 className="text-3xl font-bold">{pet.name}</h1>
            <div className="flex flex-wrap gap-2 mt-2">
              <Badge variant="outline">{pet.breed || "ไม่ระบุสายพันธุ์"}</Badge>
              {pet.gender && (
                <Badge variant="outline">
                  {pet.gender === "male"
                    ? "เพศผู้"
                    : pet.gender === "female"
                      ? "เพศเมีย"
                      : "ไม่ระบุเพศ"}
                </Badge>
              )}
              {age !== null && (
                <Badge variant="outline">
                  {age === 0 ? "น้อยกว่า 1 ปี" : `${age} ปี`}
                </Badge>
              )}
            </div>
            {pet.birthDate && (
              <p className="text-muted-foreground mt-2">
                <Baby className="inline h-4 w-4 mr-1" />
                วันเกิด:{" "}
                {format(new Date(pet.birthDate), "d MMMM yyyy", { locale: th })}
              </p>
            )}
          </div>

          <Link href={`/pets/${pet.id}/edit`}>
            <Button variant="outline">แก้ไขข้อมูล</Button>
          </Link>
        </div>

        <Separator />

        {/* Quick Actions Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Link href={`/health-records?petId=${pet.id}`}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Heart className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">บันทึกสุขภาพ</CardTitle>
                      <CardDescription>
                        บันทึกการตรวจสุขภาพและการไปหาหมอ
                      </CardDescription>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardHeader>
              {healthRecords && healthRecords.length > 0 && (
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    มีบันทึก {healthRecords.length} รายการ
                  </p>
                </CardContent>
              )}
            </Card>
          </Link>

          <Link href={`/vaccinations?petId=${pet.id}`}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Syringe className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">วัคซีน</CardTitle>
                      <CardDescription>จัดการตารางวัคซีน</CardDescription>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardHeader>
              {vaccinations && vaccinations.length > 0 && (
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    มีวัคซีน {vaccinations.length} รายการ
                  </p>
                </CardContent>
              )}
            </Card>
          </Link>

          <Link href={`/behavior-logs?petId=${pet.id}`}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Activity className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">
                        บันทึกพฤติกรรม
                      </CardTitle>
                      <CardDescription>ติดตามพฤติกรรมประจำวัน</CardDescription>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardHeader>
            </Card>
          </Link>

          <Link href={`/weight-tracking?petId=${pet.id}`}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <TrendingUp className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">ติดตามน้ำหนัก</CardTitle>
                      <CardDescription>
                        ติดตามแนวโน้มการเจริญเติบโต
                      </CardDescription>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardHeader>
            </Card>
          </Link>

          <Link href={`/feeding-schedule?petId=${pet.id}`}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Utensils className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">ตารางให้อาหาร</CardTitle>
                      <CardDescription>จัดการตารางให้อาหาร</CardDescription>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardHeader>
            </Card>
          </Link>

          <Link href={`/medications?petId=${pet.id}`}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Pill className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">ยาและการรักษา</CardTitle>
                      <CardDescription>
                        ติดตามการให้ยาเห็บหมัดและยาถ่ายพยาธิ
                      </CardDescription>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardHeader>
              {medications && medications.length > 0 && (
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    มียาที่ต้องติดตาม {medications.length} รายการ
                  </p>
                </CardContent>
              )}
            </Card>
          </Link>

          <Link href={`/daily-activities?petId=${pet.id}`}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Calendar className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">กิจกรรมรายวัน</CardTitle>
                      <CardDescription>
                        บันทึกกิจกรรมประจำวันและแชร์ไปยัง Instagram
                      </CardDescription>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardHeader>
            </Card>
          </Link>

          <Link href={`/expenses?petId=${pet.id}`}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <DollarSign className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">ค่าใช้จ่าย</CardTitle>
                      <CardDescription>
                        ติดตามค่าใช้จ่าย (Premium)
                      </CardDescription>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardHeader>
            </Card>
          </Link>

          <Link href={`/sick-care?petId=${pet.id}`}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Stethoscope className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">ดูแลสัตว์ป่วย</CardTitle>
                      <CardDescription>
                        จัดการการดูแลสัตว์ป่วย (Premium)
                      </CardDescription>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardHeader>
            </Card>
          </Link>
        </div>
      </div>
    </DashboardLayout>
  );
}
