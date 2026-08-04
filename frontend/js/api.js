const API_URL = "http://localhost:8000";

async function api(path, options={}, redirectOnUnathorization = true) {
    console.log(1243)
    const headers = new Headers(options.headers || {});
    if(options.body) headers.set("Content-Type", "application/json");
console.log(123)
    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
        credentials: "include"
    });

    if(response.status === 401 && redirectOnUnathorization) {
        window.location.assign("/login.html")
        throw new Error("Требуется вход.")
    }
    if (response.status === 204) return null;

    const data = await response.json().catch(() => ({}));

    if(!response.ok) {
        const detail = Array.isArray(data.detail)
            ? data.detail.map((item) => item.msg).join(". ")
            : data.detail
        throw new Error(detail || "Не удалось выполнить запрос")
    }
    return data
}