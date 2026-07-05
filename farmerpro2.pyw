import customtkinter as ctk
from tkinter import ttk
import sqlite3
from datetime import datetime
import json
import os
import webbrowser

# إعداد المظهر العام والتناسق
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SecondaryWindow(ctk.CTkToplevel):
    """Base class for secondary windows with language switching support"""
    
    def __init__(self, main_app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_app = main_app
        self.translations = main_app.translations
        self.current_language = main_app.current_language
        
        # Auto-register with main app
        self.main_app.register_sub_window(self)
        
        # Bind destroy event to unregister
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def tr(self, key, **kwargs):
        """Get translated string using main app's translation system"""
        return self.main_app.tr(key, **kwargs)
    
    def refresh_ui(self):
        """Refresh UI elements with current language - to be overridden by subclasses"""
        pass
    
    def on_close(self):
        """Handle window close - unregister and destroy"""
        self.main_app.unregister_sub_window(self)
        self.destroy()

class FellahApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Load translations
        self.translations = {}
        self.current_language = 'ar'
        self.load_language()
        
        # Subscriber pattern for secondary windows
        self.sub_windows = []
        
        self.title(self.tr('app.title'))
        self.geometry("1100x850")
        self.minsize(1000, 650)
        
        # متغيرات التحكم والتعديل
        self.selected_expense_id = None
        self.selected_stock_id = None
        
        # إنشاء وتحديث قاعدة البيانات
        self.init_db()
        
        # --- إنشاء الحاوية الرئيسية القابلة للتمرير لحل مشكلة الافيشاج ---
        self.main_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # العنوان الرئيسي
        self.title_label = ctk.CTkLabel(self.main_container, text=self.tr('app.subtitle'), font=("Arial", 22, "bold"))
        self.title_label.pack(pady=10)
        
        # Language selector
        self.lang_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.lang_frame.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(self.lang_frame, text=self.tr('common.language'), font=("Arial", 11)).pack(side="right", padx=5)
        self.lang_combo = ctk.CTkComboBox(self.lang_frame, 
                                          values=[self.tr('common.language_names.ar'), 
                                                 self.tr('common.language_names.fr'), 
                                                 self.tr('common.language_names.en')],
                                          command=lambda e: self.on_language_change(),
                                          width=120)
        self.lang_combo.pack(side="right", padx=5)
        self.lang_combo.set(self.tr('common.language_names.ar'))
        
        # --- استخدام نظام التبويب (Tabs) لتنظيم الشاشة بشكل مريح ---
        self.tab_view = ctk.CTkTabview(self.main_container, width=1050)
        self.tab_view.pack(pady=5, padx=10, fill="both", expand=True)
        
        # Store tab names for recreation during language change
        self.tab_names = {
            'finance': self.tr('tabs.finance'),
            'inventory': self.tr('tabs.inventory')
        }
        
        self.tab_finance = self.tab_view.add(self.tab_names['finance'])
        self.tab_inventory = self.tab_view.add(self.tab_names['inventory'])
        
        # =========================================================================
        # 1. تصميم واجهة الحسابات والعمليات المالية (التبويب الأول)
        # =========================================================================
        self.form_frame = ctk.CTkFrame(self.tab_finance)
        self.form_frame.pack(pady=10, padx=10, fill="x")
        
        # السطر الأول: الأرض والنوع
        self.row1 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.row1.pack(fill="x", pady=5, padx=10)
        
        self.plot_label = ctk.CTkLabel(self.row1, text=self.tr('finance.labels.plot'), font=("Arial", 12))
        self.plot_label.pack(side="right", padx=5)
        self.plot_combo = ctk.CTkComboBox(self.row1, values=self.get_plot_names(), width=180)
        self.plot_combo.pack(side="right", padx=10)
        
        self.type_label = ctk.CTkLabel(self.row1, text=self.tr('finance.labels.operation_type'), font=("Arial", 12))
        self.type_label.pack(side="right", padx=5)
        self.type_combo = ctk.CTkComboBox(self.row1, values=self.get_operation_types(), width=180)
        self.type_combo.pack(side="right", padx=10)
        
        # السطر الثاني: البيان والمبلغ
        self.row2 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.row2.pack(fill="x", pady=5, padx=10)
        
        self.item_entry = ctk.CTkEntry(self.row2, placeholder_text=self.tr('finance.labels.item'), width=300)
        self.item_entry.pack(side="right", padx=5, expand=True, fill="x")
        
        self.category_combo = ctk.CTkComboBox(self.row2, values=self.get_categories(), width=130)
        self.category_combo.pack(side="right", padx=5)
        
        self.cost_entry = ctk.CTkEntry(self.row2, placeholder_text=self.tr('finance.labels.amount'), width=100)
        self.cost_entry.pack(side="right", padx=5)
        
        # أزرار المالية
        self.btn_frame = ctk.CTkFrame(self.tab_finance, fg_color="transparent")
        self.btn_frame.pack(pady=5)
        
        self.save_btn = ctk.CTkButton(self.btn_frame, text=self.tr('finance.buttons.save'), command=self.save_expense, fg_color="green", hover_color="darkgreen", width=120)
        self.save_btn.grid(row=0, column=0, padx=5)
        
        self.refresh_btn = ctk.CTkButton(self.btn_frame, text=self.tr('finance.buttons.refresh'), command=self.load_finance_data, fg_color="blue", width=120)
        self.refresh_btn.grid(row=0, column=1, padx=5)
        
        self.update_btn = ctk.CTkButton(self.btn_frame, text=self.tr('finance.buttons.update'), command=self.update_expense, fg_color="#e67e22", hover_color="#d35400", width=120)
        self.update_btn.grid(row=0, column=2, padx=5)
        
        self.delete_btn = ctk.CTkButton(self.btn_frame, text=self.tr('finance.buttons.delete'), command=self.delete_expense, fg_color="#c0392b", hover_color="#962d22", width=120)
        self.delete_btn.grid(row=0, column=3, padx=5)
        
        self.status_label = ctk.CTkLabel(self.tab_finance, text="", font=("Arial", 13))
        self.status_label.pack(pady=2)
        
        # الفلترة والجدوى
        self.filter_frame = ctk.CTkFrame(self.tab_finance, fg_color="transparent")
        self.filter_frame.pack(pady=5, padx=10, fill="x")
        
        self.filter_label = ctk.CTkLabel(self.filter_frame, text=self.tr('finance.labels.filter_label'), font=("Arial", 13, "bold"))
        self.filter_label.pack(side="right", padx=10)
        self.filter_combo = ctk.CTkComboBox(self.filter_frame, values=self.get_filter_plots(), command=lambda e: self.load_finance_data())
        self.filter_combo.pack(side="right", padx=10)
        # Use original Arabic value for database compatibility
        self.filter_combo.set(self.translations['finance']['plots']['all']['ar'])
        
        # جدول المالية
        self.table_frame = ctk.CTkFrame(self.tab_finance)
        self.table_frame.pack(pady=5, padx=10, fill="x")
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        columns_fin = ("id", "plot", "type", "item", "category", "cost", "date")
        self.tree_finance = ttk.Treeview(self.table_frame, columns=columns_fin, show="headings", height=10)
        
        self.tree_finance.heading("id", text=self.tr('finance.table_headers.id'))
        self.tree_finance.heading("plot", text=self.tr('finance.table_headers.plot'))
        self.tree_finance.heading("type", text=self.tr('finance.table_headers.type'))
        self.tree_finance.heading("item", text=self.tr('finance.table_headers.item'))
        self.tree_finance.heading("category", text=self.tr('finance.table_headers.category'))
        self.tree_finance.heading("cost", text=self.tr('finance.table_headers.cost'))
        self.tree_finance.heading("date", text=self.tr('finance.table_headers.date'))
        
        self.tree_finance.column("id", width=50, anchor="center")
        self.tree_finance.column("plot", width=140, anchor="center")
        self.tree_finance.column("type", width=120, anchor="center")
        self.tree_finance.column("item", width=150, anchor="center")
        self.tree_finance.column("category", width=100, anchor="center")
        self.tree_finance.column("cost", width=90, anchor="center")
        self.tree_finance.column("date", width=130, anchor="center")
        
        self.tree_finance.pack(side="left", fill="both", expand=True)
        self.tree_finance.bind("<<TreeviewSelect>>", self.get_selected_expense)
        
        sb_fin = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree_finance.yview)
        self.tree_finance.configure(yscrollcommand=sb_fin.set)
        sb_fin.pack(side="right", fill="y")
        
        # لوحة النتائج المالية
        self.dashboard_frame = ctk.CTkFrame(self.tab_finance)
        self.dashboard_frame.pack(pady=10, padx=10, fill="x")
        
        self.total_expenses_lbl = ctk.CTkLabel(self.dashboard_frame, text=self.tr('finance.dashboard.total_expenses', amount=0), font=("Arial", 13, "bold"), text_color="#c0392b")
        self.total_expenses_lbl.pack(side="right", expand=True, pady=5)
        
        self.total_income_lbl = ctk.CTkLabel(self.dashboard_frame, text=self.tr('finance.dashboard.total_income', amount=0), font=("Arial", 13, "bold"), text_color="#27ae60")
        self.total_income_lbl.pack(side="right", expand=True, pady=5)
        
        self.net_profit_lbl = ctk.CTkLabel(self.dashboard_frame, text=self.tr('finance.dashboard.net_profit_positive', amount=0), font=("Arial", 14, "bold"))
        self.net_profit_lbl.pack(side="right", expand=True, pady=5)
        
        # =========================================================================
        # 2. تصميم واجهة إدارة المخازن (التبويب الثاني)
        # =========================================================================
        self.stock_form = ctk.CTkFrame(self.tab_inventory)
        self.stock_form.pack(pady=10, padx=10, fill="x")
        
        self.stock_item_entry = ctk.CTkEntry(self.stock_form, placeholder_text=self.tr('inventory.labels.item_name'), width=250)
        self.stock_item_entry.pack(side="right", padx=10, pady=10)
        
        self.stock_qty_entry = ctk.CTkEntry(self.stock_form, placeholder_text=self.tr('inventory.labels.quantity'), width=100)
        self.stock_qty_entry.pack(side="right", padx=10, pady=10)
        
        self.stock_unit_combo = ctk.CTkComboBox(self.stock_form, values=self.get_units(), width=100)
        self.stock_unit_combo.pack(side="right", padx=10, pady=10)
        
        # أزرار التحكم بالمخزن
        self.stock_btn_frame = ctk.CTkFrame(self.tab_inventory, fg_color="transparent")
        self.stock_btn_frame.pack(pady=5)
        
        self.add_stock_btn = ctk.CTkButton(self.stock_btn_frame, text=self.tr('inventory.buttons.add'), command=self.save_stock, fg_color="green", width=140)
        self.add_stock_btn.grid(row=0, column=0, padx=5)
        
        self.withdraw_stock_btn = ctk.CTkButton(self.stock_btn_frame, text=self.tr('inventory.buttons.withdraw'), command=self.withdraw_stock, fg_color="#e67e22", width=140)
        self.withdraw_stock_btn.grid(row=0, column=1, padx=5)
        
        self.delete_stock_btn = ctk.CTkButton(self.stock_btn_frame, text=self.tr('inventory.buttons.delete'), command=self.delete_stock, fg_color="#c0392b", width=140)
        self.delete_stock_btn.grid(row=0, column=2, padx=5)
        
        self.stock_status_lbl = ctk.CTkLabel(self.tab_inventory, text="", font=("Arial", 13))
        self.stock_status_lbl.pack(pady=2)
        
        # جدول عرض المخزون المتوفر
        self.stock_table_frame = ctk.CTkFrame(self.tab_inventory)
        self.stock_table_frame.pack(pady=5, padx=10, fill="x")
        
        columns_stk = ("id", "item", "qty", "unit", "last_update")
        self.tree_stock = ttk.Treeview(self.stock_table_frame, columns=columns_stk, show="headings", height=10)
        
        self.tree_stock.heading("id", text=self.tr('inventory.table_headers.id'))
        self.tree_stock.heading("item", text=self.tr('inventory.table_headers.item'))
        self.tree_stock.heading("qty", text=self.tr('inventory.table_headers.qty'))
        self.tree_stock.heading("unit", text=self.tr('inventory.table_headers.unit'))
        self.tree_stock.heading("last_update", text=self.tr('inventory.table_headers.last_update'))
        
        self.tree_stock.column("id", width=80, anchor="center")
        self.tree_stock.column("item", width=250, anchor="center")
        self.tree_stock.column("qty", width=150, anchor="center")
        self.tree_stock.column("unit", width=120, anchor="center")
        self.tree_stock.column("last_update", width=200, anchor="center")
        
        self.tree_stock.pack(side="left", fill="both", expand=True)
        self.tree_stock.bind("<<TreeviewSelect>>", self.get_selected_stock)
        
        sb_stk = ttk.Scrollbar(self.stock_table_frame, orient="vertical", command=self.tree_stock.yview)
        self.tree_stock.configure(yscrollcommand=sb_stk.set)
        sb_stk.pack(side="right", fill="y")
        
        # تطبيق التنسيق والتهيئة اللونية
        self.adjust_treeview_theme()
        
        # شحن البيانات الابتدائية تلقائياً للتبويبين
        self.load_finance_data()
        self.load_stock_data()
        
        # Add secondary window buttons frame
        self.secondary_windows_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.secondary_windows_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(self.secondary_windows_frame, text=self.tr('common.secondary_windows'), font=("Arial", 12, "bold")).pack(side="right", padx=5)
        
        self.btn_management = ctk.CTkButton(self.secondary_windows_frame, text=self.tr('management.title'), command=self.open_management_window, width=150)
        self.btn_management.pack(side="right", padx=5)
        
        self.btn_feasibility = ctk.CTkButton(self.secondary_windows_frame, text=self.tr('feasibility.title'), command=self.open_feasibility_window, width=150)
        self.btn_feasibility.pack(side="right", padx=5)
        
        self.btn_financial = ctk.CTkButton(self.secondary_windows_frame, text=self.tr('financial.title'), command=self.open_financial_window, width=150)
        self.btn_financial.pack(side="right", padx=5)
        
        self.btn_gemini = ctk.CTkButton(self.secondary_windows_frame, text="Google Gemini", command=self.open_gemini, fg_color="#8e44ad", hover_color="#732d91", width=150)
        self.btn_gemini.pack(side="right", padx=5)
        
        # Google Search Frame
        self.search_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.search_frame.pack(pady=5, padx=10, fill="x")
        
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="ابحث في Google...", width=300)
        self.search_entry.pack(side="right", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.google_search())
        
        self.search_btn = ctk.CTkButton(self.search_frame, text="بحث", command=self.google_search, fg_color="#4285f4", hover_color="#3367d6", width=100)
        self.search_btn.pack(side="right", padx=5)
    
    def register_sub_window(self, window):
        """Register a secondary window for language change notifications"""
        if window not in self.sub_windows:
            self.sub_windows.append(window)
            print(f"Registered sub-window: {window.__class__.__name__}")
    
    def unregister_sub_window(self, window):
        """Unregister a secondary window when it's closed"""
        if window in self.sub_windows:
            self.sub_windows.remove(window)
            print(f"Unregistered sub-window: {window.__class__.__name__}")
    
    def open_management_window(self):
        """Open the Management monitoring secondary window"""
        ManagementWindow(self)
    
    def open_feasibility_window(self):
        """Open the Feasibility analysis secondary window"""
        FeasibilityWindow(self)
    
    def open_financial_window(self):
        """Open the Financial analysis secondary window"""
        FinancialAnalysisWindow(self)
    
    def open_gemini(self):
        """Open Google Gemini in the default web browser"""
        webbrowser.open("https://gemini.google.com")
    
    def google_search(self):
        """Search in Google using the text from search entry"""
        query = self.search_entry.get()
        if query:
            encoded_query = query.replace(" ", "+")
            webbrowser.open(f"https://www.google.com/search?q={encoded_query}")
    
    def load_language(self):
        """Load translations from lang.json file"""
        try:
            if os.path.exists('lang.json'):
                with open('lang.json', 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            else:
                print("Warning: lang.json not found, using hardcoded strings")
        except Exception as e:
            print(f"Error loading translations: {e}")
    
    def tr(self, key, **kwargs):
        """
        Get translated string for a key
        key: dot-separated path (e.g., 'finance.buttons.save')
        kwargs: format placeholders (e.g., amount=123.45)
        """
        try:
            if not self.translations:
                print(f"Warning: Translations not loaded, returning key: {key}")
                return key
            
            keys = key.split('.')
            value = self.translations
            for k in keys:
                if not isinstance(value, dict) or k not in value:
                    print(f"Warning: Translation key not found: {key} (missing: {k})")
                    return key
                value = value[k]
            
            if isinstance(value, dict):
                # Get the translation for current language
                text = value.get(self.current_language, value.get('ar', key))
                if not text or not isinstance(text, str):
                    print(f"Warning: Translation value not valid for key: {key}")
                    return key
            else:
                text = str(value) if value is not None else key
            
            # Apply format placeholders if provided
            if kwargs:
                try:
                    return text.format(**kwargs)
                except (KeyError, ValueError) as e:
                    print(f"Warning: Format error for key {key} with kwargs {kwargs}: {e}")
                    return text
            return text
        except (KeyError, AttributeError, TypeError) as e:
            print(f"Warning: Translation error for key {key}: {e}")
            return key
    
    def change_language(self, lang_code):
        """Change current language and refresh UI"""
        if lang_code in ['ar', 'fr', 'en']:
            self.current_language = lang_code
            self.refresh_ui()
    
    def refresh_ui(self):
        """Refresh all UI elements with current language"""
        try:
            # Validate translation dictionary before proceeding
            if not self.translations or not isinstance(self.translations, dict):
                print('Error: Translation dictionary is invalid or empty')
                return
            
            print(f'Refreshing UI for language: {self.current_language}')
            
            # Update window title
            self.title(self.tr('app.title'))
            
            # Update main title label
            self.title_label.configure(text=self.tr('app.subtitle'))
            
            # Update language label and combo
            if hasattr(self, 'lang_frame') and self.lang_frame.winfo_children():
                self.lang_frame.winfo_children()[0].configure(text=self.tr('common.language'))
            if hasattr(self, 'lang_combo'):
                current_lang = self.lang_combo.get()
                self.lang_combo.configure(values=[self.tr('common.language_names.ar'), 
                                                 self.tr('common.language_names.fr'), 
                                                 self.tr('common.language_names.en')])
                # Restore current selection if possible
                lang_map = {
                    self.tr('common.language_names.ar'): 'ar',
                    self.tr('common.language_names.fr'): 'fr',
                    self.tr('common.language_names.en'): 'en'
                }
                if current_lang in lang_map:
                    self.lang_combo.set(current_lang)
                else:
                    # Set based on current language code
                    if self.current_language == 'ar':
                        self.lang_combo.set(self.tr('common.language_names.ar'))
                    elif self.current_language == 'fr':
                        self.lang_combo.set(self.tr('common.language_names.fr'))
                    else:
                        self.lang_combo.set(self.tr('common.language_names.en'))
            
            # Recreate tabview with new language names
            # This recreates all tab content with translated labels
            self.recreate_tabview()
            
            # Update secondary window buttons
            if hasattr(self, 'secondary_windows_frame') and self.secondary_windows_frame.winfo_children():
                self.secondary_windows_frame.winfo_children()[0].configure(text=self.tr('common.secondary_windows'))
            if hasattr(self, 'btn_management'):
                self.btn_management.configure(text=self.tr('management.title'))
            if hasattr(self, 'btn_feasibility'):
                self.btn_feasibility.configure(text=self.tr('feasibility.title'))
            if hasattr(self, 'btn_financial'):
                self.btn_financial.configure(text=self.tr('financial.title'))
            
            # Cascade refresh to all registered sub-windows
            for window in self.sub_windows[:]:  # Use slice copy to avoid modification during iteration
                try:
                    if hasattr(window, 'refresh_ui'):
                        window.refresh_ui()
                        print(f"Refreshed sub-window: {window.__class__.__name__}")
                except Exception as e:
                    print(f"Error refreshing sub-window {window.__class__.__name__}: {e}")
            
            print('UI refresh completed successfully')
        except Exception as e:
            print(f"Error refreshing UI: {e}")
            import traceback
            traceback.print_exc()
    
    def get_plot_names(self):
        """Get translated plot names"""
        return [
            self.tr('finance.plots.main'),
            self.tr('finance.plots.west'),
            self.tr('finance.plots.east'),
            self.tr('finance.plots.greenhouse1'),
            self.tr('finance.plots.greenhouse2'),
            self.tr('finance.plots.olive')
        ]
    
    def get_filter_plots(self):
        """Get translated filter plot options"""
        return [
            self.tr('finance.plots.all'),
            self.tr('finance.plots.main'),
            self.tr('finance.plots.west'),
            self.tr('finance.plots.east'),
            self.tr('finance.plots.greenhouse1'),
            self.tr('finance.plots.greenhouse2'),
            self.tr('finance.plots.olive')
        ]
    
    def get_operation_types(self):
        """Get translated operation types"""
        return [
            self.tr('finance.operation_types.expense'),
            self.tr('finance.operation_types.income')
        ]
    
    def get_categories(self):
        """Get translated categories"""
        return [
            self.tr('finance.categories.seeds'),
            self.tr('finance.categories.fertilizers'),
            self.tr('finance.categories.labor'),
            self.tr('finance.categories.irrigation'),
            self.tr('finance.categories.sales'),
            self.tr('finance.categories.other')
        ]
    
    def get_units(self):
        """Get translated units"""
        try:
            return [
                self.tr('inventory.units.bag'),
                self.tr('inventory.units.kg'),
                self.tr('inventory.units.liter'),
                self.tr('inventory.units.box'),
                self.tr('inventory.units.carton')
            ]
        except Exception as e:
            print(f"Error getting translated units: {e}")
            return ['كيس', 'كغ', 'لتر', 'صندوق', 'علبة']
    
    def get_original_plot(self, translated_plot):
        """Convert translated plot name to original Arabic for database"""
        plot_keys = ['main', 'west', 'east', 'greenhouse1', 'greenhouse2', 'olive']
        for key in plot_keys:
            if translated_plot == self.tr(f'finance.plots.{key}'):
                return self.translations['finance']['plots'][key]['original']
        return translated_plot
    
    def get_original_operation_type(self, translated_type):
        """Convert translated operation type to original Arabic for database"""
        type_keys = ['expense', 'income']
        for key in type_keys:
            if translated_type == self.tr(f'finance.operation_types.{key}'):
                return self.translations['finance']['operation_types'][key]['original']
        return translated_type
    
    def get_original_category(self, translated_category):
        """Convert translated category to original Arabic for database"""
        category_keys = ['seeds', 'fertilizers', 'labor', 'irrigation', 'sales', 'other']
        for key in category_keys:
            if translated_category == self.tr(f'finance.categories.{key}'):
                return self.translations['finance']['categories'][key]['original']
        return translated_category
    
    def get_translated_plot(self, original_plot):
        """Convert original Arabic plot name to translated for display"""
        if original_plot is None or original_plot == '':
            print(f'Warning: get_translated_plot received None or empty value')
            return original_plot or ''
        
        try:
            plot_keys = ['main', 'west', 'east', 'greenhouse1', 'greenhouse2', 'olive']
            for key in plot_keys:
                if original_plot == self.translations['finance']['plots'][key]['original']:
                    return self.tr(f'finance.plots.{key}')
            return original_plot
        except (KeyError, TypeError, AttributeError) as e:
            print(f'Warning: Translation error in get_translated_plot for value "{original_plot}": {e}')
            return original_plot
    
    def get_translated_operation_type(self, original_type):
        """Convert original Arabic operation type to translated for display"""
        if original_type is None or original_type == '':
            print(f'Warning: get_translated_operation_type received None or empty value')
            return original_type or ''
        
        try:
            type_keys = ['expense', 'income']
            for key in type_keys:
                if original_type == self.translations['finance']['operation_types'][key]['original']:
                    return self.tr(f'finance.operation_types.{key}')
            return original_type
        except (KeyError, TypeError, AttributeError) as e:
            print(f'Warning: Translation error in get_translated_operation_type for value "{original_type}": {e}')
            return original_type
    
    def get_translated_category(self, original_category):
        """Convert original Arabic category to translated for display"""
        if original_category is None or original_category == '':
            print(f'Warning: get_translated_category received None or empty value')
            return original_category or ''
        
        try:
            category_keys = ['seeds', 'fertilizers', 'labor', 'irrigation', 'sales', 'other']
            for key in category_keys:
                if original_category == self.translations['finance']['categories'][key]['original']:
                    return self.tr(f'finance.categories.{key}')
            return original_category
        except (KeyError, TypeError, AttributeError) as e:
            print(f'Warning: Translation error in get_translated_category for value "{original_category}": {e}')
            return original_category
    
    def get_translated_unit(self, original_unit):
        """Convert original Arabic unit to translated for display"""
        if original_unit is None or original_unit == '':
            print(f'Warning: get_translated_unit received None or empty value')
            return original_unit or ''
        
        try:
            unit_keys = ['bag', 'kg', 'liter', 'box', 'carton']
            for key in unit_keys:
                if original_unit == self.translations['inventory']['units'][key]['original']:
                    return self.tr(f'inventory.units.{key}')
            print(f'Warning: Unit "{original_unit}" not found in translation keys, returning original')
            return original_unit
        except (KeyError, TypeError, AttributeError) as e:
            print(f'Warning: Translation error in get_translated_unit for value "{original_unit}": {e}')
            return original_unit
    
    def get_original_unit(self, translated_unit):
        """Convert translated unit name to original Arabic for database"""
        try:
            unit_keys = ['bag', 'kg', 'liter', 'box', 'carton']
            for key in unit_keys:
                if translated_unit == self.tr(f'inventory.units.{key}'):
                    return self.translations['inventory']['units'][key]['original']
            return translated_unit
        except (KeyError, TypeError, AttributeError) as e:
            print(f'Warning: Error in get_original_unit for value "{translated_unit}": {e}')
            return translated_unit
    
    def update_finance_table_headers(self):
        """Update finance table column headers"""
        self.tree_finance.heading("id", text=self.tr('finance.table_headers.id'))
        self.tree_finance.heading("plot", text=self.tr('finance.table_headers.plot'))
        self.tree_finance.heading("type", text=self.tr('finance.table_headers.type'))
        self.tree_finance.heading("item", text=self.tr('finance.table_headers.item'))
        self.tree_finance.heading("category", text=self.tr('finance.table_headers.category'))
        self.tree_finance.heading("cost", text=self.tr('finance.table_headers.cost'))
        self.tree_finance.heading("date", text=self.tr('finance.table_headers.date'))
    
    def update_stock_table_headers(self):
        """Update stock table column headers"""
        self.tree_stock.heading("id", text=self.tr('inventory.table_headers.id'))
        self.tree_stock.heading("item", text=self.tr('inventory.table_headers.item'))
        self.tree_stock.heading("qty", text=self.tr('inventory.table_headers.qty'))
        self.tree_stock.heading("unit", text=self.tr('inventory.table_headers.unit'))
        self.tree_stock.heading("last_update", text=self.tr('inventory.table_headers.last_update'))
    
    def on_language_change(self):
        """Handle language combo box change"""
        selected = self.lang_combo.get()
        lang_map = {
            self.tr('common.language_names.ar'): 'ar',
            self.tr('common.language_names.fr'): 'fr',
            self.tr('common.language_names.en'): 'en'
        }
        if selected in lang_map:
            self.change_language(lang_map[selected])
    
    def recreate_tabview(self):
        """Recreate tabview with translated tab names"""
        try:
            # Save current tab index
            current_tab = self.tab_view.get()
            
            # Destroy old tabview
            self.tab_view.destroy()
            
            # Create new tabview with translated names
            self.tab_view = ctk.CTkTabview(self.main_container, width=1050)
            self.tab_view.pack(pady=5, padx=10, fill="both", expand=True)
            
            # Update tab names dictionary
            self.tab_names = {
                'finance': self.tr('tabs.finance'),
                'inventory': self.tr('tabs.inventory')
            }
            
            # Add tabs with new names
            self.tab_finance = self.tab_view.add(self.tab_names['finance'])
            self.tab_inventory = self.tab_view.add(self.tab_names['inventory'])
            
            # Re-create finance tab content
            self.form_frame = ctk.CTkFrame(self.tab_finance)
            self.form_frame.pack(pady=10, padx=10, fill="x")
            
            # السطر الأول: الأرض والنوع
            self.row1 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            self.row1.pack(fill="x", pady=5, padx=10)
            
            self.plot_label = ctk.CTkLabel(self.row1, text=self.tr('finance.labels.plot'), font=("Arial", 12))
            self.plot_label.pack(side="right", padx=5)
            self.plot_combo = ctk.CTkComboBox(self.row1, values=self.get_plot_names(), width=180)
            self.plot_combo.pack(side="right", padx=10)
            
            self.type_label = ctk.CTkLabel(self.row1, text=self.tr('finance.labels.operation_type'), font=("Arial", 12))
            self.type_label.pack(side="right", padx=5)
            self.type_combo = ctk.CTkComboBox(self.row1, values=self.get_operation_types(), width=180)
            self.type_combo.pack(side="right", padx=10)
            
            # السطر الثاني: البيان والمبلغ
            self.row2 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            self.row2.pack(fill="x", pady=5, padx=10)
            
            self.item_entry = ctk.CTkEntry(self.row2, placeholder_text=self.tr('finance.labels.item'), width=300)
            self.item_entry.pack(side="right", padx=5, expand=True, fill="x")
            
            self.category_combo = ctk.CTkComboBox(self.row2, values=self.get_categories(), width=130)
            self.category_combo.pack(side="right", padx=5)
            
            self.cost_entry = ctk.CTkEntry(self.row2, placeholder_text=self.tr('finance.labels.amount'), width=100)
            self.cost_entry.pack(side="right", padx=5)
            
            # أزرار المالية
            self.btn_frame = ctk.CTkFrame(self.tab_finance, fg_color="transparent")
            self.btn_frame.pack(pady=5)
            
            self.save_btn = ctk.CTkButton(self.btn_frame, text=self.tr('finance.buttons.save'), command=self.save_expense, fg_color="green", hover_color="darkgreen", width=120)
            self.save_btn.grid(row=0, column=0, padx=5)
            
            self.refresh_btn = ctk.CTkButton(self.btn_frame, text=self.tr('finance.buttons.refresh'), command=self.load_finance_data, fg_color="blue", width=120)
            self.refresh_btn.grid(row=0, column=1, padx=5)
            
            self.update_btn = ctk.CTkButton(self.btn_frame, text=self.tr('finance.buttons.update'), command=self.update_expense, fg_color="#e67e22", hover_color="#d35400", width=120)
            self.update_btn.grid(row=0, column=2, padx=5)
            
            self.delete_btn = ctk.CTkButton(self.btn_frame, text=self.tr('finance.buttons.delete'), command=self.delete_expense, fg_color="#c0392b", hover_color="#962d22", width=120)
            self.delete_btn.grid(row=0, column=3, padx=5)
            
            self.status_label = ctk.CTkLabel(self.tab_finance, text="", font=("Arial", 13))
            self.status_label.pack(pady=2)
            
            # الفلترة والجدوى
            self.filter_frame = ctk.CTkFrame(self.tab_finance, fg_color="transparent")
            self.filter_frame.pack(pady=5, padx=10, fill="x")
            
            self.filter_label = ctk.CTkLabel(self.filter_frame, text=self.tr('finance.labels.filter_label'), font=("Arial", 13, "bold"))
            self.filter_label.pack(side="right", padx=10)
            self.filter_combo = ctk.CTkComboBox(self.filter_frame, values=self.get_filter_plots(), command=lambda e: self.load_finance_data())
            self.filter_combo.pack(side="right", padx=10)
            self.filter_combo.set(self.translations['finance']['plots']['all']['ar'])
            
            # جدول المالية
            self.table_frame = ctk.CTkFrame(self.tab_finance)
            self.table_frame.pack(pady=5, padx=10, fill="x")
            
            columns_fin = ("id", "plot", "type", "item", "category", "cost", "date")
            self.tree_finance = ttk.Treeview(self.table_frame, columns=columns_fin, show="headings", height=10)
            
            self.tree_finance.heading("id", text=self.tr('finance.table_headers.id'))
            self.tree_finance.heading("plot", text=self.tr('finance.table_headers.plot'))
            self.tree_finance.heading("type", text=self.tr('finance.table_headers.type'))
            self.tree_finance.heading("item", text=self.tr('finance.table_headers.item'))
            self.tree_finance.heading("category", text=self.tr('finance.table_headers.category'))
            self.tree_finance.heading("cost", text=self.tr('finance.table_headers.cost'))
            self.tree_finance.heading("date", text=self.tr('finance.table_headers.date'))
            
            self.tree_finance.column("id", width=50, anchor="center")
            self.tree_finance.column("plot", width=140, anchor="center")
            self.tree_finance.column("type", width=120, anchor="center")
            self.tree_finance.column("item", width=150, anchor="center")
            self.tree_finance.column("category", width=100, anchor="center")
            self.tree_finance.column("cost", width=90, anchor="center")
            self.tree_finance.column("date", width=130, anchor="center")
            
            self.tree_finance.pack(side="left", fill="both", expand=True)
            self.tree_finance.bind("<<TreeviewSelect>>", self.get_selected_expense)
            
            sb_fin = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree_finance.yview)
            self.tree_finance.configure(yscrollcommand=sb_fin.set)
            sb_fin.pack(side="right", fill="y")
            
            # لوحة النتائج المالية
            self.dashboard_frame = ctk.CTkFrame(self.tab_finance)
            self.dashboard_frame.pack(pady=10, padx=10, fill="x")
            
            self.total_expenses_lbl = ctk.CTkLabel(self.dashboard_frame, text=self.tr('finance.dashboard.total_expenses', amount=0), font=("Arial", 13, "bold"), text_color="#c0392b")
            self.total_expenses_lbl.pack(side="right", expand=True, pady=5)
            
            self.total_income_lbl = ctk.CTkLabel(self.dashboard_frame, text=self.tr('finance.dashboard.total_income', amount=0), font=("Arial", 13, "bold"), text_color="#27ae60")
            self.total_income_lbl.pack(side="right", expand=True, pady=5)
            
            self.net_profit_lbl = ctk.CTkLabel(self.dashboard_frame, text=self.tr('finance.dashboard.net_profit_positive', amount=0), font=("Arial", 14, "bold"))
            self.net_profit_lbl.pack(side="right", expand=True, pady=5)
            
            # Re-create inventory tab content
            self.stock_form = ctk.CTkFrame(self.tab_inventory)
            self.stock_form.pack(pady=10, padx=10, fill="x")
            
            self.stock_item_entry = ctk.CTkEntry(self.stock_form, placeholder_text=self.tr('inventory.labels.item_name'), width=250)
            self.stock_item_entry.pack(side="right", padx=10, pady=10)
            
            self.stock_qty_entry = ctk.CTkEntry(self.stock_form, placeholder_text=self.tr('inventory.labels.quantity'), width=100)
            self.stock_qty_entry.pack(side="right", padx=10, pady=10)
            
            self.stock_unit_combo = ctk.CTkComboBox(self.stock_form, values=self.get_units(), width=100)
            self.stock_unit_combo.pack(side="right", padx=10, pady=10)
            
            # أزرار التحكم بالمخزن
            self.stock_btn_frame = ctk.CTkFrame(self.tab_inventory, fg_color="transparent")
            self.stock_btn_frame.pack(pady=5)
            
            self.add_stock_btn = ctk.CTkButton(self.stock_btn_frame, text=self.tr('inventory.buttons.add'), command=self.save_stock, fg_color="green", width=140)
            self.add_stock_btn.grid(row=0, column=0, padx=5)
            
            self.withdraw_stock_btn = ctk.CTkButton(self.stock_btn_frame, text=self.tr('inventory.buttons.withdraw'), command=self.withdraw_stock, fg_color="#e67e22", width=140)
            self.withdraw_stock_btn.grid(row=0, column=1, padx=5)
            
            self.delete_stock_btn = ctk.CTkButton(self.stock_btn_frame, text=self.tr('inventory.buttons.delete'), command=self.delete_stock, fg_color="#c0392b", width=140)
            self.delete_stock_btn.grid(row=0, column=2, padx=5)
            
            self.stock_status_lbl = ctk.CTkLabel(self.tab_inventory, text="", font=("Arial", 13))
            self.stock_status_lbl.pack(pady=2)
            
            # جدول عرض المخزون المتوفر
            self.stock_table_frame = ctk.CTkFrame(self.tab_inventory)
            self.stock_table_frame.pack(pady=5, padx=10, fill="x")
            
            columns_stk = ("id", "item", "qty", "unit", "last_update")
            self.tree_stock = ttk.Treeview(self.stock_table_frame, columns=columns_stk, show="headings", height=10)
            
            self.tree_stock.heading("id", text=self.tr('inventory.table_headers.id'))
            self.tree_stock.heading("item", text=self.tr('inventory.table_headers.item'))
            self.tree_stock.heading("qty", text=self.tr('inventory.table_headers.qty'))
            self.tree_stock.heading("unit", text=self.tr('inventory.table_headers.unit'))
            self.tree_stock.heading("last_update", text=self.tr('inventory.table_headers.last_update'))
            
            self.tree_stock.column("id", width=80, anchor="center")
            self.tree_stock.column("item", width=250, anchor="center")
            self.tree_stock.column("qty", width=150, anchor="center")
            self.tree_stock.column("unit", width=120, anchor="center")
            self.tree_stock.column("last_update", width=200, anchor="center")
            
            self.tree_stock.pack(side="left", fill="both", expand=True)
            self.tree_stock.bind("<<TreeviewSelect>>", self.get_selected_stock)
            
            sb_stk = ttk.Scrollbar(self.stock_table_frame, orient="vertical", command=self.tree_stock.yview)
            self.tree_stock.configure(yscrollcommand=sb_stk.set)
            sb_stk.pack(side="right", fill="y")
            
            # Apply theme
            self.adjust_treeview_theme()
            
            # Reload data
            self.load_finance_data()
            self.load_stock_data()
            
            # Restore previous tab selection
            if current_tab == self.tab_names['finance']:
                self.tab_view.set(self.tab_names['finance'])
            elif current_tab == self.tab_names['inventory']:
                self.tab_view.set(self.tab_names['inventory'])
            else:
                self.tab_view.set(self.tab_names['finance'])
            
            print(f"Tabview recreated with language: {self.current_language}")
        except Exception as e:
            print(f"Error recreating tabview: {e}")
            import traceback
            traceback.print_exc()

    def adjust_treeview_theme(self):
        if ctk.get_appearance_mode() == "Dark":
            bg, fg, h_bg = "#2e2e2e", "white", "#1f1f1f"
        else:
            bg, fg, h_bg = "#ffffff", "black", "#ececec"
            
        self.style.configure("Treeview", font=("Arial", 11), rowheight=25, background=bg, foreground=fg, fieldbackground=bg)
        self.style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background=h_bg, foreground=fg)
        
        self.tree_finance.tag_configure(self.tr('common.tags.expense'), foreground="#e74c3c")
        self.tree_finance.tag_configure(self.tr('common.tags.income'), foreground="#2ed573")

    def init_db(self):
        conn = sqlite3.connect('fellah.db')
        cursor = conn.cursor()
        # جدول المالية والجدوى للأراضي
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plot_name TEXT,
                type_name TEXT DEFAULT 'مصروف',
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                total_cost REAL,
                date_added TEXT
            )
        ''')
        # جدول إدارة المخازن
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT UNIQUE NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                last_updated TEXT
            )
        ''')
        conn.commit()
        conn.close()

    # =========================================================================
    # دالات التبويب الأول: العمليات المالية والجدوى
    # =========================================================================
    def save_expense(self):
        plot = self.plot_combo.get()
        op_type = self.type_combo.get()
        item = self.item_entry.get().strip()
        category = self.category_combo.get()
        cost = self.cost_entry.get().strip()
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if item and cost:
            try:
                cost_value = float(cost)
                if cost_value < 0: raise ValueError
                
                # Convert translated values to original Arabic for database
                plot_original = self.get_original_plot(plot)
                op_type_original = self.get_original_operation_type(op_type)
                category_original = self.get_original_category(category)
                    
                conn = sqlite3.connect('fellah.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO expenses (plot_name, type_name, item_name, category, total_cost, date_added)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (plot_original, op_type_original, item, category_original, cost_value, date_now))
                conn.commit()
                conn.close()
                
                self.clear_finance_entries()
                self.status_label.configure(text=self.tr('finance.messages.save_success'), text_color="green")
                self.load_finance_data()
            except ValueError:
                self.status_label.configure(text=self.tr('finance.messages.invalid_amount'), text_color="red")
        else:
            self.status_label.configure(text=self.tr('finance.messages.fill_fields'), text_color="orange")

    def get_selected_expense(self, event):
        selected = self.tree_finance.focus()
        if selected:
            values = self.tree_finance.item(selected, 'values')
            if values:
                self.selected_expense_id = values[0]
                # Convert database values to translated for display in combo boxes
                self.plot_combo.set(self.get_translated_plot(values[1]))
                self.type_combo.set(self.get_translated_operation_type(values[2]))
                self.item_entry.delete(0, 'end')
                self.item_entry.insert(0, values[3])
                self.category_combo.set(self.get_translated_category(values[4]))
                self.cost_entry.delete(0, 'end')
                self.cost_entry.insert(0, values[5])

    def update_expense(self):
        if not self.selected_expense_id:
            self.status_label.configure(text=self.tr('finance.messages.select_to_update'), text_color="orange")
            return
        plot = self.plot_combo.get()
        op_type = self.type_combo.get()
        item = self.item_entry.get().strip()
        category = self.category_combo.get()
        cost = self.cost_entry.get().strip()
        
        if item and cost:
            try:
                cost_value = float(cost)
                # Convert translated values to original Arabic for database
                plot_original = self.get_original_plot(plot)
                op_type_original = self.get_original_operation_type(op_type)
                category_original = self.get_original_category(category)
                
                conn = sqlite3.connect('fellah.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE expenses SET plot_name=?, type_name=?, item_name=?, category=?, total_cost=? WHERE id=?
                ''', (plot_original, op_type_original, item, category_original, cost_value, self.selected_expense_id))
                conn.commit()
                conn.close()
                self.clear_finance_entries()
                self.selected_expense_id = None
                self.status_label.configure(text=self.tr('finance.messages.update_success'), text_color="green")
                self.load_finance_data()
            except ValueError: self.status_label.configure(text=self.tr('finance.messages.amount_error'), text_color="red")
        else: self.status_label.configure(text=self.tr('finance.messages.fill_fields'), text_color="orange")

    def delete_expense(self):
        selected = self.tree_finance.focus()
        if not selected:
            self.status_label.configure(text=self.tr('finance.messages.select_to_delete'), text_color="orange")
            return
        row_id = self.tree_finance.item(selected, 'values')[0]
        conn = sqlite3.connect('fellah.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id=?", (row_id,))
        conn.commit()
        conn.close()
        self.clear_finance_entries()
        self.status_label.configure(text=self.tr('finance.messages.delete_success'), text_color="red")
        self.load_finance_data()

    def clear_finance_entries(self):
        self.item_entry.delete(0, 'end')
        self.cost_entry.delete(0, 'end')

    def load_finance_data(self):
        self.adjust_treeview_theme()
        for row in self.tree_finance.get_children(): self.tree_finance.delete(row)
            
        filter_plot = self.filter_combo.get()
        conn = sqlite3.connect('fellah.db')
        cursor = conn.cursor()
        
        # Convert translated filter value to original Arabic for database comparison
        filter_plot_original = self.get_original_plot(filter_plot)
        all_plots_original = self.translations['finance']['plots']['all']['original']
        if filter_plot_original == all_plots_original:
            cursor.execute("SELECT id, plot_name, type_name, item_name, category, total_cost, date_added FROM expenses ORDER BY id DESC")
        else:
            cursor.execute("SELECT id, plot_name, type_name, item_name, category, total_cost, date_added FROM expenses WHERE plot_name=? ORDER BY id DESC", (filter_plot_original,))
            
        rows = cursor.fetchall()
        sum_expenses, sum_income = 0.0, 0.0
        
        # Use original Arabic values for database comparisons
        expense_original = self.translations['common']['tags']['expense']['original']
        income_original = self.translations['common']['tags']['income']['original']
        expense_tag = self.tr('common.tags.expense')
        income_tag = self.tr('common.tags.income')
        
        for row in rows:
            tag = expense_tag if expense_original in row[2] else income_tag
            if expense_original in row[2]: sum_expenses += row[5]
            else: sum_income += row[5]
            # Translate database values for display in table
            translated_row = (
                row[0],  # id
                self.get_translated_plot(row[1]),  # plot_name
                self.get_translated_operation_type(row[2]),  # type_name
                row[3],  # item_name
                self.get_translated_category(row[4]),  # category
                row[5],  # total_cost
                row[6]   # date_added
            )
            self.tree_finance.insert("", "end", values=translated_row, tags=(tag,))
        conn.close()
        
        net_profit = sum_income - sum_expenses
        self.total_expenses_lbl.configure(text=self.tr('finance.dashboard.total_expenses', amount=sum_expenses))
        self.total_income_lbl.configure(text=self.tr('finance.dashboard.total_income', amount=sum_income))
        if net_profit >= 0:
            self.net_profit_lbl.configure(text=self.tr('finance.dashboard.net_profit_positive', amount=net_profit), text_color="#2ecc71")
        else:
            self.net_profit_lbl.configure(text=self.tr('finance.dashboard.net_profit_negative', amount=net_profit), text_color="#e74c3c")

    # =========================================================================
    # دالات التبويب الثاني: إدارة المخازن
    # =========================================================================
    def save_stock(self):
        item = self.stock_item_entry.get().strip()
        qty = self.stock_qty_entry.get().strip()
        unit = self.stock_unit_combo.get()
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if item and qty:
            try:
                qty_val = float(qty)
                if qty_val <= 0: raise ValueError
                
                # Convert translated unit to original Arabic for database
                unit_original = self.get_original_unit(unit)
                
                conn = sqlite3.connect('fellah.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO inventory (item_name, quantity, unit, last_updated)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(item_name) DO UPDATE SET 
                    quantity = quantity + excluded.quantity,
                    last_updated = excluded.last_updated
                ''', (item, qty_val, unit_original, date_now))
                conn.commit()
                conn.close()
                
                self.stock_item_entry.delete(0, 'end')
                self.stock_qty_entry.delete(0, 'end')
                self.stock_status_lbl.configure(text=self.tr('inventory.messages.add_success'), text_color="green")
                self.load_stock_data()
            except ValueError: self.stock_status_lbl.configure(text=self.tr('inventory.messages.invalid_quantity'), text_color="red")
        else: self.stock_status_lbl.configure(text=self.tr('inventory.messages.fill_stock_fields'), text_color="orange")

    def withdraw_stock(self):
        item = self.stock_item_entry.get().strip()
        qty = self.stock_qty_entry.get().strip()
        plot = self.plot_combo.get()
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if item and qty:
            try:
                qty_to_withdraw = float(qty)
                conn = sqlite3.connect('fellah.db')
                cursor = conn.cursor()
                
                cursor.execute("SELECT quantity, unit FROM inventory WHERE item_name=?", (item,))
                res = cursor.fetchone()
                
                if res:
                    current_qty, unit = res[0], res[1]
                    if current_qty >= qty_to_withdraw:
                        new_qty = current_qty - qty_to_withdraw
                        cursor.execute("UPDATE inventory SET quantity=?, last_updated=? WHERE item_name=?", (new_qty, date_now, item))
                        
                        statement = self.tr('inventory.withdraw_statement', qty=qty_to_withdraw, unit=unit, item=item)
                        cursor.execute('''
                            INSERT INTO expenses (plot_name, type_name, item_name, category, total_cost, date_added)
                            VALUES (?, 'مصروف (رأس مال مستثمر)', ?, 'أخرى', 0.0, ?)
                        ''', (plot, statement, date_now))
                        
                        conn.commit()
                        self.stock_status_lbl.configure(text=self.tr('inventory.messages.withdraw_success', plot=plot), text_color="green")
                        self.stock_item_entry.delete(0, 'end')
                        self.stock_qty_entry.delete(0, 'end')
                    else:
                        self.stock_status_lbl.configure(text=self.tr('inventory.messages.withdraw_failed_insufficient', qty=current_qty), text_color="red")
                else:
                    self.stock_status_lbl.configure(text=self.tr('inventory.messages.item_not_found'), text_color="red")
                conn.close()
                self.load_stock_data()
                self.load_finance_data()
            except ValueError: self.stock_status_lbl.configure(text=self.tr('inventory.messages.quantity_error'), text_color="red")
        else: self.stock_status_lbl.configure(text=self.tr('inventory.messages.select_withdraw'), text_color="orange")

    def get_selected_stock(self, event):
        selected = self.tree_stock.focus()
        if selected:
            values = self.tree_stock.item(selected, 'values')
            if values:
                self.selected_stock_id = values[0]
                self.stock_item_entry.delete(0, 'end')
                self.stock_item_entry.insert(0, values[1])
                self.stock_qty_entry.delete(0, 'end')
                self.stock_qty_entry.insert(0, values[2])
                # Translate unit from database (Arabic) to current language for dropdown
                translated_unit = self.get_translated_unit(values[3])
                # Try to set the combo box with translated value, fallback to original if fails
                try:
                    self.stock_unit_combo.set(translated_unit)
                except Exception as e:
                    print(f'Warning: Could not set unit combo to "{translated_unit}": {e}')
                    # Fallback: set to first available unit or empty
                    available_units = self.get_units()
                    if available_units:
                        self.stock_unit_combo.set('')
                    else:
                        self.stock_unit_combo.set('')

    def delete_stock(self):
        selected = self.tree_stock.focus()
        if not selected:
            self.stock_status_lbl.configure(text=self.tr('inventory.messages.select_to_delete_stock'), text_color="orange")
            return
        item_name = self.tree_stock.item(selected, 'values')[1]
        conn = sqlite3.connect('fellah.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory WHERE item_name=?", (item_name,))
        conn.commit()
        conn.close()
        self.stock_item_entry.delete(0, 'end')
        self.stock_qty_entry.delete(0, 'end')
        self.stock_status_lbl.configure(text=self.tr('inventory.messages.delete_stock_success'), text_color="red")
        self.load_stock_data()

    def load_stock_data(self):
        print('Loading stock data...')
        try:
            # Clear previous state
            for row in self.tree_stock.get_children(): 
                self.tree_stock.delete(row)
            print('Stock tree cleared successfully')
            
            conn = sqlite3.connect('fellah.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, item_name, quantity, unit, last_updated FROM inventory ORDER BY quantity ASC")
            rows = cursor.fetchall()
            print(f'Found {len(rows)} stock items to load')
            
            for row in rows:
                print(f'Loading item: {row}')
                # Defensive check for None values
                safe_row = []
                for i, value in enumerate(row):
                    if value is None:
                        print(f'Warning: None value found in stock row at index {i}, replacing with empty string')
                        safe_row.append('')
                    else:
                        # Translate unit from database (Arabic) to current language for display
                        if i == 3:  # unit column
                            translated_unit = self.get_translated_unit(value)
                            safe_row.append(translated_unit)
                            print(f'Translated unit: {value} -> {translated_unit}')
                        else:
                            safe_row.append(value)
                self.tree_stock.insert("", "end", values=tuple(safe_row))
            
            conn.close()
            print('Stock data loaded successfully')
        except Exception as e:
            print(f'Error loading stock data: {e}')
            import traceback
            traceback.print_exc()

# =========================================================================
# Secondary Window Classes with Language Switching Support
# =========================================================================

class InventoryWindow(SecondaryWindow):
    """Inventory management secondary window"""
    
    def __init__(self, main_app):
        super().__init__(main_app)
        self.title(self.tr('tabs.inventory'))
        self.geometry("800x600")
        
        # Create UI elements
        self.create_ui()
    
    def create_ui(self):
        """Create the UI elements for this window"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.title_label = ctk.CTkLabel(self.main_frame, text=self.tr('tabs.inventory'), font=("Arial", 18, "bold"))
        self.title_label.pack(pady=10)
        
        self.info_label = ctk.CTkLabel(self.main_frame, text=self.tr('inventory.labels.item_name'))
        self.info_label.pack(pady=5)
    
    def refresh_ui(self):
        """Refresh all UI elements with current language"""
        self.title(self.tr('tabs.inventory'))
        if hasattr(self, 'title_label'):
            self.title_label.configure(text=self.tr('tabs.inventory'))
        if hasattr(self, 'info_label'):
            self.info_label.configure(text=self.tr('inventory.labels.item_name'))

class ManagementWindow(SecondaryWindow):
    """Management monitoring secondary window"""
    
    def __init__(self, main_app):
        super().__init__(main_app)
        self.title(self.tr('management.title'))
        self.geometry("800x600")
        
        # Create UI elements
        self.create_ui()
    
    def create_ui(self):
        """Create the UI elements for this window"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.title_label = ctk.CTkLabel(self.main_frame, text=self.tr('management.title'), font=("Arial", 18, "bold"))
        self.title_label.pack(pady=10)
        
        self.info_label = ctk.CTkLabel(self.main_frame, text=self.tr('management.operations'))
        self.info_label.pack(pady=5)
    
    def refresh_ui(self):
        """Refresh all UI elements with current language"""
        self.title(self.tr('management.title'))
        if hasattr(self, 'title_label'):
            self.title_label.configure(text=self.tr('management.title'))
        if hasattr(self, 'info_label'):
            self.info_label.configure(text=self.tr('management.operations'))

class FeasibilityWindow(SecondaryWindow):
    """Feasibility analysis secondary window"""
    
    def __init__(self, main_app):
        super().__init__(main_app)
        self.title(self.tr('feasibility.title'))
        self.geometry("800x600")
        
        # Create UI elements
        self.create_ui()
    
    def create_ui(self):
        """Create the UI elements for this window"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.title_label = ctk.CTkLabel(self.main_frame, text=self.tr('feasibility.title'), font=("Arial", 18, "bold"))
        self.title_label.pack(pady=10)
        
        self.info_label = ctk.CTkLabel(self.main_frame, text=self.tr('feasibility.analysis'))
        self.info_label.pack(pady=5)
    
    def refresh_ui(self):
        """Refresh all UI elements with current language"""
        self.title(self.tr('feasibility.title'))
        if hasattr(self, 'title_label'):
            self.title_label.configure(text=self.tr('feasibility.title'))
        if hasattr(self, 'info_label'):
            self.info_label.configure(text=self.tr('feasibility.analysis'))

class FinancialAnalysisWindow(SecondaryWindow):
    """Financial analysis secondary window"""
    
    def __init__(self, main_app):
        super().__init__(main_app)
        self.title(self.tr('financial.title'))
        self.geometry("800x600")
        
        # Create UI elements
        self.create_ui()
    
    def create_ui(self):
        """Create the UI elements for this window"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.title_label = ctk.CTkLabel(self.main_frame, text=self.tr('financial.title'), font=("Arial", 18, "bold"))
        self.title_label.pack(pady=10)
        
        self.info_label = ctk.CTkLabel(self.main_frame, text=self.tr('financial.detailed'))
        self.info_label.pack(pady=5)
    
    def refresh_ui(self):
        """Refresh all UI elements with current language"""
        self.title(self.tr('financial.title'))
        if hasattr(self, 'title_label'):
            self.title_label.configure(text=self.tr('financial.title'))
        if hasattr(self, 'info_label'):
            self.info_label.configure(text=self.tr('financial.detailed'))

if __name__ == "__main__":
    app = FellahApp()
    app.mainloop()