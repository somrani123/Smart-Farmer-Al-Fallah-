import customtkinter as ctk

# إعدادات الواجهة
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class GlassApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("نظام إدارة المؤسسة - Karim System")
        self.geometry("900x500")
        
        # حاوية زجاجية رئيسية
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # شريط البحث الذكي
        self.search_entry = ctk.CTkEntry(self.main_frame, placeholder_text="ابحث في بياناتك أو اسأل Gemini...", height=50)
        self.search_entry.pack(fill="x", pady=(0, 30))

        # حاوية الأزرار (4 مكعبات)
        self.buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.buttons_frame.pack(fill="both", expand=True)

        # إنشاء الأزرار الملونة بتأثير الزجاج
        btn_data = [
            ("إدارة المخزن", "#27AE60"),
            ("جمع الحليب", "#F39C12"),
            ("الأفراد والعمال", "#8E44AD"),
            ("إدارة السيارات", "#C0392B")
        ]

        for text, color in btn_data:
            btn = ctk.CTkButton(
                self.buttons_frame, 
                text=text, 
                fg_color=color,
                hover_color="#333333",
                height=150, 
                font=("Arial", 18, "bold"),
                corner_radius=20
            )
            btn.pack(side="left", expand=True, fill="both", padx=10)

if __name__ == "__main__":
    app = GlassApp()
    app.mainloop()