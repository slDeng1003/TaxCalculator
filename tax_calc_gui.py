import tkinter as tk
from tkinter import ttk, messagebox
from data import CITY_SOCIAL_UPPER_LIMITS
from core import calculate_monthly_details


# ------------------- GUI逻辑 -------------------
class TaxCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("中国薪资明细计算器")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        self._init_styles()
        self._create_input_panel()
        self._create_result_area()


    def _init_styles(self):
        self.style = ttk.Style(self.root)
        self.style.configure('Treeview', font=('微软雅黑', 10))
        self.style.map('Treeview', background=[('selected', '#e0e0ff')])
        self.style.configure("Accent.TButton", font=('微软雅黑', 10, 'bold'), fg="#fff", bg="#0078d4")


    def _create_input_panel(self):
        input_frame = ttk.LabelFrame(self.root, text="输入参数", padding=15)
        input_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(input_frame, text="税前月薪（元）：").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.salary_entry = ttk.Entry(input_frame, width=22)
        self.salary_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.salary_entry.insert(0, "40000")
        
        ttk.Label(input_frame, text="社保基数（元）：").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.social_base_entry = ttk.Entry(input_frame, width=22)
        self.social_base_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        self.social_base_entry.insert(0, "40000")
        
        ttk.Label(input_frame, text="所在城市：").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.city_combo = ttk.Combobox(
            input_frame,
            values=list(CITY_SOCIAL_UPPER_LIMITS.keys()),
            state="readonly",
            width=20
        )
        self.city_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        self.city_combo.set("杭州")
        
        ttk.Label(input_frame, text="五险个人比例（%）：").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.insurance_rate_entry = ttk.Entry(input_frame, width=22)
        self.insurance_rate_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        self.insurance_rate_entry.insert(0, "10.5")
        
        ttk.Label(input_frame, text="公积金个人比例（%）：").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.fund_rate_entry = ttk.Entry(input_frame, width=22)
        self.fund_rate_entry.grid(row=4, column=1, sticky=tk.W, pady=5)
        self.fund_rate_entry.insert(0, "12")
        
        self.calc_btn = ttk.Button(
            input_frame,
            text="计算全年薪资明细",
            command=self._calculate_and_display,
            style="Accent.TButton"
        )
        self.calc_btn.grid(row=5, column=0, columnspan=2, pady=15)


    def _create_result_area(self):
        result_frame = ttk.LabelFrame(self.root, text="计算结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        self._create_monthly_table(result_frame)
        self._create_annual_summary(result_frame)


    def _create_monthly_table(self, parent):
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_tree = ttk.Treeview(
            table_frame,
            columns=(
                "month", "pre_tax_income", "pension", "medical", "unemployment",
                "housing_fund", "taxable_income", "current_tax", "takehome"
            ),
            show="headings",
            yscrollcommand=scrollbar.set,
            height=12
        )
        
        column_setup = [
            ("month", "月份", 50),
            ("pre_tax_income", "税前收入（元）", 80),
            ("pension", "养老保险（元）", 80),
            ("medical", "医疗保险（元）", 80),  # 展示修正后的医疗保险
            ("unemployment", "失业保险（元）", 80),
            ("housing_fund", "公积金（元）", 80),
            ("taxable_income", "累计应纳税所得额（元）", 140),
            ("current_tax", "当月个税（元）", 80),
            ("takehome", "当月税后收入（元）", 80)
        ]
        
        for col_id, col_text, col_width in column_setup:
            self.result_tree.heading(col_id, text=col_text)
            self.result_tree.column(col_id, width=col_width, anchor=tk.CENTER)
        
        self.result_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.result_tree.yview)


    def _create_annual_summary(self, parent):
        summary_frame = ttk.LabelFrame(parent, text="年度总额汇总", padding=10)
        summary_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.summary_labels = {}
        labels = [
            ("全年税前收入", "total_pre_tax"),
            ("全年个税合计", "total_tax"),
            ("全年双边公积金合计", "total_housing_fund"),
            ("全年税后收入", "total_takehome"),
            ("全年税后收入（含公积金）", "total_takehome_with_housing")
        ]
        
        for i, (text, key) in enumerate(labels):
            label = ttk.Label(
                summary_frame,
                text=f"{text}：0.00元",
                font=('微软雅黑', 10, 'bold'),
                foreground="#2F5496"
            )
            label.grid(row=0, column=i*2, padx=20, sticky=tk.W)
            self.summary_labels[key] = label


    def _calculate_and_display(self):
        try:
            salary = float(self.salary_entry.get())
            social_base = float(self.social_base_entry.get())
            city = self.city_combo.get()
            insurance_rate = float(self.insurance_rate_entry.get()) / 100
            fund_rate = float(self.fund_rate_entry.get()) / 100
            
            if salary <= 0 or social_base <= 0:
                raise ValueError("税前月薪/社保基数必须大于0")
            if not (0 < insurance_rate < 1) or not (0 < fund_rate < 1):
                raise ValueError("比例需在0-100%之间")
            if not city:
                raise ValueError("请选择所在城市")
            
            result = calculate_monthly_details(
                monthly_salaries=salary,
                social_security_bases=social_base,
                city=city,
                five_insurance_rate=insurance_rate,
                housing_fund_rate=fund_rate
            )
            monthly_data = result["monthly"]
            annual_summary = result["annual"]
            
            self.result_tree.delete(*self.result_tree.get_children())
            for data in monthly_data:
                self.result_tree.insert("", tk.END, values=(
                    data["month"],
                    data["pre_tax_income"],
                    data["pension"],
                    data["medical"],
                    data["unemployment"],
                    data["housing_fund"],
                    # data["total_social_housing"],
                    data["taxable_income"],
                    data["current_tax"],
                    data["takehome"]
                ))
            
            self.summary_labels["total_pre_tax"].config(text=f"全年税前收入：{annual_summary['total_pre_tax']:.2f}元")
            self.summary_labels["total_housing_fund"].config(text=f"全年双边公积金合计：{2*annual_summary['total_housing_fund']:.2f}元")
            self.summary_labels["total_tax"].config(text=f"全年个税合计：{annual_summary['total_tax']:.2f}元")
            self.summary_labels["total_takehome"].config(text=f"全年税后收入：{annual_summary['total_takehome']:.2f}元")
            self.summary_labels["total_takehome_with_housing"].config(text=f"全年税后收入（含公积金）：{annual_summary['total_takehome_with_housing']:.2f}元")
        
        except ValueError as e:
            messagebox.showerror("输入错误", str(e), parent=self.root)
        except Exception as e:
            messagebox.showerror("计算失败", f"未知错误：{str(e)}", parent=self.root)


if __name__ == "__main__":
    root = tk.Tk()
    app = TaxCalculatorGUI(root)
    root.mainloop()