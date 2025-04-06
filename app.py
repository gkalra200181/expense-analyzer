from flask import Flask, request, send_file, render_template
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import requests
import io
import os

app = Flask(__name__, template_folder="templates")

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

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

        # Save BytesIO to a file on /tmp
        path1 = '/tmp/chart1.png'
        with open(path1, 'wb') as f:
            f.write(buf1.read())
        chart_paths.append(path1)
        plt.clf()

        # Bar Chart (Monthly Spending)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col_
