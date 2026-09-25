require("dotenv").config();
const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const { createProxyMiddleware } = require("http-proxy-middleware");

const authRoutes = require("./routes/authRoutes");
const portfolioRoutes = require("./routes/portfolioRoutes");

const app = express();
app.use(cors());
app.use(express.json());

mongoose
  .connect(process.env.MONGO_URI)
  .then(() => console.log("MongoDB Connected Successfully"))
  .catch((err) => console.error("MongoDB connection error", err));

app.use("/api/auth", authRoutes);
app.use("/api/portfolio", portfolioRoutes);
app.use(
  "/api/nifty100-performance",
  createProxyMiddleware({
    target: "http://localhost:8000",
    changeOrigin: true,
    pathRewrite: (path, req) => req.originalUrl,
  })
);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Node server is running on port ${PORT}`));
