import DashboardLayout from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { UpcomingReminders } from "@/components/UpcomingReminders";
import { trpc } from "@/lib/trpc";
import {
  Heart,
  PawPrint,
  Syringe,
  TrendingUp,
  DollarSign,
  Plus,
  Pill,
  Calendar,
} from "lucide-react";
import { Link } from "wouter";

export default function Home() {
  const { data: pets, isLoading: petsLoading } = trpc.pets.list.useQuery();
  const { data: subscription } = trpc.subscriptions.get.useQuery();

  const tier = subscription?.tier || "free";
  const isPremium = tier === "premium";

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">
              ยินดีต้อนรับสู่ PetHealth
            </h1>
            <p className="text-muted-foreground mt-1">
              จัดการสุขภาพ วัคซีน และอื่นๆ ของสัตว์เลี้ยงของคุณ
            </p>
          </div>
          <Link href="/pets">
            <Button size="lg" className="gap-2">
              <Plus className="h-5 w-5" />
              เพิ่มสัตว์เลี้ยง
            </Button>
          </Link>
        </div>

        {/* Subscription Status */}
        {!isPremium && (
          <Card className="border-primary/50 bg-primary/5">
            <CardHeader>
              <CardTitle className="text-primary">
                อัพเกรดเป็น Premium
              </CardTitle>
              <CardDescription>
                ปลดล็อกสัตว์เลี้ยงไม่จำกัด, ติดตามค่าใช้จ่าย,
                และการจัดการดูแลสัตว์ป่วย
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/subscription">
                <Button variant="default">อัพเกรดตอนนี้</Button>
              </Link>
            </CardContent>
          </Card>
        )}

        {/* Quick Stats */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                สัตว์เลี้ยงทั้งหมด
              </CardTitle>
              <PawPrint className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {petsLoading ? "..." : pets?.length || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {tier === "free" ? "สูงสุด 1 ตัวในแผนฟรี" : "ไม่จำกัด"}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                บันทึกสุขภาพ
              </CardTitle>
              <Heart className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">
                {tier === "free" ? "10/เดือน ในแผนฟรี" : "ไม่จำกัด"}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">วัคซีน</CardTitle>
              <Syringe className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">
                ติดตามวันที่กำลังจะถึง
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {isPremium ? "ค่าใช้จ่าย" : "ฟีเจอร์ Premium"}
              </CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{isPremium ? "-" : "🔒"}</div>
              <p className="text-xs text-muted-foreground">
                {isPremium ? "ติดตามการใช้จ่าย" : "อัพเกรดเพื่อปลดล็อก"}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Pets List */}
        <div>
          <h2 className="text-2xl font-semibold mb-4">สัตว์เลี้ยงของคุณ</h2>
          {petsLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              กำลังโหลด...
            </div>
          ) : pets && pets.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {pets.map(pet => (
                <Link key={pet.id} href={`/pets/${pet.id}`}>
                  <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                    <CardHeader>
                      <div className="flex items-center gap-4">
                        {pet.photoUrl ? (
                          <img
                            src={pet.photoUrl}
                            alt={pet.name}
                            className="w-16 h-16 rounded-full object-cover"
                          />
                        ) : (
                          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                            <PawPrint className="h-8 w-8 text-primary" />
                          </div>
                        )}
                        <div>
                          <CardTitle>{pet.name}</CardTitle>
                          <CardDescription>
                            {pet.breed || "ไม่ระบุสายพันธุ์"}
                            {pet.birthDate &&
                              ` • ${Math.floor((Date.now() - new Date(pet.birthDate).getTime()) / (1000 * 60 * 60 * 24 * 365))} ปี`}
                          </CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                  </Card>
                </Link>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <PawPrint className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">
                  ยังไม่มีสัตว์เลี้ยง
                </h3>
                <p className="text-muted-foreground mb-4">
                  เพิ่มสัตว์เลี้ยงตัวแรกของคุณเพื่อเริ่มติดตามสุขภาพ
                </p>
                <Link href="/pets">
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    เพิ่มสัตว์เลี้ยงตัวแรกของคุณ
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Upcoming Reminders */}
        <UpcomingReminders />

        {/* Quick Actions */}
        <div>
          <h2 className="text-2xl font-semibold mb-4">การดำเนินการด่วน</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Link href="/health-records">
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Heart className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">บันทึกสุขภาพ</CardTitle>
                      <CardDescription>
                        ติดตามประวัติทางการแพทย์
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            </Link>

            <Link href="/vaccinations">
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Syringe className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">วัคซีน</CardTitle>
                      <CardDescription>จัดการตารางวัคซีน</CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            </Link>

            <Link href="/weight-tracking">
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader>
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
                </CardHeader>
              </Card>
            </Link>

            <Link href="/medications">
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader>
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
                </CardHeader>
              </Card>
            </Link>

            <Link href="/daily-activities">
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader>
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
                </CardHeader>
              </Card>
            </Link>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
