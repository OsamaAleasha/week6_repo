async function analyzeText() {
    const text = document.getElementById("text").value;
    const resultBox = document.getElementById("resultBox");
    
    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "/login";
        return;
    }

    resultBox.innerHTML = "Analyzing...";

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token // Correctly attach token
            },
            body: JSON.stringify({ text })
        });

        if (response.status === 401) {
            localStorage.removeItem("token");
            window.location.href = "/login";
            return;
        }

        const data = await response.json();

        resultBox.innerHTML = `
            <p><strong>Sentiment:</strong> ${data.sentiment}</p>
            <p><strong>Confidence:</strong> ${data.confidence}</p>
        `;

    } catch (err) {
        resultBox.innerHTML = "Error connecting to the server.";
        console.error(err);
    }
}