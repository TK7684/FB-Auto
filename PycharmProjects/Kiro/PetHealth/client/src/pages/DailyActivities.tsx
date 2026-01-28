import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { CalendarIcon, Clock, MapPin, Instagram, Edit, Plus, Trash2, Camera, Link2 } from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { th } from "date-fns/locale";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/trpc";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { ImageUpload } from "@/components/ImageUpload";

const activityTypeOptions = [
  { value: "walk", label: "เดินเล่น" },
  { value: "play", label: "เล่น" },
  { value: "training", label: "ฝึกสอน" },
  { value: "grooming", label: "อาบน้ำ/ตัดขน" },
  { value: "social", label: "สังสรรค์กับสัตว์อื่น" },
  { value: "meal", label: "มื้ออาหาร" },
  { value: "trip", label: "เที่ยว/ท่องเที่ยว" },
  { value: "health_check", label: "ตรวจสุขภาพ" },
  { value: "other", label: "อื่นๆ" }
];

export default function DailyActivities() {
  const [activeTab, setActiveTab] = useState("all");
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState<any>(null);
  const [uploadedImages, setUploadedImages] = useState<string[]>([]);

  // Form state for adding activity
  const [formData, setFormData] = useState({
    petId: 0,
    date: new Date().toISOString().split('T')[0],
    activityType: "play",
    description: "",
    photoUrls: [] as string[],
    instagramPostUrl: "",
    duration: 0,
    location: "",
    notes: ""
  });

  const { data: pets, isLoading: petsLoading } = useQuery({
    queryKey: ["pets"],
    queryFn: () => api.pets.list.query(),
  });

  const { data: activities, isLoading: activitiesLoading } = useQuery({
    queryKey: ["daily-activities"],
    queryFn: () => api.dailyActivities.list.query(),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.dailyActivities.create.mutate(data),
    onSuccess: () => {
      toast.success("เพิ่มกิจกรรมสำเร็จแล้ว");
      setAddDialogOpen(false);
      setFormData({
        petId: 0,
        date: new Date().toISOString().split('T')[0],
        activityType: "play",
        description: "",
        photoUrls: [],
        instagramPostUrl: "",
        duration: 0,
        location: "",
        notes: ""
      });
      setUploadedImages([]);
    },
    onError: (error) => {
      toast.error(`เพิ่มกิจกรรมไม่สำเร็จ: ${error.message}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      api.dailyActivities.update.mutate({ activityId: id, ...data }),
    onSuccess: () => {
      toast.success("อัพเดทข้อมูลกิจกรรมสำเร็จแล้ว");
      setEditDialogOpen(false);
    },
    onError: (error) => {
      toast.error(`อัพเดทข้อมูลกิจกรรมไม่สำเร็จ: ${error.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.dailyActivities.delete.mutate({ activityId: id }),
    onSuccess: () => {
      toast.success("ลบกิจกรรมสำเร็จแล้ว");
    },
    onError: (error) => {
      toast.error(`ลบกิจกรรมไม่สำเร็จ: ${error.message}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.petId || !formData.description) {
      toast.error("กรุณากรอกข้อมูลที่จำเป็นทั้งหมด");
      return;
    }

    const activityData = {
      ...formData,
      photoUrls: uploadedImages.length > 0 ? JSON.stringify(uploadedImages) : null,
      date: new Date(formData.date).toISOString(),
    };

    createMutation.mutate(activityData);
  };

  const handleEdit = (activity: any) => {
    setSelectedActivity(activity);
    const photoUrls = activity.photoUrls ? JSON.parse(activity.photoUrls) : [];
    setUploadedImages(photoUrls);

    setFormData({
      petId: activity.petId,
      date: format(new Date(activity.date), "yyyy-MM-dd"),
      activityType: activity.activityType,
      description: activity.description,
      photoUrls: photoUrls,
      instagramPostUrl: activity.instagramPostUrl || "",
      duration: activity.duration || 0,
      location: activity.location || "",
      notes: activity.notes || ""
    });
    setEditDialogOpen(true);
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedActivity) return;

    const activityData = {
      ...formData,
      photoUrls: uploadedImages.length > 0 ? JSON.stringify(uploadedImages) : null,
      date: new Date(formData.date).toISOString(),
    };

    updateMutation.mutate({
      id: selectedActivity.id,
      data: activityData
    });
  };

  const handleDelete = (id: number) => {
    if (window.confirm("คุณแน่ใจหรือไม่ที่จะลบกิจกรรมนี้?")) {
      deleteMutation.mutate(id);
    }
  };

  const filterActivities = (activities: any[]) => {
    if (activeTab === "all") return activities;
    if (activeTab === "recent") {
      const oneWeekAgo = new Date();
      oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
      return activities.filter(activity => new Date(activity.date) >= oneWeekAgo);
    }
    if (activeTab === "instagram") {
      return activities.filter(activity => activity.instagramPostUrl);
    }
    return activities;
  };

  const filteredActivities = filterActivities(activities || []);

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">บันทึกกิจกรรมรายวัน</h1>
          <p className="text-muted-foreground">บันทึกกิจกรรมประจำวันและแชร์ไปยัง Instagram</p>
        </div>
        <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              เพิ่มกิจกรรม
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px]">
            <form onSubmit={handleSubmit}>
              <DialogHeader>
                <DialogTitle>เพิ่มกิจกรรมใหม่</DialogTitle>
                <DialogDescription>
                  บันทึกกิจกรรมที่สัตว์เลี้ยงของคุณทำในแต่ละวัน
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4 max-h-[70vh] overflow-y-auto">
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
                  <Label htmlFor="date" className="text-right">
                    วันที่
                  </Label>
                  <Input
                    id="date"
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
                    className="col-span-3"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="activityType" className="text-right">
                    ประเภทกิจกรรม
                  </Label>
                  <Select
                    value={formData.activityType}
                    onValueChange={(value) => setFormData(prev => ({ ...prev, activityType: value }))}
                  >
                    <SelectTrigger className="col-span-3">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {activityTypeOptions.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="description" className="text-right">
                    คำอธิบาย
                  </Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    className="col-span-3"
                    rows={2}
                    placeholder="อธิบายเกี่ยวกับกิจกรรมนี้"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="duration" className="text-right">
                    ระยะเวลา (นาที)
                  </Label>
                  <Input
                    id="duration"
                    type="number"
                    value={formData.duration}
                    onChange={(e) => setFormData(prev => ({ ...prev, duration: parseInt(e.target.value) || 0 }))}
                    className="col-span-3"
                    placeholder="60"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="location" className="text-right">
                    สถานที่
                  </Label>
                  <Input
                    id="location"
                    value={formData.location}
                    onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                    className="col-span-3"
                    placeholder="สวนสาธารณะ, บ้าน, เป็นต้น"
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="instagramPostUrl" className="text-right">
                    ลิงก์ Instagram
                  </Label>
                  <Input
                    id="instagramPostUrl"
                    value={formData.instagramPostUrl}
                    onChange={(e) => setFormData(prev => ({ ...prev, instagramPostUrl: e.target.value }))}
                    className="col-span-3"
                    placeholder="https://instagram.com/p/..."
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label className="text-right">
                    รูปภาพ
                  </Label>
                  <div className="col-span-3">
                    <ImageUpload
                      onImagesUploaded={setUploadedImages}
                      initialImages={uploadedImages}
                      maxImages={5}
                    />
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
                    rows={2}
                    placeholder="บันทึกอื่นๆ ที่อยากจดจำ"
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
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="all">ทั้งหมด</TabsTrigger>
          <TabsTrigger value="recent">ล่าสุด (7 วัน)</TabsTrigger>
          <TabsTrigger value="instagram">มี Instagram</TabsTrigger>
        </TabsList>
        <TabsContent value={activeTab} className="space-y-4">
          {activitiesLoading ? (
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
          ) : filteredActivities.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredActivities.map((activity) => (
                <Card key={activity.id} className="relative">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {activityTypeOptions.find(opt => opt.value === activity.activityType)?.label || activity.activityType}
                      {activity.instagramPostUrl && (
                        <Badge variant="outline" className="flex items-center gap-1">
                          <Instagram className="h-3 w-3" />
                          Instagram
                        </Badge>
                      )}
                    </CardTitle>
                    <CardDescription>
                      {pets?.find(pet => pet.id === activity.petId)?.name}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm">
                        <CalendarIcon className="h-4 w-4 text-muted-foreground" />
                        <span>{format(new Date(activity.date), "d MMMM yyyy", { locale: th })}</span>
                      </div>
                      <div className="text-sm">
                        <p>{activity.description}</p>
                      </div>
                      {activity.duration && (
                        <div className="flex items-center gap-2 text-sm">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span>ระยะเวลา: {activity.duration} นาที</span>
                        </div>
                      )}
                      {activity.location && (
                        <div className="flex items-center gap-2 text-sm">
                          <MapPin className="h-4 w-4 text-muted-foreground" />
                          <span>สถานที่: {activity.location}</span>
                        </div>
                      )}
                      {activity.photoUrls && JSON.parse(activity.photoUrls).length > 0 && (
                        <div className="flex items-center gap-2 text-sm">
                          <Camera className="h-4 w-4 text-muted-foreground" />
                          <span>มีรูปภาพ {JSON.parse(activity.photoUrls).length} ภาพ</span>
                        </div>
                      )}
                      {activity.instagramPostUrl && (
                        <div className="flex items-center gap-2 text-sm">
                          <Link2 className="h-4 w-4 text-muted-foreground" />
                          <a
                            href={activity.instagramPostUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-500 hover:underline"
                          >
                            ดูใน Instagram
                          </a>
                        </div>
                      )}
                      {activity.notes && (
                        <div className="text-sm">
                          <span className="font-medium">หมายเหตุ:</span> {activity.notes}
                        </div>
                      )}
                    </div>
                    <div className="mt-4 flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(activity)}
                      >
                        <Edit className="h-4 w-4 mr-1" />
                        แก้ไข
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(activity.id)}
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
                <CardTitle>ไม่มีข้อมูลกิจกรรม</CardTitle>
                <CardDescription>
                  คุณยังไม่ได้เพิ่มกิจกรรมใดๆ คลิกปุ่ม "เพิ่มกิจกรรม" เพื่อเริ่มต้น
                </CardDescription>
              </CardHeader>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <form onSubmit={handleEditSubmit}>
            <DialogHeader>
              <DialogTitle>แก้ไขข้อมูลกิจกรรม</DialogTitle>
              <DialogDescription>
                แก้ไขข้อมูลกิจกรรมที่คุณได้บันทึกไว้
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4 max-h-[70vh] overflow-y-auto">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-activityType" className="text-right">
                  ประเภทกิจกรรม
                </Label>
                <Select
                  value={formData.activityType}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, activityType: value }))}
                >
                  <SelectTrigger className="col-span-3" id="edit-activityType">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {activityTypeOptions.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-date" className="text-right">
                  วันที่
                </Label>
                <Input
                  id="edit-date"
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-description" className="text-right">
                  คำอธิบาย
                </Label>
                <Textarea
                  id="edit-description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="col-span-3"
                  rows={2}
                  placeholder="อธิบายเกี่ยวกับกิจกรรมนี้"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-duration" className="text-right">
                  ระยะเวลา (นาที)
                </Label>
                <Input
                  id="edit-duration"
                  type="number"
                  value={formData.duration}
                  onChange={(e) => setFormData(prev => ({ ...prev, duration: parseInt(e.target.value) || 0 }))}
                  className="col-span-3"
                  placeholder="60"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-location" className="text-right">
                  สถานที่
                </Label>
                <Input
                  id="edit-location"
                  value={formData.location}
                  onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                  className="col-span-3"
                  placeholder="สวนสาธารณะ, บ้าน, เป็นต้น"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-instagramPostUrl" className="text-right">
                  ลิงก์ Instagram
                </Label>
                <Input
                  id="edit-instagramPostUrl"
                  value={formData.instagramPostUrl}
                  onChange={(e) => setFormData(prev => ({ ...prev, instagramPostUrl: e.target.value }))}
                  className="col-span-3"
                  placeholder="https://instagram.com/p/..."
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">
                  รูปภาพ
                </Label>
                <div className="col-span-3">
                  <ImageUpload
                    onImagesUploaded={setUploadedImages}
                    initialImages={uploadedImages}
                    maxImages={5}
                  />
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
                  rows={2}
                  placeholder="บันทึกอื่นๆ ที่อยากจดจำ"
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
