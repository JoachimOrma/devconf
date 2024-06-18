from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField


class DpForm(FlaskForm):
    dp = FileField("Upload Dp", validators=[FileRequired(), FileAllowed(['jpg', 'png', "Invalid file format"])])
    submit = SubmitField("Upload")
