const express = require('express');
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const cors = require('cors');
require('dotenv').config();
const app = express();
const port = 3002;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// MongoDB Connection
mongoose.connect(process.env.MONGODB_URI, 
    { useNewUrlParser: true, useUnifiedTopology: true })
    .then(() => console.log("Connected to MongoDB"))
    .catch(err => console.error("Could not connect to MongoDB:", err));
// Define Schema and Model
const attendanceSchema = new mongoose.Schema({
    event_name: String,
    name: String,
    Register_Date: {
        type: Date,
        default: function() {
            return new Date(); // Automatically stores the current date and time
        }
    },
    email: String,
    studentID: String,
    year: String,
    section: String,
});


const Attendance = mongoose.model('Attendance', attendanceSchema);


// API Endpoint to Save Attendance
app.post('/api/attendance', async (req, res) => {
    try {
        const attendanceData = new Attendance(req.body);
        await attendanceData.save();
        res.status(201).send({ message: "Attendance recorded successfully" });
    } catch (error) {
        res.status(500).send({ message: "Failed to record attendance", error });
    }
});

// Start Server
app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
