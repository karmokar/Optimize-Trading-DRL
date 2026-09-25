const mongoose = require("mongoose");

const portfolioSchema = new mongoose.Schema({
  user: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
  date: { type: Date, default: Date.now },
  active_allocations: Object,
  cash_reserve: Number,
  pending_review: Array,
  sharpe_ratio: Number,
  sentiment_log: Array,
  performance_history: [
    {
      month: String,
      ai: Number,
      value: Number,
    },
  ],
});

module.exports = mongoose.model("Portfolio", portfolioSchema);
