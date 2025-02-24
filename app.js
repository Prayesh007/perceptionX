const express = require("express");
const multer = require("multer");
const fs = require("fs");
const { spawn } = require("child_process");
const cors = require("cors");
const path = require("path");
const methodOverride = require("method-override");
const ejsMate = require("ejs-mate");

const app = express();
app.use(cors());
// app.use(express.static("public"));


app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

app.use(express.urlencoded({ extended: true }));
app.use(methodOverride("_method"));

app.engine("ejs", ejsMate);

app.use(express.static(path.join(__dirname, "/public")));

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

app.get("/home", async(req, res) => {
    res.render("./perceps/index.ejs")
})

app.get("/home/detect", async (req, res) => {
    res.render("./perceps/detect.ejs")
});

app.post("/process", upload.single("file"), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
    }

    const inputPath = path.join(__dirname, "public/uploads", req.file.filename);
    const fileType = req.file.mimetype.startsWith("image") ? "image" : "video";

    // Define output file extension
    let outputExt = fileType === "image" ? ".jpg" : ".mp4"; // Processed videos as .mp4
    const outputPath = path.join(__dirname, "public/processed", req.file.filename + outputExt);

    // Run Python script
    const pythonScript = path.join(__dirname, "yolov11", "app.py");
    const pythonProcess = spawn("python", [pythonScript, inputPath, outputPath, fileType]);

    pythonProcess.stdout.on("data", (data) => {
        console.log(`Python Output: ${data}`);
    });

    pythonProcess.stderr.on("data", (data) => {
        console.error(`Python Error: ${data}`);
    });

    pythonProcess.on("close", (code) => {
        if (code === 0) {
            res.json({ filename: req.file.filename, processedFilename: req.file.filename + outputExt });
        } else {
            res.status(500).json({ error: "Processing failed" });
        }
    });
});

// Serve uploaded and processed files
app.use("/uploads", express.static("public/uploads"));
app.use("/processed", express.static("public/processed"));

app.listen(3000, () => console.log("Server running on http://localhost:3000"));
