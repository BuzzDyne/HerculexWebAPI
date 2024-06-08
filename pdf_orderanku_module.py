import time
import random
import string
import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pdf417 import encode, render_image

doc_type_mapping = {"Q": "QUO", "I": "INV"}
CAP_IMAGE_PATH = "res/CapTTD.png"
NORMAL_FONT = "Reddit-Medium"
BOLD_FONT = "Reddit-Black"
ITALIC_FONT = "MyPoppin-Italic"


def format_number_with_commas(number):
    """
    Format a number with commas as thousands separators.

    Parameters
    ----------
    number : int or float
        The number to be formatted.

    Returns
    -------
    str
        A string representing the formatted number with commas as thousands separators.

    Examples
    --------
    >>> format_number_with_commas(1000)
    '1,000'
    >>> format_number_with_commas(1000000)
    '1,000,000'
    >>> format_number_with_commas(1234567890)
    '1,234,567,890'
    """
    formatted_number = "{:,}".format(number)
    return formatted_number


def split_string(input_string, max_length=70, br_token="~!~"):
    """
    Split the input string into lines based on the maximum length.

    Parameters
    ----------
    input_string : str
        The input string to be split into lines.
    max_length : int, optional
        The maximum length of each line (default is 70).
    br_token : str, optional
        The token used to indicate line breaks within the input string (default is "~!~").

    Returns
    -------
    list of str
        A list of strings representing the lines after splitting the input string.

    Notes
    -----
    This function splits the input string into lines based on the maximum length specified.
    The input string may contain line breaks indicated by the br_token.
    Each segment separated by the br_token is split into words, and then concatenated into lines.
    If a word exceeds the maximum length, it is split into multiple lines.

    Examples
    --------
    >>> split_string("This is a long string that needs to be split into multiple lines.", max_length=20)
    ['This is a long string', 'that needs to be split', 'into multiple lines.']
    >>> split_string("Line 1~!~Line 2~!~Line 3", br_token="~!~")
    ['Line 1', 'Line 2', 'Line 3']
    """
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


def process_invoice_item_rows(inv_data):
    """
    Process invoice item rows based on the provided invoice data.

    Parameters
    ----------
    inv_data : dict
        A dictionary containing invoice data with the following keys:
        - 'receipent_name': str, the recipient's name.
        - 'receipent_telp': str, the recipient's telephone number.
        - 'receipent_addr': str, the recipient's address.
        - 'sender_name': str, the sender's name.
        - 'sender_telp': str, the sender's telephone number.
        - 'total_amount': float, the total amount of the invoice.
        - 'bank_name': str, the name of the bank (optional).
        - 'order_detail': str, details of the order.

    Returns
    -------
    tuple
        A tuple containing:
        - A dictionary mapping item keys to their respective rows and lines.
        - The maximum number of rows required for the invoice.

    Notes
    -----
    This function processes the invoice item rows by splitting the provided data into left and right columns
    and determining the number of rows required based on the content.

    The left column contains recipient information (name, telephone, address) and sender information (name, telephone).
    The right column contains the total amount, bank name (if available), and order details.

    The minimum number of rows required is determined by the MIN_ROWS constant.
    The maximum length of lines in the left column is determined by L_MAX_LENGTH constant.
    The maximum length of lines in the right column is determined by R_MAX_LENGTH constant.

    """
    MIN_ROWS = 13
    L_MAX_LENGTH = 37
    R_MAX_LENGTH = 46

    item_mapping = {}

    # region Left Col
    curr_row = 1

    data_rows = split_string(inv_data["receipent_name"], L_MAX_LENGTH)
    item_mapping["r_name"] = {
        "iRow": curr_row,
        "lines": data_rows,
    }

    curr_row += max(len(data_rows), 1)
    item_mapping["r_telp"] = {
        "iRow": curr_row,
        "lines": [inv_data["receipent_telp"]],
    }

    curr_row += 1
    data_rows = split_string(inv_data["receipent_addr"], L_MAX_LENGTH)
    item_mapping["r_addr"] = {
        "iRow": curr_row,
        "lines": data_rows,
    }

    curr_row += max(len(data_rows), 1)
    data_rows = split_string(inv_data["sender_name"], L_MAX_LENGTH)
    item_mapping["s_name"] = {
        "iRow": curr_row,
        "lines": data_rows,
    }

    curr_row += max(len(data_rows), 1)
    item_mapping["s_telp"] = {
        "iRow": curr_row,
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
        "iRow": curr_row,
        "lines": [totalText],
    }

    curr_row += 2
    data_rows = split_string(inv_data["order_detail"], R_MAX_LENGTH)
    item_mapping["d_detail"] = {
        "iRow": curr_row,
        "lines": data_rows,
    }

    r_row_count = curr_row + len(data_rows) - 1
    # endregion

    l_row_count = l_row_count + 1 if l_row_count >= MIN_ROWS else l_row_count
    r_row_count = r_row_count + 1 if r_row_count >= MIN_ROWS else r_row_count

    return item_mapping, max(MIN_ROWS, l_row_count, r_row_count)


def generate_id_header(order_id=5001):
    """
    Generate a formatted order ID header.

    Parameters
    ----------
    order_id : int, optional
        The order ID integer part (default is 5001).

    Returns
    -------
    str
        A string representing the formatted order ID header, which consists of:
        - Three random uppercase letters.
        - A hyphen.
        - The integer part of the order ID, with leading zeros to ensure it is at least 4 characters long.

    Examples
    --------
    >>> generate_id_header(123)
    'XX-0123'
    >>> generate_id_header()
    'XX-5001'
    """
    # Generate three random uppercase letters
    random_letters = "".join(random.choices(string.ascii_uppercase, k=2))

    # Ensure the integer part is at least 4 characters long with leading zeros
    formatted_order_id = f"{order_id:04d}"

    # Combine the parts with a hyphen
    oid_str = f"{random_letters}-{formatted_order_id}"

    return oid_str


def generate_orderanku(data_arr):
    """
    Generate a PDF document with order details and barcodes for a list of orders.

    Parameters:
    -----------
    data_arr : list of dict
        A list of dictionaries, where each dictionary contains order details.
        Each dictionary should have the following keys:
        - orderanku_id: str
            Unique identifier for the order.
        - receipent_name: str
            Name of the recipient.
        - receipent_telp: str
            Telephone number of the recipient.
        - receipent_addr: str
            Address of the recipient.
        - sender_name: str
            Name of the sender.
        - sender_telp: str
            Telephone number of the sender.
        - paid_flag: bool
            Flag indicating if the order is paid.
        - invoice_date: str
            Invoice date in the format "yyyy-mm-dd HH:MM:SS".
        - total_amount: int
            Total amount of the order.
        - order_detail: str
            Order details in a specific format.

    Returns:
    --------
    pdf_buffer (BytesIO): A buffer containing the PDF data.
    """
    UNIT = 12
    A4_width, A4_height = A4
    MID_X = A4_width / 2
    BARCODE_W = 100 / 2
    BARCODE_H = 350 / 2
    TEXT_LEV = 3.3

    pdfmetrics.registerFont(TTFont("Reddit-Black", "res/fonts/RedditMono-Black.ttf"))
    pdfmetrics.registerFont(TTFont("Reddit-Medium", "res/fonts/RedditMono-Medium.ttf"))

    pdf_buffer = BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=A4)

    curr_caret_y = A4_height
    for data in data_arr:
        # region Definitions

        data_map, data_row_count = process_invoice_item_rows(data)
        area_rows = data_row_count + 3  # top-padding, header, spacing

        if curr_caret_y - (area_rows * UNIT) <= 0:
            p.showPage()
            curr_caret_y = A4_height

        table_top_y = curr_caret_y - UNIT
        table_bot_y = table_top_y - ((data_row_count + 2) * UNIT)

        left_top = (2 * UNIT, table_top_y)
        left_bot = (2 * UNIT, table_bot_y)
        right_top = (A4_width - 2 * UNIT, table_top_y)
        right_bot = (A4_width - 2 * UNIT, table_bot_y)
        mid_top = (MID_X, table_top_y)
        mid_bot = (MID_X, table_bot_y)

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
        sub_y = table_top_y - UNIT + TEXT_LEV

        lunas_str = "LUNAS" if data["paid_flag"] else "BELUM LUNAS"
        oid_str = generate_id_header(data["orderanku_id"])
        date_str = (
            data["invoice_date"][:10]
            if data["invoice_date"]
            else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        subheader_text = f"{lunas_str} (ORDER {oid_str}) {date_str}"

        p.drawRightString(sub_x1, sub_y, subheader_text)
        p.drawRightString(sub_x2, sub_y, subheader_text)
        # endregion

        # region Helper Line
        # for i in range(1, area_rows - 2):
        #     row_y = table_top_y - ((2 + i) * UNIT)
        #     p.line(left_top[0], row_y, right_top[0], row_y)
        #     p.drawString(MID_X - 10, row_y + TEXT_LEV, f"{i}")
        # endregion
        # region Barcodes
        # Generate the barcode image
        text_encode = f"{data['orderanku_id']}~^~{data['receipent_name']}~^~{data['receipent_telp']}~^~{data['receipent_addr']}~^~{data['sender_name']}~^~{data['sender_telp']}"
        barcode_image = create_pdf417_barcode(text_encode)

        # Draw the barcode (Left)
        barcode_x = left_top[0] + 2
        barcode_y = left_top[1] - BARCODE_H - 2 - (((data_row_count - 13) / 2) * UNIT)

        p.drawInlineImage(
            barcode_image, barcode_x, barcode_y, width=BARCODE_W, height=BARCODE_H
        )

        barcode_line_x_1 = barcode_x + BARCODE_W + 2
        p.line(barcode_line_x_1, left_bot[1], barcode_line_x_1, left_top[1])

        # Draw the barcode (Right)
        barcode_x = mid_top[0] + 2

        p.drawInlineImage(
            barcode_image, barcode_x, barcode_y, width=BARCODE_W, height=BARCODE_H
        )
        barcode_line_x_2 = barcode_x + BARCODE_W + 2
        p.line(barcode_line_x_2, table_bot_y, barcode_line_x_2, table_top_y)
        # endregion

        # region Data
        p.setFont(BOLD_FONT, 8)
        dh_x_l = barcode_line_x_1 + 5
        colon_x_l = dh_x_l + 37
        base_text_y = left_top[1] - (2 * UNIT) + TEXT_LEV

        p.drawString(
            dh_x_l, base_text_y - (data_map["r_name"]["iRow"] * UNIT), "Kepada"
        )
        p.drawString(dh_x_l, base_text_y - (data_map["r_telp"]["iRow"] * UNIT), "Telp")
        p.drawString(
            dh_x_l, base_text_y - (data_map["r_addr"]["iRow"] * UNIT), "Alamat"
        )
        p.drawString(
            dh_x_l, base_text_y - (data_map["s_name"]["iRow"] * UNIT), "Pengirim"
        )
        p.drawString(dh_x_l, base_text_y - (data_map["s_telp"]["iRow"] * UNIT), "Telp")

        p.drawString(colon_x_l, base_text_y - (data_map["r_name"]["iRow"] * UNIT), ":")
        p.drawString(colon_x_l, base_text_y - (data_map["r_telp"]["iRow"] * UNIT), ":")
        p.drawString(colon_x_l, base_text_y - (data_map["r_addr"]["iRow"] * UNIT), ":")
        p.drawString(colon_x_l, base_text_y - (data_map["s_name"]["iRow"] * UNIT), ":")
        p.drawString(colon_x_l, base_text_y - (data_map["s_telp"]["iRow"] * UNIT), ":")

        p.setFont(NORMAL_FONT, 8)  # Max Length for data 37 char

        left_row_data = ["r_name", "r_telp", "r_addr", "s_name", "s_telp"]

        data_x = colon_x_l + 5

        for key in left_row_data:
            start_row = data_map[key]["iRow"]
            for i, line in enumerate(data_map[key]["lines"]):
                row = start_row + i
                line = line if line else ""
                p.drawString(data_x, base_text_y - (row * UNIT), line)

        dh_x_2 = barcode_line_x_2 + 5
        colon_x_2 = dh_x_2 + 32

        p.setFont(BOLD_FONT, 8)
        p.drawString(dh_x_2, base_text_y - (1 * UNIT), "Total")
        p.drawString(dh_x_2, base_text_y - (2 * UNIT), "Pesanan")
        p.drawString(colon_x_2, base_text_y - (1 * UNIT), ":")
        p.drawString(colon_x_2, base_text_y - (2 * UNIT), ":")

        p.setFont(NORMAL_FONT, 8)
        data_x = colon_x_2 + 5
        p.drawString(data_x, base_text_y - (1 * UNIT), data_map["d_total"]["lines"][0])

        for i, line in enumerate(data_map["d_detail"]["lines"]):
            row = data_map["d_detail"]["iRow"] + i
            p.drawString(dh_x_2, base_text_y - (row * UNIT), line)

        # endregion
        curr_caret_y -= area_rows * UNIT  # Move the Caret

    p.save()
    pdf_buffer.seek(0)
    filename = f"{int(time.time())}.pdf"

    return pdf_buffer
    # with open(os.path.join(os.getcwd(), filename), "wb") as f:
    #     f.write(pdf_buffer.getbuffer())


def create_pdf417_barcode(data_str):
    """
    Create a PDF417 barcode image from the provided data string.

    Parameters
    ----------
    data_str : str
        The data string to be encoded in the barcode.

    Returns
    -------
    PIL.Image.Image
        A PIL Image object representing the generated PDF417 barcode.

    Notes
    -----
    This function generates a PDF417 barcode image from the provided data string.
    The barcode image is initially rendered with a scale of 10 and a ratio of 1.
    If the length of the data string exceeds 790 characters, it is truncated.
    If the length of the data string is less than 300 characters, it is padded with random alphabets
    followed by the "~EOF~" token to ensure a minimum length of 300 characters.
    The final barcode image is resized to fit the target dimensions of 350x100 pixels
    and rotated 90 degrees clockwise.

    """
    # Hardcoded dimensions for the output image
    target_width = 350
    target_height = 100
    MAX_LEN = 790
    MIN_LEN = 300

    # Truncate data_str to the first 790 characters if necessary
    if len(data_str) > MAX_LEN:
        data_str = data_str[:MAX_LEN]
    # Ensure data_str is at least 6 characters long
    if len(data_str) < MIN_LEN:
        remaining_length = MIN_LEN - len(data_str)
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


def generate_dummy_order():
    receipent_names = [
        "Johnathan Edward Michaelson",
        "Jane Samantha Elizabeth Smith",
        "Alice Johanna Catherine Johnson",
        "Robert Benjamin Oliver Brown",
        "Emily Alexandra Davis Parker",
    ]
    sender_names = [
        "MegaStore Inc.",
        "QuickShop",
        "Online Fashion",
        "Tech Supplies",
        "Book Haven",
    ]
    products = [
        "Long Sleeve Cotton Shirt with Striped Pattern",
        "Slim Fit Denim Jeans with Distressed Look",
        "High-Performance Gaming Laptop",
        "Bestselling Hardcover Novel",
        "Latest Model Smartphone with Advanced Features",
        "Noise-Cancelling Over-Ear Headphones",
    ]
    colors = ["red", "blue", "green", "black", "white", "yellow"]
    addresses = [
        "123 Maple Street, Springfield",
        "456 Oak Avenue, Metropolis",
        "789 Pine Road, Gotham",
        "101 Birch Boulevard, Star City",
        "202 Cedar Lane, Central City",
    ]
    phone_prefix = ["081", "082", "083", "084", "085"]

    receipent_name = (
        random.choice(receipent_names)
        + " "
        + " ".join(random.choices(receipent_names, k=3))
    )
    sender_name = (
        random.choice(sender_names) + " " + " ".join(random.choices(sender_names, k=3))
    )
    receipent_telp = random.choice(phone_prefix) + "".join(
        random.choices("0123456789", k=8)
    )
    sender_telp = "".join(random.choices("0123456789", k=35))
    receipent_addr = random.choice(addresses)
    total_amount = random.randint(100000, 5000000)
    bank_name = random.choice(["BCA", "Mandiri", "BNI", "BRI", "CIMB Niaga"])

    order_detail = "~!~".join(
        [
            f"{random.choice(products)} in {random.choice(colors)} color - Qty: {random.randint(1, 5)}"
            for _ in range(random.randint(1, 10))
        ]
    )

    invoice_date = datetime.datetime.now() - datetime.timedelta(
        days=random.randint(1, 365)
    )
    invoice_date = invoice_date.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "orderanku_id": "".join(random.choices("0123456789", k=8)),
        "receipent_name": receipent_name,
        "receipent_telp": receipent_telp,
        "receipent_addr": receipent_addr,
        "sender_name": sender_name,
        "sender_telp": sender_telp,
        "total_amount": total_amount,
        "bank_name": bank_name,
        "order_detail": order_detail,
        "paid_flag": random.choice([True, False]),
        "invoice_date": invoice_date,
    }


# if __name__ == "__main__":
#     generate_orderanku([generate_dummy_order() for i in range(1000)])
# o = {
#     "orderanku_id": 1,
#     "receipent_name": "Rudi Syahrudin Aulia Muhammad Rocky Gerung Super",
#     "receipent_telp": "0815912034",
#     "receipent_addr": "Jl. Babakan Madang No. 8 Sirkuit Sentul Bogor No 10",
#     "sender_name": "Herculex Indonesia Aulia Muhammad Rocky Gerung Super",
#     "sender_telp": "0000100002000030000400005000060000700",
#     "total_amount": 2525000,
#     "bank_name": "BCA",
#     "order_detail": "Kemeja polos warna merah 1~!~Celana Chino Warna Coklat 1",
#     # "order_detail": "Kemeja polos warna merah 1~!~elana Chino Warna Coklat 1~!~000003~!~000004~!~000005~!~000006~!~000007saya sudah~!~pernah bilang erbkali berkali kalau kamu janga begitu~!~000008~!~000009~!~0",
#     "paid_flag": True,
#     "orderanku_id": "073",
#     "invoice_date": "2023-01-25 11:20:00",
# }
