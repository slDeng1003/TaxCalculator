import tkinter as tk
from tax_calc_gui import TaxCalculatorGUI



if __name__ == "__main__":
    root = tk.Tk()
    app = TaxCalculatorGUI(root)
    root.mainloop()