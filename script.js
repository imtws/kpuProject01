function uploadFile() {
    const fileInput = document.getElementById('log-file');
    if (fileInput.files.length === 0) {
        alert('로그 파일을 선택하세요.');
        return;
    }

    const formData = new FormData();
    formData.append('log-file', fileInput.files[0]);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            window.location.href = 'log_type_selection.html';
        } else {
            alert('파일 업로드 실패. 다시 시도하세요.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('파일 업로드 중 오류 발생.');
    });
}
