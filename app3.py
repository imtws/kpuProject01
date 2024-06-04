import os
from flask import Flask, request, jsonify, send_from_directory, session, make_response, render_template
import pandas as pd
from rpy2 import robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# 업로드 및 플롯 저장 디렉토리 설정
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
PLOT_FOLDER = os.path.join(app.root_path, 'plots')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PLOT_FOLDER'] = PLOT_FOLDER

# 만약 디렉토리가 없으면 생성
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(PLOT_FOLDER):
    os.makedirs(PLOT_FOLDER)

# HTML 랜더링 영역

# 메인 페이지
@app.route('/')
def index():
    result = session.get('result')
    recommendations = session.get('recommendations')
    plot_url = session.get('plot_url')
    return render_template('index.html', result=result, recommendations=recommendations, plot_url=plot_url)

# 로그 타입 선택 페이지
@app.route('/log_type_selection')
def log_type_selection():
    result = session.get('result')
    recommendations = session.get('recommendations')
    plot_url = session.get('plot_url')
    return render_template('log_type_selection.html', result=result, recommendations=recommendations, plot_url=plot_url)

# 결과 페이지
@app.route('/result')
def show_result():
    result = session.get('result')
    recommendations = session.get('recommendations')
    plot_url = session.get('plot_url')
    return render_template('result.html', result=result, recommendations=recommendations, plot_url=plot_url)


## API 영역

# 업로드 API
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

# 분석 API
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

# 로그 분석 결과 조회 API
@app.route('/get_results', methods=['GET'])
def get_results():
    result = session.get('result')
    recommendations = session.get('recommendations')
    plot_url = session.get('plot_url')
    
    if result and recommendations and plot_url:
        return jsonify(success=True, result=result, recommendations=recommendations, plot_url=plot_url)
    else:
        return jsonify(success=False)

# 그래프 파일 API
@app.route('/plots/<filename>')
def get_plot(filename):
    return send_from_directory(app.config['PLOT_FOLDER'], filename)

# 함수 영역

# 허용 파일 검사 함수
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv'}

# 로그 분석 함수
def analyze_log(file_path, log_type):
    pandas2ri.activate()

    # 로그 파일을 텍스트로 읽기
    with open(file_path, 'r') as file:
        log_data = file.read().replace('\n', '\\n')

    # R 코드 준비
    r_script = f"""
    library(ggplot2)
    library(gridExtra)

    # 로그 데이터를 텍스트로 저장
    log_data <- "{log_data}"
    
    # 텍스트 데이터를 데이터 프레임으로 변환
    log_lines <- strsplit(log_data, "\\n")[[1]]
    log_df <- do.call(rbind, lapply(log_lines, function(line) {{
      pattern <- '^(\\S+) - - \\[.*\\] "(\\S+) (\\S+) .*" (\\d+) \\d+ "(\\S+)"'
      matches <- regmatches(line, regexec(pattern, line))[[1]]
      data.frame(IP=matches[2], RequestType=matches[3], RequestPath=matches[4], StatusCode=matches[5], Referrer=matches[6], stringsAsFactors=FALSE)
    }}))

    # Top 5 IP
    top_ips <- head(sort(table(log_df$IP), decreasing=TRUE), 5)
    plot_ips <- ggplot(data.frame(IP=names(top_ips), Count=as.integer(top_ips)), aes(x=reorder(IP, -Count), y=Count)) +
      geom_bar(stat="identity") +
      xlab("IP Address") + ylab("Count") +
      ggtitle("Top 5 IP Addresses")

    # Top 5 Request Types
    top_request_types <- head(sort(table(log_df$RequestType), decreasing=TRUE), 5)
    plot_request_types <- ggplot(data.frame(RequestType=names(top_request_types), Count=as.integer(top_request_types)), aes(x=reorder(RequestType, -Count), y=Count)) +
      geom_bar(stat="identity") +
      xlab("Request Type") + ylab("Count") +
      ggtitle("Top 5 Request Types")

    # Top 5 Request Paths
    top_request_paths <- head(sort(table(log_df$RequestPath), decreasing=TRUE), 5)
    plot_request_paths <- ggplot(data.frame(RequestPath=names(top_request_paths), Count=as.integer(top_request_paths)), aes(x=reorder(RequestPath, -Count), y=Count)) +
      geom_bar(stat="identity") +
      xlab("Request Path") + ylab("Count") +
      ggtitle("Top 5 Request Paths")

    # Top 5 Status Codes
    top_status_codes <- head(sort(table(log_df$StatusCode), decreasing=TRUE), 5)
    plot_status_codes <- ggplot(data.frame(StatusCode=names(top_status_codes), Count=as.integer(top_status_codes)), aes(x=reorder(StatusCode, -Count), y=Count)) +
      geom_bar(stat="identity") +
      xlab("Status Code") + ylab("Count") +
      ggtitle("Top 5 Status Codes")

    # Top 5 Referrers
    top_referrers <- head(sort(table(log_df$Referrer), decreasing=TRUE), 5)
    plot_referrers <- ggplot(data.frame(Referrer=names(top_referrers), Count=as.integer(top_referrers)), aes(x=reorder(Referrer, -Count), y=Count)) +
      geom_bar(stat="identity") +
      xlab("Referrer") + ylab("Count") +
      ggtitle("Top 5 Referrers")

    # 모든 그래프를 한 페이지에 배치
    plot_file <- tempfile(fileext = '.png')
    ggsave(plot_file, grid.arrange(plot_ips, plot_request_types, plot_request_paths, plot_status_codes, plot_referrers, ncol=2))
    plot_file
    """

    # R 코드 실행
    plot_file = robjects.r(r_script)[0]

    # 플롯 파일명을 얻기 위한 처리
    plot_filename = os.path.basename(plot_file)
    plot_target_path = os.path.join(app.config['PLOT_FOLDER'], plot_filename)
    os.rename(plot_file, plot_target_path)

    # 가상의 분석 결과 및 추천사항 생성
    result = f"로그 타입: {log_type}에 따른 분석 결과"
    recommendations = f"로그 타입: {log_type}에 따른 추천 사항"

    return result, recommendations, plot_filename

# Flask 실행 함수, 지우지 마십시오.
if __name__ == '__main__':
    app.run()