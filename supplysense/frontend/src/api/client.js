import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

export async function sendChatMessage(message, sessionId) {
  const { data } = await apiClient.post("/chat", { message, session_id: sessionId });
  return data;
}

export async function getHealth() {
  const { data } = await apiClient.get("/health");
  return data;
}

export async function listInventory(params = {}) {
  const { data } = await apiClient.get("/inventory", { params });
  return data;
}

export async function listShipments(params = {}) {
  const { data } = await apiClient.get("/shipments", { params });
  return data;
}

export async function listRisks(limit = 50) {
  const { data } = await apiClient.get("/risks", { params: { limit } });
  return data;
}

export async function listRecommendations(limit = 50) {
  const { data } = await apiClient.get("/recommendations", { params: { limit } });
  return data;
}

export async function listReports(limit = 20) {
  const { data } = await apiClient.get("/reports", { params: { limit } });
  return data;
}

export function reportPdfUrl(reportId) {
  return `${API_BASE_URL}/reports/${reportId}/pdf`;
}

export async function downloadReport(reportId) {
  try {
    const response = await apiClient.get(`/reports/${reportId}/pdf`, {
      responseType: "blob",
    });

    const blob = new Blob([response.data], {
      type: "application/pdf",
    });

    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `report-${reportId}.pdf`;

    document.body.appendChild(link);
    link.click();

    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Failed to download report", err);
    alert("Unable to download report.");
  }
}

export async function searchKnowledge(q, topK = 5) {
  const { data } = await apiClient.get("/knowledge/search", { params: { q, top_k: topK } });
  return data;
}
