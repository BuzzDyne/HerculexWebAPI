import os
import time
import random
import string
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pdf417 import encode, render_image
from PIL import Image

doc_type_mapping = {"Q": "QUO", "I": "INV"}
CAP_IMAGE_PATH = "res/CapTTD.png"
NORMAL_FONT = "Reddit-Medium"
BOLD_FONT = "Reddit-Black"
ITALIC_FONT = "MyPoppin-Italic"


def generate_invoice_number(invoice_id, doc_type):
    # Get the current year and month
    now = datetime.now()
    year = now.year
    month = now.strftime("%m")  # Get the month in numerical format

    # Convert month to Roman numerals
    roman_numerals = [
        "",
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI",
        "VII",
        "VIII",
        "IX",
        "X",
        "XI",
        "XII",
    ]
    roman_month = roman_numerals[int(month)]
    shorthand_doc = doc_type_mapping.get(doc_type, "OTH")

    # Generate the invoice number
    invoice_number = f"HCX/{shorthand_doc}/{year}/{roman_month}/{invoice_id}"

    return invoice_number


def format_number_with_commas(number):
    formatted_number = "{:,}".format(number)
    return formatted_number


def capitalize_words(input_string, max_length=60):
    # Define the delimiters
    delimiters = [" ", "/", ",", "-"]

    # Split the input string into words using any of the delimiters
    words = []
    current_word = ""
    current_delimiter = ""

    for char in input_string:
        if char in delimiters:
            if current_word:
                words.append(current_word)
                current_word = ""
            current_delimiter = char
        else:
            current_word += char

    if current_word:
        words.append(current_word)

    # Capitalize each word and join them back into a string using the original delimiters
    result_string = current_delimiter.join(word.capitalize() for word in words)

    # Check if the resulting string exceeds the maximum length
    if len(result_string) > max_length:
        # Find the last space within the limit
        last_space_index = max_length
        while last_space_index > 0 and result_string[last_space_index] != " ":
            last_space_index -= 1

        # Trim the string to the last space within the limit
        result_string = result_string[:last_space_index].rstrip()

    return result_string


def convert_to_terbilang(number):
    # Define the words for each digit
    satuan = [
        "",
        "SATU",
        "DUA",
        "TIGA",
        "EMPAT",
        "LIMA",
        "ENAM",
        "TUJUH",
        "DELAPAN",
        "SEMBILAN",
    ]
    belasan = [
        "",
        "SEBELAS",
        "DUA BELAS",
        "TIGA BELAS",
        "EMPAT BELAS",
        "LIMA BELAS",
        "ENAM BELAS",
        "TUJUH BELAS",
        "DELAPAN BELAS",
        "SEMBILAN BELAS",
    ]
    puluhan = [
        "",
        "SEPULUH",
        "DUA PULUH",
        "TIGA PULUH",
        "EMPAT PULUH",
        "LIMA PULUH",
        "ENAM PULUH",
        "TUJUH PULUH",
        "DELAPAN PULUH",
        "SEMBILAN PULUH",
    ]

    # Function to convert a group of three digits into words
    def convert_group_of_three(num):
        result = ""

        # Ensure num is an integer
        num = int(num)

        # Handle digit in hundreds place
        if num >= 100:
            if num >= 100 and num < 200:
                result += "SERATUS "
            else:
                result += satuan[num // 100] + " RATUS "
            num %= 100

        # Handle digit in tens and ones place
        if num >= 10:
            if num < 20:
                result += belasan[num - 10] + " "
                num = 0  # Set num to 0 to avoid processing the ones place
            else:
                result += puluhan[num // 10] + " "
                num %= 10

        # Handle digit in ones place
        if num > 0:
            result += satuan[num] + " "

        return result

    # Convert the given number into "Terbilang"
    terbilang_result = ""
    if number == 0:
        terbilang_result = "NOL"
    else:
        groups = []
        while number > 0:
            groups.append(number % 1000)
            number //= 1000

        for i in range(len(groups) - 1, -1, -1):
            if groups[i] != 0:
                terbilang_result += convert_group_of_three(groups[i])

                # Append the unit (RIBU, JUTA, MILYAR) only if it's not the last group
                if i > 0:
                    terbilang_result += ["", "RIBU ", "JUTA ", "MILYAR "][i]

    terbilang_result += "RUPIAH"

    return split_string(terbilang_result.strip())


def split_string(input_string, max_length=70, br_token="~!~"):
    # Split the input string by the special token
    segments = input_string.split(br_token)
    result_list = []

    for segment in segments:
        words = segment.split()
        current_line = ""

        for word in words:
            if len(current_line + word) <= max_length:
                current_line += word + " "
            else:
                result_list.append(current_line.strip())
                current_line = word + " "

        if current_line:
            result_list.append(current_line.strip())

    return result_list


def print_sample_pdf():
    pdfmetrics.registerFont(TTFont("Reddit-Black", "res/fonts/RedditMono-Black.ttf"))
    pdfmetrics.registerFont(TTFont("Reddit-Medium", "res/fonts/RedditMono-Medium.ttf"))

    # Generate PDF using ReportLab
    ts = int(time.time())
    pdf_buffer = BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=A4)
    row_height = 20
    width, height = A4

    p.setTitle(ts)

    p.setFont(NORMAL_FONT, 10)
    p.setFillColorRGB(0.20784313725490197, 0.1843137254901961, 0.21176470588235294)

    # 106 Char
    p.drawString(0, 0, "123")
    p.drawString(width / 2, height / 2, "123123123123123123123123")

    # Finish the first page and start a new one
    p.showPage()

    # Add content to the second page
    p.drawString(100, 100, "This is the second page")

    # Save the PDF to the current working directory
    p.save()
    pdf_buffer.seek(0)
    with open(os.path.join(os.getcwd(), f"{ts}.pdf"), "wb") as f:
        f.write(pdf_buffer.getbuffer())


def process_invoice_item_rows(inv_data):
    """
    Processes invoice data to map various invoice components to their respective
    positions within a predefined layout. It ensures that each item (such as recipient
    name, address, and order details) fits within the specified maximum lengths for the
    left and right columns of the invoice layout.

    Args:
        inv_data (dict): A dictionary containing invoice details with the following keys:
            - receipent_name (str): The name of the recipient.
            - receipent_telp (str): The telephone number of the recipient.
            - receipent_addr (str): The address of the recipient.
            - sender_name (str): The name of the sender.
            - sender_telp (str): The telephone number of the sender.
            - total_amount (float): The total amount of the invoice.
            - bank_name (str): The name of the bank (optional).
            - order_detail (str): Details of the order.

    Returns:
        tuple: A tuple containing:
            - item_mapping (dict): A dictionary where each key represents a component
              of the invoice and each value is a dictionary with:
                - start_index_row (int): The starting row index for this component.
                - lines (list of str): The lines of text for this component, split to fit
                  within the column width.
            - max_row_count (int): The maximum number of rows required to fit all components,
              ensuring a minimum row count of 13.
    """
    MIN_ROWS = 13
    L_MAX_LENGTH = 37
    R_MAX_LENGTH = 46

    item_mapping = {}

    # region Left Col
    curr_row = 1

    data_rows = split_string(inv_data["receipent_name"], L_MAX_LENGTH)
    item_mapping["r_name"] = {
        "start_index_row": curr_row,
        "lines": data_rows,
    }

    curr_row += max(len(data_rows), 1)
    item_mapping["r_telp"] = {
        "start_index_row": curr_row,
        "lines": [inv_data["receipent_telp"]],
    }

    curr_row += 1
    data_rows = split_string(inv_data["receipent_addr"], L_MAX_LENGTH)
    item_mapping["r_addr"] = {
        "start_index_row": curr_row,
        "lines": data_rows,
    }

    curr_row += max(len(data_rows), 1)
    data_rows = split_string(inv_data["sender_name"], L_MAX_LENGTH)
    item_mapping["s_name"] = {
        "start_index_row": curr_row,
        "lines": data_rows,
    }

    curr_row += max(len(data_rows), 1)
    item_mapping["s_telp"] = {
        "start_index_row": curr_row,
        "lines": [inv_data["sender_telp"]],
    }

    l_row_count = curr_row
    # endregion

    # region Right Col
    curr_row = 1

    totalText = f"Rp {format_number_with_commas(inv_data['total_amount'])}"
    if inv_data["bank_name"]:
        totalText += f" - {inv_data['bank_name']}"

    item_mapping["d_total"] = {
        "start_index_row": curr_row,
        "lines": [totalText],
    }

    curr_row += 2
    data_rows = split_string(inv_data["order_detail"], R_MAX_LENGTH)
    item_mapping["d_detail"] = {
        "start_index_row": curr_row,
        "lines": data_rows,
    }

    r_row_count = curr_row + len(data_rows) - 1
    # endregion

    return item_mapping, max(MIN_ROWS, l_row_count, r_row_count)


def generate_orderanku(data):
    pdfmetrics.registerFont(TTFont("Reddit-Black", "res/fonts/RedditMono-Black.ttf"))
    pdfmetrics.registerFont(TTFont("Reddit-Medium", "res/fonts/RedditMono-Medium.ttf"))

    # Generate PDF using ReportLab
    pdf_buffer = BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=A4)

    # region Calculate Invoice Height

    # endregion

    # region Definitions
    UNIT = 12
    width, height = A4
    MID_X = width / 2
    BARCODE_W = 100 / 2
    BARCODE_H = 350 / 2
    TEXT_LEV = 3.3

    table_rows = 16  # Need to be calculated
    top_y = height - UNIT
    bot_y = height - (table_rows * UNIT)

    left_top = (2 * UNIT, top_y)
    left_bot = (2 * UNIT, bot_y)
    right_top = (width - 2 * UNIT, top_y)
    right_bot = (width - 2 * UNIT, bot_y)
    mid_top = (MID_X, top_y)
    mid_bot = (MID_X, bot_y)

    p.setFont(NORMAL_FONT, 8)
    p.setFillColorRGB(0, 0, 0)
    p.setStrokeColorRGB(0.25, 0.25, 0.25)
    # endregion

    # region Create Table
    # Vertical Lines
    p.line(*mid_top, *mid_bot)
    p.line(*left_top, *left_bot)
    p.line(*right_top, *right_bot)

    # Horizontal Lines
    p.line(*left_top, *right_top)
    p.line(*left_bot, *right_bot)

    # Subheader
    sub_x1 = MID_X - 5
    sub_x2 = right_top[0] - 5
    sub_y = top_y - UNIT + TEXT_LEV

    lunas_str = "LUNAS" if data["paid_flag"] else "BELUM LUNAS"
    oid_str = data["orderanku_id"]

    subheader_text = f"{lunas_str} (ORDER {oid_str}) 2024-12-31"

    p.drawRightString(sub_x1, sub_y, subheader_text)
    p.drawRightString(sub_x2, sub_y, subheader_text)
    # endregion

    # Helper Line
    for i in range(1, table_rows - 2):
        row_y = top_y - ((2 + i) * UNIT)
        p.line(left_top[0], row_y, right_top[0], row_y)
        p.drawString(MID_X - 10, row_y + TEXT_LEV, f"{i}")

    # region Barcodes
    # Generate the barcode image
    barcode_image = create_pdf417_barcode(data["receipent_name"])

    # Draw the barcode (Left)
    barcode_x = left_bot[0] + 2
    barcode_y = left_bot[1] + 3  # Adjust the y pos

    p.drawInlineImage(
        barcode_image, barcode_x, barcode_y, width=BARCODE_W, height=BARCODE_H
    )

    barcode_line_x_1 = barcode_x + BARCODE_W + 2
    p.line(barcode_line_x_1, left_bot[1], barcode_line_x_1, left_top[1])

    # Draw the barcode (Right)
    barcode_x = mid_bot[0] + 2
    barcode_y = mid_bot[1] + 3  # Adjust the y pos

    p.drawInlineImage(
        barcode_image, barcode_x, barcode_y, width=BARCODE_W, height=BARCODE_H
    )
    barcode_line_x_2 = barcode_x + BARCODE_W + 2
    p.line(barcode_line_x_2, bot_y, barcode_line_x_2, top_y)
    # endregion

    # region Data Header
    p.setFont(BOLD_FONT, 8)
    dh_x_l = barcode_line_x_1 + 5
    colon_x_l = dh_x_l + 37
    base_text_y = left_top[1] - (2 * UNIT) + TEXT_LEV

    p.drawString(dh_x_l, base_text_y - (1 * UNIT), "Kepada")
    p.drawString(dh_x_l, base_text_y - (2 * UNIT), "Telp")
    p.drawString(dh_x_l, base_text_y - (3 * UNIT), "Alamat")
    p.drawString(dh_x_l, base_text_y - (5 * UNIT), "Pengirim")
    p.drawString(dh_x_l, base_text_y - (6 * UNIT), "Telp")

    p.drawString(colon_x_l, base_text_y - (1 * UNIT), ":")
    p.drawString(colon_x_l, base_text_y - (2 * UNIT), ":")
    p.drawString(colon_x_l, base_text_y - (3 * UNIT), ":")
    p.drawString(colon_x_l, base_text_y - (5 * UNIT), ":")
    p.drawString(colon_x_l, base_text_y - (6 * UNIT), ":")

    p.setFont(NORMAL_FONT, 8)  # Max Length for data 37 char
    p.drawString(colon_x_l + 5, base_text_y - (1 * UNIT), f"{data['receipent_name']}")
    p.drawString(colon_x_l + 5, base_text_y - (2 * UNIT), f"{data['receipent_telp']}")
    p.drawString(colon_x_l + 5, base_text_y - (3 * UNIT), f"{data['receipent_addr']}")
    p.drawString(colon_x_l + 5, base_text_y - (5 * UNIT), f"{data['sender_name']}")
    p.drawString(colon_x_l + 5, base_text_y - (6 * UNIT), f"{data['sender_telp']}")

    dh_x_2 = barcode_line_x_2 + 5
    colon_x_2 = dh_x_2 + 32

    p.setFont(BOLD_FONT, 8)
    p.drawString(dh_x_2, base_text_y - (1 * UNIT), "Total")
    p.drawString(dh_x_2, base_text_y - (2 * UNIT), "Pesanan")

    p.drawString(colon_x_2, base_text_y - (1 * UNIT), ":")
    p.drawString(colon_x_2, base_text_y - (2 * UNIT), ":")

    p.setFont(NORMAL_FONT, 8)
    totalText = f"Rp {format_number_with_commas(data['total_amount'])}"
    if data["bank_name"]:
        totalText += f" - {data['bank_name']}"

    p.drawString(colon_x_2 + 5, base_text_y - (1 * UNIT), totalText)
    p.drawString(colon_x_2 + 5, base_text_y - (2 * UNIT), f"{data['order_detail']}")
    p.drawString(dh_x_2, base_text_y - (3 * UNIT), f"{data['order_detail']}")

    # endregion

    # Save the PDF to the current working directory
    p.save()
    pdf_buffer.seek(0)
    with open(os.path.join(os.getcwd(), f"{int(time.time())}.pdf"), "wb") as f:
        f.write(pdf_buffer.getbuffer())


def create_pdf417_barcode(data_str):
    # Hardcoded dimensions for the output image
    target_width = 350
    target_height = 100

    # Truncate data_str to the first 790 characters if necessary
    if len(data_str) > 790:
        data_str = data_str[:790]
    # Ensure data_str is at least 6 characters long
    if len(data_str) < 300:
        remaining_length = 300 - len(data_str)
        random_alphabets = "".join(
            random.choice(string.ascii_lowercase) for _ in range(remaining_length)
        )
        data_str += "~EOF~" + random_alphabets

    # Encode the data
    codes = encode(data_str)

    # Render the barcode image with an initial scale
    image = render_image(codes, scale=10, ratio=1, padding=2)

    # Resize the image to fit the target dimensions
    resized_image = image.resize((target_width, target_height))

    # Rotate the image 90 degrees clockwise
    rotated_image = resized_image.rotate(-90, expand=True)

    # Save the final image
    # rotated_image.save(f"{int(time.time())}_{len(data_str)}.jpg")

    return rotated_image


if __name__ == "__main__":
    invoice_data = {
        "doc_type": "INV",  # 'Q' for quotation or 'INV' for invoice
        "customer_name": "John Doe",
        "customer_addr_1": "123 Main St",
        "customer_addr_2": "Apt 4B",
        "customer_addr_3": "Springfield",
        "customer_addr_4": "IL, 62701",
        "cust_phone": "555-1234",
        "cust_fax": "555-5678",
        "due_date": "2024-06-30",
        "doc_number": "INV-2024-0001",
        "items": [
            {"item_name": "Widget A", "price": 1000, "quantity": 2},
            {"item_name": "Widget B", "price": 1500, "quantity": 3},
            {"item_name": "Service Fee", "price": 500, "quantity": 1},
        ],
        "diskon": 200,  # discount amount
    }

    orderanku_data = {
        "orderanku_id": 1,
        "receipent_name": "Rudi Syahrudin Aulia Muhammad Rocky Gerung Super",
        "receipent_telp": "0815912034",
        "receipent_addr": "Jl. Babakan Madang No. 8 Sirkuit Sentul Bogor No 10",
        "sender_name": "Herculex Indonesia Aulia Muhammad Rocky Gerung Super",
        "sender_telp": "0000100002000030000400005000060000700",
        "total_amount": 2525000,
        "bank_name": "BCA",
        # "order_detail": "Kemeja polos warna merah 1 Celana Chino Warna Coklat 1",
        "order_detail": "000001~!~000~!~002~!~0000~!~03~!~000~!~004~!~000005~!~000006~!~000007~!~000008~!~000009~!~0",
        "paid_flag": False,
        "orderanku_id": "073-00068330",
        "invoice_date": "2023-01-25 11:20:00",
    }

    # generate_orderanku(orderanku_data)

    print(process_invoice_item_rows(orderanku_data))

    # print(split_string("Kemeja polos warna merah 1 Celana Chino Warna Coklat 1", 20))
