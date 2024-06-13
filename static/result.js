document.addEventListener('DOMContentLoaded', function() {
    fetch('/get_results')
        .then(response => response.json())
        .then(data => {
            const errorCodeDescriptionsDiv = document.getElementById('error_code_descriptions');
            const plotImage = document.getElementById('plot-image');
            const histogramImage = document.getElementById('hist-plot-image');
            const piePlotImage = document.getElementById('pie-plot-image');
            const resultDiv = document.getElementById('result');
            const errorMessageDiv = document.getElementById('error-message');
            const mostQueriedIpDiv = document.getElementById('most_queried_ip');

            if (data.success) {
                const errorCodeInfo = data.error_code_info;

                if (errorCodeInfo) {
                    errorCodeDescriptionsDiv.innerHTML = `
                        <p><strong>${errorCodeInfo.code}</strong>: ${errorCodeInfo.description} - ${errorCodeInfo.action}</p>
                    `;
                }

                if (data.plot_url) {
                    plotImage.src = data.plot_url;
                }

                if (data.histogram_url) {
                    histogramImage.src = data.histogram_url;
                }

                if (data.pie_plot_url) {
                    piePlotImage.src = data.pie_plot_url;
                }

                if (data.most_queried_ip && data.ip_query_count !== undefined) {
                    mostQueriedIpDiv.innerHTML = `
                        <p><strong>가장 많이 조회된 IP:</strong> ${data.most_queried_ip} (${data.ip_query_count}회)</p>
                    `;
                }

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
