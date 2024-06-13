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

error_code_descriptions = {
    '302': {
        'description': '사용자가 요청한 리소스가 일시적으로 다른 URL로 이동되었을 때 발생합니다.',
        'action': '서버 내 리다이렉션 설정을 확인해보는 것이 좋습니다.'
    },
    '404': {
        'description': '요청한 페이지를 찾을 수 없습니다.',
        'action': 'URL이 정확한지 확인하고, 필요한 경우 서버 설정을 수정합니다.'
    },
    '500': {
        'description': '서버 내부 오류가 발생했습니다.',
        'action': '서버 로그를 확인하고, 코드나 서버 설정을 점검합니다.'
    }
    # 추가적인 에러 코드 설명을 여기에 추가할 수 있습니다.
}

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify(success=False, message='No file part')

    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, message='No selected file')

    if file:
        df = pd.read_csv(file)
        if 'Code' not in df.columns:
            return jsonify(success=False, message='No Code column in CSV')

        most_common_code = df['Code'].value_counts().idxmax()
        description = error_code_descriptions.get(str(most_common_code), {}).get('description', 'No description available')
        action = error_code_descriptions.get(str(most_common_code), {}).get('action', 'No action available')

        result = f"현재 {most_common_code} 에러 코드가 가장 많이 조회되었으며, 해당 코드는 {description}"
        recommendations = f"조치 방법으로는 {action}"

        return jsonify(success=True, result=result, error_code_description=description, recommendations=recommendations, plot_url='plot.png', histogram_url='histogram.png', pie_plot_url='pie_plot.png')

    return jsonify(success=False, message='File processing error')

# 메인 페이지
@app.route('/')
def index():
    result = session.get('result')
    recommendations = session.get('recommendations')
    plot_url = session.get('plot_url')
    pie_plot_url = session.get('pie_plot_url')
    histogram_url = session.get('histogram_url')
    return render_template('index.html', result=result, recommendations=recommendations, plot_url=plot_url, pie_plot_url=pie_plot_url)

# 로그 타입 선택 페이지
@app.route('/log_type_selection')
def log_type_selection():
    result = session.get('result')
    recommendations = session.get('recommendations')
    plot_url = session.get('plot_url')
    pie_plot_url = session.get('pie_plot_url')
    histogram_url = session.get('histogram_url')
    return render_template('log_type_selection.html', result=result, recommendations=recommendations, plot_url=plot_url, pie_plot_url=pie_plot_url)

# 결과 페이지
@app.route('/result')
def show_result():
    result = session.get('result')
    recommendations = session.get('recommendations')
    plot_url = session.get('plot_url')
    pie_plot_url = session.get('pie_plot_url')
    histogram_url = session.get('histogram_url')
    return render_template('result.html', result=result, recommendations=recommendations, plot_url=plot_url, pie_plot_url=pie_plot_url, histogram_url=histogram_url)

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
        return jsonify(success=False, error="No log file found in session")
    
    log_type = request.form.get('log-type')
    if not log_type:
        return jsonify(success=False, error="No log type provided")
    
    error_code_info, plot_filename, pie_filename, hist_filename = analyze_log(log_file_path, log_type)
    
    if error_code_info and plot_filename and pie_filename and hist_filename:
        plot_url = f'/plots/{plot_filename}'
        pie_plot_url = f'/plots/{pie_filename}'
        histogram_url = f'/plots/{hist_filename}'
        session['error_code_info'] = error_code_info
        session['plot_url'] = plot_url
        session['pie_plot_url'] = pie_plot_url
        session['histogram_url'] = histogram_url
        return jsonify(success=True, plot_url=plot_url, pie_plot_url=pie_plot_url, histogram_url=histogram_url)
    else:
        return jsonify(success=False, error="Analysis failed")

# 로그 분석 결과 조회 API
@app.route('/get_results', methods=['GET'])
def get_results():
    error_code_info = session.get('error_code_info')
    plot_url = session.get('plot_url')
    pie_plot_url = session.get('pie_plot_url')
    histogram_url = session.get('histogram_url')  
    
    if error_code_info and plot_url and pie_plot_url and histogram_url:
        return jsonify(success=True, error_code_info=error_code_info, plot_url=plot_url, pie_plot_url=pie_plot_url, histogram_url=histogram_url)
    else:
        return jsonify(success=False)


# 그래프 파일 API
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

    # 가장 많이 조회된 Code 값을 추출
    most_common_code = int(df['Code'].value_counts().idxmax())

    # R 라이브러리 및 함수 임포트
    ggplot2 = importr('ggplot2')
    dplyr = importr('dplyr')

    # 예제 데이터 프레임
    robjects.globalenv['df'] = r_df

    # R 코드로 ggplot2 그래프 생성
    r_plot_code = f"""
    library(ggplot2)
    plot <- ggplot(df, aes(x = factor(Code, levels=c("{most_common_code}")), y = IP)) + 
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

    # 원 그래프 생성 코드
    r_pie_code = f"""
    library(dplyr)
    pie_data <- df %>% count(Code) %>% mutate(pct = n / sum(n) * 100)
    pie_plot <- ggplot(pie_data, aes(x = "", y = pct, fill = factor(Code))) +
                geom_bar(stat = "identity", width = 1) +
                coord_polar(theta = "y") +
                theme_void() +
                labs(title = 'Pie Chart of Codes')
    pie_file <- tempfile(fileext = '.png')
    ggsave(pie_file, pie_plot, width = 10, height = 6, dpi = 300)
    pie_file
    """
    # 히스토그램 생성 코드
    r_hist_code = f"""
    library(ggplot2)
    hist_plot <- ggplot(df, aes(x = factor(Code, levels=c("{most_common_code}")))) + 
                geom_histogram(stat="count", fill = 'blue', color = 'black') + 
                theme_minimal() + 
                labs(title = 'Histogram of Codes', x = 'Code', y = 'Frequency')
    hist_file <- tempfile(fileext = '.png')
    ggsave(hist_file, hist_plot, width = 10, height = 6, dpi = 300)
    hist_file
    """

    # R 코드 실행하여 플롯 파일 생성
    try:
        plot_file = robjects.r(r_plot_code)[0]
        pie_file = robjects.r(r_pie_code)[0]
        hist_file = robjects.r(r_hist_code)[0]
    except Exception as e:
        print(f"Error generating plots: {e}")
        return None, None, None

    # 플롯 파일명을 얻기 위한 처리
    plot_filename = os.path.basename(plot_file)
    pie_filename = os.path.basename(pie_file)
    hist_filename = os.path.basename(hist_file)

    plot_target_path = os.path.join(app.config['PLOT_FOLDER'], plot_filename)
    pie_target_path = os.path.join(app.config['PLOT_FOLDER'], pie_filename)
    hist_target_path = os.path.join(app.config['PLOT_FOLDER'], hist_filename)

    # 파일 복사 (shutil.copy() 사용)
    try:
        shutil.copy(plot_file, plot_target_path)
        shutil.copy(pie_file, pie_target_path)
        shutil.copy(hist_file, hist_target_path)
    except Exception as e:
        print(f"Error copying plot file: {e}")
        return None, None, None

    # 복사된 파일을 삭제
    try:
        os.remove(plot_file)
        os.remove(pie_file)
        os.remove(hist_file)
    except Exception as e:
        print(f"Error removing temporary plot file: {e}")

    # 가장 많이 발생한 에러 코드에 대한 설명과 조치 방법 가져오기
    description = error_code_descriptions.get(str(most_common_code), {}).get('description', 'No description available')
    action = error_code_descriptions.get(str(most_common_code), {}).get('action', 'No action available')
    error_code_info = {
        'code': most_common_code,
        'description': description,
        'action': action
    }

    return error_code_info, plot_filename, pie_filename, hist_filename

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv'}

@app.route('/plots/<filename>')
def get_plot(filename):
    return send_from_directory(app.config['PLOT_FOLDER'], filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if not file:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    
    try:
        df = pd.read_csv(file)
        most_queried_ip = df['IP'].value_counts().idxmax()
        ip_query_count = df['IP'].value_counts().max()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({
        "success": True,
        "most_queried_ip": most_queried_ip,
        "ip_query_count": ip_query_count
    })

#if __name__ == "__main__":
#    app.run(debug=True)

# Flask 실행 함수, 지우지 마십시오.
if __name__ == '__main__':
    app.run()