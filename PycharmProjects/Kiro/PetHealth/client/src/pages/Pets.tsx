import DashboardLayout from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { trpc } from "@/lib/trpc";
import { PawPrint, Plus, Trash2, Edit } from "lucide-react";
import { useState } from "react";
import { Link } from "wouter";
import { toast } from "sonner";

export default function Pets() {
  const [open, setOpen] = useState(false);
  const [editingPet, setEditingPet] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: "",
    breed: "",
    birthDate: "",
    gender: "unknown" as "male" | "female" | "unknown",
  });

  const { data: pets, isLoading } = trpc.pets.list.useQuery();
  const { data: subscription } = trpc.subscription.get.useQuery();
  const utils = trpc.useUtils();

  const createMutation = trpc.pets.create.useMutation({
    onSuccess: () => {
      utils.pets.list.invalidate();
      toast.success("Pet added successfully!");
      setOpen(false);
      resetForm();
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const updateMutation = trpc.pets.update.useMutation({
    onSuccess: () => {
      utils.pets.list.invalidate();
      toast.success("Pet updated successfully!");
      setOpen(false);
      resetForm();
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const deleteMutation = trpc.pets.delete.useMutation({
    onSuccess: () => {
      utils.pets.list.invalidate();
      toast.success("Pet deleted successfully!");
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const resetForm = () => {
    setFormData({ name: "", breed: "", birthDate: "", gender: "unknown" });
    setEditingPet(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (editingPet) {
      updateMutation.mutate({
        petId: editingPet.id,
        ...formData,
      });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleEdit = (pet: any) => {
    setEditingPet(pet);
    setFormData({
      name: pet.name,
      breed: pet.breed || "",
      birthDate: pet.birthDate ? new Date(pet.birthDate).toISOString().split("T")[0] : "",
      gender: pet.gender || "unknown",
    });
    setOpen(true);
  };

  const handleDelete = (petId: number) => {
    if (confirm("Are you sure you want to delete this pet?")) {
      deleteMutation.mutate({ petId });
    }
  };

  const tier = subscription?.tier || "free";
  const canAddMore = tier === "premium" || (pets?.length || 0) < 1;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">My Pets</h1>
            <p className="text-muted-foreground mt-1">
              Manage your pets and their information
            </p>
          </div>
          <Dialog open={open} onOpenChange={(isOpen) => {
            setOpen(isOpen);
            if (!isOpen) resetForm();
          }}>
            <DialogTrigger asChild>
              <Button size="lg" className="gap-2" disabled={!canAddMore}>
                <Plus className="h-5 w-5" />
                Add Pet
              </Button>
            </DialogTrigger>
            <DialogContent>
              <form onSubmit={handleSubmit}>
                <DialogHeader>
                  <DialogTitle>{editingPet ? "Edit Pet" : "Add New Pet"}</DialogTitle>
                  <DialogDescription>
                    {editingPet ? "Update your pet's information" : "Add a new pet to your account"}
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Name *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="breed">Breed</Label>
                    <Input
                      id="breed"
                      value={formData.breed}
                      onChange={(e) => setFormData({ ...formData, breed: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="birthDate">Birth Date</Label>
                    <Input
                      id="birthDate"
                      type="date"
                      value={formData.birthDate}
                      onChange={(e) => setFormData({ ...formData, birthDate: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gender">Gender</Label>
                    <Select
                      value={formData.gender}
                      onValueChange={(value: "male" | "female" | "unknown") =>
                        setFormData({ ...formData, gender: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="male">Male</SelectItem>
                        <SelectItem value="female">Female</SelectItem>
                        <SelectItem value="unknown">Unknown</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setOpen(false);
                      resetForm();
                    }}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                    {editingPet ? "Update" : "Add"} Pet
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {!canAddMore && (
          <Card className="border-primary/50 bg-primary/5">
            <CardHeader>
              <CardTitle className="text-primary">Free Tier Limit Reached</CardTitle>
              <CardDescription>
                You've reached the maximum of 1 pet on the free tier. Upgrade to Premium for unlimited pets.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/subscription">
                <Button variant="default">Upgrade to Premium</Button>
              </Link>
            </CardContent>
          </Card>
        )}

        {isLoading ? (
          <div className="text-center py-12 text-muted-foreground">Loading your pets...</div>
        ) : pets && pets.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {pets.map((pet) => (
              <Card key={pet.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
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
                          {pet.breed || "Unknown breed"}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => handleEdit(pet)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => handleDelete(pet.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Gender:</span>
                      <span className="font-medium capitalize">{pet.gender}</span>
                    </div>
                    {pet.birthDate && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Age:</span>
                        <span className="font-medium">
                          {Math.floor(
                            (Date.now() - new Date(pet.birthDate).getTime()) /
                              (1000 * 60 * 60 * 24 * 365)
                          )}{" "}
                          years old
                        </span>
                      </div>
                    )}
                  </div>
                  <Link href={`/pets/${pet.id}`}>
                    <Button className="w-full mt-4" variant="outline">
                      View Profile
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-12 text-center">
              <PawPrint className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">No pets yet</h3>
              <p className="text-muted-foreground mb-6">
                Add your first pet to start tracking their health and wellness
              </p>
              <Button onClick={() => setOpen(true)} size="lg">
                <Plus className="h-5 w-5 mr-2" />
                Add Your First Pet
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
