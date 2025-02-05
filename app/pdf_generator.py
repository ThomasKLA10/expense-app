from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfgen import canvas
import os
from PyPDF2 import PdfMerger
from datetime import datetime
import uuid

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
        
        # Build content
        story = []
        
        # Add logo
        story.append(Paragraph("B&B", self.styles['Heading1']))
        story.append(Spacer(1, 20))
        
        # Add title
        story.append(Paragraph("Expense claim", self.styles['Heading1']))
        story.append(Spacer(1, 20))
        
        # Add employee info
        story.append(Paragraph(f"Employee", self.styles['Heading2']))
        story.append(Paragraph(self.user_name, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add comment if exists
        if comment:
            story.append(Paragraph("Comment", self.styles['Heading2']))
            story.append(Paragraph(comment, self.styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Add travel details if travel expense
        if self.expense_type == 'travel' and travel_details:
            story.append(Paragraph("Travel Details", self.styles['Heading2']))
            travel_data = [
                ["Purpose:", travel_details.get('purpose', '')],
                ["From:", travel_details.get('from', '')],
                ["To:", travel_details.get('to', '')],
                ["Departure:", travel_details.get('departure', '')],
                ["Return:", travel_details.get('return', '')]
            ]
            travel_table = Table(travel_data, colWidths=[100, 400])
            travel_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(travel_table)
            story.append(Spacer(1, 20))
        
        # Add expenses table
        story.append(Paragraph("Expenses", self.styles['Heading2']))
        expense_data = [['Date', 'Description', 'EUR', 'Foreign currency']]
        total_eur = 0
        
        for expense in expenses:
            expense_data.append([
                expense['date'],
                expense['description'],
                f"EUR {expense['amount']:.2f}",
                expense.get('foreign_amount', '-')
            ])
            total_eur += float(expense['amount'])
        
        expense_table = Table(expense_data, colWidths=[100, 200, 100, 100])
        expense_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        story.append(expense_table)
        story.append(Spacer(1, 20))
        
        # Add total
        story.append(Paragraph(f"Total: EUR {total_eur:.2f}", self.styles['Heading2']))
        
        # Generate the PDF
        doc.build(story)
        return temp_path, report_id
    
    @staticmethod
    def merge_with_receipts(summary_pdf, receipt_files):
        merger = PdfMerger()
        
        # Add summary page
        merger.append(summary_pdf)
        
        # Add each receipt
        for receipt in receipt_files:
            merger.append(receipt)
        
        # Generate final PDF path in the same directory as summary_pdf
        final_path = summary_pdf.replace('_summary.pdf', '_complete.pdf')
        
        # Write the complete PDF
        merger.write(final_path)
        merger.close()
        
        # Clean up summary PDF
        os.remove(summary_pdf)
        
        return final_path 