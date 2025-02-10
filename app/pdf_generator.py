from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from PyPDF2 import PdfMerger
from datetime import datetime
import uuid
from PIL import Image
import io
from reportlab.graphics.shapes import Drawing, String

class ExpenseReportGenerator:
    def __init__(self, user_name, expense_type='other'):
        self.user_name = user_name
        self.expense_type = expense_type
        self.styles = getSampleStyleSheet()
        
    def generate_report(self, expenses, travel_details=None, comment=None):
        print("\n=== PDF GENERATION DEBUG ===")
        print("1. Initial Setup")
        
        # Create absolute path for temp directory
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        temp_dir = os.path.join(base_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate unique filename and receipt number
        report_id = f"{self.user_name.lower().replace(' ', '')}-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6]}"
        receipt_number = f"{self.user_name.lower().replace(' ', '')}-{datetime.now().strftime('%Y-%m')}-n{uuid.uuid4().hex[:3]}a"
        final_pdf = os.path.join(temp_dir, f"{report_id}_summary.pdf")
        
        # Create document with SMALLER top margin
        doc = SimpleDocTemplate(
            final_pdf,
            pagesize=A4,
            rightMargin=30,  # Reduced right margin
            leftMargin=72,
            topMargin=30,    # Reduced top margin
            bottomMargin=72
        )
        
        story = []
        
        # Create header table
        from reportlab.graphics.shapes import Drawing, String
        
        # Create the drawing for B&B with just a small offset
        logo_width = 300
        logo_height = 60
        d = Drawing(logo_width, logo_height)
        logo = String(20, 10, 'B&B', fontName='Times-Bold', fontSize=52)  # Just 20 points offset instead of 72
        d.add(logo)
        
        # Format receipt number and date
        current_date = datetime.now().strftime('%d.%m.%Y')
        
        header_data = [
            [
                d,
                Paragraph(
                    f"Rechnungsnummer: {receipt_number}<br/>"
                    f"Datum: {current_date}",
                    ParagraphStyle(
                        'Receipt',
                        fontName='Helvetica',
                        fontSize=10,
                        alignment=2,
                        rightIndent=0,
                        spaceBefore=0,
                        spaceAfter=0,
                        leading=12
                    )
                )
            ]
        ]
        
        # Adjust table to remove left padding
        header_table = Table(header_data, colWidths=[doc.width * 0.6, doc.width * 0.4])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('RIGHTPADDING', (1, 0), (1, 0), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Remove left padding
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 12))
        
        # Add "Expense claim" subtitle
        story.append(Paragraph("Expense claim", ParagraphStyle(
            'Subtitle',
            fontName='Helvetica',
            fontSize=18,
            leading=22,
            spaceAfter=30
        )))
        
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
            # Convert dates to European format (DD-MM-YYYY)
            departure_date = datetime.strptime(travel_details['departure'], '%Y-%m-%d').strftime('%d-%m-%Y')
            return_date = datetime.strptime(travel_details['return'], '%Y-%m-%d').strftime('%d-%m-%Y')
            
            travel_info = [
                Paragraph(f"Purpose: {travel_details['purpose']}", self.styles['Normal']),
                Paragraph(f"From: {travel_details['from']}", self.styles['Normal']),
                Paragraph(f"To: {travel_details['to']}", self.styles['Normal']),
                Paragraph(f"Departure: {departure_date}", self.styles['Normal']),
                Paragraph(f"Return: {return_date}", self.styles['Normal'])
            ]
            story.extend(travel_info)
            story.append(Spacer(1, 20))
        
        # Create the table data
        table_data = [
            ['Date', 'Description', 'EUR', 'Foreign currency']  # Header row
        ]
        
        # Add expense rows
        for expense in expenses:
            foreign_currency = f"{expense['original_currency']} {expense['original_amount']:.2f}" if 'original_currency' in expense and expense['original_currency'] != 'EUR' else ''
            
            row = [
                expense['date'],
                expense['description'],
                f"EUR {expense['amount']:.2f}",
                foreign_currency
            ]
            table_data.append(row)
        
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
        story.append(expense_table)
        
        # Build the document
        doc.build(story)
        
        return final_pdf, report_id
    
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