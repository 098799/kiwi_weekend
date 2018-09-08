import logging

from flask import Flask, render_template, request

import wtforms

from . import main as main_bot


app = Flask(__name__, template_folder='template')
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'super_fucking_secret_key'


@app.route('/search', methods=['GET'])
def list_all():
    src = request.args.get('src')
    dst = request.args.get('dst')
    date = request.args.get('date')

    bot = main_bot.Bot()
    json_ = bot.scrape(src, dst, date)
    return render_template('layout.html', search_for=[src, dst, date], json_=json_)


class RequestForm(wtforms.Form):
    cities = ["Alicante", "Castelldefels", "Barcelona", "Madrid", "Valencia"]
    city_choices = [(city, city) for city in cities]

    source = wtforms.SelectField('Source', choices=city_choices)
    destination = wtforms.SelectField('Destination', choices=city_choices)

    date = wtforms.SelectField('Date', choices=[
        ("2018-10-{}".format(str(i).zfill(2)), "2018-10-{}".format(str(i).zfill(2)))
        for i in range(1, 30)
    ])


@app.route('/input_form', methods=['GET', 'POST'])
def input_form():
    form = RequestForm(request.form)

    logging.debug("Form errors for now: %s", form.errors)

    if request.method == "POST":

        if form.validate():
            src = form.source.data
            dst = form.destination.data
            date = form.date.data

            bot = main_bot.Bot()
            json_ = bot.scrape(src, dst, date)

            if not json_:
                return "Ooops, no connections"

            return render_template('layout.html', search_for=[src, dst, date], json_=json_)

        else:
            return "Wrong input"

    return render_template("index.html", form=form)
