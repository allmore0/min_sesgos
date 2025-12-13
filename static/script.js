document.getElementById('candidateForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    // Show Loading
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';

    // Construct JSON
    const getData = (selector) => {
        const inputs = document.querySelectorAll(selector);
        const obj = {};
        inputs.forEach(input => {
            obj[input.name] = input.value;
        });
        return obj;
    };

    const datos_personales = getData('.dp');
    const datos_laborales_raw = getData('.dl');
    const porcentajes_conocimiento = getData('.pc');

    // Handle Lists
    const habilidades = [];
    if (document.getElementById('hab1_name').value) habilidades.push({ nombre: document.getElementById('hab1_name').value, nivel: "Alto" });
    if (document.getElementById('hab2_name').value) habilidades.push({ nombre: document.getElementById('hab2_name').value, nivel: "Medio" });

    const certificaciones = [];
    if (document.getElementById('cert1').value) certificaciones.push(document.getElementById('cert1').value);
    if (document.getElementById('cert2').value) certificaciones.push(document.getElementById('cert2').value);

    const payload = {
        datos_personales: datos_personales,
        datos_laborales_y_habilidades: {
            ...datos_laborales_raw,
            habilidades: habilidades,
            certificaciones: certificaciones
        },
        porcentajes_conocimiento: porcentajes_conocimiento
    };

    try {
        const response = await fetch('/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.status === 'success') {
            displayResults(data.results, data.id);
        } else {
            alert('Error: ' + data.message);
        }
    } catch (err) {
        console.error(err);
        alert('Error de conexión.');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
});

let currentResults = null;

function displayResults(results, newId) {
    currentResults = results;
    const container = document.getElementById('results');
    const isRecruiter = document.getElementById('userRoleToggle').checked;

    renderView(isRecruiter);
    container.style.display = 'block';

    // Scroll to results
    container.scrollIntoView({ behavior: 'smooth' });
}

document.getElementById('userRoleToggle').addEventListener('change', (e) => {
    if (currentResults) {
        renderView(e.target.checked);
    }
});

function renderView(isRecruiter) {
    const container = document.getElementById('results');
    const r = currentResults;
    const myScore = r.current_candidate.score.toFixed(4);
    const bestScore = r.best_candidate.score.toFixed(4);
    const isBest = r.current_candidate.is_best;

    let html = `
        <div class="score-card">
            <h3>Tu Resultado Final</h3>
            <div class="score-display">${myScore}</div>
            <p>ID Asignado: <strong>${r.current_candidate.is_best ? 'WINNER-ID' : ''} ${r.best_candidate.id === r.current_candidate.id ? r.best_candidate.id : '...'}</strong> (Internal Use)</p>
        </div>
    `;

    if (isBest) {
        html += `
            <div style="background: rgba(0,255,100,0.2); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h2>🎉 ¡Felicidades! 🎉</h2>
                <p>Obtuviste la <strong>Mejor Puntuación</strong> de todos los candidatos.</p>
            </div>
        `;
    } else {
        html += `
             <div style="background: rgba(255,100,100,0.2); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h2>Gracias por Participar</h2>
                <p>No obtuviste la mejor puntuación en esta ocasión.</p>
                ${isRecruiter ? `<p>Mejor Puntuación Actual: <strong>${bestScore}</strong> (${r.best_candidate.name})</p>` : ''}
            </div>
        `;
    }

    if (isRecruiter) {
        html += `
            <h3>Resumen de Eliminación de Sesgos (Top 10 vs Total)</h3>
            <p style="font-size: 0.9em; color: var(--text-muted)">Comparativa de distribución porcentual para detectar anomalías.</p>
        `;

        for (const [colName, rows] of Object.entries(r.bias_summary)) {
            html += `<h4>${colName}</h4>`;
            html += `<table class="bias-table">
                <thead>
                    <tr>
                        <th>Categoría</th>
                        <th>Población Total (%)</th>
                        <th>Top 10 (%)</th>
                        <th>Diferencia (%)</th>
                    </tr>
                </thead>
                <tbody>`;

            rows.forEach(row => {
                const color = Math.abs(row.difference) > 10 ? '#ff4d4d' : '#4dff4d';
                html += `
                    <tr>
                        <td>${row.category}</td>
                        <td>${row.population}</td>
                        <td>${row.top_selected}</td>
                        <td style="color:${color}">${row.difference > 0 ? '+' : ''}${row.difference}</td>
                    </tr>
                `;
            });
            html += `</tbody></table>`;
        }
    }

    container.innerHTML = html;
}
