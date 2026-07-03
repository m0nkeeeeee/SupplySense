import { jsPDF } from "jspdf";

export function generateConversationPdf(messages) {
  try {
    if (!messages || messages.length === 0) {
      alert("No messages to export. Ask a question first.");
      return;
    }

    const doc = new jsPDF();
    const pageHeight = doc.internal.pageSize.height;
    const pageWidth = doc.internal.pageSize.width;
    const margin = 15;
    const contentWidth = pageWidth - margin * 2;
    let y = margin;

    function checkPageBreak(requiredHeight = 20) {
      if (y + requiredHeight > pageHeight - margin) {
        doc.addPage();
        y = margin;
      }
    }

    function addText(text, size = 10, style = "normal", color = [0, 0, 0], lineGap = 4) {
      doc.setFont("helvetica", style);
      doc.setFontSize(size);
      doc.setTextColor(color[0], color[1], color[2]);

      const lines = doc.splitTextToSize(String(text), contentWidth);
      lines.forEach((line) => {
        checkPageBreak(size + lineGap);
        doc.text(line, margin, y);
        y += lineGap;
      });
      y += lineGap;
    }

    // Title page
    addText("SupplySense Agent Network", 18, "bold", [0, 110, 150], 7);
    addText("Executive Report", 14, "bold", [80, 80, 80], 6);
    addText(new Date().toLocaleString(), 9, "normal", [120, 120, 120], 5);

    y += 5;
    doc.setDrawColor(0, 110, 150);
    doc.setLineWidth(1);
    doc.line(margin, y, pageWidth - margin, y);
    y += 10;

    const questionCount = messages.filter((m) => m.role === "user").length;
    const responseCount = messages.filter((m) => m.role === "assistant").length;
    const recommendationCount = messages.reduce(
      (sum, m) => sum + (m.recommendations?.length || 0),
      0
    );
    const riskCount = messages.reduce((sum, m) => sum + (m.risk_events?.length || 0), 0);

    addText(`Questions: ${questionCount}`, 11, "bold", [0, 0, 0], 6);
    addText(`Responses: ${responseCount}`, 11, "bold", [0, 0, 0], 6);
    addText(`Recommendations: ${recommendationCount}`, 11, "bold", [0, 0, 0], 6);
    addText(`Risks: ${riskCount}`, 11, "bold", [0, 0, 0], 6);

    addText("Executive Summary", 12, "bold", [0, 110, 150], 6);
    addText(
      `This report summarizes the Agent Network conversation history, including total questions, answers, recommendations and risk events. The following pages provide the full conversation log and key findings extracted from the agent responses.`,
      10,
      "normal",
      [50, 50, 50],
      5
    );

    // New page for details
    doc.addPage();
    y = margin;

    addText("Conversation Log", 14, "bold", [0, 110, 150], 7);
    doc.setDrawColor(150, 150, 150);
    doc.setLineWidth(0.5);
    doc.line(margin, y - 2, pageWidth - margin, y - 2);
    y += 8;

    messages.forEach((msg, index) => {
      if (msg.role === "user") {
        addText(`Question ${Math.floor(index / 2) + 1}: ${msg.content}`, 11, "bold", [0, 80, 0], 6);
      } else {
        addText("Answer:", 11, "bold", [0, 110, 150], 6);
        if (msg.answer) {
          addText(msg.answer, 10, "normal", [30, 30, 30], 5);
        }

        if (msg.plan?.length > 0) {
          addText(`Agents: ${msg.plan.join(" → ")}`, 9, "normal", [90, 90, 90], 5);
        }

        if (msg.recommendations?.length > 0) {
          addText(`Recommendations (${msg.recommendations.length}):`, 9, "bold", [0, 110, 0], 5);
          msg.recommendations.forEach((rec) => {
            addText(`- ${rec.title}: ${rec.rationale}`, 9, "normal", [50, 50, 50], 5);
          });
        }

        if (msg.risk_events?.length > 0) {
          addText(`Risk Events (${msg.risk_events.length}):`, 9, "bold", [150, 0, 0], 5);
          msg.risk_events.forEach((risk) => {
            addText(`- ${risk.title} (${risk.severity})`, 9, "normal", [50, 50, 50], 5);
          });
        }

        y += 5;
        doc.setDrawColor(200, 200, 200);
        doc.line(margin, y, pageWidth - margin, y);
        y += 8;
      }
    });

    const totalPages = doc.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      doc.setFontSize(7);
      doc.setTextColor(150, 150, 150);
      doc.text(`Page ${i} of ${totalPages}`, margin, pageHeight - 10);
      doc.text("SupplySense Agent Network", margin + 40, pageHeight - 10);
    }

    const timestamp = new Date().toISOString().split("T")[0];
    doc.save(`SupplySense-Report-${timestamp}.pdf`);
  } catch (error) {
    console.error("PDF generation error:", error);
    alert("Failed to generate PDF: " + error.message);
  }
}
