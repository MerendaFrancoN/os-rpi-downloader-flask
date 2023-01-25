from flask import render_template_string


def index():
    return render_template_string('''\
<a href="{{ url_for('.enqueue') }}">launch job</a>
''')





