import os
from flask import Flask, request, jsonify, send_from_directory, session, render_template
import pandas as pd
from rpy2 import robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
PLOT_FOLDER = 'plots'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PLOT_FOLDER'] = PLOT_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(PLOT_FOLDER):
    os.makedirs(PLOT_FOLDER)

@app.route('/')
def index():
    result = session.get('result')
    recommendations = session.get('recommendations')
    plot_url = session.get('plot_url')
    return render_template('index.html', result=result, recommendations=recommendations, plot_url=plot_url)

@app.route('/upload', methods=['POST'])
def upload():
    if 'log-file' not in request.files:
        return jsonify(success=False, error="No file part")

    log_file = request.files['log-file']

    if log_file.filename == '':
        return jsonify(success=False, error="No selected file")

    if log_file and allowed_file(log_file.filename):
        log_file_path = os.path.join(app.config['UPLOAD_FOLDER'], log_file.filename)
        log_file.save(log_file_path)
        session['log_file_path'] = log_file_path
        return jsonify(success=True)
    else:
        return jsonify(success=False, error="Invalid file type")

@app.route('/analyze', methods=['POST'])
def analyze():
    log_file_path = session.get('log_file_path')
    if not log_file_path:
        return jsonify(success=False)
    
    log_type = request.form['log-type']
    
    result, recommendations, plot_filename = analyze_log(log_file_path, log_type)
    
    if result and recommendations and plot_filename:
        plot_url = f'/plots/{plot_filename}'
        session['result'] = result
        session['recommendations'] = recommendations
        session['plot_url'] = plot_url
        return jsonify(success=True)
    else:
        return jsonify(success=False)

@app.route('/get_results', methods=['GET'])
def get_results():
    result = session.get('result')
    recommendations = session.get('recommendations')
    plot_url = session.get('plot_url')
    
    if result and recommendations and plot_url:
        return jsonify(success=True, result=result, recommendations=recommendations, plot_url=plot_url)
    else:
        return jsonify(success=False)

@app.route('/plots/<filename>')
def get_plot(filename):
    return send_from_directory(app.config['PLOT_FOLDER'], filename)

@app.route('/css/<path:filename>')
def send_css(filename):
    return send_from_directory('css', filename)

@app.route('/scripts/<path:filename>')
def send_scripts(filename):
    return send_from_directory('scripts', filename)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv'}

def analyze_log(file_path, log_type):
    pandas2ri.activate()
    
    # R 라이브러리 및 함수 임포트
    ggplot2 = importr('ggplot2')
    
    # CSV 파일을 Pandas DataFrame으로 읽기
    df = pd.read_csv(file_path)
    
    # Pandas DataFrame을 R DataFrame으로 변환
    r_df = pandas2ri.py2rpy(df)
    
    # 예제 데이터 프레임
    robjects.globalenv['df'] = r_df
    
    # R 코드로 ggplot2 그래프 생성
    r_plot_code = """
    library(ggplot2)
    plot <- ggplot(df, aes(x = Sepal.Length, y = Sepal.Width)) + geom_point()
    plot_file <- tempfile(fileext = '.png')
    ggsave(plot_file, plot)
    plot_file
    """
    
    # R 코드 실행
    plot_file = robjects.r(r_plot_code)[0]

    # 플롯 파일명을 얻기 위한 처리
    plot_filename = os.path.basename(plot_file)
    plot_target_path = os.path.join(app.config['PLOT_FOLDER'], plot_filename)
    os.rename(plot_file, plot_target_path)
    
    # 가상의 분석 결과 및 추천사항 생성
    result = "Analysis result based on log type: " + log_type
    recommendations = "Recommendations based on analysis of log type: " + log_type
    
    return result, recommendations, plot_filename

if __name__ == '__main__':
    app.run()