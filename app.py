from flask import Flask, render_template, redirect, url_for, request, session
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired, FileSize
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired, ValidationError
from speech_utils import vid_summarizer
import shutil


app = Flask(__name__)
app.secret_key="123"

app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/files'
summary=''
file_uploaded=False

vs = vid_summarizer()


class UploadFileForm(FlaskForm):
    file = FileField("File", 
    validators=[FileRequired(),
     FileAllowed(upload_set=['mp4','mov', 'wmv'],message="Note: Video Only!"),
      FileSize(max_size=5*10**8,message="File Size Seems to be above 500MB")])

    submit = SubmitField("Upload File")



@app.route('/', methods=['GET',"POST"])
@app.route('/home', methods=['GET',"POST"])
def home():
    form = UploadFileForm()
    folder = 'static/files'   
    for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
            try:
                os.mkdir('static/files/a_chunks')
            except:
                print('"a_chunks" already exsists!') 

    
    if form.validate_on_submit():             
        
        file = form.file.data # First grab the file
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) # Then save the file
        # print(str('static/files/'+str(file.filename)))
        old_name =  r'static\files\{}'.format(file.filename).replace(' ','_')
        new_name = r'static\files\video.mp4'
        os.rename(old_name, new_name)
        session["file_dir"] = new_name
        file_uploaded = True

        return redirect(url_for("process"))
    # print([file_dir,file_uploaded])
    else:
        return render_template('index.html', form=form)

@app.route('/process', methods=['GET','POST' ])
def process():
    msg="Please wait converted your video to audio..."
    img_src="https://cloudinary.com/blog/wp-content/uploads/sites/12/2022/02/Mario_1.gif"
    if request.method=='GET':
        return render_template('loading.html',session=session,msg=msg, img_src=img_src, redirect_to='/transcripting',current_page='/process')
    elif request.method=='POST':
        vs.vid2aud(session.pop("file_dir"))
        return 'done'

@app.route('/transcripting', methods=['GET','POST' ])
def transcripting():
    msg="Please wait Transcripting...\nThis might take a long time please wait"
    img_src='https://i0.wp.com/www.printmag.com/wp-content/uploads/2021/02/4cbe8d_f1ed2800a49649848102c68fc5a66e53mv2.gif?fit=476%2C280&ssl=1'
    if request.method=='GET':
        return render_template('loading.html',session=session,msg=msg,img_src=img_src,redirect_to='/summarizing',current_page='/transcripting')
    elif request.method=='POST':
        session['text'] = vs.ibm_stt()
        return 'done'

@app.route('/summarizing', methods=['GET','POST' ])
def summarizing():
    global summary
    msg="Almost done!\nSummarizing your content..."
    img_src='https://onlinegiftools.com/images/examples-onlinegiftools/hadouken.gif'
    if request.method=='GET':
        return render_template('loading.html',session=session,msg=msg,img_src=img_src,redirect_to='/summary',current_page='/summarizing')
    elif request.method=='POST' and 'text' in session:
        session['summary'] = vs.hft_summarizer(session.pop('text'))
        return 'done'

@app.route('/summary', methods=['GET','POST' ])
def success():
    return render_template('result.html',summary=session.pop('summary'))

if __name__ == '__main__':
    app.run(debug=True)