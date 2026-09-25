const express = require("express");
const route = express.Router();
const { registerUser } = require("../controllers/authController.js");

route.post("/register", registerUser);
module.exports = route;
