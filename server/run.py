# --- Declare imports ---
import os
import subprocess
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv


# --- Own ---
import paths as _path
import utils as _util


# --- Declare constants ---
ALLOWED_EXTENSIONS = {'hs'}
CREATE_TESTBENCH_SCRIPT = 'create_testbench.py'
EXECUTE_TESTBENCH_SCRIPT = 'runhaskell'


# --- File prefix ---
PREF_TEST = 'test_'
PREF_RESULTS = 'result_'



# --- Set app configurations ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = _path.UPLOAD_FOLDER
app.config['TESTS_FOLDER'] = _path.TEST_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # Max file size allowed = 50 Mb
app.secret_key = os.urandom(24)


# --- Load enviroment vars ---
load_dotenv()
SERVER_PORT = os.getenv('SERVER_PORT')
SERVER_HOST = os.getenv('SERVER_HOST')


# --- Main method ---
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Method to manager and driving the index page render.
    """

    if not request.method == 'POST':
        return renderIndex()

    else:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return renderIndex("No file part")

        file = request.files['file']

        # Check if the filename is empty
        if not file.filename:
            return renderIndex("No se ha seleccionado ningun archivo")

        # Che if the selected file is allowed
        if not allowedFile(file.filename):
            return renderIndex("Archivo no permitido. Solo extensiones '.hs'")

        # Secure name verification
        filename = secure_filename(file.filename)

        # Rename to have a unique and unmistakable filename
        date = (datetime.now()).strftime("%H:%M:%S")
        filename = request.remote_addr+"_"+date+"_proy.hs"

        # Upload file
        uploadFile(file, filename)

        # check if compile ToDo

        # Run test and output results
        test_outputs, test_avg = runTest(filename)

        # Delete file upload, test and results
        cleanAll(filename)

        return renderIndex( "Archivo cargado y corregido exitosamente",
                            test_outputs,
                            test_avg)



# --- Auxiliar methods ---
def renderIndex(messages="", test_outputs=[], test_avg=""):
    data = {'messages':messages,'test_results':(test_outputs, test_avg)}
    return render_template('index.html', data=data)


def allowedFile(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def uploadFile(file_descriptor, filename):
    path_name = os.path.join(_path.UPLOAD_FOLDER, filename)
    file_descriptor.save(path_name)


def runTest(filename):
    # Use os.path.relpath to hidden abspath in case of Exceptions in testing outputs
    proy_name_file = os.path.relpath(os.path.join(_path.UPLOAD_FOLDER, filename))
    testbench_name_file = os.path.relpath(os.path.join(_path.TEST_FOLDER, PREF_TEST+filename))
    result_name_file = os.path.relpath(os.path.join(_path.TEST_FOLDER, PREF_RESULTS+filename))

    # Create an new testbench_name_file with incluided functions of proy file
    _util.createNewTestbench(proy_name_file, testbench_name_file)

    # Execute new_test, and save results in result_name_file
    os.system("{} {} -> {} ".format(EXECUTE_TESTBENCH_SCRIPT,testbench_name_file,result_name_file))

    return getTestResults(result_name_file)

def getTestResults(result_name_file):
    # Read result_name_file with obteined tests results
    results_file = open(result_name_file,'r')
    output_results = []
    props_count = 0
    ok_cout = 0

    for line in results_file:
        if line.find("prop_") != (-1):
            props_count += 1

        if line.find("+++ OK") != (-1):
            ok_cout += 1

        line = line.rstrip().split("from")[0]
        output_results.append(line)

    results_file.close()

    average = "0" if props_count == 0 else round(ok_cout / props_count * 100.0, 1)
    return output_results, str(average)+'%'

def cleanAll(filename):
    # Remove proy file upload
    path = os.path.join(_path.UPLOAD_FOLDER, filename)
    os.system("rm {}".format(path))

    # Remove testbech file generated
    path = os.path.join(_path.TEST_FOLDER, PREF_TEST+filename)
    os.system("rm {}".format(path))

    # Remove result file tested
    path = os.path.join(_path.TEST_FOLDER, PREF_RESULTS+filename)
    os.system("rm {}".format(path))


if __name__ == '__main__':
    app.run(port=SERVER_PORT, host=SERVER_HOST, debug=True, threaded=True)
