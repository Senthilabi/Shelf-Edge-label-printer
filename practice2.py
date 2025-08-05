import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas

from reportlab.lib.pagesizes import landscape
from reportlab.pdfbase import pdfmetrics 
from reportlab.pdfbase.ttfonts import TTFont 
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from io import BytesIO
import base64
import os

# Set label size (width=80mm, height=30mm)

# Label size in mm
LABEL_WIDTH_MM = 80
LABEL_HEIGHT_MM = 30
LABEL_WIDTH = LABEL_WIDTH_MM * mm
LABEL_HEIGHT = LABEL_HEIGHT_MM * mm

# Define column widths in mm
NAME_COL_WIDTH = 50 * mm
MRP_COL_WIDTH = 15 * mm
SP_COL_WIDTH = 15 * mm

# Define row heights in mm (total = 30mm): 12 + 12 + 6
ROW1_Y = LABEL_HEIGHT - 6 * mm   # Top row starts at top
ROW2_Y = LABEL_HEIGHT - 18 * mm  # 12mm down
ROW3_Y = LABEL_HEIGHT - 30 * mm  # Bottom

st.title("🖨️ Label Generator with Barcode Preview and Print")

# Load Tamil and Unicode fonts from local 'fonts' folder
if not os.path.exists("fonts/Noto_Sans_Tamil/NotoSansTamil-VariableFont_wdth,wght.ttf"):#("fonts/NotoSansTamil-Regular.ttf"):
    st.error("Tamil font file not found. Please place 'NotoSansTamil-Regular.ttf' inside the 'fonts' folder.")
    st.stop()

# Register the Tamil font
pdfmetrics.registerFont(TTFont("Tamil", "fonts/Noto_Sans_Tamil/NotoSansTamil-VariableFont_wdth,wght.ttf"))
# Register a Unicode font that supports ₹
pdfmetrics.registerFont(TTFont("Unicode", "fonts/Noto_Sans_Tamil/NotoSansTamil-VariableFont_wdth,wght.ttf"))


uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.dataframe(df)

    selected_rows = st.multiselect("Select Products", df.index, format_func=lambda x: df.loc[x, 'Item Name'])
    
    if selected_rows:
        updated_data = []

        st.subheader("Edit Prices if Needed")
        for idx in selected_rows:
            row = df.loc[idx]
            item_name = row['Item Name']
            tamil_name = row['Tamil']
            mrp = st.text_input(f"MRP for {item_name}", value=str(row['MRP']))
            sp = st.text_input(f"SP for {item_name}", value=str(row['SP']))
            barcode = str(row['Barcode'])
            updated_data.append((item_name, tamil_name, mrp, sp, barcode))

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=landscape((LABEL_WIDTH, LABEL_HEIGHT)))
        
        for item_name, tamil_name, mrp, sp, barcode_text in updated_data:
            # Row 1: English product name + MRP/SP label headings
            c.setFont("Helvetica-Bold", 15)
            c.drawString(2 * mm, ROW1_Y, item_name)

            c.setFont("Helvetica", 10)
            c.drawString(NAME_COL_WIDTH + 1 * mm, ROW1_Y, "MRP")
            c.drawString(NAME_COL_WIDTH + MRP_COL_WIDTH + 1 * mm, ROW1_Y, "SP")

            # Row 2: Tamil product name + Price values
            c.setFont("Tamil", 15)
            c.drawString(2 * mm, ROW2_Y, tamil_name)

            c.setFont("Unicode", 15)
            c.drawString(NAME_COL_WIDTH + 1 * mm, ROW2_Y, f"₹{mrp}")
            # Get text width for ₹MRP
            text_width = pdfmetrics.stringWidth(f"₹{mrp}", "Unicode", 15)
            mrp_x = NAME_COL_WIDTH + 1 * mm
            mrp_y = ROW2_Y

            # Draw line over the text for strike-through
            #c.setLineWidth(1)
            #c.line(mrp_x, mrp_y + 5, mrp_x + text_width, mrp_y + 5)
            
            # Draw cross lines
            c.setLineWidth(2)
            text_height = 12  # Approximate text height in points (1 pt = 1/72 inch)
            # Shorten the diagonal lines
            scale = 0.7  # adjust this to make the X smaller or larger
            dx = text_width * scale
            dy = text_height * scale

            # Center of the text
            center_x = mrp_x + text_width / 2
            center_y = mrp_y + text_height / 2

            # Draw shorter cross lines (scaled diagonals)
            c.setLineWidth(1)
            c.line(center_x - dx / 2, center_y - dy / 2, center_x + dx / 2, center_y + dy / 2)
            c.line(center_x - dx / 2, center_y + dy / 2, center_x + dx / 2, center_y - dy / 2)
                
            # Diagonal from top-left to bottom-right
            #c.line(mrp_x +2, mrp_y + 2, mrp_x + text_width, mrp_y + text_height + 2)
            # Diagonal from bottom-left to top-right
            #c.line(mrp_x+2, mrp_y + text_height + 2, mrp_x + text_width, mrp_y + 2)
            
            c.drawString(NAME_COL_WIDTH + MRP_COL_WIDTH + 1 * mm, ROW2_Y, f"₹{sp}")

            # Row 3: Barcode and number
            barcode = code128.Code128(barcode_text, barHeight=5*mm, barWidth=0.4)
            barcode.drawOn(c, x=2 * mm, y=4 * mm)
            c.setFont("Helvetica", 8)
            c.drawCentredString(LABEL_WIDTH / 2, 2 * mm, barcode_text)

             
            c.showPage()

        c.save()
        buffer.seek(0)

        st.subheader("Label Preview")
        base64_pdf = base64.b64encode(buffer.read()).decode('utf-8')
        pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="500" type="application/pdf">'
        st.markdown(pdf_display, unsafe_allow_html=True)

        # Download button
        st.download_button("Download Labels PDF", data=buffer, file_name="labels.pdf", mime="application/pdf")
        
        # Print Button (browser print)
        st.markdown("""
            <button onclick="window.print()" style="margin-top: 20px; padding: 10px 20px; font-size: 16px;">
                🖨️ Print Label
            </button>
    """, unsafe_allow_html=True)

        # Optional: Local printer (Windows only)
        if st.checkbox("Send to default printer (Windows only)"):
            with open("temp_label.pdf", "wb") as f:
                f.write(buffer.getvalue())

            try:
                import win32api
                win32api.ShellExecute(0, "print", "temp_label.pdf", None, ".", 0)
                st.success("Sent to printer.")
            except Exception as e:
                st.error(f"Print failed: {e}")
else: 
    st.info("Please upload an Excel file with columns: Item Name, Tamil, MRP, SP, Barcode")  