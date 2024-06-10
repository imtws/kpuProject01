document.getElementById('log-type-form').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const logType = document.getElementById('log-type').value;
    const formData = new FormData();
    formData.append('log-type', logType);
    
    fetch('/analyze', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        // 응답의 content-type이 JSON인지 확인
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            return response.text().then(text => {
                throw new Error('Unexpected response type: ' + contentType + '\n' + text);
            });
        }
    })
    .then(data => {
        if (data.success) {
            displayResults(data);
            window.location.href = 'result.html';
        } else {
            alert('분석 불가: 업로드한 로그 데이터에 대해 각 셀 위치, 파일 정상 여부 등 확인 바랍니다.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('오류 발생: 분석 불가\n' + error.message);
    });
});

function displayResults(data) {
    // Store data in session or pass it to the result page somehow
}
