if (process.env.NODE_ENV !== "production") {
    require("dotenv").config();
}
const express = require("express");
const mongoose = require("mongoose");
const multer = require("multer");
const File = require("./models/perceps.js");
const { spawn } = require("child_process");
const cors = require("cors");
const path = require("path");
const methodOverride = require("method-override");
const ejsMate = require("ejs-mate");
const http = require("http"); // For WebSockets
const socketIo = require("socket.io");
const fs = require("fs");
const os = require("os");

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

app.use(cors());
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.urlencoded({ extended: true }));
app.use(methodOverride("_method"));
app.engine("ejs", ejsMate);
app.use(express.static(path.join(__dirname, "/public")));

// MongoDB Connection
const dbUrl = "mongodb+srv://aitools2104:kDTRxzV6MgO4nicA@cluster0.tqkyb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&tls=true&tlsInsecure=false";
// const dbUrl = process.env.ATLASDB_URL;

mongoose.connect(dbUrl, { useNewUrlParser: true, useUnifiedTopology: true })
    .then(() => console.log("MongoDB Connected"))
    .catch(err => console.error("MongoDB Connection Failed:", err));

// Multer Configuration (Store in Memory)
const storage = multer.memoryStorage();
const upload = multer({ storage });

app.get("/", async (req, res) => {
    res.render("./perceps/index.ejs");
});

app.get("/detect", async (req, res) => {
    res.render("./perceps/detect.ejs");
});



// Upload & Process File (MongoDB Atlas)
app.post("/process", upload.single("file"), async (req, res) => {
    if (!req.file) {
        console.error("No file uploaded.");
        return res.status(400).json({ error: "No file uploaded" });
    }

    const fileType = req.file.mimetype.startsWith("image") ? "image" : "video";
    console.log("Received file of type:", fileType);

    try {
        //  Save uploaded file to MongoDB
        const newFile = new File({
            filename: req.file.originalname,
            mimetype: req.file.mimetype,
            size: req.file.size,
            data: Buffer.from(req.file.buffer),  // Ensure binary storage
            processedData: null
        });

        const savedFile = await newFile.save();
        console.log(" File successfully saved to MongoDB with ID:", savedFile._id.toString());

        //  Run Python script, passing file ID and type
        const pythonScript = path.join(__dirname, "yolov11", "app.py");
        const pythonProcess = spawn("python", [pythonScript, savedFile._id.toString(), fileType]);

        pythonProcess.stdout.on("data", (data) => {
            console.log(`Python Output: ${data.toString()}`);
            let progressMatch = data.toString().match(/Progress: (\d+)%/);
            if (progressMatch) {
                io.emit("progress", parseInt(progressMatch[1]));
            }
        });

        pythonProcess.stderr.on("data", (data) => {
            console.error(`Python Error: ${data.toString()}`);
        });

        pythonProcess.on("close", async (code) => {
            console.log("Python process closed with code:", code);
            if (code === 0) {
                io.emit("progress", 100);
                res.json({ fileId: savedFile._id });
            } else {
                console.error(" Processing failed. Python script exited with error code:", code);
                res.status(500).json({ error: "Processing failed" });
            }
        });

    } catch (error) {
        console.error("Error processing file:", error);
        res.status(500).json({ error: "Error processing file." });
    }
});

// Fetch Uploaded & Processed Files from MongoDB
app.get("/file/:id", async (req, res) => {
    try {
        const file = await File.findById(req.params.id);
        if (!file) {
            console.error(`File with ID ${req.params.id} not found.`);
            return res.status(404).json({ error: "File not found" });
        }

        console.log(` Fetching file with ID: ${req.params.id}`);
        res.set("Content-Type", file.mimetype);
        res.send(file.data);
    } catch (error) {
        console.error("Error fetching file:", error);
        res.status(500).json({ error: "Error retrieving file." });
    }
});

app.get("/file/:id/processed", async (req, res) => {
    try {
        const file = await File.findById(req.params.id);
        if (!file || !file.processedData) {
            console.error(`Processed file not found for ID: ${req.params.id}`);
            return res.status(404).json({ error: "Processed file not found" });
        }

        //  Check if file is a video or image
        if (file.mimetype.startsWith("video")) {
            console.log(` Sending processed video file for ID: ${req.params.id}`);
            res.set("Content-Type", file.mimetype);
            res.send(file.processedData);
        } else if (file.mimetype.startsWith("image")) {
            console.log(` Sending processed image file for ID: ${req.params.id}`);
            res.set("Content-Type", "image/jpeg");
            res.send(file.processedData);
        } else {
            console.error(`Unsupported file type for ID: ${req.params.id}`);
            res.status(400).json({ error: "Unsupported file type" });
        }
    } catch (error) {
        console.error("Error retrieving processed file:", error);
        res.status(500).json({ error: "Error retrieving file." });
    }
});

server.listen(3000, () => {
    console.log(" Server running on http://localhost:3000/");
});