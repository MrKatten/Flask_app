from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, FileField, IntegerField
from wtforms import SubmitField
from wtforms.validators import DataRequired


class ProductsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    price = IntegerField("Цена", validators=[DataRequired()])
    file = FileField('File', validators=[FileRequired(), FileAllowed(["png", "jpg", "bmp"])])
    submit = SubmitField('Применить')