from flask import Flask, request, send_file, render_template
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import io
import os

app = Flask(__name__)

# Set a directory for saving files
UPLOAD_FOLDER = '/tmp/charts'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def generate_pdf_report():
    file = request.files['file']

    try:
        # Read the uploaded Excel file into a DataFrame
        df = pd.read_excel(file)

        # Identify relevant columns (category, date, value)
        category_col = next((col for col in df.columns if 'category' in col.lower()), None)
        date_col = next((col for col in df.columns if 'date' in col.lower()), None)
        value_col = next((col for col in df.select_dtypes(include='number').columns), None)

        if not category_col or not value_col:
            return "Missing required columns (category or value).", 400

        # Predefined Insights:
        total_spending = df[value_col].sum()
        top_3_categories = df.groupby(category_col)[value_col].sum().sort_values(ascending=False).head(3)
        monthly_trends = df.groupby(df[date_col].dt.to_period("M"))[value_col].sum() if date_col else None

        # Generate Charts
        chart_paths = []

        # Pie Chart: Spending by Category
      
        df.groupby(category_col)[value_col].sum().plot.pie(autopct='%1.1f%%', figsize=(6,6))
        plt.title("Spending by Category")
        plt.ylabel('')
        plt.tight_layout()
        chart_path1 = os.path.join(UPLOAD_FOLDER, 'chart1.png')
        plt.savefig(chart_path1)
        chart_paths.append(chart_path1)
        plt.clf()

        # Bar Chart: Monthly Spending
        if monthly_trends is not None:
          
            monthly_trends.plot.bar(figsize=(8,5))
            plt.title("Monthly Spending")
            plt.ylabel("Amount")
            plt.xticks(rotation=45)
            plt.tight_layout()
            chart_path2 = os.path.join(UPLOAD_FOLDER, 'chart2.png')
            plt.savefig(chart_path2)
            chart_paths.append(chart_path2)
            plt.clf()

        # Bar Chart: Top 3 Categories
      
        top_3_categories.plot(kind='bar', figsize=(6,4))
        plt.title("Top 3 Categories")
        plt.tight_layout()
        chart_path3 = os.path.join(UPLOAD_FOLDER, 'chart3.png')
        plt.savefig(chart_path3)
        chart_paths.append(chart_path3)
        plt.clf()

        # Generate PDF with Insights and Charts
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Expense Analysis Report", ln=True, align='C')
        pdf.set_font("Arial", size=12)

        # Add Predefined Insights Text
        pdf.multi_cell(0, 10, f"Total Spending: ${total_spending:,.2f}")
        pdf.multi_cell(0, 10, f"\nTop 3 Categories:\n{top_3_categories.to_string()}")
        if monthly_trends is not None:
            pdf.multi_cell(0, 10, f"\nMonthly Spending Trends:\n{monthly_trends.to_string()}")

        # Add Charts to the PDF
        for chart_path in chart_paths:
            pdf.add_page()
            if os.path.exists(chart_path):
                pdf.image(chart_path, x=20, w=170)  # Uses file path, not BytesIO
            else:
                print(f"Warning: Chart file not found: {chart_path}")

        pdf_buf = io.BytesIO()
        pdf.output(pdf_buf)
        pdf_buf.seek(0)

        return send_file(pdf_buf, as_attachment=True,
                         download_name="Expense_Report.pdf",
                         mimetype='application/pdf')

    except Exception as e:
        print("Error:", e)
        return f"Something went wrong: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
