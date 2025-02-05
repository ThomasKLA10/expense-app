from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfgen import canvas
import os
from PyPDF2 import PdfMerger
from datetime import datetime
import uuid
from PIL import Image
import io

class ExpenseReportGenerator:
    def __init__(self, user_name, expense_type='other'):
        self.user_name = user_name
        self.expense_type = expense_type
        self.styles = getSampleStyleSheet()
        
    def generate_report(self, expenses, travel_details=None, comment=None):
        # Generate unique filename
        report_id = f"{self.user_name.lower().replace(' ', '')}-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6]}"
        
        # Create absolute path for temp directory
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        temp_dir = os.path.join(base_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = os.path.join(temp_dir, f"{report_id}_summary.pdf")
        
        doc = SimpleDocTemplate(
            temp_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create the table data
        table_data = [
            ['Date', 'Description', 'EUR', 'Foreign currency']  # Header row
        ]
        
        # Add expense rows
        for expense in expenses:
            date = expense['date']
            description = expense['description']
            amount_eur = f"EUR {expense['amount']:.2f}"
            # Add foreign currency info if not EUR
            foreign_currency = f"{expense['currency']} {expense['original_amount']:.2f}" if expense['currency'] != 'EUR' else '-'
            
            table_data.append([date, description, amount_eur, foreign_currency])
        
        # Add total row
        total_eur = sum(expense['amount'] for expense in expenses)
        table_data.append(['', 'Total:', f"EUR {total_eur:.2f}", ''])
        
        # Create table style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # Style for total row
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ])
        
        # Create the table
        expense_table = Table(table_data, colWidths=[80, 200, 100, 100])
        expense_table.setStyle(style)
        
        # Build the story
        story = []
        
        # Add header
        story.append(Paragraph("B&B;", self.styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Expense claim", self.styles['Title']))
        story.append(Spacer(1, 20))
        
        # Add employee info
        story.append(Paragraph("Employee", self.styles['Heading2']))
        story.append(Paragraph(self.user_name, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add comment if exists
        if comment:
            story.append(Paragraph("Comment", self.styles['Heading2']))
            story.append(Paragraph(comment, self.styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Add travel details if exists
        if travel_details:
            story.append(Paragraph("Travel Details", self.styles['Heading2']))
            for key, value in travel_details.items():
                if value:  # Only add if value exists
                    story.append(Paragraph(f"{key.capitalize()}: {value}", self.styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Add expenses table
        story.append(Paragraph("Expenses", self.styles['Heading2']))
        story.append(expense_table)
        
        # Generate the PDF
        doc.build(story)
        return temp_path, report_id
    
    @staticmethod
    def merge_with_receipts(summary_pdf, receipt_paths):
        merger = PdfMerger()
        
        # Add the summary PDF first
        merger.append(summary_pdf)
        
        # Process and add each receipt
        for receipt_path in receipt_paths:
            if receipt_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                # Convert image to PDF
                img = Image.open(receipt_path)
                pdf_path = receipt_path.rsplit('.', 1)[0] + '_temp.pdf'
                img.save(pdf_path, 'PDF', resolution=100.0)
                merger.append(pdf_path)
                # Clean up temporary PDF
                os.remove(pdf_path)
            else:
                # Assume it's already a PDF
                merger.append(receipt_path)
        
        # Generate final PDF path
        final_path = summary_pdf.replace('_summary.pdf', '_complete.pdf')
        
        # Write the complete PDF
        merger.write(final_path)
        merger.close()
        
        # Clean up summary PDF
        os.remove(summary_pdf)
        
        return final_path 