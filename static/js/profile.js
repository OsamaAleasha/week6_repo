async function loadProfile() {
    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "/login";
        return;
    }

    try {
        const response = await fetch("/api/profile", {
            method: "GET",
            headers: {
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();

        if (response.status === 401) {
            localStorage.removeItem("token");
            window.location.href = "/login";
            return;
        }

        document.getElementById("avatar").innerText = data.user.username[0].toUpperCase();
        document.getElementById("username").innerText = data.user.username;
        document.getElementById("email").innerText = data.user.email;
        document.getElementById("joined").innerText = data.user.joined;

        document.getElementById("total").innerText = data.stats.total;
        document.getElementById("avg_conf").innerText = data.stats.avg_conf + "%";
        document.getElementById("top_sentiment").innerText = data.stats.top_sentiment;

        const container = document.getElementById("recentActivity");
        let html = "";

        for (let i = 0; i < data.recent_activity.length; i++) {
            const activity = data.recent_activity[i];
            html += `
            <div style="padding: 10px 0; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between;">
                <span style="font-size: 14px;">
                    ${activity.text.slice(0, 40)}...
                </span>
                <span class="badge badge-${activity.label.toLowerCase()}">
                    ${activity.label}
                </span>
            </div>`;
        }
        container.innerHTML = html;

    } catch (err) {
        console.error("Failed to load profile:", err);
    }
}

loadProfile();