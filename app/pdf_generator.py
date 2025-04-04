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
from reportlab.lib.enums import TA_RIGHT

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
        
        # Get first name only
        first_name = self.user_name.split()[0].lower()  # Split name and take first part
        
        # Generate unique filename and receipt number
        report_id = f"{first_name}-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6]}"
        receipt_number = f"{first_name}-{datetime.now().strftime('%Y-%m')}-n{uuid.uuid4().hex[:3]}a"
        final_pdf = os.path.join(temp_dir, f"{report_id}_summary.pdf")
        
        # Adjust document margins
        doc = SimpleDocTemplate(
            final_pdf,
            pagesize=A4,
            leftMargin=30,  # Reduced from default (usually around 72)
            rightMargin=30,  # Reduced from default
            topMargin=30,   # Reduced from default
        )
        
        story = []
        
        # Create header table
        from reportlab.graphics.shapes import Drawing, String
        
        # Create the drawing for B&B with more elegant styling
        logo_width = 300
        logo_height = 40
        d = Drawing(logo_width, logo_height)
        logo = String(0, 5, 'B&B', fontName='Times-Bold', fontSize=56)
        d.add(logo)
        
        # Format receipt number and date
        current_date = datetime.now().strftime('%d.%m.%Y')
        
        # More elegant styles for text elements
        receipt_style = ParagraphStyle(
            'Receipt',
            fontName='Helvetica',  # Changed from Helvetica-Light to standard Helvetica
            fontSize=10,
            alignment=2,
            rightIndent=0,
            spaceBefore=0,
            spaceAfter=0,
            leading=12
        )
        
        title_style = ParagraphStyle(
            'Title',
            fontName='Helvetica',
            fontSize=18,
            leading=22,
            spaceBefore=6,
            spaceAfter=16
        )
        
        heading_style = ParagraphStyle(
            'Heading2',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=14,
            spaceBefore=6,
            spaceAfter=4
        )
        
        normal_style = ParagraphStyle(
            'Normal',
            fontName='Helvetica',  # Changed from Helvetica-Light to standard Helvetica
            fontSize=11,
            leading=13
        )
        
        # Create styles with darker, bolder labels
        label_style = ParagraphStyle(
            'Label',
            fontName='Helvetica-Bold',  # Bold font
            fontSize=11,
            textColor=colors.HexColor('#1a1a1a'),  # Darker text
            leading=14
        )
        
        # Table styles with standard fonts
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC'))
        ])
        
        # Add negative space at the top of the page
        story.append(Spacer(1, -20))  # This will pull everything up
        
        # Create two separate paragraphs for header info
        rechnungsnummer = Paragraph(
            f"Rechnungsnummer: {receipt_number}",
            ParagraphStyle(
                'RightStyle',
                parent=self.styles['Normal'],
                alignment=TA_RIGHT,
                fontSize=10,
                leading=12
            )
        )
        
        datum = Paragraph(
            f"Datum: {current_date}",
            ParagraphStyle(
                'RightStyle',
                parent=self.styles['Normal'],
                alignment=TA_RIGHT,
                fontSize=10,
                leading=12
            )
        )

        # Add them to the story
        story.append(rechnungsnummer)
        story.append(datum)
        
        story.append(d)
        story.append(Spacer(1, -8))  # Reduced from -4 to -8 to bring "Expense claim" closer to B&B
        
        # Add "Expense claim" subtitle
        story.append(Paragraph("Expense claim", title_style))
        
        # Add employee info
        story.append(Paragraph("Employee", heading_style))
        story.append(Paragraph(self.user_name, normal_style))
        story.append(Spacer(1, 20))
        
        # Add comment if exists
        if comment:
            story.append(Paragraph("Comment", heading_style))
            story.append(Paragraph(comment, normal_style))
            story.append(Spacer(1, 20))
        
        # Add travel details if exists
        if travel_details:
            # Convert dates to European format (DD.MM.YYYY)
            departure_date = datetime.strptime(travel_details['departure'], '%Y-%m-%d').strftime('%d.%m.%Y')
            return_date = datetime.strptime(travel_details['return'], '%Y-%m-%d').strftime('%d.%m.%Y')
            
            travel_info = [
                Paragraph("Purpose:", label_style),
                Paragraph(travel_details['purpose'], normal_style),
                Paragraph("From:", label_style),
                Paragraph(travel_details['from'], normal_style),
                Paragraph("To:", label_style),
                Paragraph(travel_details['to'], normal_style),
                Paragraph("Departure:", label_style),
                Paragraph(departure_date, normal_style),
                Paragraph("Return:", label_style),
                Paragraph(return_date, normal_style)
            ]
            story.extend(travel_info)
            story.append(Spacer(1, 20))
        
        # Create the table data
        table_data = [
            ['Date', 'Description', 'EUR', 'Foreign currency']  # Header row
        ]
        
        # Add expense rows
        for expense in expenses:
            # Convert date format from YYYY-MM-DD to DD.MM.YYYY
            date = datetime.strptime(expense['date'], '%Y-%m-%d').strftime('%d.%m.%Y')
            
            foreign_currency = f"{expense['original_currency']} {expense['original_amount']:.2f}" if 'original_currency' in expense and expense['original_currency'] != 'EUR' else ''
            
            row = [
                date,  # Using the reformatted date
                expense['description'],
                f"EUR {expense['amount']:.2f}",
                foreign_currency
            ]
            table_data.append(row)
        
        # Add total row
        total_eur = sum(expense['amount'] for expense in expenses)
        table_data.append(['', 'Total:', f"EUR {total_eur:.2f}", ''])
        
        # Create the table
        expense_table = Table(table_data, colWidths=[80, 200, 100, 100])
        expense_table.setStyle(table_style)
        
        # Build the story
        story.append(expense_table)
        
        # Build the document
        doc.build(story)
        
        return final_pdf, report_id
    
    @staticmethod
    def merge_with_receipts(summary_pdf, receipt_paths):
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from PyPDF2 import PdfReader, PdfWriter
            import io
            
            # Create a new PDF writer for the final document
            final_writer = PdfWriter()
            
            # Add the summary PDF first
            summary_reader = PdfReader(summary_pdf)
            for page in summary_reader.pages:
                final_writer.add_page(page)
            
            # Process and add each receipt
            for receipt_path in receipt_paths:
                if receipt_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff')):
                    try:
                        # Open image
                        img = Image.open(receipt_path)
                        
                        # Convert to RGB if needed
                        if img.mode not in ('RGB', 'L'):
                            img = img.convert('RGB')
                        
                        # Create a PDF with reportlab
                        packet = io.BytesIO()
                        c = canvas.Canvas(packet, pagesize=A4)
                        width, height = A4
                        
                        # Calculate dimensions to COMPLETELY fill the page (100%)
                        img_ratio = img.width / img.height
                        page_ratio = width / height
                        
                        if img_ratio > page_ratio:
                            # Image is wider than page ratio - fit to width
                            new_width = width  # Use 100% of page width
                            new_height = new_width / img_ratio
                        else:
                            # Image is taller than page ratio - fit to height
                            new_height = height  # Use 100% of page height
                            new_width = new_height * img_ratio
                        
                        # Calculate position to center the image
                        x = (width - new_width) / 2
                        y = (height - new_height) / 2
                        
                        # Draw the image on the canvas
                        c.drawImage(receipt_path, x, y, width=new_width, height=new_height)
                        c.save()
                        
                        # Create a new PDF with the image
                        packet.seek(0)
                        new_pdf = PdfReader(packet)
                        final_writer.add_page(new_pdf.pages[0])
                        
                    except Exception as e:
                        print(f"Error processing image {receipt_path}: {str(e)}")
                else:
                    # For existing PDFs
                    try:
                        reader = PdfReader(receipt_path)
                        for page in reader.pages:
                            final_writer.add_page(page)
                    except Exception as e:
                        print(f"Error processing PDF {receipt_path}: {str(e)}")
            
            # Generate final PDF path
            final_path = summary_pdf.replace('_summary.pdf', '_complete.pdf')
            
            # Write the complete PDF
            with open(final_path, 'wb') as f:
                final_writer.write(f)
            
            # Clean up summary PDF
            os.remove(summary_pdf)
            
            return final_path
        except Exception as e:
            import traceback
            print(f"Error merging PDFs: {str(e)}")
            print(traceback.format_exc())
            return summary_pdf 