from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mock Page</title>
            <style>
                #element-to-snapshot {
                    width: 200px;
                    height: 100px;
                    background-color: lightblue;
                    border: 1px solid blue;
                }
            </style>
        </head>
        <body>
            <h1 id="header">Welcome to Mock Page</h1>
            <button id="click-me" onclick="document.getElementById('header').innerText = 'Button Clicked'">Click Me</button>
            <input type="text" id="input-field" placeholder="Type here">
            <div id="element-to-snapshot">Target Element</div>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(port=5000)
