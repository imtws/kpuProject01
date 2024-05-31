document.addEventListener('DOMContentLoaded', function() {
    // Load data from session or API and display results
    fetch('/get_results')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const analysisResultDiv = document.getElementById('analysis-result');
                const recommendationsDiv = document.getElementById('recommendations');
                const plotImage = document.getElementById('plot-image');

                analysisResultDiv.innerHTML = `<p>${data.result}</p>`;
                recommendationsDiv.innerHTML = `<p>${data.recommendations}</p>`;
                plotImage.src = data.plot_url;
            } else {
                document.getElementById('result').classList.add('hidden');
                document.getElementById('error-message').classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('result').classList.add('hidden');
            document.getElementById('error-message').classList.remove('hidden');
        });
});
