const axios = require("axios");
const Portfolio = require("../models/Portfolio");

exports.generatePortfolio = async (req, res) => {
  // 1. Safely extract the ID or use the fallback FIRST
  const userId = req.user?.id || "000000000000000000000000";

  // 2. Safely log the action
  console.log(`Triggering AI for user: ${userId}`);

  try {
    const fastApiResponse = await axios.get(
      "http://localhost:8000/api/v1/generate-portfolio",
    );
    const aiData = fastApiResponse.data.data;
    const newRecord = new Portfolio({
      user: userId, // 3. Use the safe variable here
      active_allocations: aiData.active_allocations,
      cash_reserve: aiData.cash_reserve,
      pending_review: aiData.pending_review,
      performance_history: aiData.performance_history,
      sharpe_ratio:aiData.sharpe_ratio,
      sentiment_log: aiData.sentiment_log,
    });
    await newRecord.save();
    res.json({ status: "success", data: newRecord });
  } catch (error) {
    console.error("AI Engine Error:", error.message);
    res.status(500).json({ error: "Failed to connect the FastAPI Engine" });
  }
};
