import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Check, Star, Heart, Shield, Clock, Zap, Users, ArrowRight, Calendar, Bell, FileText, Download, ChevronRight, PawPrint, Camera, Instagram, Crown, Mail } from "lucide-react";
import { useState } from "react";
import { Link } from "wouter";

export default function LandingPage() {
  const [activeTestimonial, setActiveTestimonial] = useState(0);

  const testimonials = [
    {
      name: "คุณสมชาย",
      petName: "โมโม่",
      role: "เจ้าของสุนัข",
      content: "PetHealth ช่วยให้ฉันจัดการวัคซีนของโมโม่ได้อย่างง่ายดาย ไม่พลาดการฉีดวัคซีนอีกเลย! แจ้งเตือนล่วงหน้ามากมาย",
      avatar: "🐕",
      rating: 5,
    },
    {
      name: "คุณมานี",
      petName: "ลูนา",
      role: "เจ้าของแมว",
      content: "ฉันชอบฟีเจอร์บันทึกกิจกรรมรายวันและการเชื่อมต่อกับ Instagram สามารถเก็บความทรงจำช่วงเวลาที่ดีๆ ของลูนาได้",
      avatar: "🐱",
      rating: 5,
    },
    {
      name: "คุณวีระ",
      petName: "ฮามี",
      role: "เจ้าของกระต่าย",
      content: "แผนพรีเมียมคุ้มค่ากับฟีเจอร์ทั้งหมด! สามารถติดตามค่าใช้จ่ายและสุขภาพของฮามีได้ในที่เดียว",
      avatar: "🐹",
      rating: 5,
    },
  ];

  const features = [
    {
      title: "จัดการสัตว์เลี้ยงหลายตัว",
      description: "เก็บข้อมูลสัตว์เลี้ยงทั้งหมดของคุณไว้ในที่เดียว",
      icon: <PawPrint className="h-8 w-8 text-primary" />,
      premium: true,
    },
    {
      title: "บันทึกสุขภาพและการไปหาหมอ",
      description: "บันทึกประวัติการแพทย์ อาการ คำวินิจฉัย และค่าใช้จ่าย",
      icon: <Heart className="h-8 w-8 text-primary" />,
      premium: false,
    },
    {
      title: "แจ้งเตือนอัตโนมัติ",
      description: "รับการแจ้งเตือนทางอีเมลก่อนถึงวันฉีดวัคซีนและวันที่ต้องให้ยา",
      icon: <Bell className="h-8 w-8 text-primary" />,
      premium: true,
    },
    {
      title: "ติดตามยาเห็บหมัดและยาถ่ายพยาธิ",
      description: "ตั้งค่าการแจ้งเตือนสำหรับการให้ยาเห็บหมัดและยาถ่ายพยาธิ",
      icon: <Shield className="h-8 w-8 text-primary" />,
      premium: true,
    },
    {
      title: "บันทึกกิจกรรมรายวัน",
      description: "จดบันทึกกิจกรรมประจำวันและเชื่อมต่อกับ Instagram",
      icon: <Calendar className="h-8 w-8 text-primary" />,
      premium: true,
    },
    {
      title: "อัปโหลดรูปภาพ",
      description: "อัปโหลดรูปสัตว์เลี้ยงและเอกสารสำคัญได้อย่างปลอดภัย",
      icon: <Camera className="h-8 w-8 text-primary" />,
      premium: true,
    },
    {
      title: "ติดตามค่าใช้จ่าย",
      description: "บันทึกและวิเคราะห์ค่าใช้จ่ายทั้งหมดเกี่ยวกับสัตว์เลี้ยง",
      icon: <FileText className="h-8 w-8 text-primary" />,
      premium: true,
    },
    {
      title: "ดูแลสัตว์ป่วย",
      description: "จัดการข้อมูลและการดูแลเมื่อสัตว์เลี้ยงป่วย",
      icon: <Shield className="h-8 w-8 text-primary" />,
      premium: true,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-blue-100">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="text-2xl">🐾</div>
            <span className="text-xl font-bold text-primary">PetHealth</span>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-sm font-medium hover:text-primary transition-colors">คุณสมบัติ</a>
            <a href="#pricing" className="text-sm font-medium hover:text-primary transition-colors">ราคา</a>
            <a href="#testimonials" className="text-sm font-medium hover:text-primary transition-colors">รีวิว</a>
          </nav>
          <div className="flex gap-3">
            <Link href="/login">
              <Button variant="outline">เข้าสู่ระบบ</Button>
            </Link>
            <Link href="/signup">
              <Button>สมัครสมาชิก</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="max-w-3xl mx-auto">
          <Badge className="mb-4 bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors">
            🎉 ใหม่! ระบบแจ้งเตือนอัตโนมัติและการจัดการยา
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 text-transparent bg-clip-text">
            แอปจัดการสุขภาพสัตว์เลี้ยงที่สมบูรณ์
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            เก็บข้อมูลสุขภาพ วัคซีน การให้ยา และกิจกรรมของสัตว์เลี้ยงของคุณไว้ในที่เดียว
            พร้อมระบบแจ้งเตือนอัตโนมัติเพื่อไม่พลาดวันสำคัญ
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/signup">
              <Button size="lg" className="text-lg px-8 py-3 h-auto">
                เริ่มใช้งานฟรี
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Button variant="outline" size="lg" className="text-lg px-8 py-3 h-auto">
              ดูตัวอย่าง
            </Button>
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          <div>
            <h3 className="text-3xl font-bold text-primary">1,000+</h3>
            <p className="text-sm text-muted-foreground">สัตว์เลี้ยงที่ลงทะเบียน</p>
          </div>
          <div>
            <h3 className="text-3xl font-bold text-primary">5,000+</h3>
            <p className="text-sm text-muted-foreground">บันทึกสุขภาพ</p>
          </div>
          <div>
            <h3 className="text-3xl font-bold text-primary">98%</h3>
            <p className="text-sm text-muted-foreground">ความพึงพอใจของผู้ใช้</p>
          </div>
          <div>
            <h3 className="text-3xl font-bold text-primary">24/7</h3>
            <p className="text-sm text-muted-foreground">การแจ้งเตือนอัตโนมัติ</p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="container mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">คุณสมบัติทั้งหมดที่คุณต้องการ</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            จัดการสัตว์เลี้ยงของคุณได้อย่างง่ายดายด้วยเครื่องมือที่ออกแบบมาเพื่อให้ใช้งานง่าย
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <Card key={index} className="relative overflow-hidden">
              {feature.premium && (
                <Badge className="absolute top-4 right-4 bg-gradient-to-r from-amber-500 to-orange-500 text-white">
                  <Crown className="h-3 w-3 mr-1" />
                  Premium
                </Badge>
              )}
              <CardHeader className="text-center pb-4">
                <div className="mx-auto mb-4 p-3 rounded-full bg-blue-50 w-fit">
                  {feature.icon}
                </div>
                <CardTitle className="text-xl">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-center text-base">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="container mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">เลือกแผนที่เหมาะกับคุณ</h2>
          <p className="text-lg text-muted-foreground">
            เริ่มต้นได้ฟรี อัพเกรดเมื่อคุณพร้อมใช้ฟีเจอร์เพิ่มเติม
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 max-w-4xl mx-auto">
          {/* Free Plan */}
          <Card className="relative">
            <CardHeader className="text-center pb-4">
              <CardTitle className="text-2xl">ฟรี</CardTitle>
              <CardDescription>เหมาะสำหรับการลองใช้งาน</CardDescription>
              <div className="mt-4">
                <span className="text-5xl font-bold">฿0</span>
                <span className="text-lg text-muted-foreground">/เดือน</span>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="space-y-3">
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>สัตว์เลี้ยง 1 ตัว</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>บันทึกสุขภาพ 10 รายการ/เดือน</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>บันทึกพฤติกรรม 5 รายการ/เดือน</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>ติดตามวัคซีนและน้ำหนัก</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>ตารางให้อาหารและกิจกรรมรายวัน</span>
                </li>
                <Separator />
                <li className="flex items-start gap-2">
                  <div className="h-5 w-5 flex items-center justify-center">
                    <div className="h-4 w-4 rounded-full bg-gray-200"></div>
                  </div>
                  <span className="text-muted-foreground">สัตว์เลี้ยงไม่จำกัด</span>
                </li>
                <li className="flex items-start gap-2">
                  <div className="h-5 w-5 flex items-center justify-center">
                    <div className="h-4 w-4 rounded-full bg-gray-200"></div>
                  </div>
                  <span className="text-muted-foreground">ติดตามค่าใช้จ่ายและดูแลสัตว์ป่วย</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Premium Plan */}
          <Card className="relative border-2 border-primary shadow-lg">
            <Badge className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-primary to-blue-600 text-white">
              ยอดนิยมที่สุด
            </Badge>
            <CardHeader className="text-center pb-4">
              <CardTitle className="text-2xl flex items-center justify-center gap-2">
                <Crown className="h-6 w-6 text-primary" />
                พรีเมียม
              </CardTitle>
              <CardDescription>เข้าถึงฟีเจอร์ทั้งหมด</CardDescription>
              <div className="mt-4">
                <span className="text-5xl font-bold">฿350</span>
                <span className="text-lg text-muted-foreground">/เดือน</span>
                <div className="text-sm text-muted-foreground mt-1">
                  หรือ฿3,500/ปี (ประหยัด 2 เดือน)
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="space-y-3">
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                  <span>สัตว์เลี้ยงไม่จำกัด</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                  <span>บันทึกไม่จำกัด</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                  <span>ติดตามค่าใช้จ่ายและดูแลสัตว์ป่วย</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                  <span>อัปโหลดรูปภาพและเอกสาร</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                  <span>การแจ้งเตือนอัตโนมัติ</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                  <span>จัดการยาเห็บหมัดและยาถ่ายพยาธิ</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                  <span>บันทึกกิจกรรมและเชื่อมต่อกับ Instagram</span>
                </li>
                <Separator />
                <li className="flex items-start gap-2">
                  <Zap className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                  <span>ฟีเจอร์ใหม่ที่เพิ่มเข้ามาทุกเดือน</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="container mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">ผู้ใช้งานพูดถึงเรา</h2>
          <p className="text-lg text-muted-foreground">
            ความคิดเห็นจากผู้ใช้ PetHealth ทั่วประเทศ
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <div className="grid gap-8 lg:grid-cols-3">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className={`h-full ${activeTestimonial === index ? 'ring-2 ring-primary/20' : ''}`}>
                <CardHeader>
                  <div className="flex items-center gap-3 mb-2">
                    <div className="text-4xl">{testimonial.avatar}</div>
                    <div>
                      <h4 className="font-semibold">{testimonial.name}</h4>
                      <p className="text-sm text-muted-foreground">{testimonial.role}</p>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star
                        key={i}
                        className={`h-4 w-4 ${
                          i < testimonial.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                  <CardDescription className="italic text-base">
                    "{testimonial.content}"
                  </CardDescription>
                  <p className="text-sm font-medium mt-2">- {testimonial.petName}</p>
                </CardHeader>
              </Card>
            ))}
          </div>

          {/* Testimonial Navigation */}
          <div className="flex justify-center gap-2 mt-8">
            {testimonials.map((_, index) => (
              <button
                key={index}
                className={`w-2 h-2 rounded-full ${
                  activeTestimonial === index ? 'bg-primary' : 'bg-gray-300'
                }`}
                onClick={() => setActiveTestimonial(index)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-primary to-blue-600 text-white py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">พร้อมเริ่มจัดการสุขภาพสัตว์เลี้ยงของคุณหรือ?</h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            เข้าร่วมกับผู้ใช้งานมากกว่า 1,000 คนที่เชื่อถือใน PetHealth
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/signup">
              <Button size="lg" variant="secondary" className="text-lg px-8 py-3 h-auto">
                สมัครสมาชิกฟรี
              </Button>
            </Link>
            <Link href="/pricing">
              <Button size="lg" variant="outline" className="text-lg px-8 py-3 h-auto bg-white text-primary border-white hover:bg-white/90">
                ดูแผนราคา
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">คำถามที่พบบ่อย</h2>
        </div>

        <div className="max-w-3xl mx-auto space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">PetHealth ฟรีหรือเปล่า?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                PetHealth มีแผนฟรีและพรีเมียม แผนฟรีเหมาะสำหรับผู้ที่ต้องการลองใช้งาน และแผนพรีเมียมสำหรับผู้ที่ต้องการฟีเจอร์ครบถ้วย
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">ฉันสามารถเปลี่ยนแผนได้หรือไม่?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                ได้ค่ะ คุณสามารถเปลี่ยนระหว่างแผนฟรีและพรีเมียมได้ทุกเวลา
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">ข้อมูลของฉันปลอดภัยหรือไม่?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                ใช่ เราใช้การเข้ารหัสแบบ end-to-end และจัดเก็บข้อมูลในเซิร์ฟเวอร์ที่ปลอดภัย
                ข้อมูลสัตว์เลี้ยงของคุณจะถูกเก็บเป็นความลับเสมอ
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">ฉันสามารถใช้งานบนมือถือได้หรือไม่?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                ได้ค่ะ PetHealth รองรับบนอุปกรณ์ทุกชนิด ทั้งบนคอมพิวเตอร์และมือถือ
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-100 py-12">
        <div className="container mx-auto px-4">
          <div className="grid gap-8 md:grid-cols-4 mb-8">
            <div>
              <h3 className="text-lg font-semibold mb-4">PetHealth</h3>
              <p className="text-muted-foreground text-sm">
                แอปจัดการสุขภาพสัตว์เลี้ยงที่สมบูรณ์ สำหรับผู้ที่รักสัตว์เลี้ยง
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4">คุณสมบัติ</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" className="text-muted-foreground hover:text-primary transition-colors">บันทึกสุขภาพ</a></li>
                <li><a href="#features" className="text-muted-foreground hover:text-primary transition-colors">จัดการวัคซีน</a></li>
                <li><a href="#features" className="text-muted-foreground hover:text-primary transition-colors">บันทึกกิจกรรม</a></li>
                <li><a href="#features" className="text-muted-foreground hover:text-primary transition-colors">จัดการยา</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4">บริษัท</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#pricing" className="text-muted-foreground hover:text-primary transition-colors">แผนราคา</a></li>
                <li><a href="#" className="text-muted-foreground hover:text-primary transition-colors">ความเป็นส่วนตัว</a></li>
                <li><a href="#" className="text-muted-foreground hover:text-primary transition-colors">นโยบายความเป็นส่วนตัว</a></li>
                <li><a href="#" className="text-muted-foreground hover:text-primary transition-colors">ติดต่อเรา</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4">ติดต่อ</h3>
              <div className="flex gap-3">
                <Button variant="outline" size="icon" className="h-10 w-10">
                  <Mail className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="icon" className="h-10 w-10">
                  <Instagram className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
          <Separator />
          <div className="text-center text-sm text-muted-foreground py-4">
            <p>&copy; {new Date().getFullYear()} PetHealth. สงวนลิขสิทธิ์</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
