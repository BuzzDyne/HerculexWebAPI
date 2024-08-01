from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

doc_type_mapping = {"Q": "QUO", "I": "INV"}
CAP_IMAGE_PATH = "res/CapTTD.webp"
NORMAL_FONT = "MyPoppin"
BOLD_FONT = "MyPoppin-Bold"
ITALIC_FONT = "MyPoppin-Italic"

# NORMAL_FONT = "Helvetica"
# BOLD_FONT = "Helvetica-Bold"
# ITALIC_FONT = "Helvetica-Oblique"


def generate_pdf(invoice_data):
    pdfmetrics.registerFont(TTFont("MyPoppin", "res/fonts/Poppins-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("MyPoppin-Bold", "res/fonts/Poppins-SemiBold.ttf"))
    pdfmetrics.registerFont(TTFont("MyPoppin-Italic", "res/fonts/Poppins-Italic.ttf"))

    table_header = ["Keterangan", "Harga(Rp)", "Qty", "Jml(Rp)"]
    col_widths = [350, 70, 30, 75]
    row_height = 20
    x, y = 42, 600

    # Generate PDF using ReportLab
    pdf_buffer = BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=A4)

    # Add Background Image
    background_image_path = (
        "res/PageTemplate_QUO.jpg"
        if invoice_data["doc_type"] == "Q"
        else "res/PageTemplate_INV.jpg"
    )

    img = ImageReader(background_image_path)
    p.drawImage(img, 0, 0, width=A4[0], height=A4[1], preserveAspectRatio=True)

    # Populate Header
    p.setFont(NORMAL_FONT, 10)
    p.setFillColorRGB(0.20784313725490197, 0.1843137254901961, 0.21176470588235294)
    p.drawString(363, 721, invoice_data["customer_name"])
    # p.drawString(295, 709.5, f"Alamat")
    p.drawString(363, 709.5, invoice_data["customer_addr_1"])
    p.drawString(363, 698, invoice_data["customer_addr_2"])
    p.drawString(363, 686.5, invoice_data["customer_addr_3"])
    p.drawString(363, 675, invoice_data["customer_addr_4"])
    p.drawString(363, 663.5, invoice_data["cust_phone"])
    p.drawString(363, 652, invoice_data["cust_fax"])

    # p.drawString(42, 653.75, f"Jatuh Tempo:")
    p.drawString(110, 653.75, invoice_data["due_date"])

    p.setFont(ITALIC_FONT, 12)
    # p.drawString(40, 705.5, f"No.")
    doc_number = invoice_data["doc_number"]
    p.drawString(
        62,
        705.5,
        doc_number,
    )
    p.setTitle(doc_number)
    # Customer Information
    p.setFont(NORMAL_FONT, 12)

    # Table Header
    for i, header in enumerate(table_header):
        p.setFont(BOLD_FONT, 12)
        p.drawString(x + sum(col_widths[:i]), y, header)

    # Table Data
    subtotal = 0
    p.setFont(NORMAL_FONT, 11)
    for item in invoice_data["items"]:
        y -= row_height
        item_total = item["price"] * item["quantity"]

        p.line(36, y + row_height - 5, A4[0] - 36, y + row_height - 5)

        p.drawString(x, y, capitalize_words(item["item_name"]))
        p.drawString(x + col_widths[0], y, format_number_with_commas(item["price"]))
        p.drawString(x + col_widths[0] + col_widths[1], y, str(item["quantity"]))
        p.drawString(
            x + col_widths[0] + col_widths[1] + col_widths[2],
            y,
            format_number_with_commas(item_total),
        )
        subtotal += item_total

    p.line(36, y - 5, A4[0] - 36, y - 5)

    # Subtable Data
    subtable_base_x = x + col_widths[0]
    subtable_line_x1 = subtable_base_x - 10
    # Subtotal
    p.drawString(subtable_base_x, y - row_height, f"Subtotal")
    p.drawString(
        x + col_widths[0] + col_widths[1] + col_widths[2],
        y - row_height,
        f"{format_number_with_commas(subtotal)}",
    )
    p.line(
        subtable_line_x1,
        y - row_height - 5,
        A4[0] - 36,
        y - row_height - 5,
    )
    # Diskon
    p.drawString(subtable_base_x, y - (row_height * 2), f"Diskon")
    p.drawString(
        x + col_widths[0] + col_widths[1] + col_widths[2],
        y - (row_height * 2),
        f"{format_number_with_commas(invoice_data['diskon'])}",
    )
    p.line(
        subtable_line_x1,
        y - (row_height * 2) - 5,
        A4[0] - 36,
        y - (row_height * 2) - 5,
    )
    # Total
    grand_total = subtotal - invoice_data["diskon"]
    p.setFont(BOLD_FONT, 12)
    # p.drawString(subtable_base_x, y - (row_height * 3), f"Total")
    # p.drawString(
    #     x + col_widths[0] + col_widths[1] + col_widths[2],
    #     y - (row_height * 3),
    #     f"{format_number_with_commas(grand_total)}",
    # )
    # p.line(
    #     subtable_line_x1,
    #     y - (row_height * 3) - 5,
    #     A4[0] - 36,
    #     y - (row_height * 3) - 5,
    # )
    # DownPayment
    p.setFont(NORMAL_FONT, 12)
    p.drawString(subtable_base_x, y - (row_height * 3), f"DP")
    p.drawString(
        x + col_widths[0] + col_widths[1] + col_widths[2],
        y - (row_height * 3),
        f"{format_number_with_commas(invoice_data['down_payment'])}",
    )
    p.line(
        subtable_line_x1,
        y - (row_height * 3) - 5,
        A4[0] - 36,
        y - (row_height * 3) - 5,
    )
    # Sisa
    grand_sisa = grand_total - invoice_data["down_payment"]
    p.setFont(BOLD_FONT, 12)
    p.drawString(subtable_base_x, y - (row_height * 4), f"Pelunasan")
    p.drawString(
        x + col_widths[0] + col_widths[1] + col_widths[2],
        y - (row_height * 4),
        f"{format_number_with_commas(grand_sisa)}",
    )
    p.line(
        subtable_line_x1,
        y - (row_height * 4) - 5,
        A4[0] - 36,
        y - (row_height * 4) - 5,
    )

    # Terbilang
    terbilang_y = y - (row_height * 5)
    row_height = 15
    p.drawString(x, terbilang_y, f"Terbilang")
    p.setFont(NORMAL_FONT, 12)
    list_of_terbilang = convert_to_terbilang(grand_sisa)

    for item in list_of_terbilang:
        terbilang_y -= row_height
        p.drawString(x, terbilang_y, f"{item}")

    # TTD
    p.setFont(BOLD_FONT, 12)
    ttd_base_x = x + col_widths[0] - 10
    ttd_base_y = terbilang_y - (row_height * 1) - 5
    p.drawString(
        ttd_base_x + 27,
        ttd_base_y - (row_height * 4.6),
        f"HERCULEX INDONESIA",
    )

    p.drawImage(
        CAP_IMAGE_PATH,
        ttd_base_x + 30,
        ttd_base_y - (row_height * 4),
        120,
        90,
        mask="auto",
    )

    p.setFont(NORMAL_FONT, 12)
    p.drawString(
        ttd_base_x,
        ttd_base_y - (row_height * 5),
        f"(.................................................................)",
    )

    # Pembayaran
    byr_base_x = x
    byr_base_y = ttd_base_y - (row_height * 4)

    p.setFont(BOLD_FONT, 12)
    p.drawString(byr_base_x, byr_base_y, "Informasi Pembayaran")
    p.setFont(NORMAL_FONT, 12)
    p.drawString(
        byr_base_x, byr_base_y - row_height, "BCA a.n. Ivan Leonardo - 0845248007"
    )

    p.save()

    # Move the buffer position to the beginning
    pdf_buffer.seek(0)
    return pdf_buffer, doc_number


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


def split_string(input_string, max_length=70):
    words = input_string.split()
    result_list = []
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
