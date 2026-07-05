import customtkinter as ctk

class InventoryModule(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("إدارة المخزن - Collect Milk System")
        self.geometry("800x600")

        # العنوان الرئيسي
        ctk.CTkLabel(self, text="نظام إدارة المخزن", font=("Segoe UI", 24, "bold")).pack(pady=20)

        # التبويبات (Tabview)
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # إنشاء التبويبين
        self.tab_maintenance = self.tabview.add("قطع الصيانة")
        self.tab_agri = self.tabview.add("الأعلاف والمواد الفلاحية")

        # محتوى تبويب الصيانة
        self._setup_maintenance()
        
        # محتوى تبويب الفلاحة
        self._setup_agri()

    def _setup_maintenance(self):
        ctk.CTkLabel(self.tab_maintenance, text="سجل قطع غيار الأسطول", font=("Arial", 16)).pack(pady=10)
        # هنا سنضع جدول البيانات لاحقاً
        btn = ctk.CTkButton(self.tab_maintenance, text="إضافة قطعة صيانة", fg_color="#C0392B")
        btn.pack(pady=10)

    def _setup_agri(self):
        ctk.CTkLabel(self.tab_agri, text="سجل صرف المواد للفلاحين", font=("Arial", 16)).pack(pady=10)
        # حقل إدخال ID الفلاح
        self.farmer_id_entry = ctk.CTkEntry(self.tab_agri, placeholder_text="أدخل ID الفلاح")
        self.farmer_id_entry.pack(pady=5)
        
        btn = ctk.CTkButton(self.tab_agri, text="صرف مادة (ربط بالـ ID)", fg_color="#F39C12")
        btn.pack(pady=10)