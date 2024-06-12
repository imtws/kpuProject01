import os
from flask import Flask, request, jsonify, send_from_directory, session, render_template
import pandas as pd
from rpy2 import robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.conversion import localconverter
import shutil

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
    pie_plot_url = session.get('pie_plot_url')
    return render_template('index.html', result=result, recommendations=recommendations, plot_url=plot_url, pie_plot_url=pie_plot_url)

# 로그 타입 선택 페이지
@app.route('/log_type_selection')
def log_type_selection():
    result = session.get('result')
    recommendations = session.get('recommendations')
    plot_url = session.get('plot_url')
    pie_plot_url = session.get('pie_plot_url')
    return render_template('log_type_selection.html', result=result, recommendations=recommendations, plot_url=plot_url, pie_plot_url=pie_plot_url)

# 결과 페이지
@app.route('/result')
def show_result():
    result = session.get('result')
    recommendations = session.get('recommendations')
    plot_url = session.get('plot_url')
    pie_plot_url = session.get('pie_plot_url')
    return render_template('result.html', result=result, recommendations=recommendations, plot_url=plot_url, pie_plot_url=pie_plot_url)

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
    
    result, recommendations, plot_filename, pie_plot_filename = analyze_log(log_file_path, log_type)
    
    if result and recommendations and plot_filename and pie_plot_filename:
        plot_url = f'/plots/{plot_filename}'
        pie_plot_url = f'/plots/{pie_plot_filename}'
        session['result'] = result
        session['recommendations'] = recommendations
        session['plot_url'] = plot_url
        session['pie_plot_url'] = pie_plot_url
        return jsonify(success=True, plot_url=plot_url, pie_plot_url=pie_plot_url)
    else:
        return jsonify(success=False)

# 로그 분석 결과 조회 API
@app.route('/get_results', methods=['GET'])
def get_results():
    result = session.get('result')
    recommendations = session.get('recommendations')
    plot_url = session.get('plot_url')
    pie_plot_url = session.get('pie_plot_url')
    
    if result and recommendations and plot_url and pie_plot_url:
        return jsonify(success=True, result=result, recommendations=recommendations, plot_url=plot_url, pie_plot_url=pie_plot_url)
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
    
    # CSV 파일을 Pandas DataFrame으로 읽기
    df = pd.read_csv(file_path)

    try:
        # Pandas DataFrame을 R DataFrame으로 변환
        with localconverter(robjects.default_converter + pandas2ri.converter):
            r_df = robjects.conversion.py2rpy(df)
    except Exception as e:
        print(f"Error converting DataFrame to R DataFrame: {e}")
        return None, None, None, None

    # 고유한 Code 값을 추출
    unique_codes = df['Code'].unique().tolist()

    # R 라이브러리 및 함수 임포트
    ggplot2 = importr('ggplot2')
    dplyr = importr('dplyr')

    # 예제 데이터 프레임
    robjects.globalenv['df'] = r_df

    # R 코드로 ggplot2 그래프 생성
    r_plot_code = f"""
    library(ggplot2)
    plot <- ggplot(df, aes(x = factor(Code, levels=c({','.join(map(str, unique_codes))})), y = IP)) + 
            geom_point() + 
            theme(
                legend.text = element_text(size = 5),  # 범례 텍스트 크기
                legend.title = element_text(size = 5), # 범례 제목 크기
                axis.title = element_text(size = 5),   # 축 제목 크기
                axis.text = element_text(size = 5)     # 축 텍스트 크기
            ) +
            scale_x_discrete(drop=FALSE) +
            labs(x = 'Status Code')
    plot_file <- tempfile(fileext = '.png')
    ggsave(plot_file, plot, width = 10, height = 6, dpi = 300)
    plot_file
    """

    # R 코드로 ggplot2 원 그래프 및 히스토그램 생성
    r_pie_plot_code = """
    library(ggplot2)
    library(dplyr)
    pie_data <- df %>%
        count(Code) %>%
        arrange(desc(n))
        
    top_code <- head(pie_data$Code, 1)
    top_code_desc <- switch(top_code,
        "300" = "비정상적인 리다이렉트",
        "301" = "컨텐츠가 영구적으로 이동되어 발생",
        "302" = "컨텐츠가 일시적으로 이동되어 발생",
        "303" = "서버에서 GET 메소드를 처리하여 다른 URL에서 요청된 정보를 가져올 수 있도록 응답",
        "400" = "잘못된 요청을 보냈을 때 발생",
        "401" = "인증이 필요한 리소스에 잘못된 인증으로 접근 시도하였을 때 발생",
        "403" = "서버에서 요청을 거부하였을 때 발생",
        "404" = "요청한 리소스를 찾을 수 없을 때 발생",
        "408" = "요청한 시간이 기본 요청 시간보다 오래 걸릴 때 발생",
        "500" = "서버 내부적으로 시스템 상 오류가 있을 때 발생",
        "502" = "게이트웨이가 연결된 서버에서 응답을 잘못 받을 때 발생",
        "503" = "서비스를 사용할 수 없을 때 발생",
        "504" = "게이트웨이가 연결된 서버에서 응답을 가져올 수 없을 때 발생"
    )

    pie_plot <- ggplot(pie_data, aes(x = "", y = n, fill = factor(Code))) +
                geom_bar(width = 1, stat = "identity") +
                coord_polar(theta = "y") +
                geom_text(aes(label = n), position = position_stack(vjust = 0.5), size = 3, color = "white") + # 수치 표시 및 색상 변경
                theme_void() +
                theme(legend.text = element_text(size = 5), legend.title = element_text(size = 5)) +
                labs(fill = "Code")  # 범례 이름을 Code로 변경

    pie_plot_file <- tempfile(fileext = '.png')
    ggsave(pie_plot_file, pie_plot, width = 5, height = 3, dpi = 300)  # 크기와 해상도를 설정
    pie_plot_file

    # 히스토그램 생성
    hist_plot <- ggplot(df, aes(x = Code)) +
                geom_histogram(fill = "skyblue", color = "black", bins = 15) +
                labs(x = "Code", y = "Count") +
                theme_minimal()

    hist_plot_file <- tempfile(fileext = '.png')
    ggsave(hist_plot_file, hist_plot, width = 10, height = 6, dpi = 300)
    hist_plot_file
    """

    # R 코드 실행
    plot_file = robjects.r(r_plot_code)[0]
    pie_plot_file = plot_files[0]
    hist_plot_file = plot_files[1]


    # 플롯 파일명을 얻기 위한 처리
    pie_plot_filename = os.path.basename(pie_plot_file)
    pie_plot_target_path = os.path.join(app.config['PLOT_FOLDER'], pie_plot_filename)

    hist_plot_filename = os.path.basename(hist_plot_file)
    hist_plot_target_path = os.path.join(app.config['PLOT_FOLDER'], hist_plot_filename)

    # 파일 복사 (shutil.copy() 사용)
    try:
        shutil.copy(plot_file, plot_target_path)
        shutil.copy(pie_plot_file, pie_plot_target_path)
    except Exception as e:
        print(f"Error copying plot file: {e}")
        return None, None, None, None

    # 복사된 파일을 삭제
    try:
        os.remove(plot_file)
        os.remove(pie_plot_file)
    except Exception as e:
        print(f"Error removing copied plot file: {e}")

    # 가상의 분석 결과 및 추천사항 생성
    result = "Analysis result based on log type: " + log_type
    recommendations = "Recommendations based on analysis of log type: " + log_type

    return result, recommendations, plot_filename, pie_plot_filename


# Flask 실행 함수, 지우지 마십시오.
if __name__ == '__main__':
    app.run()