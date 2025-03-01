const express = require("express");
const mongoose = require("mongoose")
const multer = require("multer");
const File = require("./models/perceps.js");
const fs = require("fs");
const { spawn } = require("child_process");
const cors = require("cors");
const path = require("path");
const methodOverride = require("method-override");
const ejsMate = require("ejs-mate");
const http = require("http"); // For WebSockets
const socketIo = require("socket.io");

const app = express();
const server = http.createServer(app);
const io = socketIo(server); // Attach Socket.IO to server

app.use(cors());
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.urlencoded({ extended: true }));
app.use(methodOverride("_method"));
app.engine("ejs", ejsMate);
app.use(express.static(path.join(__dirname, "/public")));



const connectDB = async () => {
    try {
        await mongoose.connect("mongodb://127.0.0.1:27017/perceptionX", {
            useNewUrlParser: true,
            useUnifiedTopology: true,
            serverSelectionTimeoutMS: 10000, // Set timeout
        });
        console.log("✅ MongoDB Connected");
    } catch (error) {
        console.error("❌ MongoDB Connection Failed:", error);
        process.exit(1);
    }
};

connectDB();

module.exports = connectDB;




// Ensure directories exist
const ensureDir = (dir) => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
};
ensureDir("public/uploads");
ensureDir("public/processed");

// Configure multer storage
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, "public/uploads/");
    },
    filename: function (req, file, cb) {
        cb(null, Date.now() + path.extname(file.originalname)); // Keep original extension
    },
});
const upload = multer({ storage });

app.get("/home", async (req, res) => {
    res.render("./perceps/index.ejs");
});

app.get("/home/detect", async (req, res) => {
    res.render("./perceps/detect.ejs");
});

// app.post("/process", upload.single("file"), (req, res) => {
//     if (!req.file) {
//         return res.status(400).json({ error: "No file uploaded" });
//     }

//     const inputPath = path.join(__dirname, "public/uploads", req.file.filename);
//     const fileType = req.file.mimetype.startsWith("image") ? "image" : "video";

//     let outputExt = fileType === "image" ? ".jpg" : ".mp4";
//     const outputPath = path.join(__dirname, "public/processed", req.file.filename + outputExt);

//     // Run Python script
//     const pythonScript = path.join(__dirname, "yolov11", "app.py");
//     const pythonProcess = spawn("python", [pythonScript, inputPath, outputPath, fileType]);

//     pythonProcess.stdout.on("data", (data) => {
//         console.log(`Python Output: ${data}`);
//         let progressMatch = data.toString().match(/Progress: (\d+)%/);
//         if (progressMatch) {
//             let progress = parseInt(progressMatch[1]);
//             io.emit("progress", progress); // Send progress update to the client
//         }
//     });

//     pythonProcess.stderr.on("data", (data) => {
//         console.error(`Python Error: ${data}`);
//     });

//     pythonProcess.on("close", (code) => {
//         if (code === 0) {
//             io.emit("progress", 100); // Send 100% completion
//             res.json({ filename: req.file.filename, processedFilename: req.file.filename + outputExt });
//         } else {
//             res.status(500).json({ error: "Processing failed" });
//         }
//     });
// });



app.post("/process", upload.single("file"), async (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
    }

    const inputPath = path.join(__dirname, "public/uploads", req.file.filename);
    const fileType = req.file.mimetype.startsWith("image") ? "image" : "video";
    let outputExt = fileType === "image" ? ".jpg" : ".mp4";
    const outputPath = path.join(__dirname, "public/processed", req.file.filename + outputExt);

    // Run Python script
    const pythonScript = path.join(__dirname, "yolov11", "app.py");
    const pythonProcess = spawn("python", [pythonScript, inputPath, outputPath, fileType]);

    pythonProcess.stdout.on("data", (data) => {
        console.log(`Python Output: ${data}`);
        let progressMatch = data.toString().match(/Progress: (\d+)%/);
        if (progressMatch) {
            let progress = parseInt(progressMatch[1]);
            io.emit("progress", progress); // Send progress update to the client
        }
    });

    pythonProcess.stderr.on("data", (data) => {
        console.error(`Python Error: ${data}`);
    });

    pythonProcess.on("close", async (code) => {
        if (code === 0) {
            io.emit("progress", 100); // Send 100% completion
            
            // Save file details in MongoDB
            const fileData = new File({
                filename: req.file.filename,
                filepath: `/uploads/${req.file.filename}`,
                mimetype: req.file.mimetype,
                size: req.file.size,
                processedFilename: `/processed/${req.file.filename + outputExt}`,
            });

            await fileData.save();

            res.json({ filename: req.file.filename, processedFilename: req.file.filename + outputExt });
        } else {
            res.status(500).json({ error: "Processing failed" });
        }
    });
});


// Serve uploaded and processed files
app.use("/uploads", express.static("public/uploads"));
app.use("/processed", express.static("public/processed"));

server.listen(3000, () => console.log("Server running on http://localhost:3000/home"));
