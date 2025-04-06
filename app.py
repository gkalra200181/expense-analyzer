
from flask import Flask, request, send_file, render_template
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import requests
import io
import os
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def generate_pdf_report():
    file = request.files['file']

    try:
        df = pd.read_excel(file)

        category_col = next((col for col in df.columns if 'category' in col.lower()), None)
        date_col = next((col for col in df.columns if 'date' in col.lower()), None)
        value_col = next((col for col in df.select_dtypes(include='number').columns), None)

        if not category_col or not value_col:
            return "Missing required columns (category or value).", 400

        chart_paths = []

        # Pie Chart
        buf1 = io.BytesIO()
        df.groupby(category_col)[value_col].sum().plot.pie(autopct='%1.1f%%', figsize=(6,6))
        plt.title("Spending by Category")
        plt.ylabel('')
        plt.tight_layout()
        plt.savefig(buf1, format='png')
        buf1.seek(0)
        path1 = '/tmp/chart1.png'
        with open(path1, 'wb') as f: f.write(buf1.read())
        chart_paths.append(path1)
        plt.clf()

        # Bar Chart (Monthly Spending)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df_time = df.groupby(df[date_col].dt.to_period("M"))[value_col].sum()
            df_time.index = df_time.index.astype(str)
            df_time.plot.bar(figsize=(8,5))
            plt.title("Monthly Spending")
            plt.ylabel("Amount")
            plt.xticks(rotation=45)
            plt.tight_layout()
            buf2 = io.BytesIO()
            plt.savefig(buf2, format='png')
            buf2.seek(0)
            path2 = '/tmp/chart2.png'
            with open(path2, 'wb') as f: f.write(buf2.read())
            chart_paths.append(path2)
            plt.clf()

        # Top 5 Expenses
        top5 = df.sort_values(value_col, ascending=False).head(5)
        top5.set_index(category_col)[value_col].plot(kind='barh', figsize=(6,4))
        plt.title("Top 5 Expenses")
        plt.tight_layout()
        buf3 = io.BytesIO()
        plt.savefig(buf3, format='png')
        buf3.seek(0)
        path3 = '/tmp/chart3.png'
        with open(path3, 'wb') as f: f.write(buf3.read())
        chart_paths.append(path3)
        plt.clf()

        # AI Insights
        csv_text = df.to_csv(index=False)
        prompt = f"""You are a helpful AI financial assistant. Here's a CSV of someone's expenses:

{csv_text}

Please provide:
1. Main spending categories
2. Cost-saving opportunities
3. Any unusual patterns
4. Budgeting advice"""

        # Fetching response from Together AI (Claude)
        response = requests.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {TOGETHER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-3-haiku-20240307",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
            }
        )

        # Debugging: print the raw response
        print("Together AI raw response:", response.text)

        try:
            insights = response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print("Failed to parse Claude insights:", e)
            insights = "AI response could not be parsed. Please check the server logs."

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Expense Analysis Report", ln=True, align='C')
        pdf.set_font("Arial", size=12)

        for line in insights.split('\n'):
            pdf.multi_cell(0, 10, line)

        for chart_path in chart_paths:
            pdf.add_page()
            pdf.image(chart_path, x=20, w=170)

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

