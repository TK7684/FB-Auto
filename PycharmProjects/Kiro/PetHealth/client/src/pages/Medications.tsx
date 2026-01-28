import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { CalendarIcon, Clock, Edit, Plus, Trash2, AlertCircle } from "lucide-react";
import { format, formatDistanceToNow, isAfter, addDays } from "date-fns";
import { th } from "date-fns/locale";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/trpc";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";

const medicationTypeLabels = {
  flea_tick: "ยากำจัดเห็บหมัด",
  deworming: "ยาถ่ายพยาธิ",
  other: "ยาอื่นๆ"
};

const frequencyOptions = [
  { value: "monthly", label: "รายเดือน" },
  { value: "quarterly", label: "ราย 3 เดือน" },
  { value: "biannually", label: "ราย 6 เดือน" },
  { value: "annually", label: "รายปี" },
  { value: "custom", label: "กำหนดเอง" }
];

export default function Medications() {
  const [activeTab, setActiveTab] = useState("active");
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedMedication, setSelectedMedication] = useState<any>(null);

  // Form state for adding medication
  const [formData, setFormData] = useState({
    petId: 0,
    medicationType: "flea_tick",
    medicationName: "",
    lastGivenDate: "",
    nextDueDate: "",
    dosage: "",
    frequency: "monthly",
    reminderEnabled: true,
    notes: ""
  });

  const { data: pets, isLoading: petsLoading } = useQuery({
    queryKey: ["pets"],
    queryFn: () => api.pets.list.query(),
  });

  const { data: medications, isLoading: medicationsLoading } = useQuery({
    queryKey: ["medications"],
    queryFn: () => api.medications.list.query(),
    enabled: !!formData.petId,
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.medications.create.mutate(data),
    onSuccess: () => {
      toast.success("เพิ่มยาสำเร็จแล้ว");
      setAddDialogOpen(false);
      setFormData({
        petId: 0,
        medicationType: "flea_tick",
        medicationName: "",
        lastGivenDate: "",
        nextDueDate: "",
        dosage: "",
        frequency: "monthly",
        reminderEnabled: true,
        notes: ""
      });
    },
    onError: (error) => {
      toast.error(`เพิ่มยาไม่สำเร็จ: ${error.message}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      api.medications.update.mutate({ medicationId: id, ...data }),
    onSuccess: () => {
      toast.success("อัพเดทข้อมูลยาสำเร็จแล้ว");
      setEditDialogOpen(false);
    },
    onError: (error) => {
      toast.error(`อัพเดทข้อมูลยาไม่สำเร็จ: ${error.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.medications.delete.mutate({ medicationId: id }),
    onSuccess: () => {
      toast.success("ลบยาสำเร็จแล้ว");
    },
    onError: (error) => {
      toast.error(`ลบยาไม่สำเร็จ: ${error.message}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.petId || !formData.medicationName || !formData.lastGivenDate) {
      toast.error("กรุณากรอกข้อมูลที่จำเป็นทั้งหมด");
      return;
    }

    // Calculate nextDueDate based on frequency if not provided
    let nextDueDate = formData.nextDueDate;
    if (!nextDueDate) {
      const lastGiven = new Date(formData.lastGivenDate);
      let daysToAdd = 30; // Default to monthly

      switch (formData.frequency) {
        case "monthly": daysToAdd = 30; break;
        case "quarterly": daysToAdd = 90; break;
        case "biannually": daysToAdd = 180; break;
        case "annually": daysToAdd = 365; break;
      }

      nextDueDate = format(addDays(lastGiven, daysToAdd), "yyyy-MM-dd");
    }

    const medicationData = {
      ...formData,
      nextDueDate,
      lastGivenDate: new Date(formData.lastGivenDate).toISOString(),
    };

    createMutation.mutate(medicationData);
  };

  const handleEdit = (medication: any) => {
    setSelectedMedication(medication);
    setFormData({
      petId: medication.petId,
      medicationType: medication.medicationType,
      medicationName: medication.medicationName,
      lastGivenDate: format(new Date(medication.lastGivenDate), "yyyy-MM-dd"),
      nextDueDate: medication.nextDueDate ? format(new Date(medication.nextDueDate), "yyyy-MM-dd") : "",
      dosage: medication.dosage || "",
      frequency: medication.frequency || "monthly",
      reminderEnabled: Boolean(medication.reminderEnabled),
      notes: medication.notes || ""
    });
    setEditDialogOpen(true);
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedMedication) return;

    const medicationData = {
      ...formData,
      lastGivenDate: new Date(formData.lastGivenDate).toISOString(),
      nextDueDate: formData.nextDueDate ? new Date(formData.nextDueDate).toISOString() : null,
    };

    updateMutation.mutate({
      id: selectedMedication.id,
      data: medicationData
    });
  };

  const handleDelete = (id: number) => {
    if (window.confirm("คุณแน่ใจหรือไม่ที่จะลบข้อมูลยานี้?")) {
      deleteMutation.mutate(id);
    }
  };

  const filteredMedications = medications?.filter(med => {
    if (activeTab === "active") {
      return !med.nextDueDate || isAfter(new Date(med.nextDueDate), new Date());
    }
    return med.nextDueDate && !isAfter(new Date(med.nextDueDate), new Date());
  }) || [];

  const isOverdue = (nextDueDate: string | null) => {
    if (!nextDueDate) return false;
    return !isAfter(new Date(nextDueDate), new Date());
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">บันทึกการให้ยา</h1>
          <p className="text-muted-foreground">จัดการการให้ยาเห็บหมัดและยาถ่ายพยาธิ</p>
        </div>
        <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              เพิ่มบันทึกยา
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <form onSubmit={handleSubmit}>
              <DialogHeader>
                <DialogTitle>เพิ่มบันทึกการให้ยา</DialogTitle>
                <DialogDescription>
                  บันทึกข้อมูลการให้ยาเพื่อติดตามและแจ้งเตือน
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="pet" className="text-right">
                    สัตว์เลี้ยง
                  </Label>
                  <Select
                    value={formData.petId.toString()}
                    onValueChange={(value) => setFormData(prev => ({ ...prev, petId: parseInt(value) }))}
                  >
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="เลือกสัตว์เลี้ยง" />
                    </SelectTrigger>
                    <SelectContent>
                      {pets?.map((pet) => (
                        <SelectItem key={pet.id} value={pet.id.toString()}>
                          {pet.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="medicationType" className="text-right">
                    ประเภทยา
                  </Label>
                  <Select
                    value={formData.medicationType}
                    onValueChange={(value) => setFormData(prev => ({ ...prev, medicationType: value }))}
                  >
                    <SelectTrigger className="col-span-3">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(medicationTypeLabels).map(([value, label]) => (
                        <SelectItem key={value} value={value}>
                          {label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="medicationName" className="text-right">
                    ชื่อยา
                  </Label>
                  <Input
                    id="medicationName"
                    value={formData.medicationName}
                    onChange={(e) => setFormData(prev => ({ ...prev, medicationName: e.target.value }))}
                    className="col-span-3"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="lastGivenDate" className="text-right">
                    วันที่ให้ยาล่าสุด
                  </Label>
                  <Input
                    id="lastGivenDate"
                    type="date"
                    value={formData.lastGivenDate}
                    onChange={(e) => setFormData(prev => ({ ...prev, lastGivenDate: e.target.value }))}
                    className="col-span-3"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="frequency" className="text-right">
                    ความถี่
                  </Label>
                  <Select
                    value={formData.frequency}
                    onValueChange={(value) => setFormData(prev => ({ ...prev, frequency: value }))}
                  >
                    <SelectTrigger className="col-span-3">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {frequencyOptions.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="nextDueDate" className="text-right">
                    วันที่ครบกำหนดถัดไป
                  </Label>
                  <Input
                    id="nextDueDate"
                    type="date"
                    value={formData.nextDueDate}
                    onChange={(e) => setFormData(prev => ({ ...prev, nextDueDate: e.target.value }))}
                    className="col-span-3"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="dosage" className="text-right">
                    ขนาดยา
                  </Label>
                  <Input
                    id="dosage"
                    value={formData.dosage}
                    onChange={(e) => setFormData(prev => ({ ...prev, dosage: e.target.value }))}
                    className="col-span-3"
                    placeholder="เช่น 1 เม็ด"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="reminderEnabled" className="text-right">
                    เปิดการแจ้งเตือน
                  </Label>
                  <div className="col-span-3 flex items-center space-x-2">
                    <Switch
                      id="reminderEnabled"
                      checked={formData.reminderEnabled}
                      onCheckedChange={(checked) => setFormData(prev => ({ ...prev, reminderEnabled: checked }))}
                    />
                    <Label htmlFor="reminderEnabled">รับการแจ้งเตือนก่อนวันครบกำหนด</Label>
                  </div>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="notes" className="text-right">
                    บันทึกเพิ่มเติม
                  </Label>
                  <Textarea
                    id="notes"
                    value={formData.notes}
                    onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                    className="col-span-3"
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? "กำลังบันทึก..." : "บันทึก"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="active">ใช้งานอยู่</TabsTrigger>
          <TabsTrigger value="expired">หมดอายุ/หมดกำหนด</TabsTrigger>
        </TabsList>
        <TabsContent value="active" className="space-y-4">
          {medicationsLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-5 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-4 w-full mb-2" />
                    <Skeleton className="h-4 w-full mb-2" />
                    <Skeleton className="h-4 w-3/4" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredMedications.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredMedications.map((med) => (
                <Card key={med.id} className="relative">
                  {isOverdue(med.nextDueDate) && (
                    <div className="absolute top-2 right-2">
                      <Badge variant="destructive" className="flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        หมดกำหนด
                      </Badge>
                    </div>
                  )}
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {med.medicationName}
                      <Badge variant="outline">
                        {medicationTypeLabels[med.medicationType as keyof typeof medicationTypeLabels]}
                      </Badge>
                    </CardTitle>
                    <CardDescription>
                      {pets?.find(pet => pet.id === med.petId)?.name}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm">
                        <CalendarIcon className="h-4 w-4 text-muted-foreground" />
                        <span>ให้ครั้งล่าสุด: {format(new Date(med.lastGivenDate), "d MMMM yyyy", { locale: th })}</span>
                      </div>
                      {med.nextDueDate && (
                        <div className={`flex items-center gap-2 text-sm ${isOverdue(med.nextDueDate) ? "text-red-600" : ""}`}>
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span>
                            ครบกำหนด: {format(new Date(med.nextDueDate), "d MMMM yyyy", { locale: th })}
                            {isOverdue(med.nextDueDate) && (
                              <span className="ml-1">
                                ({formatDistanceToNow(new Date(med.nextDueDate), { addSuffix: true, locale: th })})
                              </span>
                            )}
                          </span>
                        </div>
                      )}
                      {med.dosage && (
                        <div className="text-sm">
                          <span className="font-medium">ขนาดยา:</span> {med.dosage}
                        </div>
                      )}
                      {med.frequency && (
                        <div className="text-sm">
                          <span className="font-medium">ความถี่:</span> {frequencyOptions.find(f => f.value === med.frequency)?.label || med.frequency}
                        </div>
                      )}
                      {med.notes && (
                        <div className="text-sm">
                          <span className="font-medium">หมายเหตุ:</span> {med.notes}
                        </div>
                      )}
                    </div>
                    <div className="mt-4 flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(med)}
                      >
                        <Edit className="h-4 w-4 mr-1" />
                        แก้ไข
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(med.id)}
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        ลบ
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>ไม่มีข้อมูลยา</CardTitle>
                <CardDescription>
                  คุณยังไม่ได้เพิ่มข้อมูลยาใดๆ คลิกปุ่ม "เพิ่มบันทึกยา" เพื่อเริ่มต้น
                </CardDescription>
              </CardHeader>
            </Card>
          )}
        </TabsContent>
        <TabsContent value="expired" className="space-y-4">
          {medicationsLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 2 }).map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-5 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-4 w-full mb-2" />
                    <Skeleton className="h-4 w-full mb-2" />
                    <Skeleton className="h-4 w-3/4" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : medications?.filter(med => med.nextDueDate && !isAfter(new Date(med.nextDueDate), new Date())).length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {medications
                .filter(med => med.nextDueDate && !isAfter(new Date(med.nextDueDate), new Date()))
                .map((med) => (
                <Card key={med.id} className="relative opacity-75">
                  <div className="absolute top-2 right-2">
                    <Badge variant="destructive" className="flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      หมดกำหนด
                    </Badge>
                  </div>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {med.medicationName}
                      <Badge variant="outline">
                        {medicationTypeLabels[med.medicationType as keyof typeof medicationTypeLabels]}
                      </Badge>
                    </CardTitle>
                    <CardDescription>
                      {pets?.find(pet => pet.id === med.petId)?.name}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm">
                        <CalendarIcon className="h-4 w-4 text-muted-foreground" />
                        <span>ให้ครั้งล่าสุด: {format(new Date(med.lastGivenDate), "d MMMM yyyy", { locale: th })}</span>
                      </div>
                      {med.nextDueDate && (
                        <div className="flex items-center gap-2 text-sm text-red-600">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span>
                            ครบกำหนด: {format(new Date(med.nextDueDate), "d MMMM yyyy", { locale: th })}
                            <span className="ml-1">
                              ({formatDistanceToNow(new Date(med.nextDueDate), { addSuffix: true, locale: th })})
                            </span>
                          </span>
                        </div>
                      )}
                      {med.dosage && (
                        <div className="text-sm">
                          <span className="font-medium">ขนาดยา:</span> {med.dosage}
                        </div>
                      )}
                      {med.frequency && (
                        <div className="text-sm">
                          <span className="font-medium">ความถี่:</span> {frequencyOptions.find(f => f.value === med.frequency)?.label || med.frequency}
                        </div>
                      )}
                    </div>
                    <div className="mt-4 flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(med)}
                      >
                        <Edit className="h-4 w-4 mr-1" />
                        แก้ไข
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(med.id)}
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        ลบ
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>ไม่มียาที่หมดกำหนด</CardTitle>
                <CardDescription>
                  ไม่มียาที่หมดกำหนดในขณะนี้
                </CardDescription>
              </CardHeader>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleEditSubmit}>
            <DialogHeader>
              <DialogTitle>แก้ไขข้อมูลยา</DialogTitle>
              <DialogDescription>
                แก้ไขข้อมูลการให้ยาเพื่อติดตามและแจ้งเตือน
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-medicationType" className="text-right">
                  ประเภทยา
                </Label>
                <Select
                  value={formData.medicationType}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, medicationType: value }))}
                >
                  <SelectTrigger className="col-span-3" id="edit-medicationType">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(medicationTypeLabels).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-medicationName" className="text-right">
                  ชื่อยา
                </Label>
                <Input
                  id="edit-medicationName"
                  value={formData.medicationName}
                  onChange={(e) => setFormData(prev => ({ ...prev, medicationName: e.target.value }))}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-lastGivenDate" className="text-right">
                  วันที่ให้ยาล่าสุด
                </Label>
                <Input
                  id="edit-lastGivenDate"
                  type="date"
                  value={formData.lastGivenDate}
                  onChange={(e) => setFormData(prev => ({ ...prev, lastGivenDate: e.target.value }))}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-frequency" className="text-right">
                  ความถี่
                </Label>
                <Select
                  value={formData.frequency}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, frequency: value }))}
                >
                  <SelectTrigger className="col-span-3" id="edit-frequency">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {frequencyOptions.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-nextDueDate" className="text-right">
                  วันที่ครบกำหนดถัดไป
                </Label>
                <Input
                  id="edit-nextDueDate"
                  type="date"
                  value={formData.nextDueDate}
                  onChange={(e) => setFormData(prev => ({ ...prev, nextDueDate: e.target.value }))}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-dosage" className="text-right">
                  ขนาดยา
                </Label>
                <Input
                  id="edit-dosage"
                  value={formData.dosage}
                  onChange={(e) => setFormData(prev => ({ ...prev, dosage: e.target.value }))}
                  className="col-span-3"
                  placeholder="เช่น 1 เม็ด"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-reminderEnabled" className="text-right">
                  เปิดการแจ้งเตือน
                </Label>
                <div className="col-span-3 flex items-center space-x-2">
                  <Switch
                    id="edit-reminderEnabled"
                    checked={formData.reminderEnabled}
                    onCheckedChange={(checked) => setFormData(prev => ({ ...prev, reminderEnabled: checked }))}
                  />
                  <Label htmlFor="edit-reminderEnabled">รับการแจ้งเตือนก่อนวันครบกำหนด</Label>
                </div>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-notes" className="text-right">
                  บันทึกเพิ่มเติม
                </Label>
                <Textarea
                  id="edit-notes"
                  value={formData.notes}
                  onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                  className="col-span-3"
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? "กำลังบันทึก..." : "บันทึกการแก้ไข"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
