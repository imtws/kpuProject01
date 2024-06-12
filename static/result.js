// result.js
document.addEventListener('DOMContentLoaded', function() {
    // Load data from session or API and display results
    fetch('/get_results')
        .then(response => response.json())
        .then(data => {
            const analysisResultDiv = document.getElementById('analysis-result');
            const recommendationsDiv = document.getElementById('recommendations');
            const plotImage = document.getElementById('plot-image');
            const piePlotImage = document.getElementById('pie-plot-image');
            const resultDiv = document.getElementById('result');
            const errorMessageDiv = document.getElementById('error-message');

            if (data.success) {
                analysisResultDiv.innerHTML = `<p>${data.result}</p>`;
                recommendationsDiv.innerHTML = `<p>${data.recommendations}</p>`;
                plotImage.src = data.plot_url;
                piePlotImage.src = data.pie_plot_url;
                resultDiv.classList.remove('hidden');
                errorMessageDiv.classList.add('hidden');
            } else {
                resultDiv.classList.add('hidden');
                errorMessageDiv.classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('result').classList.add('hidden');
            document.getElementById('error-message').classList.remove('hidden');
        });
});