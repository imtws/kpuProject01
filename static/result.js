document.addEventListener('DOMContentLoaded', function() {
    // Fetch results from the server
    fetch('/get_results')
        .then(response => response.json())
        .then(data => {
            const errorCodeDescriptionsDiv = document.getElementById('error_code_descriptions');
            const plotImage = document.getElementById('plot-image');
            const histogramImage = document.getElementById('hist-plot-image');
            const piePlotImage = document.getElementById('pie-plot-image');
            const resultDiv = document.getElementById('result');
            const errorMessageDiv = document.getElementById('error-message');

            if (data.success) {
                errorCodeDescriptionsDiv.innerHTML = Object.entries(data.error_code_descriptions).map(([code, desc]) => 
                    `<p><strong>${code}</strong>: ${desc.description} - ${desc.action}</p>`
                ).join('');
                plotImage.src = data.plot_url;
                histogramImage.src = data.histogram_url;
                piePlotImage.src = data.pie_plot_url;

                console.log('Plot URL:', data.plot_url);
                console.log('Histogram URL:', data.histogram_url);
                console.log('Pie Plot URL:', data.pie_plot_url);

                resultDiv.classList.remove('hidden');
                errorMessageDiv.classList.add('hidden');

                // Initially show only the first graph
                showGraph(0);
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

    const graphs = document.querySelectorAll('.graph');
    let currentGraphIndex = 0;

    document.getElementById('prev-graph').addEventListener('click', function() {
        showGraph(currentGraphIndex - 1);
    });

    document.getElementById('next-graph').addEventListener('click', function() {
        showGraph(currentGraphIndex + 1);
    });

    function showGraph(index) {
        if (index < 0 || index >= graphs.length) {
            return;
        }
        graphs[currentGraphIndex].style.display = 'none';
        graphs[index].style.display = 'block';
        currentGraphIndex = index;
    }

    // Initially hide all graphs
    graphs.forEach(graph => graph.style.display = 'none');

    // Show the first graph initially
    if (graphs.length > 0) {
        graphs[0].style.display = 'block';
    }
});
