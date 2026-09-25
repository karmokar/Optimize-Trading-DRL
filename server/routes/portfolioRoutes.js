const express = require('express');
const router = express.Router();
const { generatePortfolio } = require('../controllers/portfolioController');
const protect = require('../middlewares/authMiddleware');

// The 'protect' middleware ensures only logged-in users can hit this route
router.post('/run-ai', generatePortfolio);

module.exports = router;