async function loadHistory() {
    const token = localStorage.getItem("token");

    const response = await fetch("/api/history", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
    });

    const data = await response.json();

    const tbody = document.getElementById("historyBody");

    let html = "";

    for (let i = 0; i < data.length; i++) {
        const entry = data[i];

        html += `
            <tr>
                <td>
                    <div class="text-truncate">${entry.input_text}</div>
                </td>

                <td>
                    <span class="badge badge-${entry.sentiment_label.toLowerCase()}">
                        ${entry.sentiment_label}
                    </span>
                </td>

                <td><strong>${entry.confidence_score}%</strong></td>

                <td style="color: var(--text-muted);">${new Date(entry.analysis_timestamp).toLocaleDateString()}</td>

                <td>
                    <button style="padding: 6px 12px; font-size: 12px; width: auto; margin: 0;">Details</button>
                </td>
            </tr>
        
        `;

        tbody.innerHTML = html;
    }
}

loadHistory();