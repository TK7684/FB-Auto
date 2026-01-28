import { useState } from "react";
import { Camera, Upload, X, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { api } from "@/lib/trpc";

interface ImageUploadProps {
  onImagesUploaded: (urls: string[]) => void;
  initialImages?: string[];
  maxImages?: number;
}

export function ImageUpload({
  onImagesUploaded,
  initialImages = [],
  maxImages = 5,
}: ImageUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedImages, setUploadedImages] = useState<string[]>(initialImages);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;

    const files = Array.from(e.target.files);
    const validFiles = files.filter(file => {
      if (!file.type.startsWith('image/')) {
        toast.error(`ไฟล์ ${file.name} ไม่ใช่รูปภาพ`);
        return false;
      }
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        toast.error(`ไฟล์ ${file.name} ใหญ่เกิน 5MB`);
        return false;
      }
      return true;
    });

    if (uploadedImages.length + validFiles.length > maxImages) {
      toast.error(`คุณสามารถอัปโหลดรูปภาพได้สูงสุด ${maxImages} รูป`);
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const newImageUrls: string[] = [];

      for (let i = 0; i < validFiles.length; i++) {
        const file = validFiles[i];

        try {
          // Get upload URL from server
          const { uploadUrl, fileUrl } = await api.storage.getUploadUrl.query({
            fileName: file.name,
            fileType: file.type,
            folder: 'pet-health',
          });

          // Upload file to S3
          const xhr = new XMLHttpRequest();

          // Use Promise to handle the upload progress
          await new Promise<void>((resolve, reject) => {
            xhr.upload.addEventListener('progress', (e) => {
              if (e.lengthComputable) {
                const progress = Math.round(((i * 100) + (e.loaded / e.total) * 100) / validFiles.length);
                setUploadProgress(progress);
              }
            });

            xhr.addEventListener('load', () => {
              if (xhr.status >= 200 && xhr.status < 300) {
                resolve();
              } else {
                reject(new Error(`อัปโหลด ${file.name} ไม่สำเร็จ`));
              }
            });

            xhr.addEventListener('error', () => {
              reject(new Error(`อัปโหลด ${file.name} ไม่สำเร็จ`));
            });

            xhr.open('PUT', uploadUrl, true);
            xhr.setRequestHeader('Content-Type', file.type);
            xhr.send(file);
          });

          newImageUrls.push(fileUrl);
          setUploadProgress(Math.round(((i + 1) / validFiles.length) * 100));
        } catch (error) {
          console.error('Upload error:', error);
          toast.error(`อัปโหลด ${file.name} ไม่สำเร็จ: ${error instanceof Error ? error.message : 'ข้อผิดพลาดที่ไม่ทราบสาเหตุ'}`);
        }
      }

      if (newImageUrls.length > 0) {
        const updatedImages = [...uploadedImages, ...newImageUrls];
        setUploadedImages(updatedImages);
        onImagesUploaded(updatedImages);
        toast.success(`อัปโหลดรูปภาพ ${newImageUrls.length} รูปสำเร็จแล้ว`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(`อัปโหลดรูปภาพไม่สำเร็จ: ${error instanceof Error ? error.message : 'ข้อผิดพลาดที่ไม่ทราบสาเหตุ'}`);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);

      // Reset file input
      if (e.target) {
        e.target.value = '';
      }
    }
  };

  const removeImage = (index: number) => {
    const updatedImages = [...uploadedImages];
    updatedImages.splice(index, 1);
    setUploadedImages(updatedImages);
    onImagesUploaded(updatedImages);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {uploadedImages.map((url, index) => (
          <div key={index} className="relative group">
            <Card className="overflow-hidden w-24 h-24">
              <CardContent className="p-0 h-full">
                <img
                  src={url}
                  alt={`อัปโหลดแล้ว ${index + 1}`}
                  className="w-full h-full object-cover"
                />
              </CardContent>
            </Card>
            <Button
              variant="destructive"
              size="icon"
              className="absolute top-1 right-1 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={() => removeImage(index)}
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        ))}
        {uploadedImages.length < maxImages && (
          <Card className="overflow-hidden w-24 h-24 border-dashed border-2 border-muted-foreground/25 hover:border-muted-foreground/50 transition-colors">
            <CardContent className="p-0 h-full">
              <label className="flex flex-col items-center justify-center h-full cursor-pointer">
                <Camera className="h-6 w-6 text-muted-foreground mb-1" />
                <span className="text-xs text-muted-foreground text-center">
                  {uploadedImages.length > 0 ? 'เพิ่ม' : 'อัปโหลด'}
                </span>
                <input
                  type="file"
                  className="hidden"
                  accept="image/*"
                  multiple
                  onChange={handleFileSelect}
                  disabled={isUploading}
                />
              </label>
            </CardContent>
          </Card>
        )}
      </div>

      {isUploading && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>กำลังอัปโหลด...</span>
            <span>{uploadProgress}%</span>
          </div>
          <Progress value={uploadProgress} className="h-2" />
        </div>
      )}

      <div className="text-xs text-muted-foreground">
        อัปโหลดรูปภาพได้สูงสุด {maxImages} รูป (สูงสุด 5MB ต่อรูป)
      </div>
    </div>
  );
}
