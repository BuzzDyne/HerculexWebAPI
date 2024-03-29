SHOPEE_SUCCESS_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css?family=Nunito+Sans:400,400i,700,900&display=swap" rel="stylesheet">
    </head>
    <style>
    body {
        text-align: center;
        padding: 40px 0;
        background: #EBF0F5;
    }
    h1 {
        color: #88B04B;
        font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
        font-weight: 900;
        font-size: 40px;
        margin-bottom: 10px;
    }
    p {
        color: #404F5E;
        font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
        font-size: 20px;
        margin: 0;
    }
    i {
        color: #9ABC66;
        font-size: 100px;
        line-height: 200px;
        margin-left: -15px;
        font-weight: bold; /* Make the checkmark bolder */
    }
    .card {
        background: white;
        padding: 60px;
        border-radius: 4px;
        box-shadow: 0 2px 3px #C8D0D8;
        display: inline-block;
        margin: 0 auto;
    }
    </style>
    <body>
    <div class="card">
        <div style="border-radius: 200px; height: 200px; width: 200px; background: #F8FAF5; margin: 0 auto;">
        <i class="checkmark">✓</i>
        </div>
        <h1>Shopee Token Refresh Success</h1>
        <p>You can now safely close this page</p>
    </div>
    </body>
    </html>
"""

SHOPEE_FAILED_SHOPID_WRONG_HTML = """
    <!DOCTYPE html>
    <html>

    <head>
        <link href="https://fonts.googleapis.com/css?family=Nunito+Sans:400,400i,700,900&display=swap" rel="stylesheet">
    </head>

    <style>
        body {
            text-align: center;
            padding: 40px 0;
            background: #EBF0F5;
        }

        h1 {
            color: #E74C3C;
            font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
            font-weight: 900;
            font-size: 40px;
            margin-bottom: 10px;
        }

        p {
            color: #404F5E;
            font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
            font-size: 20px;
            margin: 0;
        }

        i {
            color: #E74C3C;
            font-size: 100px;
            line-height: 200px;
            margin-left: -15px;
            font-weight: bold; /* Make the exclamation mark bolder */
        }

        .card {
            background: white;
            padding: 60px;
            border-radius: 4px;
            box-shadow: 0 2px 3px #C8D0D8;
            display: inline-block;
            margin: 0 auto;
        }
    </style>

    <body>
        <div class="card">
            <div style="border-radius: 200px; height: 200px; width: 200px; background: #F8FAF5; margin: 0 auto;">
                <i class="exclamation">!</i>
            </div>
            <h1>Shopee Token Refresh Failed</h1>
            <p>Wrong Shopee Account was used!</p>
        </div>
    </body>

    </html>
"""

SHOPEE_FAILED_GENERAL_ERROR_HTML = """
    <!DOCTYPE html>
    <html>

    <head>
        <link href="https://fonts.googleapis.com/css?family=Nunito+Sans:400,400i,700,900&display=swap" rel="stylesheet">
    </head>

    <style>
        body {
            text-align: center;
            padding: 40px 0;
            background: #EBF0F5;
        }

        h1 {
            color: #E74C3C;
            font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
            font-weight: 900;
            font-size: 40px;
            margin-bottom: 10px;
        }

        p {
            color: #404F5E;
            font-family: "Nunito Sans", "Helvetica Neue", sans-serif;
            font-size: 20px;
            margin: 0;
        }

        i {
            color: #E74C3C;
            font-size: 100px;
            line-height: 200px;
            margin-left: -15px;
            font-weight: bold; /* Make the exclamation mark bolder */
        }

        .card {
            background: white;
            padding: 60px;
            border-radius: 4px;
            box-shadow: 0 2px 3px #C8D0D8;
            display: inline-block;
            margin: 0 auto;
        }
    </style>

    <body>
        <div class="card">
            <div style="border-radius: 200px; height: 200px; width: 200px; background: #F8FAF5; margin: 0 auto;">
                <i class="exclamation">!</i>
            </div>
            <h1>Shopee Token Refresh Failed</h1>
            <p>Something went wrong. Please try again later.</p>
        </div>
    </body>

    </html>
"""